"""Tests for data sources."""

import pytest
from datetime import datetime

from src.data_sources.hud_fmr import HudFmrLoader, FairMarketRent, EMBEDDED_FMR_DATA
from src.data_sources.rentcast import RentCastClient, RentEstimate
from src.data_sources.url_parser import PropertyUrlParser, ParsedProperty
from src.data_sources.aggregator import DataAggregator, EnrichedMarketData


class TestHudFmrLoader:
    """Tests for HUD FMR data loader."""

    def test_embedded_data_loaded(self):
        """Test that embedded FMR data is loaded."""
        loader = HudFmrLoader()
        assert len(loader._fmr_data) > 0
        assert "indianapolis_in" in loader._fmr_data

    def test_get_fmr(self):
        """Test getting FMR for a market."""
        loader = HudFmrLoader()
        fmr = loader.get_fmr("indianapolis_in")

        assert fmr is not None
        assert fmr.state == "IN"
        assert fmr.fmr_2br > 0
        assert fmr.fmr_3br > fmr.fmr_2br  # 3br should cost more

    def test_get_fmr_case_insensitive(self):
        """Test case insensitivity of market lookup."""
        loader = HudFmrLoader()

        fmr1 = loader.get_fmr("INDIANAPOLIS_IN")
        fmr2 = loader.get_fmr("indianapolis_in")

        assert fmr1 is not None
        assert fmr1 == fmr2

    def test_get_rent_estimate(self):
        """Test getting rent estimate for bedrooms."""
        loader = HudFmrLoader()

        rent_2br = loader.get_rent_estimate("indianapolis_in", 2)
        rent_3br = loader.get_rent_estimate("indianapolis_in", 3)

        assert rent_2br is not None
        assert rent_3br is not None
        assert rent_3br > rent_2br

    def test_get_fmr_unknown_market(self):
        """Test getting FMR for unknown market returns None."""
        loader = HudFmrLoader()
        fmr = loader.get_fmr("unknown_market")
        assert fmr is None

    def test_fair_market_rent_bedrooms_dict(self):
        """Test FMR bedrooms dictionary."""
        fmr = EMBEDDED_FMR_DATA["indianapolis_in"]
        by_br = fmr.fmr_by_bedrooms

        assert 0 in by_br
        assert 1 in by_br
        assert 2 in by_br
        assert 3 in by_br
        assert 4 in by_br

    def test_get_fmr_method(self):
        """Test FMR get_fmr method for various bedroom counts."""
        fmr = EMBEDDED_FMR_DATA["indianapolis_in"]

        assert fmr.get_fmr(0) == fmr.fmr_0br
        assert fmr.get_fmr(1) == fmr.fmr_1br
        assert fmr.get_fmr(2) == fmr.fmr_2br
        assert fmr.get_fmr(3) == fmr.fmr_3br
        assert fmr.get_fmr(4) == fmr.fmr_4br
        assert fmr.get_fmr(5) == fmr.fmr_4br  # 5+ uses 4br rate


class TestRentCastClient:
    """Tests for RentCast client."""

    def test_no_api_key(self):
        """Test client without API key falls back to HUD."""
        client = RentCastClient(api_key=None)
        assert not client.has_api_key

    @pytest.mark.asyncio
    async def test_fallback_estimate(self):
        """Test fallback estimate when no API key."""
        client = RentCastClient(api_key=None)

        try:
            estimate = await client.get_rent_estimate(
                address="123 Main St",
                city="Indianapolis",
                state="IN",
                zip_code="46201",
                bedrooms=3,
                bathrooms=2,
            )

            assert estimate is not None
            assert estimate.rent_estimate > 0
            assert estimate.rent_low < estimate.rent_estimate
            assert estimate.rent_high > estimate.rent_estimate
            assert estimate.comp_count == 0  # HUD fallback has no comps
        finally:
            await client.close()


