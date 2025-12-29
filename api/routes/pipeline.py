"""
Pipeline API routes.

Phase 5.4: Offers & Pipeline
- Offer management (create, track, counter)
- Deal stages for properties
- Due diligence checklists
- Pipeline overview
"""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from src.db.models import (
    OfferDB, SavedPropertyDB, get_session, get_engine
)

router = APIRouter()


# ==================== Deal Stage Constants ====================

DEAL_STAGES = [
    {"id": "researching", "name": "Researching", "order": 1},
    {"id": "contacted", "name": "Contacted", "order": 2},
    {"id": "viewing", "name": "Viewing Scheduled", "order": 3},
    {"id": "analyzing", "name": "Analyzing", "order": 4},
    {"id": "offer_prep", "name": "Preparing Offer", "order": 5},
    {"id": "offer_submitted", "name": "Offer Submitted", "order": 6},
    {"id": "negotiating", "name": "Negotiating", "order": 7},
    {"id": "under_contract", "name": "Under Contract", "order": 8},
    {"id": "due_diligence", "name": "Due Diligence", "order": 9},
    {"id": "closing", "name": "Closing", "order": 10},
    {"id": "closed", "name": "Closed", "order": 11},
    {"id": "lost", "name": "Lost/Passed", "order": 99},
]

DUE_DILIGENCE_ITEMS = [
    {"id": "inspection", "name": "Property Inspection", "category": "inspection"},
    {"id": "appraisal", "name": "Appraisal", "category": "financing"},
    {"id": "title_search", "name": "Title Search", "category": "title"},
    {"id": "title_insurance", "name": "Title Insurance", "category": "title"},
    {"id": "survey", "name": "Property Survey", "category": "inspection"},
    {"id": "insurance_quote", "name": "Insurance Quote", "category": "insurance"},
    {"id": "rent_roll", "name": "Verify Rent Roll", "category": "income"},
    {"id": "lease_review", "name": "Review Leases", "category": "income"},
    {"id": "utility_bills", "name": "Review Utility Bills", "category": "expenses"},
    {"id": "tax_records", "name": "Verify Tax Records", "category": "expenses"},
    {"id": "hoa_docs", "name": "HOA Documents", "category": "legal"},
    {"id": "permits", "name": "Verify Permits", "category": "legal"},
    {"id": "final_walkthrough", "name": "Final Walkthrough", "category": "closing"},
    {"id": "loan_approval", "name": "Final Loan Approval", "category": "financing"},
]


# ==================== Offer Models ====================

class OfferBase(BaseModel):
    """Base offer fields."""
    offer_price: float
    down_payment_pct: float = 0.25
    financing_type: Optional[str] = None  # conventional, dscr, cash, etc.
    earnest_money: Optional[float] = None
    contingencies: List[str] = ["inspection", "financing", "appraisal"]
    inspection_days: Optional[int] = 10
    financing_days: Optional[int] = 21
    closing_days: Optional[int] = 30


class OfferCreate(OfferBase):
    """Create a new offer."""
    property_id: str


class OfferUpdate(BaseModel):
    """Update offer fields (all optional)."""
    offer_price: Optional[float] = None
    down_payment_pct: Optional[float] = None
    financing_type: Optional[str] = None
    earnest_money: Optional[float] = None
    contingencies: Optional[List[str]] = None
    inspection_days: Optional[int] = None
    financing_days: Optional[int] = None
    closing_days: Optional[int] = None
    status: Optional[str] = None
    expires_at: Optional[datetime] = None
    response_deadline: Optional[datetime] = None
    final_price: Optional[float] = None
    outcome_notes: Optional[str] = None


class CounterOfferRequest(BaseModel):
    """Log a counter offer."""
    counter_price: float
    notes: Optional[str] = None


class OfferResponse(OfferBase):
    """Offer response."""
    id: str
    property_id: str
    status: str
    submitted_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    response_deadline: Optional[datetime] = None
    counter_history: List[dict]
    final_price: Optional[float] = None
    outcome_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== Pipeline Models ====================

class DealStageUpdate(BaseModel):
    """Update deal stage for a property."""
    stage: str
    notes: Optional[str] = None


