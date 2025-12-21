"""Financial modeling data structures."""

from typing import Optional

from pydantic import BaseModel, Field, computed_field


class LoanTerms(BaseModel):
    """Loan parameters for mortgage calculation."""

    down_payment_pct: float = Field(default=0.25, ge=0, le=1, description="Down payment %")
    interest_rate: float = Field(default=0.07, ge=0, le=0.25, description="Annual rate")
    loan_term_years: int = Field(default=30, ge=1, le=40)
    points: float = Field(default=0, ge=0, description="Loan points")
    closing_cost_pct: float = Field(default=0.03, ge=0, le=0.10)


class OperatingExpenses(BaseModel):
    """Monthly/annual operating expense assumptions."""

    property_tax_rate: float = Field(default=0.012, description="Annual tax rate")
    insurance_annual: Optional[float] = Field(None, description="Annual insurance")
    insurance_rate: float = Field(default=0.005, description="Insurance as % of value")
    hoa_monthly: float = Field(default=0, ge=0)
    maintenance_rate: float = Field(default=0.01, description="Annual maintenance %")
    property_management_rate: float = Field(default=0.10, description="PM fee %")
    vacancy_rate: float = Field(default=0.08, description="Expected vacancy %")
    capex_rate: float = Field(default=0.01, description="Capital expenditure reserve %")
    utilities_monthly: float = Field(default=0, description="Landlord-paid utilities")


class Financials(BaseModel):
    """Complete financial analysis for a property."""

    property_id: str
    purchase_price: float = Field(..., gt=0)
    estimated_rent: float = Field(..., ge=0, description="Monthly rent")

    # Loan details
    loan: LoanTerms = Field(default_factory=LoanTerms)

    # Operating expenses
    expenses: OperatingExpenses = Field(default_factory=OperatingExpenses)

    # Appreciation assumptions
    annual_appreciation_rate: float = Field(default=0.03)
    annual_rent_growth_rate: float = Field(default=0.02)

    # Calculated values (set after computation)
    down_payment: Optional[float] = None
    loan_amount: Optional[float] = None
    closing_costs: Optional[float] = None
    total_cash_needed: Optional[float] = None
    monthly_mortgage: Optional[float] = None
    monthly_taxes: Optional[float] = None
    monthly_insurance: Optional[float] = None
    monthly_maintenance: Optional[float] = None
    monthly_capex: Optional[float] = None
    monthly_vacancy_reserve: Optional[float] = None
    monthly_property_management: Optional[float] = None
    total_monthly_expenses: Optional[float] = None
    net_operating_income: Optional[float] = None
    monthly_cash_flow: Optional[float] = None
    annual_cash_flow: Optional[float] = None

    def calculate(self) -> "Financials":
        """Calculate all financial metrics."""
        # Initial investment
        self.down_payment = self.purchase_price * self.loan.down_payment_pct
        self.loan_amount = self.purchase_price - self.down_payment
        self.closing_costs = self.purchase_price * self.loan.closing_cost_pct
        self.total_cash_needed = self.down_payment + self.closing_costs

        # Monthly mortgage payment (P&I)
        if self.loan_amount > 0:
            monthly_rate = self.loan.interest_rate / 12
            n_payments = self.loan.loan_term_years * 12
            if monthly_rate > 0:
                self.monthly_mortgage = self.loan_amount * (
                    monthly_rate * (1 + monthly_rate) ** n_payments
                ) / ((1 + monthly_rate) ** n_payments - 1)
            else:
                self.monthly_mortgage = self.loan_amount / n_payments
        else:
            self.monthly_mortgage = 0

        # Monthly operating expenses
        self.monthly_taxes = (self.purchase_price * self.expenses.property_tax_rate) / 12
        if self.expenses.insurance_annual:
            self.monthly_insurance = self.expenses.insurance_annual / 12
        else:
            self.monthly_insurance = (self.purchase_price * self.expenses.insurance_rate) / 12
        self.monthly_maintenance = (self.purchase_price * self.expenses.maintenance_rate) / 12
        self.monthly_capex = (self.purchase_price * self.expenses.capex_rate) / 12
        self.monthly_vacancy_reserve = self.estimated_rent * self.expenses.vacancy_rate
        self.monthly_property_management = self.estimated_rent * self.expenses.property_management_rate

        # Total expenses
        self.total_monthly_expenses = (
            self.monthly_mortgage
            + self.monthly_taxes
            + self.monthly_insurance
            + self.expenses.hoa_monthly
            + self.monthly_maintenance
            + self.monthly_capex
            + self.monthly_vacancy_reserve
            + self.monthly_property_management
            + self.expenses.utilities_monthly
        )

        # NOI (before debt service)
        annual_gross_rent = self.estimated_rent * 12
        annual_vacancy = annual_gross_rent * self.expenses.vacancy_rate
        annual_operating_expenses = (
            (self.monthly_taxes * 12)
            + (self.monthly_insurance * 12)
            + (self.expenses.hoa_monthly * 12)
            + (self.monthly_maintenance * 12)
            + (self.monthly_property_management * 12)
            + (self.expenses.utilities_monthly * 12)
        )
        self.net_operating_income = annual_gross_rent - annual_vacancy - annual_operating_expenses

        # Cash flow
        self.monthly_cash_flow = self.estimated_rent - self.total_monthly_expenses
        self.annual_cash_flow = self.monthly_cash_flow * 12

        return self


