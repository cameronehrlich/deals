"""Sensitivity analysis for stress-testing deals."""

from dataclasses import dataclass
from typing import Optional

from src.models.deal import Deal
from src.models.financials import Financials, FinancialMetrics


@dataclass
class SensitivityResult:
    """Results from sensitivity analysis."""

    property_id: str

    # Base case
    base_cash_flow: float
    base_coc: float
    base_cap_rate: float

    # Interest rate sensitivity
    rate_increase_1pct_cash_flow: float
    rate_increase_2pct_cash_flow: float
    break_even_rate: Optional[float]  # Rate at which cash flow = 0

    # Vacancy sensitivity
    vacancy_10pct_cash_flow: float
    vacancy_15pct_cash_flow: float
    break_even_vacancy: Optional[float]  # Vacancy at which cash flow = 0

    # Rent sensitivity
    rent_decrease_5pct_cash_flow: float
    rent_decrease_10pct_cash_flow: float
    break_even_rent: Optional[float]  # Rent at which cash flow = 0

    # Combined stress test
    moderate_stress_cash_flow: float  # +1% rate, 10% vacancy, -5% rent
    severe_stress_cash_flow: float  # +2% rate, 15% vacancy, -10% rent

    # Risk assessment
    survives_moderate_stress: bool
    survives_severe_stress: bool
    risk_rating: str  # "low", "medium", "high"


class SensitivityAnalyzer:
    """Analyze deal sensitivity to market changes."""

    def analyze(self, deal: Deal) -> SensitivityResult:
        """Run comprehensive sensitivity analysis on a deal."""
        if not deal.financials:
            deal.analyze()

        base = deal.financials
        assert base is not None

        # Ensure base case is calculated
        base.calculate()

        base_cash_flow = base.monthly_cash_flow
        base_coc = deal.financial_metrics.cash_on_cash_return if deal.financial_metrics else 0
        base_cap = deal.financial_metrics.cap_rate if deal.financial_metrics else 0

        # Interest rate scenarios
        rate_1pct = self._scenario_rate_change(base, 0.01)
        rate_2pct = self._scenario_rate_change(base, 0.02)
        break_even_rate = self._find_break_even_rate(base)

        # Vacancy scenarios
        vacancy_10 = self._scenario_vacancy(base, 0.10)
        vacancy_15 = self._scenario_vacancy(base, 0.15)
        break_even_vacancy = self._find_break_even_vacancy(base)

        # Rent scenarios
        rent_minus_5 = self._scenario_rent_change(base, -0.05)
        rent_minus_10 = self._scenario_rent_change(base, -0.10)
        break_even_rent = self._find_break_even_rent(base)

        # Combined stress tests
        moderate_stress = self._combined_stress(base, rate_delta=0.01, vacancy=0.10, rent_delta=-0.05)
        severe_stress = self._combined_stress(base, rate_delta=0.02, vacancy=0.15, rent_delta=-0.10)

        # Risk assessment
        survives_moderate = moderate_stress >= 0
        survives_severe = severe_stress >= 0

        if survives_severe:
            risk_rating = "low"
        elif survives_moderate:
            risk_rating = "medium"
        else:
            risk_rating = "high"

        return SensitivityResult(
            property_id=deal.property.id,
            base_cash_flow=base_cash_flow,
            base_coc=base_coc,
            base_cap_rate=base_cap,
            rate_increase_1pct_cash_flow=rate_1pct,
            rate_increase_2pct_cash_flow=rate_2pct,
            break_even_rate=break_even_rate,
            vacancy_10pct_cash_flow=vacancy_10,
            vacancy_15pct_cash_flow=vacancy_15,
            break_even_vacancy=break_even_vacancy,
            rent_decrease_5pct_cash_flow=rent_minus_5,
            rent_decrease_10pct_cash_flow=rent_minus_10,
            break_even_rent=break_even_rent,
            moderate_stress_cash_flow=moderate_stress,
            severe_stress_cash_flow=severe_stress,
            survives_moderate_stress=survives_moderate,
            survives_severe_stress=survives_severe,
            risk_rating=risk_rating,
        )

    def _create_scenario(self, base: Financials) -> Financials:
        """Create a copy of financials for scenario analysis."""
        return Financials(
            property_id=base.property_id,
            purchase_price=base.purchase_price,
            estimated_rent=base.estimated_rent,
            loan=base.loan.model_copy(),
            expenses=base.expenses.model_copy(),
        )

    def _scenario_rate_change(self, base: Financials, rate_delta: float) -> float:
        """Calculate cash flow with interest rate change."""
        scenario = self._create_scenario(base)
        scenario.loan.interest_rate = base.loan.interest_rate + rate_delta
        scenario.calculate()
        return scenario.monthly_cash_flow

    def _scenario_vacancy(self, base: Financials, vacancy_rate: float) -> float:
        """Calculate cash flow with different vacancy rate."""
        scenario = self._create_scenario(base)
        scenario.expenses.vacancy_rate = vacancy_rate
        scenario.calculate()
        return scenario.monthly_cash_flow

    def _scenario_rent_change(self, base: Financials, rent_delta: float) -> float:
        """Calculate cash flow with rent change."""
        scenario = self._create_scenario(base)
        scenario.estimated_rent = base.estimated_rent * (1 + rent_delta)
        scenario.calculate()
        return scenario.monthly_cash_flow

    def _combined_stress(
        self,
        base: Financials,
        rate_delta: float,
        vacancy: float,
        rent_delta: float,
    ) -> float:
        """Calculate cash flow under combined stress scenario."""
        scenario = self._create_scenario(base)
        scenario.loan.interest_rate = base.loan.interest_rate + rate_delta
        scenario.expenses.vacancy_rate = vacancy
        scenario.estimated_rent = base.estimated_rent * (1 + rent_delta)
        scenario.calculate()
        return scenario.monthly_cash_flow

    def _find_break_even_rate(self, base: Financials) -> Optional[float]:
        """Find interest rate at which cash flow = 0."""
        # Binary search for break-even rate
        low, high = base.loan.interest_rate, 0.20
        target = 0

        for _ in range(20):  # Max iterations
            mid = (low + high) / 2
            cf = self._scenario_rate_change(base, mid - base.loan.interest_rate)

            if abs(cf - target) < 1:  # Within $1
                return mid
            elif cf > target:
                low = mid
            else:
                high = mid

        return None  # No break-even found within range

    def _find_break_even_vacancy(self, base: Financials) -> Optional[float]:
        """Find vacancy rate at which cash flow = 0."""
        low, high = 0.0, 0.50
        target = 0

        for _ in range(20):
            mid = (low + high) / 2
            cf = self._scenario_vacancy(base, mid)

            if abs(cf - target) < 1:
                return mid
            elif cf > target:
                low = mid
            else:
                high = mid

        return None

    def _find_break_even_rent(self, base: Financials) -> Optional[float]:
        """Find rent at which cash flow = 0."""
        low, high = 0.5, 1.0  # 50% to 100% of current rent
        target = 0

        for _ in range(20):
            mid = (low + high) / 2
            cf = self._scenario_rent_change(base, mid - 1.0)  # mid is multiplier

            if abs(cf - target) < 1:
                return base.estimated_rent * mid
            elif cf > target:
                high = mid
            else:
                low = mid

        return None
