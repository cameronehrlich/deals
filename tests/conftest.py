"""Shared pytest fixtures for the test suite."""

import os
import tempfile
from datetime import datetime, timedelta
from typing import Generator
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from api.main import app
from src.db.models import (
    Base, MarketDB, SavedPropertyDB, SearchCacheDB, IncomeCacheDB, JobDB,
    get_engine, get_session
)
from src.db.sqlite_repository import SQLiteRepository, reset_repository, set_test_db_path
from src.models.property import Property, PropertyType, PropertyStatus


from src.models.financials import Financials, LoanTerms, OperatingExpenses
from src.models.market import Market, MarketTrend
from src.models.deal import Deal, DealPipeline, DealScore


# ==================== Session Setup/Teardown ====================

@pytest.fixture(scope="session", autouse=True)
def session_test_db():
    """Create a session-scoped temp database for all API tests.

    This ensures all tests that use the FastAPI app (via TestClient)
    write to a temp database instead of the main dev database.
    """
    # Create temp database file for the session
    with tempfile.NamedTemporaryFile(suffix="_test_session.db", delete=False) as f:
        session_db_path = f.name

    # Configure the global repository to use this temp database
    set_test_db_path(session_db_path)
    reset_repository()

    yield session_db_path

    # Cleanup: reset to default and delete temp file
    reset_repository()
    set_test_db_path(None)
    if os.path.exists(session_db_path):
        os.unlink(session_db_path)


# ==================== Database Fixtures ====================

@pytest.fixture
def temp_db_path() -> Generator[str, None, None]:
    """Create a temporary database file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    yield db_path
    # Cleanup after test
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def test_engine(temp_db_path: str):
    """Create a test database engine."""
    engine = create_engine(
        f"sqlite:///{temp_db_path}",
        echo=False,
        connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def test_session(test_engine) -> Generator[Session, None, None]:
    """Create a test database session."""
    SessionLocal = sessionmaker(bind=test_engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def repository(temp_db_path: str) -> Generator[SQLiteRepository, None, None]:
    """Create a test repository instance."""
    repo = SQLiteRepository(db_path=temp_db_path)
    yield repo
    repo.close()


# ==================== API Client Fixtures ====================

@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Create a FastAPI test client."""
    with TestClient(app) as c:
        yield c


# ==================== Sample Data Fixtures ====================

@pytest.fixture
def sample_property() -> Property:
    """Create a sample property for testing."""
    return Property(
        id="prop_test_123",
        address="123 Test Street",
        city="Phoenix",
        state="AZ",
        zip_code="85001",
        list_price=250000,
        estimated_rent=1800,
        bedrooms=3,
        bathrooms=2.0,
        sqft=1500,
        property_type=PropertyType.SFH,
        status=PropertyStatus.ACTIVE,
        days_on_market=30,
        year_built=2005,
        latitude=33.4484,
        longitude=-112.0740,
        source="test",
    )


@pytest.fixture
def sample_property_expensive() -> Property:
    """Create an expensive sample property for testing."""
    return Property(
        id="prop_test_456",
        address="456 Luxury Lane",
        city="Phoenix",
        state="AZ",
        zip_code="85001",
        list_price=500000,
        estimated_rent=2500,
        bedrooms=4,
        bathrooms=3.0,
        sqft=2500,
        property_type=PropertyType.SFH,
        status=PropertyStatus.ACTIVE,
        days_on_market=15,
        year_built=2015,
        latitude=33.4500,
        longitude=-112.0800,
        source="test",
    )


@pytest.fixture
def sample_financials(sample_property: Property) -> Financials:
    """Create sample financials for testing."""
    financials = Financials(
        property_id=sample_property.id,
        purchase_price=sample_property.list_price,
        estimated_rent=sample_property.estimated_rent,
        loan=LoanTerms(down_payment_pct=0.25, interest_rate=0.07),
        expenses=OperatingExpenses(),
    )
    financials.calculate()
    return financials


@pytest.fixture
def sample_market() -> Market:
    """Create a sample market for testing."""
    return Market(
        id="phoenix_az",
        name="Phoenix",
        state="AZ",
        metro="Phoenix-Mesa-Chandler",
        region="Southwest",
        population=1700000,
        population_growth_1yr=0.018,
        population_growth_5yr=0.12,
        unemployment_rate=0.038,
        job_growth_1yr=0.025,
        median_household_income=65000,
        median_home_price=380000,
        median_rent=1650,
        avg_rent_to_price=0.0043,
        price_change_1yr=0.08,
        price_change_5yr=0.45,
        rent_change_1yr=0.05,
        months_of_inventory=2.5,
        days_on_market_avg=25,
        price_trend=MarketTrend.MODERATE_GROWTH,
        rent_trend=MarketTrend.MODERATE_GROWTH,
        landlord_friendly=True,
        property_tax_rate=0.0065,
    )