class TestPropertyUrlParser:
    """Tests for URL parser."""

    def test_detect_source_zillow(self):
        """Test detecting Zillow URLs."""
        parser = PropertyUrlParser()
        assert parser.detect_source("https://www.zillow.com/homedetails/123") == "zillow"
        assert parser.detect_source("https://zillow.com/homes/12345_zpid") == "zillow"

    def test_detect_source_redfin(self):
        """Test detecting Redfin URLs."""
        parser = PropertyUrlParser()
        assert parser.detect_source("https://www.redfin.com/CA/city/address") == "redfin"
        assert parser.detect_source("https://redfin.com/property/123") == "redfin"

    def test_detect_source_realtor(self):
        """Test detecting Realtor.com URLs."""
        parser = PropertyUrlParser()
        assert parser.detect_source("https://www.realtor.com/property/123") == "realtor"
        assert parser.detect_source("https://realtor.com/home/123") == "realtor"

    def test_detect_source_unknown(self):
        """Test unknown URLs return None."""
        parser = PropertyUrlParser()
        assert parser.detect_source("https://example.com/property") is None
        assert parser.detect_source("https://google.com") is None


class TestParsedProperty:
    """Tests for ParsedProperty model."""

    def test_to_property(self):
        """Test converting ParsedProperty to Property model."""
        parsed = ParsedProperty(
            url="https://zillow.com/test",
            source="zillow",
            address="123 Main St",
            city="Indianapolis",
            state="IN",
            zip_code="46201",
            list_price=200000,
            bedrooms=3,
            bathrooms=2,
            sqft=1500,
            property_type="single_family_home",
        )

        prop = parsed.to_property()

        assert prop.address == "123 Main St"
        assert prop.city == "Indianapolis"
        assert prop.state == "IN"
        assert prop.list_price == 200000
        assert prop.bedrooms == 3
        assert prop.source == "zillow"
        assert prop.source_url == "https://zillow.com/test"

    def test_property_type_mapping(self):
        """Test property type mapping to enum."""
        from src.models.property import PropertyType

        for ptype, expected in [
            ("single_family_home", PropertyType.SFH),
            ("condo", PropertyType.CONDO),
            ("townhouse", PropertyType.TOWNHOUSE),
            ("duplex", PropertyType.DUPLEX),
        ]:
            parsed = ParsedProperty(
                url="https://test.com",
                source="test",
                address="123 Main",
                city="Test",
                state="IN",
                zip_code="12345",
                list_price=100000,
                property_type=ptype,
            )
            prop = parsed.to_property()
            assert prop.property_type == expected


class TestEnrichedMarketData:
    """Tests for EnrichedMarketData."""

    def test_to_market(self):
        """Test converting enriched data to Market model."""
        data = EnrichedMarketData(
            market_id="test_in",
            name="Test City",
            state="IN",
            median_sale_price=250000,
            fmr_2br=1200,
            price_change_yoy=5.5,
        )

        market = data.to_market()

        assert market.name == "Test City"
        assert market.state == "IN"
        assert market.median_home_price == 250000
        assert market.median_rent == 1200

    def test_rent_to_price_ratio(self):
        """Test rent to price ratio calculation."""
        data = EnrichedMarketData(
            market_id="test",
            name="Test",
            state="IN",
            median_sale_price=200000,
            fmr_2br=1500,
        )

        # rent_to_price = (1500 / 200000) * 100 = 0.75%
        assert data.rent_to_price_ratio is None  # Not calculated in constructor

        # Check calculation in to_market
        market = data.to_market()
        assert market.avg_rent_to_price is not None
        assert 0.7 < market.avg_rent_to_price < 0.8


class TestDataAggregator:
    """Tests for DataAggregator."""

    @pytest.mark.asyncio
    async def test_initialization(self):
        """Test aggregator initializes with all clients."""
        aggregator = DataAggregator()

        assert aggregator.redfin is not None
        assert aggregator.fred is not None
        assert aggregator.hud is not None
        assert aggregator.rentcast is not None
        assert aggregator.url_parser is not None

        await aggregator.close()

    @pytest.mark.asyncio
    async def test_get_rent_estimate_fallback(self):
        """Test rent estimate falls back to HUD."""
        aggregator = DataAggregator()

        try:
            # Without RentCast API key, should fall back to HUD
            rent = await aggregator.get_rent_estimate(
                address="123 Main St",
                city="Indianapolis",
                state="IN",
                zip_code="46201",
                bedrooms=3,
            )

            # Should get HUD FMR estimate
            assert rent is not None
            assert rent > 0
        finally:
            await aggregator.close()
