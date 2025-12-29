"""Integration tests for end-to-end deal and market flows."""

import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient

from api.main import app
from src.db.sqlite_repository import SQLiteRepository
from src.db.models import MarketDB, SavedPropertyDB, JobDB
from src.models.property import Property, PropertyType, PropertyStatus
from src.models.market import Market, MarketTrend
from src.models.deal import Deal, DealPipeline
from src.models.financials import Financials, LoanTerms, OperatingExpenses, FinancialMetrics


class TestDealFlowIntegration:
    """Integration tests for deal flow: search → analyze → save."""

    @pytest.fixture
    def api_client(self):
        """Create a test client."""
        return TestClient(app)

    @pytest.mark.asyncio
    async def test_save_property_flow(self, repository: SQLiteRepository, sample_deal: Deal):
        """Test saving a property after analysis."""
        await repository.save_deal(sample_deal)

        saved = repository.get_saved_property(sample_deal.id)
        assert saved is not None
        assert saved.address == sample_deal.property.address
        assert saved.list_price == sample_deal.property.list_price

    @pytest.mark.asyncio
    async def test_full_deal_lifecycle(self, repository: SQLiteRepository):
        """Test complete deal lifecycle: create → analyze → save → update → delete."""
        prop = Property(
            id="lifecycle_prop_001",
            address="123 Lifecycle Lane",
            city="Phoenix",
            state="AZ",
            zip_code="85001",
            list_price=275000,
            estimated_rent=1950,
            bedrooms=3,
            bathrooms=2.0,
            sqft=1600,
            property_type=PropertyType.SFH,
            status=PropertyStatus.ACTIVE,
            days_on_market=30,
            source="test",
        )

        financials = Financials(
            property_id=prop.id,
            purchase_price=prop.list_price,
            estimated_rent=prop.estimated_rent,
            loan=LoanTerms(down_payment_pct=0.25, interest_rate=0.07),
            expenses=OperatingExpenses(),
        )
        financials.calculate()

        market = Market(
            id="phoenix_az",
            name="Phoenix",
            state="AZ",
            metro="Phoenix-Mesa-Chandler",
            region="Southwest",
            population=1700000,
            median_home_price=380000,
            median_rent=1650,
            avg_rent_to_price=0.0043,
            price_trend=MarketTrend.MODERATE_GROWTH,
            rent_trend=MarketTrend.MODERATE_GROWTH,
            landlord_friendly=True,
            property_tax_rate=0.0065,
        )

        deal = Deal(
            id=f"deal_{prop.id}",
            property=prop,
            financials=financials,
            market=market,
            pipeline_status=DealPipeline.NEW,
        )
        deal.analyze()

        assert deal.financial_metrics is not None
        assert deal.score is not None
        assert deal.pipeline_status == DealPipeline.ANALYZED

        await repository.save_deal(deal)

        saved = repository.get_saved_property(deal.id)
        assert saved is not None
        assert saved.overall_score is not None

        repository.toggle_property_favorite(deal.id)
        updated = repository.get_saved_property(deal.id)
        assert updated.is_favorite is True

        repository.add_property_note(deal.id, "Test integration note")
        noted = repository.get_saved_property(deal.id)
        assert len(noted.notes) > 0

    @pytest.mark.asyncio
    async def test_reanalyze_saved_property(self, repository: SQLiteRepository, sample_deal: Deal):
        """Test reanalyzing a saved property with new parameters."""
        await repository.save_deal(sample_deal)

        saved = repository.get_saved_property(sample_deal.id)
        assert saved is not None

        updated_rent = sample_deal.financials.estimated_rent * 1.1
        updated_financials = Financials(
            property_id=sample_deal.property.id,
            purchase_price=sample_deal.property.list_price,
            estimated_rent=updated_rent,
            loan=LoanTerms(down_payment_pct=0.25, interest_rate=0.07),
            expenses=OperatingExpenses(),
        )
        updated_financials.calculate()

        original_cf = sample_deal.financial_metrics.monthly_cash_flow
        new_metrics = FinancialMetrics.from_financials(updated_financials)

        assert new_metrics.monthly_cash_flow > original_cf

    def test_deal_with_location_insights(self):
        """Test deal analysis with location data."""
        prop = Property(
            id="location_test_prop",
            address="456 Walkable Blvd",
            city="Phoenix",
            state="AZ",
            zip_code="85004",
            list_price=350000,
            estimated_rent=2200,
            bedrooms=2,
            bathrooms=2.0,
            sqft=1400,
            property_type=PropertyType.CONDO,
            status=PropertyStatus.ACTIVE,
            days_on_market=15,
            source="test",
        )

        market = Market(
            id="phoenix_az",
            name="Phoenix",
            state="AZ",
            metro="Phoenix-Mesa-Chandler",
            region="Southwest",
            population=1700000,
            median_home_price=380000,
            median_rent=1650,
            avg_rent_to_price=0.0043,
            price_trend=MarketTrend.MODERATE_GROWTH,
            rent_trend=MarketTrend.MODERATE_GROWTH,
            landlord_friendly=True,
            property_tax_rate=0.0065,
        )

        deal = Deal(
            id=f"deal_{prop.id}",
            property=prop,
            market=market,
            pipeline_status=DealPipeline.NEW,
        )
        deal.analyze()

        location_data = {
            "walk_score": 85,
            "walk_description": "Very Walkable",
            "transit_score": 72,
            "flood_zone": {
                "zone": "X",
                "risk_level": "low",
                "requires_insurance": False,
            },
            "schools": [
                {"name": "Test Elementary", "rating": 8, "distance": 0.5},
                {"name": "Test Middle", "rating": 7, "distance": 1.0},
            ],
            "noise": {"noise_score": 75},
        }
        deal.add_location_insights(location_data)

        assert any("walkable" in p.lower() for p in deal.pros)
        assert any("flood" in p.lower() for p in deal.pros)
        assert any("school" in p.lower() for p in deal.pros)