class DueDiligenceUpdate(BaseModel):
    """Update due diligence checklist."""
    item_id: str
    completed: bool
    notes: Optional[str] = None
    completed_date: Optional[datetime] = None


class PipelineProperty(BaseModel):
    """Property in pipeline view."""
    id: str
    address: str
    city: str
    state: str
    list_price: Optional[float] = None
    estimated_rent: Optional[float] = None
    deal_stage: Optional[str] = None
    deal_score: Optional[float] = None
    days_in_stage: Optional[int] = None
    has_active_offer: bool = False
    primary_photo: Optional[str] = None


class PipelineOverview(BaseModel):
    """Pipeline overview response."""
    stages: List[dict]
    properties_by_stage: dict
    total_properties: int
    active_offers: int
    under_contract: int


# ==================== Offer Routes ====================

@router.get("/offers", response_model=List[OfferResponse])
async def get_offers(
    property_id: Optional[str] = None,
    status: Optional[str] = None,
):
    """Get all offers with optional filtering."""
    session = get_session(get_engine())
    try:
        query = session.query(OfferDB)

        if property_id:
            query = query.filter(OfferDB.property_id == property_id)

        if status:
            query = query.filter(OfferDB.status == status)

        offers = query.order_by(OfferDB.created_at.desc()).all()
        return [OfferResponse.model_validate(o) for o in offers]
    finally:
        session.close()


@router.get("/offers/{offer_id}", response_model=OfferResponse)
async def get_offer(offer_id: str):
    """Get a specific offer."""
    session = get_session(get_engine())
    try:
        offer = session.query(OfferDB).filter(OfferDB.id == offer_id).first()
        if not offer:
            raise HTTPException(status_code=404, detail="Offer not found")
        return OfferResponse.model_validate(offer)
    finally:
        session.close()


@router.post("/offers", response_model=OfferResponse)
async def create_offer(data: OfferCreate):
    """Create a new offer."""
    session = get_session(get_engine())
    try:
        offer = OfferDB(
            property_id=data.property_id,
            offer_price=data.offer_price,
            down_payment_pct=data.down_payment_pct,
            financing_type=data.financing_type,
            earnest_money=data.earnest_money,
            contingencies=data.contingencies,
            inspection_days=data.inspection_days,
            financing_days=data.financing_days,
            closing_days=data.closing_days,
            counter_history=[],
        )
        session.add(offer)
        session.commit()
        session.refresh(offer)
        return OfferResponse.model_validate(offer)
    finally:
        session.close()


@router.patch("/offers/{offer_id}", response_model=OfferResponse)
async def update_offer(offer_id: str, data: OfferUpdate):
    """Update an offer."""
    session = get_session(get_engine())
    try:
        offer = session.query(OfferDB).filter(OfferDB.id == offer_id).first()
        if not offer:
            raise HTTPException(status_code=404, detail="Offer not found")

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(offer, key, value)

        offer.updated_at = datetime.utcnow()
        session.commit()
        session.refresh(offer)
        return OfferResponse.model_validate(offer)
    finally:
        session.close()


@router.post("/offers/{offer_id}/submit", response_model=OfferResponse)
async def submit_offer(offer_id: str):
    """Mark an offer as submitted."""
    session = get_session(get_engine())
    try:
        offer = session.query(OfferDB).filter(OfferDB.id == offer_id).first()
        if not offer:
            raise HTTPException(status_code=404, detail="Offer not found")

        offer.status = "submitted"
        offer.submitted_at = datetime.utcnow()
        offer.updated_at = datetime.utcnow()
        session.commit()
        session.refresh(offer)
        return OfferResponse.model_validate(offer)
    finally:
        session.close()


@router.post("/offers/{offer_id}/counter", response_model=OfferResponse)
async def log_counter_offer(offer_id: str, data: CounterOfferRequest):
    """Log a counter offer from the seller."""
    session = get_session(get_engine())
    try:
        offer = session.query(OfferDB).filter(OfferDB.id == offer_id).first()
        if not offer:
            raise HTTPException(status_code=404, detail="Offer not found")

        # Add to counter history
        counter_entry = {
            "price": data.counter_price,
            "date": datetime.utcnow().isoformat(),
            "notes": data.notes,
        }
        history = offer.counter_history or []
        history.append(counter_entry)
        offer.counter_history = history

        offer.status = "countered"
        offer.updated_at = datetime.utcnow()
        session.commit()
        session.refresh(offer)
        return OfferResponse.model_validate(offer)
    finally:
        session.close()


