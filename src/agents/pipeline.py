"""Pipeline agent for end-to-end deal sourcing workflow."""

import asyncio
import time
from datetime import datetime
from typing import Optional

from src.agents.base import BaseAgent, AgentResult
from src.agents.market_research import MarketResearchAgent
from src.agents.deal_analyzer import DealAnalyzerAgent
from src.models.deal import Deal, DealPipeline, InvestmentStrategy
from src.models.market import Market
from src.models.financials import LoanTerms, OperatingExpenses
from src.scrapers.mock_scraper import MockScraper


class PipelineAgent(BaseAgent):
    """
    Orchestrator agent that runs the full deal sourcing pipeline.

    Pipeline steps:
    1. Research markets
    2. Scrape properties from target markets
    3. Analyze and score deals
    4. Rank and filter results
    5. Return top deals
    """

    agent_name = "pipeline"

    def __init__(self, config: Optional[dict] = None):
        super().__init__(config)
        self.market_agent = MarketResearchAgent(config)
        self.deal_agent = DealAnalyzerAgent(config)
        self.scraper = MockScraper(config)

    async def run(
        self,
        market_ids: Optional[list[str]] = None,
        strategy: InvestmentStrategy = InvestmentStrategy.CASH_FLOW,
        max_price: Optional[float] = None,
        min_beds: int = 2,
        properties_per_market: int = 20,
        top_n: int = 10,
        loan_terms: Optional[LoanTerms] = None,
        operating_expenses: Optional[OperatingExpenses] = None,
        run_sensitivity: bool = True,
    ) -> AgentResult:
        """
        Run the complete deal sourcing pipeline.

        Args:
            market_ids: Markets to search (None = use top markets)
            strategy: Investment strategy to optimize for
            max_price: Maximum property price
            min_beds: Minimum bedrooms
            properties_per_market: Properties to fetch per market
            top_n: Number of top deals to return
            loan_terms: Custom loan assumptions
            operating_expenses: Custom expense assumptions
            run_sensitivity: Whether to run stress tests

        Returns:
            AgentResult with top ranked deals
        """
        start_time = time.time()
        self.log("Starting deal sourcing pipeline...")
        errors = []

        # Step 1: Research markets
        self.log("Step 1: Researching markets...")
        if market_ids:
            market_result = await self.market_agent.run(market_ids=market_ids)
        else:
            # Get top 5 markets for cash flow
            market_result = await self.market_agent.run()

        if not market_result.success:
            errors.extend(market_result.errors)

        markets = [m["market"] for m in market_result.data["markets"][:5]]
        self.log(f"Selected {len(markets)} markets: {[m.name for m in markets]}")

        # Step 2: Scrape properties from each market
        self.log("Step 2: Scraping properties...")
        all_properties = []

        for market in markets:
            try:
                result = await self.scraper.search(
                    city=market.name,
                    state=market.state,
                    max_price=max_price,
                    min_beds=min_beds,
                    limit=properties_per_market,
                )
                all_properties.extend(result.properties)
                self.log(f"  {market.name}: {len(result.properties)} properties")
            except Exception as e:
                errors.append(f"Scraping {market.name} failed: {str(e)}")

        self.log(f"Total properties scraped: {len(all_properties)}")

        # Step 3: Quick screen
        self.log("Step 3: Quick screening...")
        screened = await self.deal_agent.quick_screen(
            all_properties,
            max_price=max_price,
            min_beds=min_beds,
        )
        self.log(f"Properties passing quick screen: {len(screened)}")

        # Step 4: Full analysis
        self.log("Step 4: Analyzing deals...")

        # Group properties by market for analysis
        all_deals = []
        for market in markets:
            market_props = [p for p in screened if p.city == market.name and p.state == market.state]
            if not market_props:
                continue

            result = await self.deal_agent.run(
                properties=market_props,
                market=market,
                loan_terms=loan_terms,
                operating_expenses=operating_expenses,
                run_sensitivity=run_sensitivity,
            )

            if result.success:
                all_deals.extend(result.data["deals"])
            else:
                errors.extend(result.errors)

        self.log(f"Deals passing analysis: {len(all_deals)}")

        # Step 5: Final ranking across all markets
        self.log("Step 5: Final ranking...")
        all_deals.sort(
            key=lambda d: d.score.strategy_scores.get(strategy.value, d.score.overall_score)
            if d.score else 0,
            reverse=True,
        )

        # Update ranks
        for i, deal in enumerate(all_deals):
            if deal.score:
                deal.score.rank = i + 1

        top_deals = all_deals[:top_n]

        duration_ms = int((time.time() - start_time) * 1000)
        self.log(f"Pipeline complete in {duration_ms}ms. Top {len(top_deals)} deals identified.")

        return AgentResult(
            success=len(top_deals) > 0,
            data={
                "deals": top_deals,
                "all_deals": all_deals,
                "markets_analyzed": len(markets),
                "properties_scraped": len(all_properties),
                "properties_screened": len(screened),
                "deals_analyzed": len(all_deals),
            },
            message=f"Found {len(top_deals)} top deals from {len(markets)} markets",
            timestamp=datetime.utcnow(),
            duration_ms=duration_ms,
            errors=errors,
        )

    async def refresh_deal(self, deal: Deal) -> Deal:
        """Refresh analysis for an existing deal."""
        # Re-fetch property data
        property = await self.scraper.get_property(deal.property.id)
        if property:
            deal.property = property

        # Re-run analysis
        deal.analyze()
        return deal

    async def monitor_markets(
        self,
        market_ids: list[str],
        interval_seconds: int = 3600,
        callback=None,
    ):
        """
        Continuously monitor markets for new deals.

        This is a placeholder for production monitoring functionality.
        """
        self.log(f"Starting market monitoring for {market_ids}")
        while True:
            result = await self.run(market_ids=market_ids, top_n=5)
            if callback and result.success:
                await callback(result.data["deals"])
            await asyncio.sleep(interval_seconds)