class TestMarketFlowIntegration:
    """Integration tests for market flow: browse → favorite → enrich."""

    @pytest.fixture
    def api_client(self):
        """Create a test client."""
        return TestClient(app)

    def test_browse_markets(self, api_client):
        """Test browsing available markets."""
        response = api_client.get("/api/markets")
        assert response.status_code == 200
        data = response.json()
        assert "markets" in data
        assert isinstance(data["markets"], list)

    def test_favorite_market_flow(self, repository: SQLiteRepository):
        """Test marking a market as favorite."""
        market = repository.add_market(
            name="Integration City",
            state="TX",
            metro="Integration Metro",
        )
        assert market is not None
        assert market.is_favorite is False

        updated = repository.toggle_market_favorite(market.id)
        assert updated.is_favorite is True

        favorites = repository.get_favorite_markets()
        market_ids = [m.id for m in favorites]
        assert market.id in market_ids

        updated = repository.toggle_market_favorite(market.id)
        assert updated.is_favorite is False

    def test_market_enrichment_job_flow(self, repository: SQLiteRepository):
        """Test the market enrichment job flow."""
        market = repository.add_market(
            name="Enrich City",
            state="FL",
            metro="Enrich Metro",
        )
        repository.toggle_market_favorite(market.id)

        job = repository.enqueue_job(
            job_type="enrich_market",
            payload={"market_id": market.id},
            priority=1,
        )
        assert job is not None
        assert job.status == "pending"

        pending = repository.get_pending_job()
        assert pending is not None

        running_job = repository.update_job_status(job.id, "running")
        assert running_job.status == "running"

        result = {"scores_updated": True, "data_sources": ["redfin", "census"]}
        completed_job = repository.update_job_status(job.id, "completed", result=result)
        assert completed_job.status == "completed"
        assert completed_job.result == result

    def test_market_api_support_flow(self, repository: SQLiteRepository):
        """Test tracking API support per market."""
        market = repository.add_market(
            name="API Support City",
            state="NC",
        )

        repository.update_market_api_support(market.id, "listings", True)
        repository.update_market_api_support(market.id, "rent_estimates", True)
        repository.update_market_api_support(market.id, "income_data", False)

        updated = repository.session.query(MarketDB).filter_by(id=market.id).first()
        assert updated.api_support["listings"] is True
        assert updated.api_support["rent_estimates"] is True
        assert updated.api_support["income_data"] is False

    def test_full_market_lifecycle(self, repository: SQLiteRepository):
        """Test complete market lifecycle: add → favorite → enrich → unfavorite."""
        market = repository.add_market(
            name="Lifecycle City",
            state="OH",
            metro="Lifecycle Metro",
        )
        assert market is not None

        repository.toggle_market_favorite(market.id)
        market_db = repository.session.query(MarketDB).filter_by(id=market.id).first()
        assert market_db.is_favorite is True

        job = repository.enqueue_job(
            job_type="enrich_market",
            payload={"market_id": market.id},
        )
        repository.update_job_status(job.id, "running")
        repository.update_market_api_support(market.id, "listings", True)
        repository.update_job_status(job.id, "completed", result={"success": True})

        enriched = repository.session.query(MarketDB).filter_by(id=market.id).first()
        assert enriched.is_favorite is True
        assert enriched.api_support.get("listings") is True

        repository.toggle_market_favorite(market.id)
        final = repository.session.query(MarketDB).filter_by(id=market.id).first()
        assert final.is_favorite is False