@router.post("/offers/{offer_id}/accept", response_model=OfferResponse)
async def accept_offer(offer_id: str, final_price: Optional[float] = None):
    """Mark an offer as accepted."""
    session = get_session(get_engine())
    try:
        offer = session.query(OfferDB).filter(OfferDB.id == offer_id).first()
        if not offer:
            raise HTTPException(status_code=404, detail="Offer not found")

        offer.status = "accepted"
        offer.final_price = final_price or offer.offer_price
        offer.updated_at = datetime.utcnow()
        session.commit()
        session.refresh(offer)
        return OfferResponse.model_validate(offer)
    finally:
        session.close()


@router.post("/offers/{offer_id}/reject", response_model=OfferResponse)
async def reject_offer(offer_id: str, notes: Optional[str] = None):
    """Mark an offer as rejected."""
    session = get_session(get_engine())
    try:
        offer = session.query(OfferDB).filter(OfferDB.id == offer_id).first()
        if not offer:
            raise HTTPException(status_code=404, detail="Offer not found")

        offer.status = "rejected"
        if notes:
            offer.outcome_notes = notes
        offer.updated_at = datetime.utcnow()
        session.commit()
        session.refresh(offer)
        return OfferResponse.model_validate(offer)
    finally:
        session.close()


@router.post("/offers/{offer_id}/withdraw", response_model=OfferResponse)
async def withdraw_offer(offer_id: str, notes: Optional[str] = None):
    """Withdraw an offer."""
    session = get_session(get_engine())
    try:
        offer = session.query(OfferDB).filter(OfferDB.id == offer_id).first()
        if not offer:
            raise HTTPException(status_code=404, detail="Offer not found")

        offer.status = "withdrawn"
        if notes:
            offer.outcome_notes = notes
        offer.updated_at = datetime.utcnow()
        session.commit()
        session.refresh(offer)
        return OfferResponse.model_validate(offer)
    finally:
        session.close()


@router.delete("/offers/{offer_id}")
async def delete_offer(offer_id: str):
    """Delete an offer."""
    session = get_session(get_engine())
    try:
        offer = session.query(OfferDB).filter(OfferDB.id == offer_id).first()
        if not offer:
            raise HTTPException(status_code=404, detail="Offer not found")

        session.delete(offer)
        session.commit()
        return {"success": True}
    finally:
        session.close()


# ==================== Deal Stage Routes ====================

@router.get("/stages")
async def get_deal_stages():
    """Get all deal stage definitions."""
    return DEAL_STAGES


@router.get("/due-diligence-items")
async def get_due_diligence_items():
    """Get all due diligence checklist items."""
    return DUE_DILIGENCE_ITEMS


@router.patch("/properties/{property_id}/stage")
async def update_property_stage(property_id: str, data: DealStageUpdate):
    """Update the deal stage for a saved property."""
    session = get_session(get_engine())
    try:
        prop = session.query(SavedPropertyDB).filter(SavedPropertyDB.id == property_id).first()
        if not prop:
            raise HTTPException(status_code=404, detail="Property not found")

        # Validate stage
        valid_stages = [s["id"] for s in DEAL_STAGES]
        if data.stage not in valid_stages:
            raise HTTPException(status_code=400, detail=f"Invalid stage. Must be one of: {valid_stages}")

        # Update stage in deal_data JSON
        deal_data = prop.deal_data or {}
        deal_data["stage"] = data.stage
        deal_data["stage_updated_at"] = datetime.utcnow().isoformat()
        if data.notes:
            stage_history = deal_data.get("stage_history", [])
            stage_history.append({
                "stage": data.stage,
                "notes": data.notes,
                "date": datetime.utcnow().isoformat(),
            })
            deal_data["stage_history"] = stage_history
        prop.deal_data = deal_data

        prop.updated_at = datetime.utcnow()
        session.commit()

        return {
            "success": True,
            "property_id": property_id,
            "stage": data.stage,
        }
    finally:
        session.close()


