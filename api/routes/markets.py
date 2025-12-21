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
    and investment scores.
    """
    market = await agent.get_market(market_id)

    if not market:
        raise HTTPException(status_code=404, detail=f"Market not found: {market_id}")

    metrics = MarketMetrics.from_market(market)

    return MarketDetail(
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
