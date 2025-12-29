"""
Financing API routes.

Phase 5.1: Financing Scenarios
- Loan product management (presets)
- Calculate financing scenarios for properties
- DSCR calculation
- Break-even analysis
"""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.db.models import (
    LoanProductDB, get_session, get_engine
)

router = APIRouter()


# ==================== Pydantic Models ====================

class LoanProductBase(BaseModel):
    """Base loan product fields."""
    name: str
    description: Optional[str] = None
    down_payment_pct: float = 0.25
    interest_rate: float = 0.07
    loan_term_years: int = 30
    points: float = 0
    closing_cost_pct: float = 0.03
    is_dscr: bool = False
    min_dscr_required: Optional[float] = None
    loan_type: Optional[str] = None
    is_default: bool = False


class LoanProductCreate(LoanProductBase):
    """Create a new loan product."""
    pass


class LoanProductUpdate(BaseModel):
    """Update loan product fields (all optional)."""
    name: Optional[str] = None
    description: Optional[str] = None
    down_payment_pct: Optional[float] = None
    interest_rate: Optional[float] = None
    loan_term_years: Optional[int] = None
    points: Optional[float] = None
    closing_cost_pct: Optional[float] = None
    is_dscr: Optional[bool] = None
    min_dscr_required: Optional[float] = None
    loan_type: Optional[str] = None
    is_default: Optional[bool] = None


class LoanProductResponse(LoanProductBase):
    """Loan product response."""
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FinancingScenarioRequest(BaseModel):
    """Request to calculate a financing scenario."""
    purchase_price: float
    monthly_rent: float
    down_payment_pct: float = 0.25
    interest_rate: float = 0.07
    loan_term_years: int = 30
    closing_cost_pct: float = 0.03
    points: float = 0
    # Operating expenses (optional overrides)
    property_tax_rate: float = 0.012  # Annual as % of value
    insurance_rate: float = 0.005  # Annual as % of value
    vacancy_rate: float = 0.08
    maintenance_rate: float = 0.01  # Annual as % of value
    capex_rate: float = 0.01  # Annual as % of value
    property_management_rate: float = 0.10  # % of rent
    hoa_monthly: float = 0


class FinancingScenarioResponse(BaseModel):
    """Calculated financing scenario results."""
    # Input summary
    purchase_price: float
    monthly_rent: float
    down_payment_pct: float
    interest_rate: float
    loan_term_years: int

    # Cash needed
    down_payment: float
    closing_costs: float
    points_cost: float
    total_cash_needed: float

    # Loan details
    loan_amount: float
    monthly_mortgage: float

    # Operating expenses (monthly)
    monthly_taxes: float
    monthly_insurance: float
    monthly_vacancy: float
    monthly_maintenance: float
    monthly_capex: float
    monthly_property_management: float
    monthly_hoa: float
    total_monthly_expenses: float

    # Performance metrics
    monthly_cash_flow: float
    annual_cash_flow: float
    cash_on_cash_return: float
    cap_rate: float
    gross_rent_multiplier: float
    rent_to_price_ratio: float
    break_even_occupancy: float

    # DSCR
    dscr: float
    qualifies_for_dscr: bool
    dscr_status: str  # "qualifies", "borderline", "does_not_qualify"


class CompareScenarioRequest(BaseModel):
    """Request to compare multiple financing scenarios."""
    purchase_price: float
    monthly_rent: float
    loan_product_ids: Optional[List[str]] = None  # If None, use all defaults
    # Operating expenses
    property_tax_rate: float = 0.012
    insurance_rate: float = 0.005
    vacancy_rate: float = 0.08
    maintenance_rate: float = 0.01
    capex_rate: float = 0.01
    property_management_rate: float = 0.10
    hoa_monthly: float = 0


class BreakEvenRequest(BaseModel):
    """Request to calculate break-even points."""
    purchase_price: float
    monthly_rent: float
    down_payment_pct: float = 0.25
    interest_rate: float = 0.07
    loan_term_years: int = 30
    closing_cost_pct: float = 0.03
    target_cash_on_cash: float = 0.08  # Target CoC (e.g., 8%)
    target_cash_flow: float = 200  # Target monthly cash flow