@pytest.fixture
def sample_market_unfavorable() -> Market:
    """Create an unfavorable sample market for testing."""
    return Market(
        id="expensive_ca",
        name="San Francisco",
        state="CA",
        metro="San Francisco-Oakland",
        region="West",
        population=880000,
        population_growth_1yr=-0.02,
        unemployment_rate=0.045,
        job_growth_1yr=0.01,
        median_household_income=120000,
        median_home_price=1200000,
        median_rent=3500,
        avg_rent_to_price=0.0029,
        price_change_1yr=-0.05,
        rent_change_1yr=-0.02,
        months_of_inventory=4.5,
        days_on_market_avg=45,
        price_trend=MarketTrend.MODERATE_DECLINE,
        rent_trend=MarketTrend.STABLE,
        landlord_friendly=False,
        property_tax_rate=0.012,
    )


@pytest.fixture
def sample_deal(sample_property: Property, sample_financials: Financials, sample_market: Market) -> Deal:
    """Create a sample deal for testing."""
    deal = Deal(
        id=f"deal_{sample_property.id}",
        property=sample_property,
        financials=sample_financials,
        market=sample_market,
        pipeline_status=DealPipeline.ANALYZED,
    )
    deal.analyze()
    return deal


@pytest.fixture
def sample_deal_score() -> DealScore:
    """Create a sample deal score for testing."""
    return DealScore(
        property_id="test_prop",
        financial_score=75.0,
        market_score=70.0,
        risk_score=65.0,
        liquidity_score=60.0,
        overall_score=70.0,
    )


# ==================== Database Record Fixtures ====================

@pytest.fixture
def saved_market_db(test_session: Session) -> MarketDB:
    """Create a saved market in the test database."""
    market = MarketDB(
        id="phoenix_az",
        name="Phoenix",
        state="AZ",
        metro="Phoenix-Mesa-Chandler",
        is_favorite=True,
        is_supported=True,
        overall_score=75.0,
        cash_flow_score=80.0,
        growth_score=70.0,
    )
    test_session.add(market)
    test_session.commit()
    return market


@pytest.fixture
def saved_property_db(test_session: Session) -> SavedPropertyDB:
    """Create a saved property in the test database."""
    prop = SavedPropertyDB(
        id="saved_prop_123",
        address="123 Test Street",
        city="Phoenix",
        state="AZ",
        zip_code="85001",
        list_price=250000,
        estimated_rent=1800,
        bedrooms=3,
        bathrooms=2.0,
        sqft=1500,
        property_type="single_family",
        overall_score=72.0,
        cash_flow=350.0,
        cash_on_cash=0.085,
        cap_rate=0.065,
        pipeline_status="analyzed",
        is_favorite=False,
    )
    test_session.add(prop)
    test_session.commit()
    return prop


@pytest.fixture
def cached_search_result(test_session: Session) -> SearchCacheDB:
    """Create a cached search result in the test database."""
    cache = SearchCacheDB(
        id="cache_123",
        cache_key="search:phoenix_az:250000",
        provider="us_real_estate_listings",
        endpoint="search",
        results={"properties": [{"id": "test", "address": "123 Test St"}]},
        expires_at=datetime.utcnow() + timedelta(hours=1),
    )
    test_session.add(cache)
    test_session.commit()
    return cache


@pytest.fixture
def pending_job_db(test_session: Session) -> JobDB:
    """Create a pending job in the test database."""
    job = JobDB(
        id="job_123",
        job_type="enrich_market",
        payload={"market_id": "phoenix_az"},
        status="pending",
        priority=1,
    )
    test_session.add(job)
    test_session.commit()
    return job


# ==================== Utility Functions ====================

def create_test_property(
    id: str = "test_prop",
    price: float = 250000,
    rent: float = 1800,
    city: str = "Phoenix",
    state: str = "AZ",
) -> Property:
    """Factory function to create test properties."""
    return Property(
        id=id,
        address=f"{id} Test Street",
        city=city,
        state=state,
        zip_code="85001",
        list_price=price,
        estimated_rent=rent,
        bedrooms=3,
        bathrooms=2.0,
        sqft=1500,
        property_type=PropertyType.SFH,
        status=PropertyStatus.ACTIVE,
        days_on_market=30,
        source="test",
    )


def create_test_deal(
    property: Property,
    market: Market = None,
    run_analysis: bool = True,
) -> Deal:
    """Factory function to create test deals."""
    financials = Financials(
        property_id=property.id,
        purchase_price=property.list_price,
        estimated_rent=property.estimated_rent,
        loan=LoanTerms(down_payment_pct=0.25, interest_rate=0.07),
        expenses=OperatingExpenses(),
    )
    financials.calculate()

    deal = Deal(
        id=f"deal_{property.id}",
        property=property,
        financials=financials,
        market=market,
        pipeline_status=DealPipeline.NEW,
    )

    if run_analysis:
        deal.analyze()

    return deal
