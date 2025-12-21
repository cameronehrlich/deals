"""Tests for agent layer."""

import pytest
from src.agents.market_research import MarketResearchAgent
from src.agents.deal_analyzer import DealAnalyzerAgent
from src.agents.pipeline import PipelineAgent
from src.models.property import Property
from src.scrapers.mock_scraper import MockScraper


class TestMarketResearchAgent:
    """Tests for MarketResearchAgent."""

    @pytest.mark.asyncio
    async def test_run_all_markets(self):
        """Test analyzing all markets."""
        agent = MarketResearchAgent()
        result = await agent.run()

        assert result.success
        assert result.data["count"] > 0
        assert len(result.data["markets"]) > 0

    @pytest.mark.asyncio
    async def test_run_specific_markets(self):
        """Test analyzing specific markets."""
        agent = MarketResearchAgent()
        result = await agent.run(market_ids=["indianapolis_in", "cleveland_oh"])

        assert result.success
        assert result.data["count"] == 2

    @pytest.mark.asyncio
    async def test_get_market(self):
        """Test getting single market."""
        agent = MarketResearchAgent()
        market = await agent.get_market("indianapolis_in")

        assert market is not None
        assert market.name == "Indianapolis"
        assert market.state == "IN"

    @pytest.mark.asyncio
    async def test_get_top_markets(self):
        """Test getting top markets."""
        agent = MarketResearchAgent()
        top = await agent.get_top_markets(n=3, strategy="cash_flow")

        assert len(top) == 3
        # Should be sorted by cash flow score
        assert top[0]["cash_flow_score"] >= top[1]["cash_flow_score"]


class TestDealAnalyzerAgent:
    """Tests for DealAnalyzerAgent."""

    @pytest.mark.asyncio
    async def test_analyze_properties(self):
        """Test analyzing a list of properties."""
        # Create test properties
        properties = [
            Property(
                id="test_001",
                address="123 Test St",
                city="Indianapolis",
                state="IN",
                zip_code="46201",
                list_price=200000,
                estimated_rent=1800,
                bedrooms=3,
                bathrooms=2,
                source="test",
            ),
            Property(
                id="test_002",
                address="456 Test Ave",
                city="Indianapolis",
                state="IN",
                zip_code="46202",
                list_price=150000,
                estimated_rent=1400,
                bedrooms=3,
                bathrooms=1.5,
                source="test",
            ),
        ]

        agent = DealAnalyzerAgent()
        result = await agent.run(properties)

        assert result.success
        assert result.data["total_analyzed"] == 2

    @pytest.mark.asyncio
    async def test_quick_screen(self):
        """Test quick screening of properties."""
        # Create properties with varying rent-to-price ratios
        properties = [
            Property(
                id="good_deal",
                address="100 Good St",
                city="Cleveland",
                state="OH",
                zip_code="44102",
                list_price=100000,
                estimated_rent=1000,  # 1% ratio - good
                bedrooms=3,
                bathrooms=1,
                source="test",
            ),
            Property(
                id="bad_deal",
                address="200 Bad Ave",
                city="Cleveland",
                state="OH",
                zip_code="44103",
                list_price=300000,
                estimated_rent=1500,  # 0.5% ratio - bad
                bedrooms=3,
                bathrooms=2,
                source="test",
            ),
        ]

        agent = DealAnalyzerAgent()
        passed = await agent.quick_screen(properties, min_rent_to_price=0.008)

        assert len(passed) == 1
        assert passed[0].id == "good_deal"


class TestMockScraper:
    """Tests for MockScraper."""

    @pytest.mark.asyncio
    async def test_search(self):
        """Test property search."""
        scraper = MockScraper()
        result = await scraper.search(
            city="Indianapolis",
            state="IN",
            limit=10,
        )

        assert result.success
        assert len(result.properties) <= 10
        assert all(p.source == "mock" for p in result.properties)

    @pytest.mark.asyncio
    async def test_search_with_filters(self):
        """Test property search with price filters."""
        scraper = MockScraper()
        result = await scraper.search(
            city="Cleveland",
            state="OH",
            min_price=100000,
            max_price=200000,
            min_beds=3,
            limit=20,
        )

        assert result.success
        for prop in result.properties:
            assert prop.list_price >= 100000
            assert prop.list_price <= 200000
            assert prop.bedrooms >= 3


class TestPipelineAgent:
    """Tests for PipelineAgent."""

    @pytest.mark.asyncio
    async def test_full_pipeline(self):
        """Test running full pipeline."""
        agent = PipelineAgent()
        result = await agent.run(
            market_ids=["indianapolis_in"],
            properties_per_market=10,
            top_n=5,
        )

        # Pipeline should complete even if no deals pass quick screen
        # (sample data may not meet filter criteria)
        assert result.data is not None
        assert result.data["markets_analyzed"] >= 1
        assert result.data["properties_scraped"] > 0
