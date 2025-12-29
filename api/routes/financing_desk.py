"""
Financing Desk API routes.

Phase 5.3: Financing Desk
- Borrower profile (one-time setup)
- Lender directory
- Lender quotes for properties
- Deal packet generation
"""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.db.models import (
    BorrowerProfileDB, LenderDB, LenderQuoteDB,
    get_session, get_engine
)

router = APIRouter()


# ==================== Borrower Profile Models ====================

class BorrowerProfileBase(BaseModel):
    """Base borrower profile fields."""
    full_name: Optional[str] = None
    entity_name: Optional[str] = None
    entity_type: Optional[str] = None  # individual, llc, trust
    annual_income: Optional[float] = None
    liquid_assets: Optional[float] = None
    total_net_worth: Optional[float] = None
    credit_score_range: Optional[str] = None
    properties_owned: int = 0
    years_investing: int = 0
    notes: Optional[str] = None


class BorrowerProfileUpdate(BorrowerProfileBase):
    """Update borrower profile."""
    pre_approvals: Optional[List[dict]] = None
    documents: Optional[dict] = None


class BorrowerProfileResponse(BorrowerProfileBase):
    """Borrower profile response."""
    id: str
    pre_approvals: List[dict]
    documents: dict
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== Lender Models ====================

class LenderBase(BaseModel):
    """Base lender fields."""
    name: str
    company: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    lender_type: Optional[str] = None  # bank, credit_union, mortgage_broker, portfolio, hard_money
    loan_types: List[str] = []
    markets_served: List[str] = []
    typical_rate_range: Optional[str] = None
    min_down_payment: Optional[float] = None
    min_credit_score: Optional[int] = None
    min_dscr: Optional[float] = None
    notes: Optional[str] = None
    pros: List[str] = []
    cons: List[str] = []


class LenderCreate(LenderBase):
    """Create a new lender."""
    pass


class LenderUpdate(BaseModel):
    """Update lender fields (all optional)."""
    name: Optional[str] = None
    company: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    lender_type: Optional[str] = None
    loan_types: Optional[List[str]] = None
    markets_served: Optional[List[str]] = None
    typical_rate_range: Optional[str] = None
    min_down_payment: Optional[float] = None
    min_credit_score: Optional[int] = None
    min_dscr: Optional[float] = None
    responsiveness_rating: Optional[int] = None
    accuracy_rating: Optional[int] = None
    overall_rating: Optional[int] = None
    deals_closed: Optional[int] = None
    notes: Optional[str] = None
    pros: Optional[List[str]] = None
    cons: Optional[List[str]] = None


class LenderResponse(LenderBase):
    """Lender response."""
    id: str
    responsiveness_rating: Optional[int] = None
    accuracy_rating: Optional[int] = None
    overall_rating: Optional[int] = None
    deals_closed: int = 0
    last_contacted: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== Lender Quote Models ====================

class LenderQuoteBase(BaseModel):
    """Base lender quote fields."""
    loan_amount: Optional[float] = None
    interest_rate: Optional[float] = None
    apr: Optional[float] = None
    points: Optional[float] = None
    origination_fee: Optional[float] = None
    other_fees: Optional[float] = None
    loan_type: Optional[str] = None
    term_years: Optional[int] = None
    amortization_years: Optional[int] = None
    is_fixed: bool = True
    arm_details: Optional[str] = None
    min_dscr: Optional[float] = None
    reserves_months: Optional[int] = None
    prepay_penalty: Optional[str] = None
    close_days: Optional[int] = None
    rate_lock_days: Optional[int] = None
    notes: Optional[str] = None
    conditions: List[str] = []


class LenderQuoteCreate(LenderQuoteBase):
    """Create a new lender quote."""
    lender_id: str
    property_id: str


class LenderQuoteUpdate(LenderQuoteBase):
    """Update lender quote fields."""
    status: Optional[str] = None
    expires_at: Optional[datetime] = None


class LenderQuoteResponse(LenderQuoteBase):
    """Lender quote response."""
    id: str
    lender_id: str
    property_id: str
    status: str
    expires_at: Optional[datetime] = None
    quoted_at: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class QuoteComparisonResponse(BaseModel):
    """Comparison of quotes for a property."""
    property_id: str
    quotes: List[LenderQuoteResponse]
    best_rate: Optional[LenderQuoteResponse] = None
    lowest_closing_cost: Optional[LenderQuoteResponse] = None
    fastest_close: Optional[LenderQuoteResponse] = None


