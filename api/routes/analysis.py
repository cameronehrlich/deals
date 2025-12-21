"""Analysis-related API endpoints."""

from fastapi import APIRouter, HTTPException

from api.models import (
    AnalysisRequest,
    AnalysisResponse,
    FinancialDetail,
    SensitivityResult,
)
from src.models.property import Property
from src.models.deal import Deal
from src.models.financials import Financials, LoanTerms, OperatingExpenses
from src.analysis.sensitivity import SensitivityAnalyzer

router = APIRouter()


@router.post("/calculate", response_model=AnalysisResponse)
async def calculate_financials(request: AnalysisRequest):
    """
    Calculate complete financial analysis for a hypothetical property.

    Provides detailed cash flow breakdown, returns metrics, and
    sensitivity analysis with stress testing.
    """
    # Create property
    prop = Property(
        id="analysis_temp",
        address="Analysis Property",
        city="Unknown",
        state="XX",
        zip_code="00000",
        list_price=request.purchase_price,
        estimated_rent=request.monthly_rent,
        bedrooms=3,
        bathrooms=2,
        source="user_input",
    )

    # Create financials with user parameters
    loan_terms = LoanTerms(
        down_payment_pct=request.down_payment_pct,
        interest_rate=request.interest_rate,
    )

    expenses = OperatingExpenses(
        property_tax_rate=request.property_tax_rate,
        insurance_rate=request.insurance_rate,
        vacancy_rate=request.vacancy_rate,
        maintenance_rate=request.maintenance_rate,
        property_management_rate=request.property_management_rate,
        hoa_monthly=request.hoa_monthly,
    )

    financials = Financials(
        property_id=prop.id,
        purchase_price=request.purchase_price,
        estimated_rent=request.monthly_rent,
        loan=loan_terms,
        expenses=expenses,
    )
    financials.calculate()

    # Create deal for analysis
    deal = Deal(id="analysis_deal", property=prop, financials=financials)
    deal.analyze()

    # Run sensitivity analysis
    analyzer = SensitivityAnalyzer()
    sensitivity = analyzer.analyze(deal)

    # Build financial detail response
    fm = deal.financial_metrics
    f = deal.financials

    financial_detail = FinancialDetail(
        monthly_cash_flow=fm.monthly_cash_flow,
        annual_cash_flow=fm.annual_cash_flow,
        cash_on_cash_return=fm.cash_on_cash_return,
        cap_rate=fm.cap_rate,
        gross_rent_multiplier=fm.gross_rent_multiplier,
        rent_to_price_ratio=fm.rent_to_price_ratio,
        total_cash_invested=fm.total_cash_invested,
        break_even_occupancy=fm.break_even_occupancy,
        dscr=fm.debt_service_coverage_ratio,
        purchase_price=f.purchase_price,
        down_payment=f.down_payment or 0,
        loan_amount=f.loan_amount or 0,
        closing_costs=f.closing_costs or 0,
        monthly_mortgage=f.monthly_mortgage or 0,
        monthly_taxes=f.monthly_taxes or 0,
        monthly_insurance=f.monthly_insurance or 0,
        monthly_hoa=f.expenses.hoa_monthly,
        monthly_maintenance=f.monthly_maintenance or 0,
        monthly_capex=f.monthly_capex or 0,
        monthly_vacancy_reserve=f.monthly_vacancy_reserve or 0,
        monthly_property_management=f.monthly_property_management or 0,
        total_monthly_expenses=f.total_monthly_expenses or 0,
        net_operating_income=f.net_operating_income or 0,
        interest_rate=f.loan.interest_rate,
        down_payment_pct=f.loan.down_payment_pct,
    )

    # Build sensitivity result
    sensitivity_result = SensitivityResult(
        base_cash_flow=sensitivity.base_cash_flow,
        base_coc=sensitivity.base_coc,
        base_cap_rate=sensitivity.base_cap_rate,
        rate_increase_1pct=sensitivity.rate_increase_1pct_cash_flow,
        rate_increase_2pct=sensitivity.rate_increase_2pct_cash_flow,
        break_even_rate=sensitivity.break_even_rate,
        vacancy_10pct=sensitivity.vacancy_10pct_cash_flow,
        vacancy_15pct=sensitivity.vacancy_15pct_cash_flow,
        break_even_vacancy=sensitivity.break_even_vacancy,
        rent_decrease_5pct=sensitivity.rent_decrease_5pct_cash_flow,
        rent_decrease_10pct=sensitivity.rent_decrease_10pct_cash_flow,
        break_even_rent=sensitivity.break_even_rent,
        moderate_stress=sensitivity.moderate_stress_cash_flow,
        severe_stress=sensitivity.severe_stress_cash_flow,
        survives_moderate=sensitivity.survives_moderate_stress,
        survives_severe=sensitivity.survives_severe_stress,
        risk_rating=sensitivity.risk_rating,
    )

    # Generate verdict and recommendations
    verdict = _generate_verdict(fm, sensitivity)
    recommendations = _generate_recommendations(fm, sensitivity, request)

    return AnalysisResponse(
        financials=financial_detail,
        sensitivity=sensitivity_result,
        verdict=verdict,
        recommendations=recommendations,
    )


