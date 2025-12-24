"""SQLite implementation of the DealRepository."""

from datetime import datetime, timedelta
from typing import Optional, List
import json

from sqlalchemy.orm import Session

from src.db.repository import DealRepository
from src.db.models import (
    MarketDB, SavedPropertyDB, SearchCacheDB, IncomeCacheDB, JobDB,
    get_engine, get_session, init_database, DEFAULT_FAVORITE_MARKETS
)
from src.db.cache import CacheManager
from src.models.deal import Deal, DealPipeline
from src.models.property import Property
from src.models.market import Market


class SQLiteRepository(DealRepository):
    """SQLite-backed repository for persistent storage."""

    def __init__(self, db_path: Optional[str] = None):
        self.engine = get_engine(db_path)
        init_database(self.engine)
        self._session: Optional[Session] = None
        self._cache: Optional[CacheManager] = None

    @property
    def session(self) -> Session:
        """Get the current session or create one."""
        if self._session is None:
            self._session = get_session(self.engine)
        return self._session

    @property
    def cache(self) -> CacheManager:
        """Get the cache manager."""
        if self._cache is None:
            self._cache = CacheManager(self.session)
        return self._cache

    def close(self):
        """Close the database session."""
        if self._session:
            self._session.close()
            self._session = None

    # ==================== Deal/Property Methods ====================

    async def save_deal(self, deal: Deal) -> Deal:
        """Save or update a deal (saved property)."""
        # Check if property already exists
        existing = (
            self.session.query(SavedPropertyDB)
            .filter_by(id=deal.id)
            .first()
        )

        # Calculate financial metrics
        cash_flow = None
        cash_on_cash = None
        cap_rate = None
        if deal.financials:
            cash_flow = deal.financials.monthly_cash_flow
            # Calculate cash-on-cash: annual_cash_flow / total_cash_needed
            if deal.financials.annual_cash_flow and deal.financials.total_cash_needed:
                cash_on_cash = deal.financials.annual_cash_flow / deal.financials.total_cash_needed
            # Calculate cap rate: NOI / purchase_price
            if deal.financials.net_operating_income:
                cap_rate = deal.financials.net_operating_income / deal.financials.purchase_price

        if existing:
            # Update existing
            existing.list_price = deal.property.list_price
            existing.estimated_rent = deal.property.estimated_rent
            existing.pipeline_status = deal.pipeline_status.value
            existing.analysis_data = deal.model_dump(mode='json')
            existing.overall_score = deal.score.overall_score if deal.score else None
            existing.cash_flow = cash_flow
            existing.cash_on_cash = cash_on_cash
            existing.cap_rate = cap_rate
            existing.is_favorite = deal.is_favorite
            existing.updated_at = datetime.utcnow()
        else:
            # Create new
            saved_prop = SavedPropertyDB(
                id=deal.id,
                address=deal.property.address,
                city=deal.property.city,
                state=deal.property.state,
                zip_code=deal.property.zip_code,
                list_price=deal.property.list_price,
                estimated_rent=deal.property.estimated_rent,
                bedrooms=deal.property.bedrooms,
                bathrooms=deal.property.bathrooms,
                sqft=deal.property.sqft,
                property_type=deal.property.property_type.value if deal.property.property_type else None,
                year_built=deal.property.year_built,
                source=deal.property.source,
                source_url=deal.property.source_url,
                analysis_data=deal.model_dump(mode='json'),
                overall_score=deal.score.overall_score if deal.score else None,
                cash_flow=cash_flow,
                cash_on_cash=cash_on_cash,
                cap_rate=cap_rate,
                pipeline_status=deal.pipeline_status.value,
                is_favorite=deal.is_favorite,
            )
            self.session.add(saved_prop)

        self.session.commit()
        return deal

    async def get_deal(self, deal_id: str) -> Optional[Deal]:
        """Get a deal by ID."""
        saved_prop = (
            self.session.query(SavedPropertyDB)
            .filter_by(id=deal_id)
            .first()
        )

        if not saved_prop:
            return None

        # Reconstruct Deal from stored JSON
        if saved_prop.analysis_data:
            try:
                return Deal.model_validate(saved_prop.analysis_data)
            except Exception:
                pass

        # Fallback: build minimal Deal from stored fields
        from src.models.property import PropertyType
        property = Property(
            id=saved_prop.id,
            address=saved_prop.address,
            city=saved_prop.city,
            state=saved_prop.state,
            zip_code=saved_prop.zip_code or "",
            list_price=saved_prop.list_price or 0,
            estimated_rent=saved_prop.estimated_rent,
            bedrooms=saved_prop.bedrooms or 0,
            bathrooms=saved_prop.bathrooms or 0,
            sqft=saved_prop.sqft,
            property_type=PropertyType(saved_prop.property_type) if saved_prop.property_type else PropertyType.SFH,
            source_url=saved_prop.source_url,
            source=saved_prop.source or "unknown",
        )

        return Deal(
            id=saved_prop.id,
            property=property,
            pipeline_status=DealPipeline(saved_prop.pipeline_status) if saved_prop.pipeline_status else DealPipeline.ANALYZED,
            is_favorite=saved_prop.is_favorite or False,
        )

    async def get_deals(
        self,
        status: Optional[DealPipeline] = None,
        market_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Deal]:
        """Get deals with optional filters."""
        query = self.session.query(SavedPropertyDB)

        if status:
            query = query.filter_by(pipeline_status=status.value)

        # Order by score (descending)
        query = query.order_by(SavedPropertyDB.overall_score.desc().nullslast())

        # Apply pagination
        query = query.offset(offset).limit(limit)

        deals = []
        for saved_prop in query.all():
            deal = await self.get_deal(saved_prop.id)
            if deal:
                deals.append(deal)

        return deals

    async def delete_deal(self, deal_id: str) -> bool:
        """Delete a deal."""
        saved_prop = (
            self.session.query(SavedPropertyDB)
            .filter_by(id=deal_id)
            .first()
        )

        if saved_prop:
            self.session.delete(saved_prop)
            self.session.commit()
            return True
        return False

    async def save_property(self, property: Property) -> Property:
        """Save property (creates a minimal saved property entry)."""
        # This creates an "unsaved" property - use save_deal for full analysis
        saved_prop = SavedPropertyDB(
            id=property.id,
            address=property.address,
            city=property.city,
            state=property.state,
            zip_code=property.zip_code,
            list_price=property.list_price,
            estimated_rent=property.estimated_rent,
            bedrooms=property.bedrooms,
            bathrooms=property.bathrooms,
            sqft=property.sqft,
            property_type=property.property_type.value if property.property_type else None,
            source=property.source,
            source_url=property.source_url,
            pipeline_status='new',
        )
        self.session.merge(saved_prop)
        self.session.commit()
        return property

    async def get_property(self, property_id: str) -> Optional[Property]:
        """Get a property by ID."""
        deal = await self.get_deal(property_id)
        return deal.property if deal else None

    # ==================== Market Methods ====================

    async def save_market(self, market: Market) -> Market:
        """Save or update market data."""
        from src.models.market import MarketMetrics

        market_db = (
            self.session.query(MarketDB)
            .filter_by(id=market.id)
            .first()
        )

        # Calculate scores
        metrics = MarketMetrics.from_market(market)

        if market_db:
            market_db.name = market.name
            market_db.state = market.state
            market_db.metro = market.metro
            market_db.market_data = market.model_dump(mode='json')
            market_db.overall_score = metrics.overall_score
            market_db.cash_flow_score = metrics.cash_flow_score
            market_db.growth_score = metrics.growth_score
            market_db.updated_at = datetime.utcnow()
        else:
            market_db = MarketDB(
                id=market.id,
                name=market.name,
                state=market.state,
                metro=market.metro,
                region=market.region,
                market_data=market.model_dump(mode='json'),
                overall_score=metrics.overall_score,
                cash_flow_score=metrics.cash_flow_score,
                growth_score=metrics.growth_score,
                is_favorite=False,
                is_supported=True,
            )
            self.session.add(market_db)

        self.session.commit()
        return market

    async def get_market(self, market_id: str) -> Optional[Market]:
        """Get market by ID."""
        market_db = (
            self.session.query(MarketDB)
            .filter_by(id=market_id)
            .first()
        )

        if not market_db:
            return None

        if market_db.market_data:
            try:
                return Market.model_validate(market_db.market_data)
            except Exception:
                pass

        # Minimal market from stored fields
        return Market(
            id=market_db.id,
            name=market_db.name,
            state=market_db.state,
            metro=market_db.metro or "",
            region=market_db.region,
        )

    async def get_all_markets(self) -> List[Market]:
        """Get all markets."""
        markets = []
        for market_db in self.session.query(MarketDB).all():
            market = await self.get_market(market_db.id)
            if market:
                markets.append(market)
        return markets

    # ==================== Market-specific Methods ====================

    def get_favorite_markets(self) -> List[MarketDB]:
        """Get user's favorite (researched) markets."""
        return (
            self.session.query(MarketDB)
            .filter_by(is_favorite=True)
            .order_by(MarketDB.overall_score.desc())
            .all()
        )

    def get_supported_markets(self) -> List[MarketDB]:
        """Get all markets with API support."""
        return (
            self.session.query(MarketDB)
            .filter_by(is_supported=True)
            .order_by(MarketDB.is_favorite.desc(), MarketDB.overall_score.desc())
            .all()
        )

    def get_all_markets_sorted(self) -> List[MarketDB]:
        """Get all markets sorted by favorites first, then by score."""
        return (
            self.session.query(MarketDB)
            .order_by(
                MarketDB.is_favorite.desc(),
                MarketDB.overall_score.desc().nullslast(),
                MarketDB.name.asc()
            )
            .all()
        )

    def add_market(
        self,
        name: str,
        state: str,
        metro: str = None,
        is_favorite: bool = False
    ) -> MarketDB:
        """Add a new market."""
        market_id = f"{name.lower().replace(' ', '_')}_{state.lower()}"

        existing = self.session.query(MarketDB).filter_by(id=market_id).first()
        if existing:
            existing.is_favorite = is_favorite
            self.session.commit()
            return existing

        market = MarketDB(
            id=market_id,
            name=name,
            state=state,
            metro=metro,
            is_favorite=is_favorite,
            is_supported=True,  # Assume supported until proven otherwise
        )
        self.session.add(market)
        self.session.commit()
        return market

    def toggle_market_favorite(self, market_id: str) -> Optional[MarketDB]:
        """Toggle a market's favorite status."""
        market = self.session.query(MarketDB).filter_by(id=market_id).first()
        if market:
            market.is_favorite = not market.is_favorite
            self.session.commit()
        return market

    def update_market_api_support(
        self,
        market_id: str,
        provider: str,
        supported: bool
    ) -> Optional[MarketDB]:
        """Update which APIs support this market."""
        market = self.session.query(MarketDB).filter_by(id=market_id).first()
        if market:
            api_support = market.api_support or {}
            api_support[provider] = supported
            market.api_support = api_support
            self.session.commit()
        return market

    # ==================== Saved Properties ====================

    def get_saved_properties(
        self,
        status: Optional[str] = None,
        is_favorite: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[SavedPropertyDB]:
        """Get saved properties with filters."""
        query = self.session.query(SavedPropertyDB)

        if status:
            query = query.filter_by(pipeline_status=status)
        if is_favorite is not None:
            query = query.filter_by(is_favorite=is_favorite)

        return (
            query
            .order_by(SavedPropertyDB.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def get_saved_property(self, property_id: str) -> Optional[SavedPropertyDB]:
        """Get a saved property by ID."""
        return (
            self.session.query(SavedPropertyDB)
            .filter_by(id=property_id)
            .first()
        )

    def toggle_property_favorite(self, property_id: str) -> Optional[SavedPropertyDB]:
        """Toggle a property's favorite status."""
        prop = self.session.query(SavedPropertyDB).filter_by(id=property_id).first()
        if prop:
            prop.is_favorite = not prop.is_favorite
            self.session.commit()
        return prop

    def update_property_status(
        self,
        property_id: str,
        status: str
    ) -> Optional[SavedPropertyDB]:
        """Update a property's pipeline status."""
        prop = self.session.query(SavedPropertyDB).filter_by(id=property_id).first()
        if prop:
            prop.pipeline_status = status
            prop.updated_at = datetime.utcnow()
            self.session.commit()
        return prop

    def add_property_note(
        self,
        property_id: str,
        note: str
    ) -> Optional[SavedPropertyDB]:
        """Add a note to a property."""
        prop = self.session.query(SavedPropertyDB).filter_by(id=property_id).first()
        if prop:
            existing_notes = prop.notes or ""
            timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
            prop.notes = f"{existing_notes}\n[{timestamp}] {note}".strip()
            prop.updated_at = datetime.utcnow()
            self.session.commit()
        return prop

    # ==================== Jobs ====================

    def enqueue_job(
        self,
        job_type: str,
        payload: dict = None,
        priority: int = 0,
    ) -> JobDB:
        """Add a job to the queue."""
        from src.db.models import generate_uuid
        job = JobDB(
            id=generate_uuid(),
            job_type=job_type,
            payload=payload or {},
            priority=priority,
            status='pending',
        )
        self.session.add(job)
        self.session.commit()
        return job

    def get_pending_job(self) -> Optional[JobDB]:
        """Get the next pending job (highest priority, oldest first)."""
        return (
            self.session.query(JobDB)
            .filter_by(status='pending')
            .order_by(JobDB.priority.desc(), JobDB.created_at.asc())
            .first()
        )

    def get_job(self, job_id: str) -> Optional[JobDB]:
        """Get a job by ID."""
        return self.session.query(JobDB).filter_by(id=job_id).first()

    def get_jobs(
        self,
        status: Optional[str] = None,
        job_type: Optional[str] = None,
        limit: int = 50,
    ) -> List[JobDB]:
        """Get jobs with optional filters."""
        query = self.session.query(JobDB)
        if status:
            query = query.filter_by(status=status)
        if job_type:
            query = query.filter_by(job_type=job_type)
        return (
            query
            .order_by(JobDB.created_at.desc())
            .limit(limit)
            .all()
        )

    def update_job_status(
        self,
        job_id: str,
        status: str,
        message: str = None,
        progress: int = None,
        error: str = None,
        result: dict = None,
    ) -> Optional[JobDB]:
        """Update a job's status."""
        job = self.get_job(job_id)
        if not job:
            return None

        job.status = status
        if message is not None:
            job.message = message
        if progress is not None:
            job.progress = progress
        if error is not None:
            job.error = error
        if result is not None:
            job.result = result

        if status == 'running' and job.started_at is None:
            job.started_at = datetime.utcnow()
            job.attempts += 1
        elif status in ('completed', 'failed'):
            job.completed_at = datetime.utcnow()

        self.session.commit()
        return job

    def cancel_job(self, job_id: str) -> Optional[JobDB]:
        """Cancel a pending job."""
        job = self.get_job(job_id)
        if job and job.status == 'pending':
            job.status = 'cancelled'
            job.completed_at = datetime.utcnow()
            self.session.commit()
        return job

    def cancel_jobs_by_type(self, job_type: str) -> int:
        """Cancel all pending jobs of a given type."""
        jobs = (
            self.session.query(JobDB)
            .filter_by(job_type=job_type, status='pending')
            .all()
        )
        for job in jobs:
            job.status = 'cancelled'
            job.completed_at = datetime.utcnow()
        self.session.commit()
        return len(jobs)

    def cleanup_old_jobs(self, days: int = 7) -> int:
        """Delete completed/failed/cancelled jobs older than N days."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        deleted = (
            self.session.query(JobDB)
            .filter(
                JobDB.status.in_(['completed', 'failed', 'cancelled']),
                JobDB.completed_at < cutoff
            )
            .delete(synchronize_session=False)
        )
        self.session.commit()
        return deleted

    def get_job_stats(self) -> dict:
        """Get job queue statistics."""
        pending = self.session.query(JobDB).filter_by(status='pending').count()
        running = self.session.query(JobDB).filter_by(status='running').count()
        completed = self.session.query(JobDB).filter_by(status='completed').count()
        failed = self.session.query(JobDB).filter_by(status='failed').count()
        return {
            'pending': pending,
            'running': running,
            'completed': completed,
            'failed': failed,
            'total': pending + running + completed + failed,
        }

    # ==================== Stats ====================

    async def get_stats(self) -> dict:
        """Get repository statistics."""
        total_properties = self.session.query(SavedPropertyDB).count()
        total_markets = self.session.query(MarketDB).count()
        favorite_markets = self.session.query(MarketDB).filter_by(is_favorite=True).count()
        favorite_properties = self.session.query(SavedPropertyDB).filter_by(is_favorite=True).count()

        # Status breakdown
        status_counts = {}
        for prop in self.session.query(SavedPropertyDB).all():
            status = prop.pipeline_status or 'unknown'
            status_counts[status] = status_counts.get(status, 0) + 1

        # Cache stats
        cache_stats = self.cache.get_stats()

        return {
            "total_saved_properties": total_properties,
            "favorite_properties": favorite_properties,
            "total_markets": total_markets,
            "favorite_markets": favorite_markets,
            "properties_by_status": status_counts,
            "cache": cache_stats,
        }


# Singleton instance
_repository: Optional[SQLiteRepository] = None


def get_repository() -> SQLiteRepository:
    """Get or create the SQLite repository singleton."""
    global _repository
    if _repository is None:
        _repository = SQLiteRepository()
    return _repository