# ==================== Deal Packet Models ====================

class DealPacketRequest(BaseModel):
    """Request to generate a deal packet."""
    property_id: str
    purchase_price: float
    estimated_rent: float
    down_payment_pct: float = 0.25
    exit_strategy: str = "long_term_hold"  # long_term_hold, brrrr, flip
    include_borrower_profile: bool = True


class DealPacketResponse(BaseModel):
    """Generated deal packet response."""
    property_id: str
    generated_at: datetime
    summary: dict
    financials: dict
    borrower_summary: Optional[dict] = None


# ==================== Borrower Profile Routes ====================

@router.get("/borrower-profile", response_model=Optional[BorrowerProfileResponse])
async def get_borrower_profile():
    """Get the borrower profile (single user system)."""
    session = get_session(get_engine())
    try:
        profile = session.query(BorrowerProfileDB).first()
        if not profile:
            return None
        return BorrowerProfileResponse.model_validate(profile)
    finally:
        session.close()


@router.post("/borrower-profile", response_model=BorrowerProfileResponse)
async def create_or_update_borrower_profile(data: BorrowerProfileUpdate):
    """Create or update the borrower profile."""
    session = get_session(get_engine())
    try:
        profile = session.query(BorrowerProfileDB).first()

        if not profile:
            # Create new profile
            profile = BorrowerProfileDB(
                full_name=data.full_name,
                entity_name=data.entity_name,
                entity_type=data.entity_type,
                annual_income=data.annual_income,
                liquid_assets=data.liquid_assets,
                total_net_worth=data.total_net_worth,
                credit_score_range=data.credit_score_range,
                properties_owned=data.properties_owned,
                years_investing=data.years_investing,
                notes=data.notes,
                pre_approvals=data.pre_approvals or [],
                documents=data.documents or {},
            )
            session.add(profile)
        else:
            # Update existing
            update_data = data.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(profile, key, value)
            profile.updated_at = datetime.utcnow()

        session.commit()
        session.refresh(profile)
        return BorrowerProfileResponse.model_validate(profile)
    finally:
        session.close()


# ==================== Lender Directory Routes ====================

@router.get("/lenders", response_model=List[LenderResponse])
async def get_lenders(
    lender_type: Optional[str] = None,
    loan_type: Optional[str] = None,
    market: Optional[str] = None,
    min_rating: Optional[int] = None,
):
    """Get all lenders with optional filtering."""
    session = get_session(get_engine())
    try:
        query = session.query(LenderDB)

        if lender_type:
            query = query.filter(LenderDB.lender_type == lender_type)

        if min_rating:
            query = query.filter(LenderDB.overall_rating >= min_rating)

        lenders = query.order_by(LenderDB.overall_rating.desc().nullslast()).all()

        # Filter by loan_type and market in Python (JSON columns)
        if loan_type:
            lenders = [l for l in lenders if loan_type in (l.loan_types or [])]
        if market:
            lenders = [l for l in lenders
                       if market in (l.markets_served or []) or "nationwide" in (l.markets_served or [])]

        return [LenderResponse.model_validate(l) for l in lenders]
    finally:
        session.close()


@router.get("/lenders/{lender_id}", response_model=LenderResponse)
async def get_lender(lender_id: str):
    """Get a specific lender."""
    session = get_session(get_engine())
    try:
        lender = session.query(LenderDB).filter(LenderDB.id == lender_id).first()
        if not lender:
            raise HTTPException(status_code=404, detail="Lender not found")
        return LenderResponse.model_validate(lender)
    finally:
        session.close()


@router.post("/lenders", response_model=LenderResponse)
async def create_lender(data: LenderCreate):
    """Create a new lender."""
    session = get_session(get_engine())
    try:
        lender = LenderDB(
            name=data.name,
            company=data.company,
            email=data.email,
            phone=data.phone,
            website=data.website,
            lender_type=data.lender_type,
            loan_types=data.loan_types,
            markets_served=data.markets_served,
            typical_rate_range=data.typical_rate_range,
            min_down_payment=data.min_down_payment,
            min_credit_score=data.min_credit_score,
            min_dscr=data.min_dscr,
            notes=data.notes,
            pros=data.pros,
            cons=data.cons,
        )
        session.add(lender)
        session.commit()
        session.refresh(lender)
        return LenderResponse.model_validate(lender)
    finally:
        session.close()