class FinancialMetrics(BaseModel):
    """Key investment metrics for a property."""

    property_id: str

    # Return metrics
    cash_on_cash_return: float = Field(..., description="Annual cash flow / total cash invested")
    cap_rate: float = Field(..., description="NOI / purchase price")
    gross_rent_multiplier: float = Field(..., description="Price / annual rent")
    rent_to_price_ratio: float = Field(..., description="Monthly rent / price (1% rule)")

    # Cash flow
    monthly_cash_flow: float
    annual_cash_flow: float
    total_cash_invested: float
    break_even_occupancy: float = Field(..., description="Occupancy needed to break even")

    # ROI projections
    year_1_total_return: Optional[float] = None
    year_5_irr: Optional[float] = None
    year_10_irr: Optional[float] = None

    # Debt coverage
    debt_service_coverage_ratio: Optional[float] = None

    @classmethod
    def from_financials(cls, financials: Financials) -> "FinancialMetrics":
        """Calculate metrics from a Financials object."""
        if not financials.total_cash_needed or financials.total_cash_needed == 0:
            financials.calculate()

        # Ensure calculation has been run
        assert financials.total_cash_needed is not None
        assert financials.net_operating_income is not None
        assert financials.annual_cash_flow is not None
        assert financials.monthly_mortgage is not None

        coc = (
            financials.annual_cash_flow / financials.total_cash_needed
            if financials.total_cash_needed > 0
            else 0
        )
        cap_rate = financials.net_operating_income / financials.purchase_price
        grm = financials.purchase_price / (financials.estimated_rent * 12) if financials.estimated_rent > 0 else 0
        rent_to_price = (financials.estimated_rent / financials.purchase_price) * 100

        # Break-even occupancy
        total_expenses_excl_vacancy = (
            financials.total_monthly_expenses - financials.monthly_vacancy_reserve
        )
        break_even = (
            total_expenses_excl_vacancy / financials.estimated_rent
            if financials.estimated_rent > 0
            else 1.0
        )

        # DSCR
        annual_debt_service = financials.monthly_mortgage * 12
        dscr = (
            financials.net_operating_income / annual_debt_service
            if annual_debt_service > 0
            else None
        )

        return cls(
            property_id=financials.property_id,
            cash_on_cash_return=coc,
            cap_rate=cap_rate,
            gross_rent_multiplier=grm,
            rent_to_price_ratio=rent_to_price,
            monthly_cash_flow=financials.monthly_cash_flow,
            annual_cash_flow=financials.annual_cash_flow,
            total_cash_invested=financials.total_cash_needed,
            break_even_occupancy=min(break_even, 1.0),
            debt_service_coverage_ratio=dscr,
        )
