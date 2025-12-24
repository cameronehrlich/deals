"""Market-related API endpoints."""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from api.models import (
    MarketSummary,
    MarketDetail,
    MarketsResponse,
    APIResponse,
)
from src.agents.market_research import MarketResearchAgent
from src.models.market import MarketMetrics

router = APIRouter()
agent = MarketResearchAgent()


@router.get("", response_model=MarketsResponse)
async def list_markets(
    sort_by: str = Query("overall", description="Sort by: overall, cash_flow, growth, affordability"),
    limit: int = Query(20, ge=1, le=50),
    min_population: Optional[int] = Query(None, description="Minimum metro population"),
    landlord_friendly: Optional[bool] = Query(None, description="Filter by landlord-friendly states"),
):
    """
    List and rank investment markets.

    Returns markets sorted by the specified criteria with scores and key metrics.
    """
    result = await agent.run(
        min_population=min_population,
        landlord_friendly_only=landlord_friendly or False,
    )

    if not result.success and not result.data.get("markets"):
        raise HTTPException(status_code=500, detail="Failed to fetch market data")

    markets_data = result.data["markets"]

    # Sort by requested field
    sort_keys = {
        "overall": lambda x: x["overall_score"],
        "cash_flow": lambda x: x["cash_flow_score"],
        "growth": lambda x: x["growth_score"],
        "affordability": lambda x: x["metrics"].affordability_score,
    }

    if sort_by in sort_keys:
        markets_data.sort(key=sort_keys[sort_by], reverse=True)

    # Convert to response models
    markets = []
    for i, m in enumerate(markets_data[:limit]):
        market = m["market"]
        metrics = m["metrics"]

        markets.append(MarketSummary(
            id=market.id,
            name=market.name,
            state=market.state,
            metro=market.metro,
            population=market.population,
            median_home_price=market.median_home_price,
            median_rent=market.median_rent,
            rent_to_price_ratio=market.avg_rent_to_price,
            price_change_1yr=market.price_change_1yr,
            job_growth_1yr=market.job_growth_1yr,
            overall_score=metrics.overall_score,
            cash_flow_score=metrics.cash_flow_score,
            growth_score=metrics.growth_score,
            rank=i + 1,
        ))

    return MarketsResponse(markets=markets, total=len(markets))