@router.patch("/lenders/{lender_id}", response_model=LenderResponse)
async def update_lender(lender_id: str, data: LenderUpdate):
    """Update a lender."""
    session = get_session(get_engine())
    try:
        lender = session.query(LenderDB).filter(LenderDB.id == lender_id).first()
        if not lender:
            raise HTTPException(status_code=404, detail="Lender not found")

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(lender, key, value)

        lender.updated_at = datetime.utcnow()
        session.commit()
        session.refresh(lender)
        return LenderResponse.model_validate(lender)
    finally:
        session.close()


@router.delete("/lenders/{lender_id}")
async def delete_lender(lender_id: str):
    """Delete a lender."""
    session = get_session(get_engine())
    try:
        lender = session.query(LenderDB).filter(LenderDB.id == lender_id).first()
        if not lender:
            raise HTTPException(status_code=404, detail="Lender not found")

        # Also delete associated quotes
        session.query(LenderQuoteDB).filter(LenderQuoteDB.lender_id == lender_id).delete()

        session.delete(lender)
        session.commit()
        return {"success": True, "message": f"Deleted lender: {lender.name}"}
    finally:
        session.close()


# ==================== Lender Quote Routes ====================

@router.get("/quotes", response_model=List[LenderQuoteResponse])
async def get_quotes(
    property_id: Optional[str] = None,
    lender_id: Optional[str] = None,
    status: Optional[str] = None,
):
    """Get quotes with optional filtering."""
    session = get_session(get_engine())
    try:
        query = session.query(LenderQuoteDB)

        if property_id:
            query = query.filter(LenderQuoteDB.property_id == property_id)

        if lender_id:
            query = query.filter(LenderQuoteDB.lender_id == lender_id)

        if status:
            query = query.filter(LenderQuoteDB.status == status)

        quotes = query.order_by(LenderQuoteDB.quoted_at.desc()).all()
        return [LenderQuoteResponse.model_validate(q) for q in quotes]
    finally:
        session.close()


@router.post("/quotes", response_model=LenderQuoteResponse)
async def create_quote(data: LenderQuoteCreate):
    """Create a new lender quote."""
    session = get_session(get_engine())
    try:
        # Verify lender exists
        lender = session.query(LenderDB).filter(LenderDB.id == data.lender_id).first()
        if not lender:
            raise HTTPException(status_code=404, detail="Lender not found")

        quote = LenderQuoteDB(
            lender_id=data.lender_id,
            property_id=data.property_id,
            loan_amount=data.loan_amount,
            interest_rate=data.interest_rate,
            apr=data.apr,
            points=data.points,
            origination_fee=data.origination_fee,
            other_fees=data.other_fees,
            loan_type=data.loan_type,
            term_years=data.term_years,
            amortization_years=data.amortization_years,
            is_fixed=data.is_fixed,
            arm_details=data.arm_details,
            min_dscr=data.min_dscr,
            reserves_months=data.reserves_months,
            prepay_penalty=data.prepay_penalty,
            close_days=data.close_days,
            rate_lock_days=data.rate_lock_days,
            notes=data.notes,
            conditions=data.conditions,
        )
        session.add(quote)
        session.commit()
        session.refresh(quote)
        return LenderQuoteResponse.model_validate(quote)
    finally:
        session.close()


@router.patch("/quotes/{quote_id}", response_model=LenderQuoteResponse)
async def update_quote(quote_id: str, data: LenderQuoteUpdate):
    """Update a lender quote."""
    session = get_session(get_engine())
    try:
        quote = session.query(LenderQuoteDB).filter(LenderQuoteDB.id == quote_id).first()
        if not quote:
            raise HTTPException(status_code=404, detail="Quote not found")

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(quote, key, value)

        quote.updated_at = datetime.utcnow()
        session.commit()
        session.refresh(quote)
        return LenderQuoteResponse.model_validate(quote)
    finally:
        session.close()


