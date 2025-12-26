"""API routes for background job management."""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from datetime import datetime

from src.db.sqlite_repository import get_repository
from src.db.models import MarketDB

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


# ==================== Models ====================


class JobCreate(BaseModel):
    """Request to create a new job."""
    job_type: str
    payload: dict = {}
    priority: int = 0


class JobResponse(BaseModel):
    """Job status response."""
    id: str
    job_type: str
    payload: dict
    priority: int
    status: str
    progress: int
    message: Optional[str]
    error: Optional[str]
    result: Optional[dict]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    attempts: int
    max_attempts: int


class JobStatsResponse(BaseModel):
    """Job queue statistics."""
    pending: int
    running: int
    completed: int
    failed: int
    total: int


class EnqueueMarketsRequest(BaseModel):
    """Request to enqueue market enrichment jobs."""
    market_ids: Optional[List[str]] = None  # If None, enqueue all saved markets
    favorites_only: bool = False


class EnqueueMarketsResponse(BaseModel):
    """Response from enqueueing market jobs."""
    jobs_created: int
    job_ids: List[str]


class EnqueuePropertyRequest(BaseModel):
    """Request to create a property and enqueue enrichment job."""
    # Property location
    address: str
    city: str
    state: str
    zip_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    # Property details
    list_price: float
    bedrooms: Optional[int] = 3
    bathrooms: Optional[float] = 2.0
    sqft: Optional[int] = None
    property_type: str = "single_family"

    # Source info
    source: str = "manual"
    source_url: Optional[str] = None
    photos: Optional[List[str]] = None

    # Financing params for analysis
    down_payment_pct: float = 0.25
    interest_rate: float = 0.07


class EnqueuePropertyResponse(BaseModel):
    """Response from property enrichment job creation."""
    property_id: str
    job_id: str
    status: str
    message: str


# ==================== Helper ====================


def job_to_response(job) -> JobResponse:
    """Convert JobDB to JobResponse."""
    return JobResponse(
        id=job.id,
        job_type=job.job_type,
        payload=job.payload or {},
        priority=job.priority or 0,
        status=job.status,
        progress=job.progress or 0,
        message=job.message,
        error=job.error,
        result=job.result,
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
        attempts=job.attempts or 0,
        max_attempts=job.max_attempts or 3,
    )


# ==================== Routes ====================


@router.post("", response_model=JobResponse)
async def create_job(request: JobCreate):
    """
    Create a new background job.

    Job types:
    - enrich_market: Enrich a single market with data from all sources
      payload: {"market_id": "phoenix_az"}
    - enrich_property: Enrich a property with location data
      payload: {"property_id": "abc123"}
    """
    repo = get_repository()

    # Validate job type
    valid_types = ["enrich_market", "enrich_property"]
    if request.job_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid job type. Valid types: {valid_types}"
        )

    job = repo.enqueue_job(
        job_type=request.job_type,
        payload=request.payload,
        priority=request.priority,
    )

    return job_to_response(job)


@router.post("/enqueue-markets", response_model=EnqueueMarketsResponse)
async def enqueue_market_jobs(request: EnqueueMarketsRequest):
    """
    Enqueue enrichment jobs for multiple markets.

    If market_ids is provided, enqueues jobs for those specific markets.
    If market_ids is None and favorites_only is True, enqueues for all favorite markets.
    If both are empty, enqueues for ALL saved markets.

    Skips markets that already have pending/running jobs to prevent duplicates.
    """
    repo = get_repository()

    # Determine which markets to enrich
    if request.market_ids:
        # Specific markets
        market_ids = request.market_ids
    elif request.favorites_only:
        # All favorites
        markets = repo.get_favorite_markets()
        market_ids = [m.id for m in markets]
    else:
        # All markets
        markets = repo.get_supported_markets()
        market_ids = [m.id for m in markets]

    # Get markets that already have pending/running jobs
    existing_jobs = repo.get_jobs(job_type="enrich_market", limit=500)
    markets_with_jobs = {
        j.payload.get("market_id")
        for j in existing_jobs
        if j.status in ("pending", "running")
    }

    # Create jobs only for markets without existing jobs
    job_ids = []
    for market_id in market_ids:
        if market_id in markets_with_jobs:
            continue  # Skip - already has a pending/running job
        job = repo.enqueue_job(
            job_type="enrich_market",
            payload={"market_id": market_id},
            priority=0,
        )
        job_ids.append(job.id)

    return EnqueueMarketsResponse(
        jobs_created=len(job_ids),
        job_ids=job_ids,
    )


