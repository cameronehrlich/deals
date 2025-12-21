"""Market research agent for analyzing metro areas."""

import time
from datetime import datetime
from typing import Optional

from src.agents.base import BaseAgent, AgentResult
from src.models.market import Market, MarketMetrics, MarketTrend


# Sample market data - in production, this would come from APIs/scrapers
SAMPLE_MARKETS: dict[str, dict] = {
    "austin_tx": {
        "name": "Austin",
        "metro": "Austin-Round Rock-Georgetown",
        "state": "TX",
        "region": "Southwest",
        "population": 2473275,
        "population_growth_1yr": 2.8,
        "population_growth_5yr": 18.5,
        "unemployment_rate": 0.032,
        "job_growth_1yr": 4.2,
        "major_employers": ["Tesla", "Apple", "Google", "Dell", "Oracle", "Samsung"],
        "median_household_income": 85000,
        "income_growth_1yr": 5.1,
        "median_home_price": 550000,
        "median_price_per_sqft": 285,
        "price_change_1yr": -3.5,
        "price_change_5yr": 55.0,
        "median_rent": 1850,
        "rent_change_1yr": -2.0,
        "avg_rent_to_price": 0.40,
        "months_of_inventory": 4.2,
        "days_on_market_avg": 52,
        "price_trend": MarketTrend.MODERATE_DECLINE,
        "rent_trend": MarketTrend.STABLE,
        "demand_trend": MarketTrend.MODERATE_GROWTH,
        "landlord_friendly": True,
        "property_tax_rate": 0.018,
        "insurance_risk": "low",
    },
    "indianapolis_in": {
        "name": "Indianapolis",
        "metro": "Indianapolis-Carmel-Anderson",
        "state": "IN",
        "region": "Midwest",
        "population": 2111040,
        "population_growth_1yr": 0.9,
        "population_growth_5yr": 5.2,
        "unemployment_rate": 0.035,
        "job_growth_1yr": 2.1,
        "major_employers": ["Eli Lilly", "Anthem", "Salesforce", "Cummins"],
        "median_household_income": 58000,
        "income_growth_1yr": 3.5,
        "median_home_price": 265000,
        "median_price_per_sqft": 145,
        "price_change_1yr": 4.2,
        "price_change_5yr": 42.0,
        "median_rent": 1350,
        "rent_change_1yr": 3.5,
        "avg_rent_to_price": 0.61,
        "months_of_inventory": 2.1,
        "days_on_market_avg": 28,
        "price_trend": MarketTrend.MODERATE_GROWTH,
        "rent_trend": MarketTrend.MODERATE_GROWTH,
        "demand_trend": MarketTrend.STABLE,
        "landlord_friendly": True,
        "property_tax_rate": 0.0085,
        "insurance_risk": "low",
    },
    "cleveland_oh": {
        "name": "Cleveland",
        "metro": "Cleveland-Elyria",
        "state": "OH",
        "region": "Midwest",
        "population": 2088251,
        "population_growth_1yr": -0.3,
        "population_growth_5yr": -1.5,
        "unemployment_rate": 0.045,
        "job_growth_1yr": 0.8,
        "major_employers": ["Cleveland Clinic", "Progressive", "KeyCorp"],
        "median_household_income": 52000,
        "income_growth_1yr": 2.8,
        "median_home_price": 185000,
        "median_price_per_sqft": 105,
        "price_change_1yr": 5.1,
        "price_change_5yr": 35.0,
        "median_rent": 1150,
        "rent_change_1yr": 4.0,
        "avg_rent_to_price": 0.75,
        "months_of_inventory": 1.8,
        "days_on_market_avg": 22,
        "price_trend": MarketTrend.MODERATE_GROWTH,
        "rent_trend": MarketTrend.MODERATE_GROWTH,
        "demand_trend": MarketTrend.STABLE,
        "landlord_friendly": True,
        "property_tax_rate": 0.0175,
        "insurance_risk": "low",
    },
    "memphis_tn": {
        "name": "Memphis",
        "metro": "Memphis-Forrest City",
        "state": "TN",
        "region": "South",
        "population": 1337779,
        "population_growth_1yr": 0.2,
        "population_growth_5yr": 1.0,
        "unemployment_rate": 0.048,
        "job_growth_1yr": 1.5,
        "major_employers": ["FedEx", "St. Jude", "AutoZone", "International Paper"],
        "median_household_income": 48000,
        "income_growth_1yr": 2.5,
        "median_home_price": 195000,
        "median_price_per_sqft": 115,
        "price_change_1yr": 3.8,
        "price_change_5yr": 38.0,
        "median_rent": 1200,
        "rent_change_1yr": 3.2,
        "avg_rent_to_price": 0.74,
        "months_of_inventory": 2.5,
        "days_on_market_avg": 35,
        "price_trend": MarketTrend.MODERATE_GROWTH,
        "rent_trend": MarketTrend.MODERATE_GROWTH,
        "demand_trend": MarketTrend.STABLE,
        "landlord_friendly": True,
        "property_tax_rate": 0.012,
        "insurance_risk": "medium",
    },
    "birmingham_al": {
        "name": "Birmingham",
        "metro": "Birmingham-Hoover",
        "state": "AL",
        "region": "South",
        "population": 1115289,
        "population_growth_1yr": 0.1,
        "population_growth_5yr": 0.8,
        "unemployment_rate": 0.038,
        "job_growth_1yr": 1.2,
        "major_employers": ["UAB", "Regions Financial", "BBVA"],
        "median_household_income": 52000,
        "income_growth_1yr": 2.8,
        "median_home_price": 205000,
        "median_price_per_sqft": 120,
        "price_change_1yr": 4.5,
        "price_change_5yr": 32.0,
        "median_rent": 1150,
        "rent_change_1yr": 3.0,
        "avg_rent_to_price": 0.67,
        "months_of_inventory": 2.8,
        "days_on_market_avg": 38,
        "price_trend": MarketTrend.MODERATE_GROWTH,
        "rent_trend": MarketTrend.STABLE,
        "demand_trend": MarketTrend.STABLE,
        "landlord_friendly": True,
        "property_tax_rate": 0.004,
        "insurance_risk": "medium",
    },
    "kansas_city_mo": {
        "name": "Kansas City",
        "metro": "Kansas City-Overland Park",
        "state": "MO",
        "region": "Midwest",
        "population": 2192035,
        "population_growth_1yr": 0.8,
        "population_growth_5yr": 4.5,
        "unemployment_rate": 0.033,
        "job_growth_1yr": 1.8,
        "major_employers": ["Cerner", "Sprint", "Garmin", "H&R Block"],
        "median_household_income": 62000,
        "income_growth_1yr": 3.2,
        "median_home_price": 285000,
        "median_price_per_sqft": 155,
        "price_change_1yr": 3.5,
        "price_change_5yr": 40.0,
        "median_rent": 1350,
        "rent_change_1yr": 2.8,
        "avg_rent_to_price": 0.57,
        "months_of_inventory": 2.3,
        "days_on_market_avg": 30,
        "price_trend": MarketTrend.MODERATE_GROWTH,
        "rent_trend": MarketTrend.STABLE,
        "demand_trend": MarketTrend.STABLE,
        "landlord_friendly": True,
        "property_tax_rate": 0.012,
        "insurance_risk": "medium",
    },
    "tampa_fl": {
        "name": "Tampa",
        "metro": "Tampa-St. Petersburg-Clearwater",
        "state": "FL",
        "region": "Southeast",
        "population": 3219514,
        "population_growth_1yr": 1.9,
        "population_growth_5yr": 12.5,
        "unemployment_rate": 0.030,
        "job_growth_1yr": 3.5,
        "major_employers": ["BayCare", "Publix", "USAA", "JPMorgan Chase"],
        "median_household_income": 62000,
        "income_growth_1yr": 4.2,
        "median_home_price": 415000,
        "median_price_per_sqft": 255,
        "price_change_1yr": -1.5,
        "price_change_5yr": 65.0,
        "median_rent": 2100,
        "rent_change_1yr": 1.0,
        "avg_rent_to_price": 0.61,
        "months_of_inventory": 3.8,
        "days_on_market_avg": 42,
        "price_trend": MarketTrend.STABLE,
        "rent_trend": MarketTrend.STABLE,
        "demand_trend": MarketTrend.MODERATE_GROWTH,
        "landlord_friendly": True,
        "property_tax_rate": 0.009,
        "insurance_risk": "high",
    },
    "phoenix_az": {
        "name": "Phoenix",
        "metro": "Phoenix-Mesa-Chandler",
        "state": "AZ",
        "region": "Southwest",
        "population": 4946145,
        "population_growth_1yr": 1.5,
        "population_growth_5yr": 10.2,
        "unemployment_rate": 0.038,
        "job_growth_1yr": 2.8,
        "major_employers": ["Banner Health", "Intel", "Wells Fargo", "Amazon"],
        "median_household_income": 68000,
        "income_growth_1yr": 4.5,
        "median_home_price": 445000,
        "median_price_per_sqft": 275,
        "price_change_1yr": -2.8,
        "price_change_5yr": 52.0,
        "median_rent": 1800,
        "rent_change_1yr": -1.5,
        "avg_rent_to_price": 0.49,
        "months_of_inventory": 4.5,
        "days_on_market_avg": 55,
        "price_trend": MarketTrend.MODERATE_DECLINE,
        "rent_trend": MarketTrend.STABLE,
        "demand_trend": MarketTrend.MODERATE_GROWTH,
        "landlord_friendly": True,
        "property_tax_rate": 0.006,
        "insurance_risk": "low",
    },
}


