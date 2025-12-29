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
    photos = Column(JSON)  # List of photo URLs

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

    # Deal pipeline data (stage, due diligence checklist, stage history)
    deal_data = Column(JSON)  # {stage, stage_updated_at, stage_history, due_diligence}

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


class JobDB(Base):
    """Background job queue for async tasks."""
    __tablename__ = 'jobs'

    id = Column(String, primary_key=True, default=generate_uuid)

    # Job definition
    job_type = Column(String, nullable=False)  # enrich_market, enrich_property, etc.
    payload = Column(JSON)  # Job-specific data (e.g., {"market_id": "phoenix_az"})
    priority = Column(Integer, default=0)  # Higher = more urgent

    # Status tracking
    status = Column(String, default='pending')  # pending, running, completed, failed, cancelled
    progress = Column(Integer, default=0)  # 0-100
    message = Column(String)  # Current status message
    error = Column(Text)  # Error details if failed
    result = Column(JSON)  # Job result data

    # Timing
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)

    # Retry handling
    attempts = Column(Integer, default=0)
    max_attempts = Column(Integer, default=3)

    def __repr__(self):
        return f"<Job {self.job_type} ({self.status})>"


# ==================== Phase 5: Transaction Pipeline ====================

class LoanProductDB(Base):
    """
    Reusable loan product templates (presets).

    Examples: "Conventional 25% down", "DSCR 20% down", "Hard Money"
    These are user-maintained templates that can be quickly applied to properties.
    """
    __tablename__ = 'loan_products'

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)  # "Conventional 25%", "DSCR 20%", etc.
    description = Column(String)

    # Loan terms
    down_payment_pct = Column(Float, default=0.25)
    interest_rate = Column(Float, default=0.07)  # Annual rate
    loan_term_years = Column(Integer, default=30)
    points = Column(Float, default=0)
    closing_cost_pct = Column(Float, default=0.03)

    # DSCR-specific
    is_dscr = Column(Boolean, default=False)
    min_dscr_required = Column(Float)  # e.g., 1.25 for DSCR loans

    # Categorization
    loan_type = Column(String)  # conventional, dscr, hard_money, portfolio, fha, va
    is_default = Column(Boolean, default=False)  # Show in quick presets

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<LoanProduct {self.name}>"


class ContactDB(Base):
    """
    Contact tied to properties (agents, sellers, lenders).

    This is property-centric CRM - contacts exist in context of deals.
    """
    __tablename__ = 'contacts'

    id = Column(String, primary_key=True, default=generate_uuid)

    # Contact info
    name = Column(String, nullable=False)
    email = Column(String)
    phone = Column(String)
    company = Column(String)  # Brokerage, lending company, etc.

    # Role
    contact_type = Column(String)  # listing_agent, buyer_agent, seller, lender, other

    # Linked properties (JSON array of property IDs)
    property_ids = Column(JSON, default=list)

    # Agent-specific data (from API)
    agent_id = Column(String)  # External agent ID from API
    agent_photo_url = Column(String)
    agent_profile_data = Column(JSON)  # Full profile from API

    # User notes
    notes = Column(Text)

    # Status tracking
    last_contacted = Column(DateTime)
    next_followup = Column(DateTime)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Contact {self.name} ({self.contact_type})>"


class CommunicationDB(Base):
    """
    Communication log entry tied to a contact and property.

    Tracks all interactions: calls, emails, notes, meetings.
    """
    __tablename__ = 'communications'

    id = Column(String, primary_key=True, default=generate_uuid)

    # Links
    contact_id = Column(String, nullable=False, index=True)
    property_id = Column(String, index=True)  # Optional - some comms may be general

    # Communication details
    comm_type = Column(String, nullable=False)  # email, call, text, meeting, note
    direction = Column(String)  # inbound, outbound, internal
    subject = Column(String)
    content = Column(Text)

    # For email templates
    template_used = Column(String)  # Template ID if used

    # Metadata
    occurred_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Communication {self.comm_type} with {self.contact_id}>"


class OfferDB(Base):
    """
    Offer tracking for properties.

    Tracks offer submissions, counteroffers, and outcomes.
    """
    __tablename__ = 'offers'

    id = Column(String, primary_key=True, default=generate_uuid)
    property_id = Column(String, nullable=False, index=True)

    # Offer terms
    offer_price = Column(Float, nullable=False)
    down_payment_pct = Column(Float, default=0.25)
    financing_type = Column(String)  # conventional, dscr, cash, etc.
    earnest_money = Column(Float)

    # Contingencies
    contingencies = Column(JSON)  # ["inspection", "financing", "appraisal"]
    inspection_days = Column(Integer)
    financing_days = Column(Integer)
    closing_days = Column(Integer)

    # Status
    status = Column(String, default='draft')  # draft, submitted, countered, accepted, rejected, withdrawn, expired
    submitted_at = Column(DateTime)
    expires_at = Column(DateTime)
    response_deadline = Column(DateTime)

    # Counter offers (JSON array)
    counter_history = Column(JSON, default=list)  # [{price, date, notes}, ...]

    # Outcome
    final_price = Column(Float)  # If accepted
    outcome_notes = Column(Text)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Offer ${self.offer_price:,.0f} on {self.property_id} ({self.status})>"