class TestCrossFlowIntegration:
    """Tests for interactions between deal and market flows."""

    def test_deal_uses_market_context(self):
        """Test that deal analysis uses correct market context."""
        prop = Property(
            id="context_test_prop",
            address="789 Context Ave",
            city="Context City",
            state="AZ",
            zip_code="85001",
            list_price=280000,
            estimated_rent=1900,
            bedrooms=3,
            bathrooms=2.0,
            sqft=1550,
            property_type=PropertyType.SFH,
            status=PropertyStatus.ACTIVE,
            days_on_market=20,
            source="test",
        )

        market_model = Market(
            id="context_city_az",
            name="Context City",
            state="AZ",
            metro="Context Metro",
            region="Southwest",
            population=500000,
            median_home_price=300000,
            median_rent=1600,
            avg_rent_to_price=0.0053,
            price_trend=MarketTrend.MODERATE_GROWTH,
            rent_trend=MarketTrend.MODERATE_GROWTH,
            landlord_friendly=True,
            property_tax_rate=0.007,
        )

        deal = Deal(
            id=f"deal_{prop.id}",
            property=prop,
            market=market_model,
            pipeline_status=DealPipeline.NEW,
        )
        deal.analyze()

        assert deal.market_metrics is not None
        assert deal.score is not None
        assert deal.score.market_score > 0

    @pytest.mark.asyncio
    async def test_saved_property_inherits_market_data(self, repository: SQLiteRepository, sample_deal: Deal):
        """Test that saved properties maintain market reference."""
        repository.add_market(
            name=sample_deal.market.name,
            state=sample_deal.market.state,
            metro=sample_deal.market.metro,
        )

        await repository.save_deal(sample_deal)

        saved = repository.get_saved_property(sample_deal.id)
        assert saved is not None
        assert saved.city == sample_deal.property.city or saved.state == sample_deal.property.state

    def test_batch_property_analysis_in_market(self):
        """Test analyzing multiple properties in the same market."""
        market = Market(
            id="batch_market",
            name="Batch City",
            state="TX",
            metro="Batch Metro",
            region="Southwest",
            population=800000,
            median_home_price=320000,
            median_rent=1700,
            avg_rent_to_price=0.0053,
            price_trend=MarketTrend.MODERATE_GROWTH,
            rent_trend=MarketTrend.STABLE,
            landlord_friendly=True,
            property_tax_rate=0.018,
        )

        properties = [
            Property(
                id=f"batch_prop_{i}",
                address=f"{100 + i} Batch Street",
                city="Batch City",
                state="TX",
                zip_code="75001",
                list_price=250000 + (i * 25000),
                estimated_rent=1600 + (i * 100),
                bedrooms=3,
                bathrooms=2.0,
                sqft=1400 + (i * 100),
                property_type=PropertyType.SFH,
                status=PropertyStatus.ACTIVE,
                days_on_market=20 + i,
                source="test",
            )
            for i in range(5)
        ]

        deals = []
        for prop in properties:
            deal = Deal(
                id=f"deal_{prop.id}",
                property=prop,
                market=market,
                pipeline_status=DealPipeline.NEW,
            )
            deal.analyze()
            deals.append(deal)

        assert all(d.pipeline_status == DealPipeline.ANALYZED for d in deals)
        assert all(d.score is not None for d in deals)

        scores = [d.score.overall_score for d in deals]
        assert len(set(scores)) > 1