class MarketResearchAgent(BaseAgent):
    """Agent for researching and analyzing real estate markets."""

    agent_name = "market_research"

    async def run(
        self,
        market_ids: Optional[list[str]] = None,
        min_population: Optional[int] = None,
        min_rent_to_price: Optional[float] = None,
        landlord_friendly_only: bool = False,
    ) -> AgentResult:
        """
        Research and rank markets based on criteria.

        Args:
            market_ids: Specific markets to analyze (None = all)
            min_population: Minimum metro population
            min_rent_to_price: Minimum rent-to-price ratio
            landlord_friendly_only: Only include landlord-friendly states

        Returns:
            AgentResult with ranked list of markets and metrics
        """
        start_time = time.time()
        self.log("Starting market research...")

        markets = []
        errors = []

        # Get markets to analyze
        target_ids = market_ids or list(SAMPLE_MARKETS.keys())

        for market_id in target_ids:
            try:
                market = await self.get_market(market_id)
                if not market:
                    errors.append(f"Market not found: {market_id}")
                    continue

                # Apply filters
                if min_population and (market.population or 0) < min_population:
                    continue
                if landlord_friendly_only and not market.landlord_friendly:
                    continue
                if min_rent_to_price and (market.avg_rent_to_price or 0) < min_rent_to_price:
                    continue

                markets.append(market)

            except Exception as e:
                errors.append(f"Error processing {market_id}: {str(e)}")

        # Calculate metrics and rank
        ranked_markets = self._rank_markets(markets)

        duration_ms = int((time.time() - start_time) * 1000)
        self.log(f"Analyzed {len(ranked_markets)} markets in {duration_ms}ms")

        return AgentResult(
            success=len(errors) == 0,
            data={
                "markets": ranked_markets,
                "count": len(ranked_markets),
            },
            message=f"Analyzed {len(ranked_markets)} markets",
            timestamp=datetime.utcnow(),
            duration_ms=duration_ms,
            errors=errors,
        )

    async def get_market(self, market_id: str) -> Optional[Market]:
        """Get market data by ID."""
        data = SAMPLE_MARKETS.get(market_id)
        if not data:
            return None

        return Market(
            id=market_id,
            name=data["name"],
            metro=data["metro"],
            state=data["state"],
            region=data.get("region"),
            population=data.get("population"),
            population_growth_1yr=data.get("population_growth_1yr"),
            population_growth_5yr=data.get("population_growth_5yr"),
            unemployment_rate=data.get("unemployment_rate"),
            job_growth_1yr=data.get("job_growth_1yr"),
            major_employers=data.get("major_employers", []),
            median_household_income=data.get("median_household_income"),
            income_growth_1yr=data.get("income_growth_1yr"),
            median_home_price=data.get("median_home_price"),
            median_price_per_sqft=data.get("median_price_per_sqft"),
            price_change_1yr=data.get("price_change_1yr"),
            price_change_5yr=data.get("price_change_5yr"),
            median_rent=data.get("median_rent"),
            rent_change_1yr=data.get("rent_change_1yr"),
            avg_rent_to_price=data.get("avg_rent_to_price"),
            months_of_inventory=data.get("months_of_inventory"),
            days_on_market_avg=data.get("days_on_market_avg"),
            price_trend=data.get("price_trend", MarketTrend.STABLE),
            rent_trend=data.get("rent_trend", MarketTrend.STABLE),
            demand_trend=data.get("demand_trend", MarketTrend.STABLE),
            landlord_friendly=data.get("landlord_friendly", True),
            property_tax_rate=data.get("property_tax_rate"),
            insurance_risk=data.get("insurance_risk"),
        )

    def _rank_markets(self, markets: list[Market]) -> list[dict]:
        """Rank markets by investment potential."""
        results = []

        for market in markets:
            metrics = MarketMetrics.from_market(market)

            results.append({
                "market": market,
                "metrics": metrics,
                "overall_score": metrics.overall_score,
                "cash_flow_score": metrics.cash_flow_score,
                "growth_score": metrics.growth_score,
            })

        # Sort by overall score descending
        results.sort(key=lambda x: x["overall_score"], reverse=True)

        # Add rankings
        for i, result in enumerate(results):
            result["rank"] = i + 1

        return results

    async def get_top_markets(
        self,
        n: int = 5,
        strategy: str = "cash_flow",
    ) -> list[dict]:
        """Get top N markets for a given strategy."""
        result = await self.run()

        if not result.success:
            return []

        markets = result.data["markets"]

        # Sort by strategy-specific score
        if strategy == "cash_flow":
            markets.sort(key=lambda x: x["cash_flow_score"], reverse=True)
        elif strategy == "growth":
            markets.sort(key=lambda x: x["growth_score"], reverse=True)
        # Default: overall score (already sorted)

        return markets[:n]

    def compare_markets(self, market_a: Market, market_b: Market) -> dict:
        """Compare two markets side by side."""
        metrics_a = MarketMetrics.from_market(market_a)
        metrics_b = MarketMetrics.from_market(market_b)

        return {
            "market_a": {
                "name": market_a.name,
                "overall_score": metrics_a.overall_score,
                "cash_flow_score": metrics_a.cash_flow_score,
                "growth_score": metrics_a.growth_score,
                "median_price": market_a.median_home_price,
                "median_rent": market_a.median_rent,
                "rent_to_price": market_a.avg_rent_to_price,
            },
            "market_b": {
                "name": market_b.name,
                "overall_score": metrics_b.overall_score,
                "cash_flow_score": metrics_b.cash_flow_score,
                "growth_score": metrics_b.growth_score,
                "median_price": market_b.median_home_price,
                "median_rent": market_b.median_rent,
                "rent_to_price": market_b.avg_rent_to_price,
            },
            "winner": market_a.name if metrics_a.overall_score > metrics_b.overall_score else market_b.name,
        }