class BorrowerProfileDB(Base):
    """
    User's borrower profile for financing.

    One-time setup that can be reused across all deal packets.
    Single record per user (for now, single-user system).
    """
    __tablename__ = 'borrower_profile'

    id = Column(String, primary_key=True, default=generate_uuid)

    # Personal info
    full_name = Column(String)
    entity_name = Column(String)  # LLC name if applicable
    entity_type = Column(String)  # individual, llc, trust

    # Financial snapshot
    annual_income = Column(Float)
    liquid_assets = Column(Float)
    total_net_worth = Column(Float)
    credit_score_range = Column(String)  # "740-760", "760-780", etc.

    # Experience
    properties_owned = Column(Integer, default=0)
    years_investing = Column(Integer, default=0)

    # Pre-approvals (JSON array)
    pre_approvals = Column(JSON, default=list)  # [{lender, amount, expires, type}, ...]

    # Document links (URLs to external storage)
    documents = Column(JSON, default=dict)  # {"pay_stubs": "url", "bank_statements": "url", ...}

    # Notes
    notes = Column(Text)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<BorrowerProfile {self.full_name or self.entity_name}>"


class LenderDB(Base):
    """
    Lender directory entry.

    User-maintained database of lenders with notes on rates,
    requirements, responsiveness, and markets served.
    """
    __tablename__ = 'lenders'

    id = Column(String, primary_key=True, default=generate_uuid)

    # Lender info
    name = Column(String, nullable=False)
    company = Column(String)
    email = Column(String)
    phone = Column(String)
    website = Column(String)

    # Specialization
    lender_type = Column(String)  # bank, credit_union, mortgage_broker, portfolio, hard_money
    loan_types = Column(JSON, default=list)  # ["conventional", "dscr", "hard_money"]
    markets_served = Column(JSON, default=list)  # ["FL", "TX"] or ["nationwide"]

    # Terms (general)
    typical_rate_range = Column(String)  # "6.5% - 7.5%"
    min_down_payment = Column(Float)
    min_credit_score = Column(Integer)
    min_dscr = Column(Float)

    # User experience tracking
    responsiveness_rating = Column(Integer)  # 1-5
    accuracy_rating = Column(Integer)  # 1-5 (quote vs final)
    overall_rating = Column(Integer)  # 1-5
    deals_closed = Column(Integer, default=0)

    # Notes
    notes = Column(Text)
    pros = Column(JSON, default=list)
    cons = Column(JSON, default=list)

    # Metadata
    last_contacted = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Lender {self.name}>"


class LenderQuoteDB(Base):
    """
    Specific quote from a lender for a property.

    Stores normalized quote data for comparison.
    """
    __tablename__ = 'lender_quotes'

    id = Column(String, primary_key=True, default=generate_uuid)

    # Links
    lender_id = Column(String, nullable=False, index=True)
    property_id = Column(String, nullable=False, index=True)

    # Loan terms
    loan_amount = Column(Float)
    interest_rate = Column(Float)
    apr = Column(Float)
    points = Column(Float)
    origination_fee = Column(Float)
    other_fees = Column(Float)

    # Structure
    loan_type = Column(String)  # conventional, dscr, arm, etc.
    term_years = Column(Integer)
    amortization_years = Column(Integer)
    is_fixed = Column(Boolean, default=True)
    arm_details = Column(String)  # "5/1 ARM" etc.

    # Requirements
    min_dscr = Column(Float)
    reserves_months = Column(Integer)
    prepay_penalty = Column(String)  # "None", "3-2-1", etc.

    # Timeline
    close_days = Column(Integer)
    rate_lock_days = Column(Integer)

    # Status
    status = Column(String, default='quoted')  # quoted, selected, declined, expired
    expires_at = Column(DateTime)

    # Notes
    notes = Column(Text)
    conditions = Column(JSON, default=list)  # ["Appraisal", "Updated bank statement"]

    # Metadata
    quoted_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<LenderQuote {self.interest_rate}% from {self.lender_id}>"