def _generate_verdict(fm, sensitivity) -> str:
    """Generate a verdict for the deal."""
    if fm.monthly_cash_flow < 0:
        return "NOT RECOMMENDED - Negative cash flow"

    if sensitivity.risk_rating == "high":
        return "CAUTION - High risk, does not survive stress tests"

    if fm.cash_on_cash_return >= 0.10 and sensitivity.risk_rating == "low":
        return "STRONG BUY - Excellent returns with low risk"

    if fm.cash_on_cash_return >= 0.08 and sensitivity.survives_moderate_stress:
        return "BUY - Good returns, survives moderate stress"

    if fm.cash_on_cash_return >= 0.06:
        return "CONSIDER - Acceptable returns, review carefully"

    return "MARGINAL - Below target returns"


def _generate_recommendations(fm, sensitivity, request: AnalysisRequest) -> list[str]:
    """Generate actionable recommendations."""
    recommendations = []

    # Cash flow recommendations
    if fm.monthly_cash_flow < 100:
        recommendations.append(
            f"Cash flow is tight at ${fm.monthly_cash_flow:.0f}/month. "
            "Consider negotiating a lower price or finding higher rent potential."
        )

    # Down payment recommendations
    if request.down_payment_pct < 0.20:
        recommendations.append(
            "Consider increasing down payment to reduce monthly mortgage "
            "and improve cash flow."
        )

    if request.down_payment_pct > 0.30 and fm.cash_on_cash_return < 0.08:
        recommendations.append(
            "High down payment with low CoC return. Consider using "
            "less capital and leveraging more for better returns."
        )

    # Interest rate sensitivity
    if not sensitivity.survives_moderate_stress:
        recommendations.append(
            "Deal is sensitive to market changes. Consider stress testing "
            "with higher reserves or negotiating better terms."
        )

    # Rent-to-price
    if fm.rent_to_price_ratio < 0.7:
        recommendations.append(
            f"Rent-to-price ratio of {fm.rent_to_price_ratio:.2f}% is below "
            "the 1% rule. Look for value-add opportunities to increase rent."
        )

    # Break-even
    if fm.break_even_occupancy > 0.85:
        recommendations.append(
            f"Break-even occupancy of {fm.break_even_occupancy:.0%} is high. "
            "Little margin for extended vacancies."
        )

    # DSCR
    if fm.debt_service_coverage_ratio and fm.debt_service_coverage_ratio < 1.2:
        recommendations.append(
            f"DSCR of {fm.debt_service_coverage_ratio:.2f} is below lender "
            "requirements (typically 1.2-1.25). May have financing challenges."
        )

    # Positive recommendations
    if fm.cash_on_cash_return >= 0.10:
        recommendations.append(
            f"Excellent cash-on-cash return of {fm.cash_on_cash_return:.1%}. "
            "This deal exceeds typical investor targets."
        )

    if sensitivity.survives_severe_stress:
        recommendations.append(
            "Strong deal that survives severe stress testing. "
            "Good protection against market downturns."
        )

    return recommendations


@router.post("/compare")
async def compare_scenarios(
    scenario_a: AnalysisRequest,
    scenario_b: AnalysisRequest,
):
    """
    Compare two investment scenarios side by side.

    Useful for evaluating different properties or financing options.
    """
    # Analyze both scenarios
    result_a = await calculate_financials(scenario_a)
    result_b = await calculate_financials(scenario_b)

    # Determine winner
    score_a = (
        result_a.financials.cash_on_cash_return * 100 +
        (1 if result_a.sensitivity.survives_severe else 0) * 20 +
        (1 if result_a.financials.monthly_cash_flow > 0 else 0) * 30
    )
    score_b = (
        result_b.financials.cash_on_cash_return * 100 +
        (1 if result_b.sensitivity.survives_severe else 0) * 20 +
        (1 if result_b.financials.monthly_cash_flow > 0 else 0) * 30
    )

    winner = "A" if score_a > score_b else "B" if score_b > score_a else "Tie"

    return {
        "scenario_a": {
            "input": scenario_a.model_dump(),
            "result": result_a.model_dump(),
            "score": score_a,
        },
        "scenario_b": {
            "input": scenario_b.model_dump(),
            "result": result_b.model_dump(),
            "score": score_b,
        },
        "winner": winner,
        "comparison": {
            "cash_flow_diff": result_a.financials.monthly_cash_flow - result_b.financials.monthly_cash_flow,
            "coc_diff": result_a.financials.cash_on_cash_return - result_b.financials.cash_on_cash_return,
            "risk_comparison": f"A: {result_a.sensitivity.risk_rating}, B: {result_b.sensitivity.risk_rating}",
        },
    }
