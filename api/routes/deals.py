"""Deal-related API endpoints."""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from api.models import (
    DealSummary,
    DealDetail,
    DealsResponse,
    PropertySummary,
    PropertyDetail,
    FinancialSummary,
    FinancialDetail,
    DealScore as DealScoreModel,
    MarketDetail,
    SearchParams,
    SensitivityResult as SensitivityResultModel,
)
from src.agents.pipeline import PipelineAgent
from src.agents.deal_analyzer import DealAnalyzerAgent
from src.agents.market_research import MarketResearchAgent
from src.models.deal import Deal, InvestmentStrategy
from src.models.financials import LoanTerms
from src.models.market import MarketMetrics
from src.scrapers.mock_scraper import MockScraper

router = APIRouter()


def _property_to_summary(prop) -> PropertySummary:
    """Convert Property model to PropertySummary."""
    return PropertySummary(
        id=prop.id,
        address=prop.address,
        city=prop.city,
        state=prop.state,
        zip_code=prop.zip_code,
        list_price=prop.list_price,
        estimated_rent=prop.estimated_rent,
        bedrooms=prop.bedrooms,
        bathrooms=prop.bathrooms,
        sqft=prop.sqft,
        property_type=prop.property_type.value,
        days_on_market=prop.days_on_market,
        price_per_sqft=prop.price_per_sqft,
    )


def _property_to_detail(prop) -> PropertyDetail:
    """Convert Property model to PropertyDetail."""
    return PropertyDetail(
        id=prop.id,
        address=prop.address,
        city=prop.city,
        state=prop.state,
        zip_code=prop.zip_code,
        full_address=prop.full_address,
        latitude=prop.latitude,
        longitude=prop.longitude,
        list_price=prop.list_price,
        estimated_rent=prop.estimated_rent,
        bedrooms=prop.bedrooms,
        bathrooms=prop.bathrooms,
        sqft=prop.sqft,
        property_type=prop.property_type.value,
        days_on_market=prop.days_on_market,
        price_per_sqft=prop.price_per_sqft,
        year_built=prop.year_built,
        lot_size_sqft=prop.lot_size_sqft,
        stories=prop.stories,
        units=prop.units,
        status=prop.status.value,
        source=prop.source,
        source_url=prop.source_url,
        annual_taxes=prop.annual_taxes,
        hoa_fee=prop.hoa_fee,
        original_price=prop.original_price,
        price_reduction_pct=prop.price_reduction_pct,
        gross_rent_multiplier=prop.gross_rent_multiplier,
        features=prop.features,
    )


def _financials_to_summary(deal: Deal) -> Optional[FinancialSummary]:
    """Convert deal financials to FinancialSummary."""
    if not deal.financial_metrics:
        return None

    fm = deal.financial_metrics
    return FinancialSummary(
        monthly_cash_flow=fm.monthly_cash_flow,
        annual_cash_flow=fm.annual_cash_flow,
        cash_on_cash_return=fm.cash_on_cash_return,
        cap_rate=fm.cap_rate,
        gross_rent_multiplier=fm.gross_rent_multiplier,
        rent_to_price_ratio=fm.rent_to_price_ratio,
        total_cash_invested=fm.total_cash_invested,
        break_even_occupancy=fm.break_even_occupancy,
        dscr=fm.debt_service_coverage_ratio,
    )


