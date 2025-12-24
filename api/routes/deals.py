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
        market=market_detail,
        pipeline_status=deal.pipeline_status.value,
        strategy=deal.strategy.value if deal.strategy else None,
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
