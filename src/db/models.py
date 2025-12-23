"""SQLAlchemy ORM models for SQLite persistence."""

from datetime import datetime
from typing import Optional
import uuid
import json

from sqlalchemy import (
    Column, String, Boolean, Float, Integer, DateTime, Text, JSON,
    create_engine, event
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


def generate_uuid() -> str:
    """Generate a UUID string."""
    return str(uuid.uuid4())


class MarketDB(Base):
    """Market/metro area for investment targeting."""
    __tablename__ = 'markets'

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    state = Column(String(2), nullable=False)
    metro = Column(String)
    region = Column(String)

    # Tiers
    is_favorite = Column(Boolean, default=False)  # User's researched markets
    is_supported = Column(Boolean, default=True)  # APIs support this market

    # API support tracking
    api_support = Column(JSON, default=dict)  # {"listings": true, "income": true}

    # Cached market data (JSON blob of Market model)
    market_data = Column(JSON)

    # Scores (denormalized for quick queries)
    overall_score = Column(Float, default=0)
    cash_flow_score = Column(Float, default=0)
    growth_score = Column(Float, default=0)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Market {self.name}, {self.state}>"


class SavedPropertyDB(Base):
    """
    Saved/analyzed property with full analysis data.

    This is the "Enriched" tier of the property journey:
    - Tier 1 (Quick Score): Search results with basic metrics
    - Tier 2 (Full Analysis): Complete analysis on property detail pages
    - Tier 3 (Enriched): Persisted properties with all data + user customizations
    """
    __tablename__ = 'saved_properties'

    id = Column(String, primary_key=True, default=generate_uuid)

    # Location
    address = Column(String, nullable=False)
    city = Column(String, nullable=False)
    state = Column(String(2), nullable=False)
    zip_code = Column(String(10))
    latitude = Column(Float)  # For location data lookups
    longitude = Column(Float)

    # Property details
    list_price = Column(Float)
    estimated_rent = Column(Float)
    bedrooms = Column(Integer)
    bathrooms = Column(Float)
    sqft = Column(Integer)
    property_type = Column(String)
    year_built = Column(Integer)
    days_on_market = Column(Integer)

    # Source
    source = Column(String)  # zillow, redfin, realtor, live_search
    source_url = Column(String)

    # Full analysis (JSON blob of complete Deal model with financials, scores, market)
    analysis_data = Column(JSON)

    # Denormalized scores for quick queries/sorting
    overall_score = Column(Float)
    financial_score = Column(Float)
    market_score = Column(Float)
    risk_score = Column(Float)
    liquidity_score = Column(Float)
    cash_flow = Column(Float)
    cash_on_cash = Column(Float)
    cap_rate = Column(Float)

    # Location insights (cached from external APIs)
    # These are fetched once and persisted to avoid repeated API calls
    location_data = Column(JSON)  # {walk_score, transit_score, bike_score, noise, schools, flood_zone}

    # User's custom financing scenarios for "What Should I Offer" feature
    custom_scenarios = Column(JSON)  # [{offer_price, down_payment_pct, interest_rate, ...}, ...]

    # Pipeline and user data
    pipeline_status = Column(String, default='analyzed')  # new, analyzing, analyzed, shortlisted, rejected
    notes = Column(Text)
    tags = Column(JSON)  # User-defined tags for organization
    is_favorite = Column(Boolean, default=False)

    # Analysis timestamps
    last_analyzed = Column(DateTime)
    location_data_fetched = Column(DateTime)  # When location data was last refreshed

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<SavedProperty {self.address}, {self.city}>"

    def needs_location_refresh(self, max_age_days: int = 30) -> bool:
        """Check if location data needs refreshing."""
        if not self.location_data_fetched:
            return True
        age = (datetime.utcnow() - self.location_data_fetched).days
        return age > max_age_days


class SearchCacheDB(Base):
    """Cache for API search results."""
    __tablename__ = 'search_cache'

    id = Column(String, primary_key=True, default=generate_uuid)
    cache_key = Column(String, unique=True, nullable=False, index=True)  # Hash of provider + params
    provider = Column(String)  # us_real_estate_listings, income, etc.
    endpoint = Column(String)  # search, detail, rent-comps

    # Cached response
    results = Column(JSON)

    # TTL
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)

    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at

    def __repr__(self):
        return f"<SearchCache {self.provider}:{self.endpoint}>"