@router.post("/enqueue-property", response_model=EnqueuePropertyResponse)
async def enqueue_property_job(request: EnqueuePropertyRequest):
    """
    Create a property record and enqueue enrichment job.

    If property already exists (by source_url or address+city+state), returns
    the existing property. Otherwise creates a new SavedPropertyDB record with
    basic data and pipeline_status="analyzing", then enqueues an enrich_property job.

    The job ID can be polled to check progress. When complete, the property
    will have pipeline_status="analyzed" with all enrichment data.
    """
    from src.db.models import SavedPropertyDB
    import uuid

    repo = get_repository()

    # Check if property already exists
    existing_property = None

    # First try to find by source_url (most reliable)
    if request.source_url:
        existing_property = repo.session.query(SavedPropertyDB).filter_by(
            source_url=request.source_url
        ).first()

    # If not found, try by address + city + state
    if not existing_property:
        existing_property = repo.session.query(SavedPropertyDB).filter_by(
            address=request.address,
            city=request.city,
            state=request.state,
        ).first()

    # If property exists and is already analyzed, return it without creating a new job
    if existing_property:
        if existing_property.pipeline_status == "analyzed":
            return EnqueuePropertyResponse(
                property_id=existing_property.id,
                job_id="",  # No job needed
                status="already_analyzed",
                message=f"Property already analyzed: {request.address}",
            )

        # If property exists but still analyzing, check for existing job
        existing_jobs = repo.get_jobs(job_type="enrich_property", limit=100)
        for job in existing_jobs:
            if job.payload.get("property_id") == existing_property.id and job.status in ("pending", "running"):
                return EnqueuePropertyResponse(
                    property_id=existing_property.id,
                    job_id=job.id,
                    status=job.status,
                    message=f"Property enrichment already in progress: {request.address}",
                )

        # Property exists but not analyzed and no running job - enqueue a new job
        property_id = existing_property.id
    else:
        # Create new property record
        property_id = str(uuid.uuid4())

        new_property = SavedPropertyDB(
            id=property_id,
            address=request.address,
            city=request.city,
            state=request.state,
            zip_code=request.zip_code,
            latitude=request.latitude,
            longitude=request.longitude,
            list_price=request.list_price,
            bedrooms=request.bedrooms,
            bathrooms=request.bathrooms,
            sqft=request.sqft,
            property_type=request.property_type,
            source=request.source,
            source_url=request.source_url,
            photos=request.photos,
            pipeline_status="analyzing",  # Will be updated to "analyzed" by job
        )

        repo.session.add(new_property)
        repo.session.commit()

    # Enqueue enrichment job
    job = repo.enqueue_job(
        job_type="enrich_property",
        payload={
            "property_id": property_id,
            "down_payment_pct": request.down_payment_pct,
            "interest_rate": request.interest_rate,
        },
        priority=1,  # Higher priority than market jobs
    )

    return EnqueuePropertyResponse(
        property_id=property_id,
        job_id=job.id,
        status="pending",
        message=f"Property created and enrichment job queued for {request.address}",
    )


@router.get("", response_model=List[JobResponse])
async def list_jobs(
    status: Optional[str] = Query(None, description="Filter by status"),
    job_type: Optional[str] = Query(None, description="Filter by job type"),
    limit: int = Query(50, ge=1, le=200),
):
    """List jobs with optional filters."""
    repo = get_repository()
    jobs = repo.get_jobs(status=status, job_type=job_type, limit=limit)
    return [job_to_response(j) for j in jobs]


@router.get("/stats", response_model=JobStatsResponse)
async def get_job_stats():
    """Get job queue statistics."""
    repo = get_repository()
    return repo.get_job_stats()


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: str):
    """Get a specific job by ID."""
    repo = get_repository()
    job = repo.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job_to_response(job)


@router.post("/{job_id}/cancel", response_model=JobResponse)
async def cancel_job(job_id: str):
    """Cancel a pending job."""
    repo = get_repository()
    job = repo.cancel_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found or not pending")
    return job_to_response(job)


@router.post("/cancel-by-type/{job_type}")
async def cancel_jobs_by_type(job_type: str):
    """Cancel all pending jobs of a given type."""
    repo = get_repository()
    cancelled = repo.cancel_jobs_by_type(job_type)
    return {"cancelled": cancelled}


@router.delete("/cleanup")
async def cleanup_old_jobs(days: int = Query(7, ge=1, le=30)):
    """Delete completed/failed jobs older than N days."""
    repo = get_repository()
    deleted = repo.cleanup_old_jobs(days=days)
    return {"deleted": deleted}


@router.post("/process")
async def process_pending_jobs(limit: int = Query(10, ge=1, le=50)):
    """
    Process pending jobs. Designed for serverless/cron invocation.

    This endpoint processes up to `limit` pending jobs and returns.
    Call via Vercel Cron or similar scheduler.

    Returns the number of jobs processed and their results.
    """
    from api.jobs.worker import JobWorker

    worker = JobWorker()
    results = []
    processed = 0

    repo = get_repository()

    # Clean up any stuck jobs before processing new ones
    stuck_failed = repo.fail_stuck_jobs(timeout_minutes=10)
    if stuck_failed > 0:
        print(f"[Jobs] Marked {stuck_failed} stuck job(s) as failed")

    for _ in range(limit):
        job = repo.get_pending_job()
        if not job:
            break  # No more pending jobs

        await worker.process_next_job()
        processed += 1

        # Get updated job status
        updated_job = repo.get_job(job.id)
        results.append({
            "job_id": job.id,
            "job_type": job.job_type,
            "status": updated_job.status if updated_job else "unknown",
            "message": updated_job.message if updated_job else None,
        })

    return {
        "processed": processed,
        "results": results,
    }