class BreakEvenResponse(BaseModel):
    """Break-even analysis results."""
    # Current scenario results
    current_cash_flow: float
    current_coc: float

    # Break-even interest rate
    break_even_rate: Optional[float] = None
    rate_cushion: Optional[float] = None  # How much rate can increase before break-even

    # Break-even vacancy
    break_even_vacancy: Optional[float] = None
    vacancy_cushion: Optional[float] = None

    # Break-even rent
    break_even_rent: Optional[float] = None
    rent_cushion_pct: Optional[float] = None

    # To achieve targets
    price_for_target_coc: Optional[float] = None
    down_payment_for_target_coc: Optional[float] = None
    rate_for_target_cash_flow: Optional[float] = None


# ==================== Helper Functions ====================

def calculate_mortgage_payment(principal: float, annual_rate: float, years: int) -> float:
    """Calculate monthly mortgage payment (P&I)."""
    if principal <= 0 or years <= 0:
        return 0
    if annual_rate == 0:
        return principal / (years * 12)
    monthly_rate = annual_rate / 12
    num_payments = years * 12
    return principal * (monthly_rate * (1 + monthly_rate) ** num_payments) / \
           ((1 + monthly_rate) ** num_payments - 1)


def calculate_scenario(
    purchase_price: float,
    monthly_rent: float,
    down_payment_pct: float,
    interest_rate: float,
    loan_term_years: int,
    closing_cost_pct: float = 0.03,
    points: float = 0,
    property_tax_rate: float = 0.012,
    insurance_rate: float = 0.005,
    vacancy_rate: float = 0.08,
    maintenance_rate: float = 0.01,
    capex_rate: float = 0.01,
    property_management_rate: float = 0.10,
    hoa_monthly: float = 0,
) -> FinancingScenarioResponse:
    """Calculate a complete financing scenario."""
    # Cash needed
    down_payment = purchase_price * down_payment_pct
    closing_costs = purchase_price * closing_cost_pct
    loan_amount = purchase_price - down_payment
    points_cost = loan_amount * (points / 100) if points > 0 else 0
    total_cash_needed = down_payment + closing_costs + points_cost

    # Monthly mortgage
    monthly_mortgage = calculate_mortgage_payment(loan_amount, interest_rate, loan_term_years)

    # Monthly operating expenses
    monthly_taxes = (purchase_price * property_tax_rate) / 12
    monthly_insurance = (purchase_price * insurance_rate) / 12
    monthly_vacancy = monthly_rent * vacancy_rate
    monthly_maintenance = (purchase_price * maintenance_rate) / 12
    monthly_capex = (purchase_price * capex_rate) / 12
    monthly_pm = monthly_rent * property_management_rate

    total_monthly_expenses = (
        monthly_mortgage + monthly_taxes + monthly_insurance +
        monthly_vacancy + monthly_maintenance + monthly_capex +
        monthly_pm + hoa_monthly
    )

    # Cash flow
    monthly_cash_flow = monthly_rent - total_monthly_expenses
    annual_cash_flow = monthly_cash_flow * 12

    # Performance metrics
    cash_on_cash = annual_cash_flow / total_cash_needed if total_cash_needed > 0 else 0

    # NOI (before debt service)
    annual_operating_expenses = (
        monthly_taxes + monthly_insurance + monthly_vacancy +
        monthly_maintenance + monthly_capex + monthly_pm + hoa_monthly
    ) * 12
    noi = (monthly_rent * 12) - annual_operating_expenses
    cap_rate = noi / purchase_price if purchase_price > 0 else 0

    gross_rent_multiplier = purchase_price / (monthly_rent * 12) if monthly_rent > 0 else 0
    rent_to_price = monthly_rent / purchase_price if purchase_price > 0 else 0

    # Break-even occupancy
    fixed_expenses = monthly_mortgage + monthly_taxes + monthly_insurance + monthly_maintenance + monthly_capex + hoa_monthly
    variable_expenses_rate = property_management_rate  # PM scales with rent
    break_even_occupancy = fixed_expenses / (monthly_rent * (1 - variable_expenses_rate)) if monthly_rent > 0 else 1

    # DSCR calculation
    # DSCR = NOI / Annual Debt Service
    annual_debt_service = monthly_mortgage * 12
    # For cash purchases (no debt), DSCR is undefined - use 999 as a placeholder
    dscr = noi / annual_debt_service if annual_debt_service > 0 else 999.0

    # DSCR qualification status
    if dscr >= 1.25:
        dscr_status = "qualifies"
        qualifies_for_dscr = True
    elif dscr >= 1.0:
        dscr_status = "borderline"
        qualifies_for_dscr = False
    else:
        dscr_status = "does_not_qualify"
        qualifies_for_dscr = False

    return FinancingScenarioResponse(
        purchase_price=purchase_price,
        monthly_rent=monthly_rent,
        down_payment_pct=down_payment_pct,
        interest_rate=interest_rate,
        loan_term_years=loan_term_years,
        down_payment=down_payment,
        closing_costs=closing_costs,
        points_cost=points_cost,
        total_cash_needed=total_cash_needed,
        loan_amount=loan_amount,
        monthly_mortgage=monthly_mortgage,
        monthly_taxes=monthly_taxes,
        monthly_insurance=monthly_insurance,
        monthly_vacancy=monthly_vacancy,
        monthly_maintenance=monthly_maintenance,
        monthly_capex=monthly_capex,
        monthly_property_management=monthly_pm,
        monthly_hoa=hoa_monthly,
        total_monthly_expenses=total_monthly_expenses,
        monthly_cash_flow=monthly_cash_flow,
        annual_cash_flow=annual_cash_flow,
        cash_on_cash_return=cash_on_cash,
        cap_rate=cap_rate,
        gross_rent_multiplier=gross_rent_multiplier,
        rent_to_price_ratio=rent_to_price,
        break_even_occupancy=min(break_even_occupancy, 1.0),
        dscr=dscr,
        qualifies_for_dscr=qualifies_for_dscr,
        dscr_status=dscr_status,
    )