@router.get("/{market_id}", response_model=MarketDetail)
async def get_market(market_id: str):
    """
    Get detailed information for a specific market.

    Returns comprehensive market data including demographics, housing metrics,
    and investment scores. Uses saved market data from the database to ensure
    consistency with the markets list page.
    """
    from src.db import get_repository
    from src.db.models import MarketDB
    from src.models.market import Market, MarketTrend

    repo = get_repository()
    market_db = repo.session.query(MarketDB).filter_by(id=market_id).first()

    if not market_db:
        raise HTTPException(status_code=404, detail=f"Market not found: {market_id}")

    # Use stored market_data if available, otherwise fall back to agent
    market_data = market_db.market_data or {}

    if market_data:
        # Build Market model from stored data
        market = Market(
            id=market_db.id,
            name=market_db.name,
            state=market_db.state,
            metro=market_db.metro or market_data.get("metro", ""),
            region=market_data.get("region"),
            population=market_data.get("population"),
            population_growth_1yr=market_data.get("population_growth_1yr"),
            population_growth_5yr=market_data.get("population_growth_5yr"),
            unemployment_rate=market_data.get("unemployment_rate"),
            job_growth_1yr=market_data.get("job_growth_yoy") or market_data.get("job_growth_1yr"),
            labor_force=market_data.get("labor_force"),
            major_employers=market_data.get("major_employers", []),
            median_household_income=market_data.get("median_household_income"),
            median_home_price=market_data.get("median_sale_price") or market_data.get("median_home_price"),
            median_rent=market_data.get("fmr_2br") or market_data.get("median_rent"),
            avg_rent_to_price=market_data.get("rent_to_price_ratio") or market_data.get("avg_rent_to_price"),
            price_change_1yr=market_data.get("price_change_yoy") or market_data.get("price_change_1yr"),
            price_change_5yr=market_data.get("price_change_5yr"),
            rent_change_1yr=market_data.get("rent_change_1yr"),
            months_of_inventory=market_data.get("months_of_supply") or market_data.get("months_of_inventory"),
            days_on_market_avg=market_data.get("days_on_market") or market_data.get("days_on_market_avg"),
            sale_to_list_ratio=market_data.get("sale_to_list_ratio"),
            pct_sold_above_list=market_data.get("pct_sold_above_list"),
            pct_sold_below_list=market_data.get("pct_sold_below_list"),
            price_trend=MarketTrend(market_data.get("price_trend", "stable")) if isinstance(market_data.get("price_trend"), str) else MarketTrend.STABLE,
            rent_trend=MarketTrend(market_data.get("rent_trend", "stable")) if isinstance(market_data.get("rent_trend"), str) else MarketTrend.STABLE,
            landlord_friendly=market_data.get("landlord_friendly", True),
            landlord_friendly_score=market_data.get("landlord_friendly_score"),
            property_tax_rate=market_data.get("avg_property_tax_rate") or market_data.get("property_tax_rate"),
            has_state_income_tax=market_data.get("has_state_income_tax"),
            insurance_risk=market_data.get("insurance_risk"),
            insurance_risk_factors=market_data.get("insurance_risk_factors", []),
            data_sources=market_data.get("data_sources", []),
        )
        # Calculate all scores from market data for consistency
        metrics = MarketMetrics.from_market(market)
        # Use stored overall scores but calculate component scores fresh
        overall_score = market_db.overall_score or metrics.overall_score
        cash_flow_score = market_db.cash_flow_score or metrics.cash_flow_score
        growth_score = market_db.growth_score or metrics.growth_score
        data_sources = market_data.get("data_sources", [])
    else:
        # Fall back to agent for markets without stored data
        market = await agent.get_market(market_id)
        if not market:
            # Market exists in DB but has no data - return basic info
            # This can happen if enrichment failed/timed out
            return MarketDetail(
                id=market_db.id,
                name=market_db.name,
                state=market_db.state,
                metro=market_db.metro or "",
                overall_score=market_db.overall_score or 0,
                cash_flow_score=market_db.cash_flow_score or 0,
                growth_score=market_db.growth_score or 0,
                rank=0,
                data_sources=[],
                enrichment_pending=True,  # Signal that data is still being fetched
            )
        metrics = MarketMetrics.from_market(market)
        overall_score = metrics.overall_score
        cash_flow_score = metrics.cash_flow_score
        growth_score = metrics.growth_score
        data_sources = []

    return MarketDetail(
        id=market.id,
        name=market.name,
        state=market.state,
        metro=market.metro,
        region=market.region,
        # Demographics
        population=market.population,
        population_growth_1yr=market.population_growth_1yr,
        population_growth_5yr=market.population_growth_5yr,
        unemployment_rate=market.unemployment_rate,
        labor_force=market.labor_force,
        job_growth_1yr=market.job_growth_1yr,
        major_employers=market.major_employers,
        median_household_income=market.median_household_income,
        # Housing
        median_home_price=market.median_home_price,
        median_rent=market.median_rent,
        rent_to_price_ratio=market.avg_rent_to_price,
        price_change_1yr=market.price_change_1yr,
        price_change_5yr=market.price_change_5yr,
        rent_change_1yr=market.rent_change_1yr,
        months_of_inventory=market.months_of_inventory,
        days_on_market_avg=market.days_on_market_avg,
        sale_to_list_ratio=market.sale_to_list_ratio,
        pct_sold_above_list=market.pct_sold_above_list,
        price_trend=market.price_trend.value,
        rent_trend=market.rent_trend.value,
        # Regulatory & Costs
        landlord_friendly=market.landlord_friendly,
        landlord_friendly_score=market.landlord_friendly_score,
        property_tax_rate=market.property_tax_rate,
        has_state_income_tax=market.has_state_income_tax,
        insurance_risk=market.insurance_risk,
        insurance_risk_factors=market.insurance_risk_factors,
        # Scores
        overall_score=overall_score,
        cash_flow_score=cash_flow_score,
        growth_score=growth_score,
        affordability_score=metrics.affordability_score,
        stability_score=metrics.stability_score,
        liquidity_score=metrics.liquidity_score,
        operating_cost_score=metrics.operating_cost_score,
        regulatory_score=metrics.regulatory_score,
        # Data quality
        data_completeness=metrics.data_completeness,
        data_sources=data_sources,
    )


@router.get("/{market_id}/compare/{other_market_id}")
async def compare_markets(market_id: str, other_market_id: str):
    """
    Compare two markets side by side.

    Returns a comparison of key metrics and a recommendation.
    """
    market_a = await agent.get_market(market_id)
    market_b = await agent.get_market(other_market_id)

    if not market_a:
        raise HTTPException(status_code=404, detail=f"Market not found: {market_id}")
    if not market_b:
        raise HTTPException(status_code=404, detail=f"Market not found: {other_market_id}")

    comparison = agent.compare_markets(market_a, market_b)

    return APIResponse(
        success=True,
        data=comparison,
        message=f"Comparison complete. Recommended: {comparison['winner']}",
    )