# Default loan products (presets)
DEFAULT_LOAN_PRODUCTS = [
    {
        "name": "Conventional 25% Down",
        "description": "Standard conventional loan with 25% down payment",
        "down_payment_pct": 0.25,
        "interest_rate": 0.07,
        "loan_term_years": 30,
        "closing_cost_pct": 0.03,
        "loan_type": "conventional",
        "is_dscr": False,
        "is_default": True,
    },
    {
        "name": "Conventional 20% Down",
        "description": "Conventional loan with 20% down (may require PMI)",
        "down_payment_pct": 0.20,
        "interest_rate": 0.0725,
        "loan_term_years": 30,
        "closing_cost_pct": 0.03,
        "loan_type": "conventional",
        "is_dscr": False,
        "is_default": True,
    },
    {
        "name": "DSCR 25% Down",
        "description": "Debt Service Coverage Ratio loan - no income verification",
        "down_payment_pct": 0.25,
        "interest_rate": 0.075,
        "loan_term_years": 30,
        "closing_cost_pct": 0.03,
        "loan_type": "dscr",
        "is_dscr": True,
        "min_dscr_required": 1.25,
        "is_default": True,
    },
    {
        "name": "DSCR 20% Down",
        "description": "DSCR loan with lower down payment",
        "down_payment_pct": 0.20,
        "interest_rate": 0.08,
        "loan_term_years": 30,
        "closing_cost_pct": 0.03,
        "loan_type": "dscr",
        "is_dscr": True,
        "min_dscr_required": 1.25,
        "is_default": True,
    },
    {
        "name": "Hard Money Bridge",
        "description": "Short-term hard money loan for acquisitions/rehab",
        "down_payment_pct": 0.25,
        "interest_rate": 0.12,
        "loan_term_years": 1,
        "points": 2.0,
        "closing_cost_pct": 0.04,
        "loan_type": "hard_money",
        "is_dscr": False,
        "is_default": True,
    },
    {
        "name": "All Cash",
        "description": "Cash purchase - no financing",
        "down_payment_pct": 1.0,
        "interest_rate": 0.0,
        "loan_term_years": 0,
        "closing_cost_pct": 0.02,
        "loan_type": "cash",
        "is_dscr": False,
        "is_default": True,
    },
]


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


def _run_migrations(engine):
    """
    Run database migrations for new columns on existing tables.
    This handles adding columns that were added after the initial schema.
    """
    from sqlalchemy import text, inspect

    inspector = inspect(engine)
    connection = engine.connect()

    try:
        # Migration 1: Add deal_data column to saved_properties if it doesn't exist
        if 'saved_properties' in inspector.get_table_names():
            columns = [col['name'] for col in inspector.get_columns('saved_properties')]
            if 'deal_data' not in columns:
                connection.execute(text(
                    "ALTER TABLE saved_properties ADD COLUMN deal_data JSON"
                ))
                connection.commit()
                print("Migration: Added deal_data column to saved_properties")

    except Exception as e:
        print(f"Migration warning: {e}")
    finally:
        connection.close()


def init_database(engine=None):
    """Initialize the database schema and seed data."""
    if engine is None:
        engine = get_engine()

    # Create all tables
    Base.metadata.create_all(engine)

    # Run migrations for new columns on existing tables
    _run_migrations(engine)

    # Seed all metros from local data
    session = get_session(engine)
    try:
        # Import local metro data
        from src.data_sources.metros import US_METROS
        from src.data_sources.hud_fmr import EMBEDDED_FMR_DATA

        # Get IDs of default favorites
        default_favorite_ids = {
            f"{m['name'].lower().replace(' ', '_')}_{m['state'].lower()}"
            for m in DEFAULT_FAVORITE_MARKETS
        }

        # Get existing market IDs to avoid duplicates
        existing_ids = {m.id for m in session.query(MarketDB).all()}

        added = 0
        for metro in US_METROS:
            if metro.id in existing_ids:
                continue

            # Check if this metro has HUD data (full support)
            has_hud = metro.id in EMBEDDED_FMR_DATA or metro.has_hud_data

            market = MarketDB(
                id=metro.id,
                name=metro.city,
                state=metro.state,
                metro=metro.metro_name,
                is_favorite=metro.id in default_favorite_ids,
                is_supported=True,
                api_support={
                    "listings": metro.has_redfin_data,
                    "bls": metro.has_bls_data,
                    "census": metro.has_census_data,
                    "hud": has_hud,
                },
            )
            session.add(market)
            added += 1

        if added > 0:
            session.commit()
            print(f"Seeded {added} markets from local metro data")
    except Exception as e:
        print(f"Warning: Could not seed metros: {e}")
        session.rollback()
    finally:
        session.close()

    # Seed default loan products
    session = get_session(engine)
    try:
        existing_loan_products = {lp.name for lp in session.query(LoanProductDB).all()}
        added_lp = 0
        for lp_data in DEFAULT_LOAN_PRODUCTS:
            if lp_data["name"] in existing_loan_products:
                continue
            loan_product = LoanProductDB(**lp_data)
            session.add(loan_product)
            added_lp += 1

        if added_lp > 0:
            session.commit()
            print(f"Seeded {added_lp} default loan products")
    except Exception as e:
        print(f"Warning: Could not seed loan products: {e}")
        session.rollback()
    finally:
        session.close()

    return engine