# ==================== Loan Products Routes ====================

@router.get("/loan-products", response_model=List[LoanProductResponse])
async def get_loan_products(
    defaults_only: bool = False,
    loan_type: Optional[str] = None,
):
    """Get all loan products (presets)."""
    session = get_session(get_engine())
    try:
        query = session.query(LoanProductDB)

        if defaults_only:
            query = query.filter(LoanProductDB.is_default == True)

        if loan_type:
            query = query.filter(LoanProductDB.loan_type == loan_type)

        products = query.order_by(LoanProductDB.name).all()
        return [LoanProductResponse.model_validate(p) for p in products]
    finally:
        session.close()


@router.get("/loan-products/{product_id}", response_model=LoanProductResponse)
async def get_loan_product(product_id: str):
    """Get a specific loan product."""
    session = get_session(get_engine())
    try:
        product = session.query(LoanProductDB).filter(LoanProductDB.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Loan product not found")
        return LoanProductResponse.model_validate(product)
    finally:
        session.close()


@router.post("/loan-products", response_model=LoanProductResponse)
async def create_loan_product(data: LoanProductCreate):
    """Create a new loan product."""
    session = get_session(get_engine())
    try:
        product = LoanProductDB(**data.model_dump())
        session.add(product)
        session.commit()
        session.refresh(product)
        return LoanProductResponse.model_validate(product)
    finally:
        session.close()


@router.patch("/loan-products/{product_id}", response_model=LoanProductResponse)
async def update_loan_product(product_id: str, data: LoanProductUpdate):
    """Update a loan product."""
    session = get_session(get_engine())
    try:
        product = session.query(LoanProductDB).filter(LoanProductDB.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Loan product not found")

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(product, key, value)

        product.updated_at = datetime.utcnow()
        session.commit()
        session.refresh(product)
        return LoanProductResponse.model_validate(product)
    finally:
        session.close()


@router.delete("/loan-products/{product_id}")
async def delete_loan_product(product_id: str):
    """Delete a loan product."""
    session = get_session(get_engine())
    try:
        product = session.query(LoanProductDB).filter(LoanProductDB.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Loan product not found")

        session.delete(product)
        session.commit()
        return {"success": True, "message": f"Deleted loan product: {product.name}"}
    finally:
        session.close()


# ==================== Scenario Calculation Routes ====================

@router.post("/calculate", response_model=FinancingScenarioResponse)
async def calculate_financing_scenario(request: FinancingScenarioRequest):
    """Calculate a financing scenario with custom inputs."""
    return calculate_scenario(
        purchase_price=request.purchase_price,
        monthly_rent=request.monthly_rent,
        down_payment_pct=request.down_payment_pct,
        interest_rate=request.interest_rate,
        loan_term_years=request.loan_term_years,
        closing_cost_pct=request.closing_cost_pct,
        points=request.points,
        property_tax_rate=request.property_tax_rate,
        insurance_rate=request.insurance_rate,
        vacancy_rate=request.vacancy_rate,
        maintenance_rate=request.maintenance_rate,
        capex_rate=request.capex_rate,
        property_management_rate=request.property_management_rate,
        hoa_monthly=request.hoa_monthly,
    )


@router.post("/compare", response_model=List[FinancingScenarioResponse])
async def compare_financing_scenarios(request: CompareScenarioRequest):
    """Compare multiple financing scenarios using loan products."""
    session = get_session(get_engine())
    try:
        # Get loan products to compare
        if request.loan_product_ids:
            products = session.query(LoanProductDB).filter(
                LoanProductDB.id.in_(request.loan_product_ids)
            ).all()
        else:
            # Use default products
            products = session.query(LoanProductDB).filter(
                LoanProductDB.is_default == True
            ).all()

        if not products:
            raise HTTPException(status_code=400, detail="No loan products found")

        # Calculate scenario for each product
        scenarios = []
        for product in products:
            scenario = calculate_scenario(
                purchase_price=request.purchase_price,
                monthly_rent=request.monthly_rent,
                down_payment_pct=product.down_payment_pct,
                interest_rate=product.interest_rate,
                loan_term_years=product.loan_term_years,
                closing_cost_pct=product.closing_cost_pct,
                points=product.points or 0,
                property_tax_rate=request.property_tax_rate,
                insurance_rate=request.insurance_rate,
                vacancy_rate=request.vacancy_rate,
                maintenance_rate=request.maintenance_rate,
                capex_rate=request.capex_rate,
                property_management_rate=request.property_management_rate,
                hoa_monthly=request.hoa_monthly,
            )
            scenarios.append(scenario)

        return scenarios
    finally:
        session.close()


@router.post("/break-even", response_model=BreakEvenResponse)
async def calculate_break_even(request: BreakEvenRequest):
    """Calculate break-even points for a financing scenario."""
    # Calculate current scenario
    current = calculate_scenario(
        purchase_price=request.purchase_price,
        monthly_rent=request.monthly_rent,
        down_payment_pct=request.down_payment_pct,
        interest_rate=request.interest_rate,
        loan_term_years=request.loan_term_years,
        closing_cost_pct=request.closing_cost_pct,
    )

    result = BreakEvenResponse(
        current_cash_flow=current.monthly_cash_flow,
        current_coc=current.cash_on_cash_return,
    )

    # Break-even interest rate (binary search)
    if current.monthly_cash_flow > 0:
        low, high = request.interest_rate, request.interest_rate + 0.20
        for _ in range(20):
            mid = (low + high) / 2
            scenario = calculate_scenario(
                purchase_price=request.purchase_price,
                monthly_rent=request.monthly_rent,
                down_payment_pct=request.down_payment_pct,
                interest_rate=mid,
                loan_term_years=request.loan_term_years,
                closing_cost_pct=request.closing_cost_pct,
            )
            if scenario.monthly_cash_flow > 0:
                low = mid
            else:
                high = mid
        result.break_even_rate = (low + high) / 2
        result.rate_cushion = result.break_even_rate - request.interest_rate

    # Break-even vacancy (binary search)
    if current.monthly_cash_flow > 0:
        low, high = 0.08, 1.0
        for _ in range(20):
            mid = (low + high) / 2
            scenario = calculate_scenario(
                purchase_price=request.purchase_price,
                monthly_rent=request.monthly_rent,
                down_payment_pct=request.down_payment_pct,
                interest_rate=request.interest_rate,
                loan_term_years=request.loan_term_years,
                closing_cost_pct=request.closing_cost_pct,
                vacancy_rate=mid,
            )
            if scenario.monthly_cash_flow > 0:
                low = mid
            else:
                high = mid
        result.break_even_vacancy = (low + high) / 2
        result.vacancy_cushion = result.break_even_vacancy - 0.08

    # Break-even rent
    if current.monthly_cash_flow > 0:
        low, high = 0, request.monthly_rent
        for _ in range(20):
            mid = (low + high) / 2
            scenario = calculate_scenario(
                purchase_price=request.purchase_price,
                monthly_rent=mid,
                down_payment_pct=request.down_payment_pct,
                interest_rate=request.interest_rate,
                loan_term_years=request.loan_term_years,
                closing_cost_pct=request.closing_cost_pct,
            )
            if scenario.monthly_cash_flow > 0:
                high = mid
            else:
                low = mid
        result.break_even_rent = (low + high) / 2
        result.rent_cushion_pct = (request.monthly_rent - result.break_even_rent) / request.monthly_rent

    # Price for target CoC (binary search)
    if request.target_cash_on_cash > 0:
        low, high = request.purchase_price * 0.5, request.purchase_price
        for _ in range(20):
            mid = (low + high) / 2
            scenario = calculate_scenario(
                purchase_price=mid,
                monthly_rent=request.monthly_rent,
                down_payment_pct=request.down_payment_pct,
                interest_rate=request.interest_rate,
                loan_term_years=request.loan_term_years,
                closing_cost_pct=request.closing_cost_pct,
            )
            if scenario.cash_on_cash_return >= request.target_cash_on_cash:
                low = mid
            else:
                high = mid
        result.price_for_target_coc = (low + high) / 2

    # Rate for target cash flow (binary search)
    if request.target_cash_flow > 0 and current.monthly_cash_flow < request.target_cash_flow:
        low, high = 0.01, request.interest_rate
        for _ in range(20):
            mid = (low + high) / 2
            scenario = calculate_scenario(
                purchase_price=request.purchase_price,
                monthly_rent=request.monthly_rent,
                down_payment_pct=request.down_payment_pct,
                interest_rate=mid,
                loan_term_years=request.loan_term_years,
                closing_cost_pct=request.closing_cost_pct,
            )
            if scenario.monthly_cash_flow >= request.target_cash_flow:
                low = mid
            else:
                high = mid
        result.rate_for_target_cash_flow = (low + high) / 2

    return result


@router.get("/dscr-check")
async def check_dscr(
    purchase_price: float,
    monthly_rent: float,
    down_payment_pct: float = 0.25,
    interest_rate: float = 0.075,
    loan_term_years: int = 30,
    min_dscr_required: float = 1.25,
):
    """Quick DSCR check for a property."""
    scenario = calculate_scenario(
        purchase_price=purchase_price,
        monthly_rent=monthly_rent,
        down_payment_pct=down_payment_pct,
        interest_rate=interest_rate,
        loan_term_years=loan_term_years,
    )

    return {
        "dscr": round(scenario.dscr, 2),
        "min_required": min_dscr_required,
        "qualifies": scenario.dscr >= min_dscr_required,
        "status": scenario.dscr_status,
        "shortfall": round(min_dscr_required - scenario.dscr, 2) if scenario.dscr < min_dscr_required else 0,
        "monthly_cash_flow": round(scenario.monthly_cash_flow, 2),
        "suggestions": _get_dscr_suggestions(scenario, min_dscr_required),
    }


def _get_dscr_suggestions(scenario: FinancingScenarioResponse, min_dscr: float) -> List[str]:
    """Generate suggestions for improving DSCR."""
    suggestions = []
    if scenario.dscr < min_dscr:
        gap = min_dscr - scenario.dscr
        # Suggest higher down payment
        if scenario.down_payment_pct < 0.30:
            suggestions.append("Increase down payment to reduce loan amount")
        # Suggest better rate
        suggestions.append(f"Find a rate ~0.5% lower to improve DSCR")
        # Suggest negotiating price
        price_reduction = scenario.purchase_price * 0.05
        suggestions.append(f"Negotiate ~${price_reduction:,.0f} off purchase price")
    return suggestions