class IncomeCacheDB(Base):
    """Permanent cache for income data (census data rarely changes)."""
    __tablename__ = 'income_cache'

    zip_code = Column(String(5), primary_key=True)
    median_income = Column(Integer)
    income_tier = Column(String)  # high, middle, low-middle, low

    # Full response data
    data = Column(JSON)

    fetched_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<IncomeCache {self.zip_code}: ${self.median_income}>"


class ApiCallLogDB(Base):
    """Log of API calls for usage tracking and debugging."""
    __tablename__ = 'api_call_log'

    id = Column(String, primary_key=True, default=generate_uuid)
    provider = Column(String, nullable=False)
    endpoint = Column(String)
    params = Column(JSON)

    # Result
    success = Column(Boolean)
    response_code = Column(Integer)
    error_message = Column(String)

    # For cache deduplication
    cache_key = Column(String, index=True)
    cache_hit = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<ApiCallLog {self.provider}:{self.endpoint}>"


# Default favorite markets (user's researched list)
DEFAULT_FAVORITE_MARKETS = [
    {"name": "Indianapolis", "state": "IN", "metro": "Indianapolis-Carmel-Anderson"},
    {"name": "Cleveland", "state": "OH", "metro": "Cleveland-Elyria"},
    {"name": "Memphis", "state": "TN", "metro": "Memphis"},
    {"name": "Birmingham", "state": "AL", "metro": "Birmingham-Hoover"},
    {"name": "Kansas City", "state": "MO", "metro": "Kansas City"},
    {"name": "Tampa", "state": "FL", "metro": "Tampa-St. Petersburg-Clearwater"},
    {"name": "Phoenix", "state": "AZ", "metro": "Phoenix-Mesa-Chandler"},
    {"name": "Austin", "state": "TX", "metro": "Austin-Round Rock-Georgetown"},
]


def get_database_path() -> str:
    """Get the database file path."""
    import os
    from pathlib import Path

    # Use project root for database
    project_root = Path(__file__).parent.parent.parent
    db_path = project_root / "data" / "deals.db"

    # Ensure data directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)

    return str(db_path)


def get_engine(db_path: Optional[str] = None):
    """Get SQLAlchemy engine."""
    if db_path is None:
        db_path = get_database_path()

    engine = create_engine(
        f"sqlite:///{db_path}",
        echo=False,
        connect_args={"check_same_thread": False}
    )

    # Enable foreign keys for SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine


def get_session(engine=None):
    """Get a new database session."""
    if engine is None:
        engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()


def init_database(engine=None):
    """Initialize the database schema and seed data."""
    if engine is None:
        engine = get_engine()

    # Create all tables
    Base.metadata.create_all(engine)

    # Seed favorite markets if empty
    session = get_session(engine)
    try:
        if session.query(MarketDB).count() == 0:
            for market_data in DEFAULT_FAVORITE_MARKETS:
                market = MarketDB(
                    id=f"{market_data['name'].lower().replace(' ', '_')}_{market_data['state'].lower()}",
                    name=market_data["name"],
                    state=market_data["state"],
                    metro=market_data.get("metro"),
                    is_favorite=True,
                    is_supported=True,
                    api_support={"listings": True, "income": True},
                )
                session.add(market)
            session.commit()
            print(f"Seeded {len(DEFAULT_FAVORITE_MARKETS)} favorite markets")
    finally:
        session.close()

    return engine