class TestErrorHandlingIntegration:
    """Tests for error handling in integration flows."""

    def test_deal_analysis_with_missing_rent(self):
        """Test deal analysis handles missing rent estimate gracefully."""
        prop = Property(
            id="no_rent_prop",
            address="123 No Rent Lane",
            city="Phoenix",
            state="AZ",
            zip_code="85001",
            list_price=300000,
            estimated_rent=None,
            bedrooms=3,
            bathrooms=2.0,
            sqft=1500,
            property_type=PropertyType.SFH,
            status=PropertyStatus.ACTIVE,
            days_on_market=30,
            source="test",
        )

        deal = Deal(
            id=f"deal_{prop.id}",
            property=prop,
            pipeline_status=DealPipeline.NEW,
        )

        deal.analyze()
        assert deal.financial_metrics is not None
        assert deal.financial_metrics.monthly_cash_flow < 0

    def test_market_enrichment_failure_handling(self, repository: SQLiteRepository):
        """Test handling of failed enrichment jobs."""
        market = repository.add_market(name="Fail City", state="XX")

        job = repository.enqueue_job(
            job_type="enrich_market",
            payload={"market_id": market.id},
        )
        repository.update_job_status(job.id, "running")

        failed_job = repository.update_job_status(job.id, "failed", error="API rate limit exceeded")
        assert failed_job.status == "failed"
        assert "rate limit" in failed_job.error

        market_check = repository.session.query(MarketDB).filter_by(id=market.id).first()
        assert market_check is not None
        # Market exists but with default score (0.0) since enrichment failed
        assert market_check.overall_score == 0.0

    @pytest.mark.asyncio
    async def test_duplicate_property_save(self, repository: SQLiteRepository, sample_deal: Deal):
        """Test saving the same property twice updates instead of duplicating."""
        await repository.save_deal(sample_deal)
        sample_deal.is_favorite = True
        await repository.save_deal(sample_deal)

        props = repository.get_saved_properties()
        matching = [p for p in props if p.id == sample_deal.id]
        assert len(matching) == 1


class TestCacheIntegration:
    """Tests for caching behavior in flows."""

    def test_search_cache_prevents_duplicate_api_calls(self, repository: SQLiteRepository):
        """Test that cached searches don't hit external API."""
        provider = "us_real_estate_listings"
        endpoint = "search"
        params = {"city": "phoenix", "state": "az", "max_price": 300000}
        cached_results = {
            "properties": [
                {"id": "cached_1", "address": "123 Cache St"},
                {"id": "cached_2", "address": "456 Cache Ave"},
            ]
        }
        repository.cache.set(provider, endpoint, params, cached_results, ttl_hours=1)

        cached = repository.cache.get(provider, endpoint, params)
        assert cached is not None
        assert len(cached["properties"]) == 2

    def test_income_cache_persistence(self, repository: SQLiteRepository):
        """Test income data caching across requests."""
        zip_code = "85001"
        median_income = 65000
        income_tier = "middle"
        income_data = {
            "income_brackets": {
                "under_25k": 0.15,
                "25k_50k": 0.25,
            }
        }

        repository.cache.set_income(zip_code, median_income, income_tier, income_data)

        cached = repository.cache.get_income(zip_code)
        assert cached is not None
        assert cached["median_income"] == 65000

    def test_cache_invalidation(self, repository: SQLiteRepository):
        """Test that cache can be invalidated."""
        provider = "test_provider_inv"
        endpoint = "test_endpoint_inv"
        params = {"key": "value"}
        repository.cache.set(provider, endpoint, params, {"data": "old"}, ttl_hours=1)

        assert repository.cache.get(provider, endpoint, params) is not None

        # Invalidate by provider and endpoint
        repository.cache.invalidate(provider, endpoint)

        assert repository.cache.get(provider, endpoint, params) is None


class TestJobQueueIntegration:
    """Tests for job queue behavior."""

    def test_job_priority_ordering(self, repository: SQLiteRepository):
        """Test that jobs are processed in priority order."""
        low_priority = repository.enqueue_job(
            job_type="test_job_int",
            payload={"order": 1},
            priority=3,
        )
        high_priority = repository.enqueue_job(
            job_type="test_job_int",
            payload={"order": 2},
            priority=10,
        )
        medium_priority = repository.enqueue_job(
            job_type="test_job_int",
            payload={"order": 3},
            priority=5,
        )

        pending = repository.get_pending_job()

        assert pending is not None
        assert pending.priority == 10

    def test_job_retry_flow(self, repository: SQLiteRepository):
        """Test that failed jobs can be retried by creating new jobs."""
        job = repository.enqueue_job(
            job_type="retry_test",
            payload={"attempt": 1},
        )

        repository.update_job_status(job.id, "running")
        repository.update_job_status(job.id, "failed", error="Temporary error")

        failed = repository.get_job(job.id)
        assert failed.status == "failed"

        retry_job = repository.enqueue_job(
            job_type="retry_test",
            payload={"attempt": 2, "original_job_id": job.id},
        )
        assert retry_job is not None
        assert retry_job.status == "pending"

    def test_job_stats_tracking(self, repository: SQLiteRepository):
        """Test job statistics are tracked."""
        initial_stats = repository.get_job_stats()

        job = repository.enqueue_job(job_type="stats_test", payload={})
        repository.update_job_status(job.id, "running")
        repository.update_job_status(job.id, "completed", result={"success": True})

        stats = repository.get_job_stats()

        assert "completed" in stats
        assert stats["completed"] >= 1
