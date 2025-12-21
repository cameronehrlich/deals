# Real Estate Deal Sourcing & Analysis Platform

An automated, agent-driven system to source, analyze, and rank residential real estate investment opportunities in target U.S. markets.

## Features

- **Market Research Agent**: Analyzes metro areas for investment potential based on population growth, job growth, rent-to-price ratios, and landlord-friendliness
- **Deal Analyzer Agent**: Evaluates individual properties with complete financial modeling including cash-on-cash returns, cap rates, and cash flow analysis
- **Sensitivity Analysis**: Stress tests deals against interest rate changes, vacancy increases, and rent decreases
- **Ranking Engine**: Scores and ranks deals based on configurable weights for financial returns, market quality, and risk
- **Multiple Strategies**: Supports cash flow, appreciation, value-add, and distressed investment strategies

## Quick Start

### Installation

```bash
# Clone the repository
cd deals

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .
```

### Usage

#### Search for Deals

```bash
# Search across top markets
python -m src.cli search

# Search specific markets
python -m src.cli search --markets indianapolis_in,cleveland_oh

# With filters
python -m src.cli search --max-price 300000 --min-beds 3 --top 10

# With custom financing
python -m src.cli search --down-payment 0.20 --rate 0.065
```

#### Analyze Markets

```bash
# List and rank all markets
python -m src.cli markets

# Top 5 markets for cash flow
python -m src.cli markets --top 5 --strategy cash_flow

# Top markets for growth
python -m src.cli markets --strategy growth
```

#### Analyze a Specific Market

```bash
python -m src.cli analyze Indianapolis IN --max-price 250000 --limit 30
```

#### Run Stress Tests

```bash
# Stress test a hypothetical deal
python -m src.cli stress-test 200000 1800 --down 0.25 --rate 0.07
```

## Project Structure

```
deals/
├── src/
│   ├── models/          # Data models (Property, Financials, Market, Deal)
│   ├── agents/          # Agent layer (MarketResearch, DealAnalyzer, Pipeline)
│   ├── scrapers/        # Property data scrapers
│   ├── analysis/        # Ranking and sensitivity analysis
│   ├── db/              # Database repository layer
│   ├── utils/           # Utility functions
│   └── cli.py           # Command-line interface
├── config/
│   ├── strategies.yaml  # Investment strategy definitions
│   └── markets.yaml     # Target market configuration
├── tests/               # Test suite
└── data/                # Data storage
```

## Investment Strategies

### Cash Flow (Default)
- Focus on immediate positive cash flow
- Minimum 8% cash-on-cash return
- Minimum $200/month cash flow
- Emphasis on rent-to-price ratio

### Appreciation
- Accept lower cash flow for growth markets
- Target 5% annual appreciation
- Focus on population and job growth

### Value-Add / BRRRR
- Properties with renovation potential
- Target 25% below ARV
- Longer days on market, price reductions

### Distressed
- Foreclosures, auctions, REO
- Minimum 30% discount to market
- Higher risk tolerance

## Financial Modeling

Default assumptions (configurable):
- Down payment: 25%
- Interest rate: 7%
- Loan term: 30 years
- Closing costs: 3%
- Property tax rate: 1.2%
- Insurance: 0.5% of value
- Vacancy: 8%
- Maintenance: 1% of value
- Property management: 10% of rent
- CapEx reserve: 1% of value

## Target Markets (Tier 1)

1. **Indianapolis, IN** - Strong rent-to-price, landlord friendly
2. **Cleveland, OH** - Excellent cash flow, low entry price
3. **Memphis, TN** - Good cash flow, FedEx hub
4. **Birmingham, AL** - Low taxes, affordable entry
5. **Kansas City, MO** - Balanced growth and cash flow

## Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src
```

## API Usage

```python
import asyncio
from src.agents.pipeline import PipelineAgent
from src.models.deal import InvestmentStrategy

async def find_deals():
    agent = PipelineAgent()
    result = await agent.run(
        market_ids=["indianapolis_in", "cleveland_oh"],
        strategy=InvestmentStrategy.CASH_FLOW,
        max_price=250000,
        top_n=10,
    )

    for deal in result.data["deals"]:
        print(f"{deal.property.address}: ${deal.financial_metrics.monthly_cash_flow}/mo")

asyncio.run(find_deals())
```

## Roadmap

### Phase 1 (Current) - Foundation
- [x] Market research agent
- [x] Basic cash flow model
- [x] Mock data scraper
- [x] CLI interface
- [x] Sensitivity analysis

### Phase 2 - Automation
- [ ] Multi-source data ingestion
- [ ] PostgreSQL persistence
- [ ] Real scraping (Zillow, Redfin)
- [ ] Automated monitoring

### Phase 3 - Intelligence
- [ ] Advanced sensitivity analysis
- [ ] Email/Slack alerting
- [ ] Explainability features
- [ ] Web dashboard

## License

MIT