@router.delete("/quotes/{quote_id}")
async def delete_quote(quote_id: str):
    """Delete a lender quote."""
    session = get_session(get_engine())
    try:
        quote = session.query(LenderQuoteDB).filter(LenderQuoteDB.id == quote_id).first()
        if not quote:
            raise HTTPException(status_code=404, detail="Quote not found")

        session.delete(quote)
        session.commit()
        return {"success": True}
    finally:
        session.close()


@router.get("/quotes/compare/{property_id}", response_model=QuoteComparisonResponse)
async def compare_quotes(property_id: str):
    """Compare all quotes for a property."""
    session = get_session(get_engine())
    try:
        quotes = session.query(LenderQuoteDB).filter(
            LenderQuoteDB.property_id == property_id,
            LenderQuoteDB.status == "quoted"
        ).all()

        quote_responses = [LenderQuoteResponse.model_validate(q) for q in quotes]

        # Find best in each category
        best_rate = None
        lowest_closing = None
        fastest_close = None

        if quotes:
            # Best rate
            rate_quotes = [q for q in quotes if q.interest_rate]
            if rate_quotes:
                best = min(rate_quotes, key=lambda q: q.interest_rate)
                best_rate = LenderQuoteResponse.model_validate(best)

            # Lowest closing cost
            cost_quotes = [q for q in quotes if q.origination_fee is not None]
            if cost_quotes:
                best = min(cost_quotes, key=lambda q: (q.origination_fee or 0) + (q.other_fees or 0) + ((q.points or 0) * (q.loan_amount or 0) / 100))
                lowest_closing = LenderQuoteResponse.model_validate(best)

            # Fastest close
            close_quotes = [q for q in quotes if q.close_days]
            if close_quotes:
                best = min(close_quotes, key=lambda q: q.close_days)
                fastest_close = LenderQuoteResponse.model_validate(best)

        return QuoteComparisonResponse(
            property_id=property_id,
            quotes=quote_responses,
            best_rate=best_rate,
            lowest_closing_cost=lowest_closing,
            fastest_close=fastest_close,
        )
    finally:
        session.close()


# ==================== Deal Packet Route ====================

@router.post("/deal-packet", response_model=DealPacketResponse)
async def generate_deal_packet(request: DealPacketRequest):
    """Generate a lender-ready deal packet for a property."""
    from api.routes.financing import calculate_scenario

    session = get_session(get_engine())
    try:
        # Get borrower profile if requested
        borrower_summary = None
        if request.include_borrower_profile:
            profile = session.query(BorrowerProfileDB).first()
            if profile:
                borrower_summary = {
                    "name": profile.full_name or profile.entity_name,
                    "entity_type": profile.entity_type,
                    "credit_score_range": profile.credit_score_range,
                    "properties_owned": profile.properties_owned,
                    "years_experience": profile.years_investing,
                    "liquid_assets": profile.liquid_assets,
                }

        # Calculate financials
        scenario = calculate_scenario(
            purchase_price=request.purchase_price,
            monthly_rent=request.estimated_rent,
            down_payment_pct=request.down_payment_pct,
            interest_rate=0.075,  # Assumed rate for packet
            loan_term_years=30,
        )

        exit_strategies = {
            "long_term_hold": "Long-term buy and hold for cash flow",
            "brrrr": "BRRRR strategy - refinance after stabilization",
            "flip": "Fix and flip within 6-12 months",
        }

        return DealPacketResponse(
            property_id=request.property_id,
            generated_at=datetime.utcnow(),
            summary={
                "purchase_price": request.purchase_price,
                "estimated_rent": request.estimated_rent,
                "down_payment_pct": request.down_payment_pct,
                "exit_strategy": exit_strategies.get(request.exit_strategy, request.exit_strategy),
            },
            financials={
                "down_payment": scenario.down_payment,
                "loan_amount": scenario.loan_amount,
                "monthly_rent": request.estimated_rent,
                "monthly_expenses": scenario.total_monthly_expenses,
                "monthly_cash_flow": scenario.monthly_cash_flow,
                "annual_cash_flow": scenario.annual_cash_flow,
                "cash_on_cash_return": scenario.cash_on_cash_return,
                "cap_rate": scenario.cap_rate,
                "dscr": scenario.dscr,
                "qualifies_for_dscr": scenario.qualifies_for_dscr,
            },
            borrower_summary=borrower_summary,
        )
    finally:
        session.close()