def _financials_to_detail(deal: Deal) -> Optional[FinancialDetail]:
    """Convert deal financials to FinancialDetail."""
    if not deal.financial_metrics or not deal.financials:
        return None

    fm = deal.financial_metrics
    f = deal.financials

    return FinancialDetail(
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


def _score_to_model(score) -> Optional[DealScoreModel]:
    """Convert DealScore to API model."""
    if not score:
        return None

    return DealScoreModel(
        overall_score=score.overall_score,
        financial_score=score.financial_score,
        market_score=score.market_score,
        risk_score=score.risk_score,
        liquidity_score=score.liquidity_score,
        rank=score.rank,
        percentile=score.percentile,
        strategy_scores=score.strategy_scores,
    )


def _sensitivity_to_model(deal: Deal) -> Optional[SensitivityResultModel]:
    """Convert sensitivity analysis to API model."""
    if not deal.sensitivity:
        return None

    s = deal.sensitivity
    return SensitivityResultModel(
        base_cash_flow=s.base_cash_flow,
        base_coc=s.base_coc,
        base_cap_rate=s.base_cap_rate,
        rate_increase_1pct=s.rate_increase_1pct_cash_flow,
        rate_increase_2pct=s.rate_increase_2pct_cash_flow,
        break_even_rate=s.break_even_rate,
        vacancy_10pct=s.vacancy_10pct_cash_flow,
        vacancy_15pct=s.vacancy_15pct_cash_flow,
        break_even_vacancy=s.break_even_vacancy,
        rent_decrease_5pct=s.rent_decrease_5pct_cash_flow,
        rent_decrease_10pct=s.rent_decrease_10pct_cash_flow,
        break_even_rent=s.break_even_rent,
        moderate_stress=s.moderate_stress_cash_flow,
        severe_stress=s.severe_stress_cash_flow,
        survives_moderate=s.survives_moderate_stress,
        survives_severe=s.survives_severe_stress,
        risk_rating=s.risk_rating,
    )


def _generate_verdict(deal: Deal) -> Optional[str]:
    """Generate a verdict for the deal based on financial metrics and sensitivity."""
    fm = deal.financial_metrics
    sensitivity = deal.sensitivity

    if not fm:
        return None

    if fm.monthly_cash_flow < 0:
        return "NOT RECOMMENDED - Negative cash flow"

    if sensitivity and sensitivity.risk_rating == "high":
        return "CAUTION - High risk, does not survive stress tests"

    if fm.cash_on_cash_return >= 0.10 and sensitivity and sensitivity.risk_rating == "low":
        return "STRONG BUY - Excellent returns with low risk"

    if fm.cash_on_cash_return >= 0.08 and sensitivity and sensitivity.survives_moderate_stress:
        return "BUY - Good returns, survives moderate stress"

    if fm.cash_on_cash_return >= 0.06:
        return "CONSIDER - Acceptable returns, review carefully"

    return "MARGINAL - Below target returns"


def _generate_recommendations(deal: Deal) -> list[str]:
    """Generate actionable recommendations for the deal."""
    recommendations = []
    fm = deal.financial_metrics
    sensitivity = deal.sensitivity

    if not fm:
        return recommendations

    # Cash flow recommendations
    if fm.monthly_cash_flow < 100:
        recommendations.append(
            f"Cash flow is tight at ${fm.monthly_cash_flow:.0f}/month. "
            "Consider negotiating a lower price or finding higher rent potential."
        )

    # Sensitivity recommendations
    if sensitivity and not sensitivity.survives_moderate_stress:
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

    if sensitivity and sensitivity.survives_severe_stress:
        recommendations.append(
            "Strong deal that survives severe stress testing. "
            "Good protection against market downturns."
        )

    return recommendations


def _deal_to_summary(deal: Deal) -> DealSummary:
    """Convert Deal to DealSummary."""
    return DealSummary(
        id=deal.id,
        property=_property_to_summary(deal.property),
        score=_score_to_model(deal.score),
        financials=_financials_to_summary(deal),
        market_name=deal.market.name if deal.market else None,
        pipeline_status=deal.pipeline_status.value,
        pros=deal.pros[:3],  # Top 3 pros
        cons=deal.cons[:3],  # Top 3 cons
    )


@router.get("/search", response_model=DealsResponse)
async def search_deals(
    markets: Optional[str] = Query(None, description="Comma-separated market IDs"),
    strategy: str = Query("cash_flow", description="Investment strategy"),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    min_beds: int = Query(2, ge=0),
    max_beds: Optional[int] = Query(None, ge=0),
    min_cash_flow: Optional[float] = Query(None),
    down_payment: float = Query(0.25, ge=0.05, le=1.0),
    interest_rate: float = Query(0.07, ge=0.01, le=0.20),
    limit: int = Query(20, ge=1, le=100),
):
    """
    Search for investment deals across markets.

    Analyzes properties, calculates financials, and returns ranked deals
    based on the specified investment strategy.
    """
    # Parse markets
    market_ids = None
    if markets:
        market_ids = [m.strip() for m in markets.split(",")]

    # Validate strategy
    try:
        inv_strategy = InvestmentStrategy(strategy)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid strategy: {strategy}")

    # Create loan terms
    loan_terms = LoanTerms(
        down_payment_pct=down_payment,
        interest_rate=interest_rate,
    )

    # Run pipeline
    pipeline = PipelineAgent()
    result = await pipeline.run(
        market_ids=market_ids,
        strategy=inv_strategy,
        max_price=max_price,
        min_beds=min_beds,
        properties_per_market=limit // 2 + 10,  # Fetch extra to account for filtering
        top_n=limit,
        loan_terms=loan_terms,
        run_sensitivity=False,  # Skip for search performance
    )

    if not result.data.get("deals"):
        return DealsResponse(
            deals=[],
            total=0,
            filters_applied={
                "markets": market_ids,
                "strategy": strategy,
                "max_price": max_price,
                "min_beds": min_beds,
            },
        )

    # Apply additional filters
    deals = result.data["deals"]

    if min_cash_flow is not None:
        deals = [
            d for d in deals
            if d.financial_metrics and d.financial_metrics.monthly_cash_flow >= min_cash_flow
        ]

    if max_beds is not None:
        deals = [d for d in deals if d.property.bedrooms <= max_beds]

    if min_price is not None:
        deals = [d for d in deals if d.property.list_price >= min_price]

    # Convert to response
    deal_summaries = [_deal_to_summary(d) for d in deals[:limit]]

    return DealsResponse(
        deals=deal_summaries,
        total=len(deal_summaries),
        filters_applied={
            "markets": market_ids,
            "strategy": strategy,
            "min_price": min_price,
            "max_price": max_price,
            "min_beds": min_beds,
            "max_beds": max_beds,
            "min_cash_flow": min_cash_flow,
        },
    )


@router.get("/{deal_id}", response_model=DealDetail)
async def get_deal(deal_id: str):
    """
    Get detailed information for a specific deal.

    Returns comprehensive deal analysis including property details,
    financial breakdown, market context, and scoring explanation.
    """
    # For now, we'll generate a fresh deal since we don't have persistence
    # In production, this would fetch from the database

    # Extract property ID from deal ID
    property_id = deal_id.replace("deal_", "")

    # Get the property from scraper cache (mock implementation)
    scraper = MockScraper()
    prop = await scraper.get_property(property_id)

    if not prop:
        raise HTTPException(status_code=404, detail=f"Deal not found: {deal_id}")

    # Get market data
    market_agent = MarketResearchAgent()
    market_id = f"{prop.city.lower().replace(' ', '_')}_{prop.state.lower()}"
    market = await market_agent.get_market(market_id)

    # Analyze deal
    deal_agent = DealAnalyzerAgent()
    deal = await deal_agent.analyze_property(prop, market=market, run_sensitivity=True)

    # Build market detail if available
    market_detail = None
    if market:
        metrics = MarketMetrics.from_market(market)
        market_detail = MarketDetail(
            id=market.id,
            name=market.name,
            state=market.state,
            metro=market.metro,
            region=market.region,
            population=market.population,
            population_growth_1yr=market.population_growth_1yr,
            population_growth_5yr=market.population_growth_5yr,
            unemployment_rate=market.unemployment_rate,
            job_growth_1yr=market.job_growth_1yr,
            major_employers=market.major_employers,
            median_household_income=market.median_household_income,
            median_home_price=market.median_home_price,
            median_rent=market.median_rent,
            rent_to_price_ratio=market.avg_rent_to_price,
            price_change_1yr=market.price_change_1yr,
            price_change_5yr=market.price_change_5yr,
            rent_change_1yr=market.rent_change_1yr,
            months_of_inventory=market.months_of_inventory,
            days_on_market_avg=market.days_on_market_avg,
            price_trend=market.price_trend.value,
            rent_trend=market.rent_trend.value,
            landlord_friendly=market.landlord_friendly,
            property_tax_rate=market.property_tax_rate,
            insurance_risk=market.insurance_risk,
            overall_score=metrics.overall_score,
            cash_flow_score=metrics.cash_flow_score,
            growth_score=metrics.growth_score,
            affordability_score=metrics.affordability_score,
            stability_score=metrics.stability_score,
            liquidity_score=metrics.liquidity_score,
        )

    return DealDetail(
        id=deal.id,
        property=_property_to_detail(deal.property),
        score=_score_to_model(deal.score),
        financials=_financials_to_detail(deal),
        sensitivity=_sensitivity_to_model(deal),
        market=market_detail,
        pipeline_status=deal.pipeline_status.value,
        strategy=deal.strategy.value if deal.strategy else None,
        verdict=_generate_verdict(deal),
        recommendations=_generate_recommendations(deal),
        pros=deal.pros,
        cons=deal.cons,
        red_flags=deal.red_flags,
        notes=deal.notes,
        first_seen=deal.first_seen,
        last_analyzed=deal.last_analyzed,
    )


@router.post("/analyze")
async def analyze_property_quick(
    city: str = Query(..., description="City name"),
    state: str = Query(..., min_length=2, max_length=2, description="State abbreviation"),
    limit: int = Query(10, ge=1, le=50),
    max_price: Optional[float] = Query(None, ge=0),
    min_beds: int = Query(2, ge=0),
):
    """
    Quick analysis of properties in a specific market.

    Fetches and analyzes properties from the specified city/state.
    """
    # Get market data
    market_agent = MarketResearchAgent()
    market_id = f"{city.lower().replace(' ', '_')}_{state.lower()}"
    market = await market_agent.get_market(market_id)

    # Scrape properties
    scraper = MockScraper()
    result = await scraper.search(
        city=city,
        state=state,
        max_price=max_price,
        min_beds=min_beds,
        limit=limit,
    )

    if not result.properties:
        raise HTTPException(status_code=404, detail=f"No properties found in {city}, {state}")

    # Analyze deals
    deal_agent = DealAnalyzerAgent()
    analysis = await deal_agent.run(
        properties=result.properties,
        market=market,
        run_sensitivity=False,
    )

    deals = [_deal_to_summary(d) for d in analysis.data["deals"]]

    return DealsResponse(
        deals=deals,
        total=len(deals),
        filters_applied={
            "city": city,
            "state": state,
            "max_price": max_price,
            "min_beds": min_beds,
        },
    )