@router.get("/properties/{property_id}/due-diligence")
async def get_property_due_diligence(property_id: str):
    """Get due diligence checklist for a property."""
    session = get_session(get_engine())
    try:
        prop = session.query(SavedPropertyDB).filter(SavedPropertyDB.id == property_id).first()
        if not prop:
            raise HTTPException(status_code=404, detail="Property not found")

        deal_data = prop.deal_data or {}
        checklist = deal_data.get("due_diligence", {})

        # Build response with all items and their status
        items = []
        for item in DUE_DILIGENCE_ITEMS:
            item_status = checklist.get(item["id"], {})
            items.append({
                **item,
                "completed": item_status.get("completed", False),
                "notes": item_status.get("notes"),
                "completed_date": item_status.get("completed_date"),
            })

        return {
            "property_id": property_id,
            "items": items,
            "completed_count": sum(1 for i in items if i["completed"]),
            "total_count": len(items),
        }
    finally:
        session.close()


@router.patch("/properties/{property_id}/due-diligence")
async def update_property_due_diligence(property_id: str, data: DueDiligenceUpdate):
    """Update a due diligence item for a property."""
    session = get_session(get_engine())
    try:
        prop = session.query(SavedPropertyDB).filter(SavedPropertyDB.id == property_id).first()
        if not prop:
            raise HTTPException(status_code=404, detail="Property not found")

        # Validate item
        valid_items = [i["id"] for i in DUE_DILIGENCE_ITEMS]
        if data.item_id not in valid_items:
            raise HTTPException(status_code=400, detail=f"Invalid item. Must be one of: {valid_items}")

        # Update checklist in deal_data JSON
        deal_data = prop.deal_data or {}
        checklist = deal_data.get("due_diligence", {})
        checklist[data.item_id] = {
            "completed": data.completed,
            "notes": data.notes,
            "completed_date": (data.completed_date or datetime.utcnow()).isoformat() if data.completed else None,
        }
        deal_data["due_diligence"] = checklist
        prop.deal_data = deal_data

        prop.updated_at = datetime.utcnow()
        session.commit()

        return {"success": True, "item_id": data.item_id, "completed": data.completed}
    finally:
        session.close()


# ==================== Pipeline Overview Route ====================

@router.get("/overview", response_model=PipelineOverview)
async def get_pipeline_overview():
    """Get an overview of the deal pipeline."""
    session = get_session(get_engine())
    try:
        # Get all saved properties
        properties = session.query(SavedPropertyDB).all()

        # Get active offers
        active_offers = session.query(OfferDB).filter(
            OfferDB.status.in_(["draft", "submitted", "countered"])
        ).all()
        active_offer_property_ids = {o.property_id for o in active_offers}

        # Get properties under contract
        under_contract = session.query(OfferDB).filter(
            OfferDB.status == "accepted"
        ).all()

        # Group properties by stage
        properties_by_stage: dict = {stage["id"]: [] for stage in DEAL_STAGES}
        properties_by_stage["none"] = []  # For properties without a stage

        for prop in properties:
            deal_data = prop.deal_data or {}
            stage = deal_data.get("stage", "none")

            # Calculate days in stage
            stage_updated = deal_data.get("stage_updated_at")
            days_in_stage = None
            if stage_updated:
                try:
                    updated_dt = datetime.fromisoformat(stage_updated)
                    days_in_stage = (datetime.utcnow() - updated_dt).days
                except Exception:
                    pass

            pipeline_prop = PipelineProperty(
                id=prop.id,
                address=prop.address or "",
                city=prop.city or "",
                state=prop.state or "",
                list_price=prop.list_price,
                estimated_rent=prop.estimated_rent,
                deal_stage=stage if stage != "none" else None,
                deal_score=prop.overall_score,
                days_in_stage=days_in_stage,
                has_active_offer=prop.id in active_offer_property_ids,
                primary_photo=prop.photos[0] if prop.photos else None,
            )

            if stage in properties_by_stage:
                properties_by_stage[stage].append(pipeline_prop.model_dump())
            else:
                properties_by_stage["none"].append(pipeline_prop.model_dump())

        return PipelineOverview(
            stages=DEAL_STAGES,
            properties_by_stage=properties_by_stage,
            total_properties=len(properties),
            active_offers=len(active_offers),
            under_contract=len(under_contract),
        )
    finally:
        session.close()
