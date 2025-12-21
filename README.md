# Real Estate Deal Sourcing & Analysis Platform

An automated, agent-driven system to source, analyze, and rank residential real estate investment opportunities in target U.S. markets.

## Features

- **Market Research Agent**: Analyzes metro areas for investment potential based on population growth, job growth, rent-to-price ratios, and landlord-friendliness
- **Deal Analyzer Agent**: Evaluates individual properties with complete financial modeling including cash-on-cash returns, cap rates, and cash flow analysis
- **Sensitivity Analysis**: Stress tests deals against interest rate changes, vacancy increases, and rent decreases
- **Ranking Engine**: Scores and ranks deals based on configurable weights for financial returns, market quality, and risk
- **Multiple Strategies**: Supports cash flow, appreciation, value-add, and distressed investment strategies
- **Web Dashboard**: Modern Next.js frontend with interactive deal search and analysis tools
- **REST API**: FastAPI backend for programmatic access

## Quick Start

### Option 1: Docker (Recommended)

```bash
# Build and run both API and web frontend
docker compose up --build

# API available at http://localhost:8000
# Web app available at http://localhost:3000
```

### Option 2: Local Development

```bash
# Install all dependencies
make install

# Run both API and web in development mode
make dev

# Or run separately:
make api  # API on http://localhost:8000
make web  # Web on http://localhost:3000
```

### Option 3: CLI Only

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -e .

# Run CLI
python -m src.cli search --markets indianapolis_in
```

## Project Structure

```
deals/
├── api/                 # FastAPI REST API
│   ├── main.py         # API entry point
│   ├── models.py       # Response models
│   └── routes/         # API endpoints (markets, deals, analysis, import)
├── web/                 # Next.js frontend
│   ├── src/app/        # Pages (dashboard, markets, deals, import, calculator)
│   ├── src/components/ # React components
│   └── src/lib/        # API client, utilities
├── src/                 # Core Python modules
│   ├── models/         # Data models (Property, Financials, Market, Deal)
│   ├── agents/         # Agent layer (MarketResearch, DealAnalyzer, Pipeline)
│   ├── scrapers/       # Property data scrapers
│   ├── data_sources/   # External data integrations (Redfin, FRED, HUD, RentCast)
│   ├── analysis/       # Ranking and sensitivity analysis
│   ├── db/             # Database repository layer
│   └── cli.py          # Command-line interface
├── config/             # Strategy and market configs
├── tests/              # Test suite
├── Dockerfile          # API Docker image
├── docker-compose.yml  # Full stack deployment
└── fly.toml            # Fly.io deployment config
```

## Web Application

### Pages

| Page | URL | Description |
|------|-----|-------------|
| Dashboard | `/` | Overview with top markets and deals |
| Markets | `/markets` | List and rank investment markets |
| Market Detail | `/markets/[id]` | Deep dive into a specific market |
| Find Deals | `/deals` | Search and filter properties |
| Deal Detail | `/deals/[id]` | Full deal analysis with financials |
| Import | `/import` | Import properties from Zillow/Redfin/Realtor URLs |
| Calculator | `/calculator` | Analyze any property with stress testing |

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/markets` | List markets with sorting/filtering |
| GET | `/api/markets/{id}` | Get market details |
| GET | `/api/deals/search` | Search deals with filters |
| GET | `/api/deals/{id}` | Get deal details |
| POST | `/api/analysis/calculate` | Calculate financials for any property |
| POST | `/api/import/url` | Import property from Zillow/Redfin/Realtor URL |
| POST | `/api/import/rent-estimate` | Get rent estimate for an address |
| GET | `/api/import/macro` | Get current mortgage rates and macro data |
| GET | `/api/import/market-data/{city}/{state}` | Get enriched market data |
| GET | `/api/health` | Health check |

## CLI Usage

```bash
# Search for deals across markets
python -m src.cli search --markets indianapolis_in,cleveland_oh --max-price 300000

# List and rank markets
python -m src.cli markets --top 5 --strategy cash_flow

# Analyze a specific market
python -m src.cli analyze Indianapolis IN --limit 30

# Stress test a hypothetical deal
python -m src.cli stress-test 200000 1800 --down 0.25 --rate 0.07
```

## Investment Strategies

| Strategy | Min CoC | Focus |
|----------|---------|-------|
| **Cash Flow** | 8% | Immediate positive cash flow, rent-to-price ratio |
| **Appreciation** | 2% | Growth markets, population & job growth |
| **Value-Add** | 10%+ | Renovation potential, forced appreciation |
| **Distressed** | 12%+ | Foreclosures, auctions, 30%+ discount |

## Financial Modeling

Default assumptions (all configurable):

| Parameter | Default | Description |
|-----------|---------|-------------|
| Down Payment | 25% | Conventional loan |
| Interest Rate | 7% | Current market rate |
| Loan Term | 30 years | Standard mortgage |
| Closing Costs | 3% | Of purchase price |
| Property Tax | 1.2% | Annual rate |
| Insurance | 0.5% | Of property value |
| Vacancy | 8% | ~1 month/year |
| Maintenance | 1% | Annual reserve |
| Property Mgmt | 10% | Of gross rent |
| CapEx | 1% | Replacement reserve |

## Target Markets

| Rank | Market | Strengths |
|------|--------|-----------|
| 1 | Indianapolis, IN | High rent-to-price, landlord friendly, diverse economy |
| 2 | Cleveland, OH | Excellent cash flow, low entry price, healthcare anchor |
| 3 | Memphis, TN | Good cash flow, FedEx hub, landlord friendly |
| 4 | Birmingham, AL | Lowest taxes, affordable, university/medical |
| 5 | Kansas City, MO | Balanced growth + cash flow, stable |
| 6 | Tampa, FL | Population growth, appreciation potential |
| 7 | Phoenix, AZ | Strong growth, cooling from peak |
| 8 | Austin, TX | Tech hub, high growth, expensive |

## Deployment

### Fly.io

```bash
# Deploy API
fly launch  # First time
fly deploy

# Deploy Web (from web/ directory)
cd web
fly launch
fly deploy
```

### Docker Compose

```bash
docker compose up -d
```

### Environment Variables

**API:**
- `LOG_LEVEL` - Logging level (default: INFO)
- `DATABASE_URL` - PostgreSQL connection (optional)

**Web:**
- `API_URL` - Backend API URL (default: http://localhost:8000)

## Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=src --cov-report=html
```

## Data Sources

| Source | Purpose | Status |
|--------|---------|--------|
| Redfin Data Center | Market metrics (prices, inventory, DOM) | Implemented |
| FRED | Macro data (mortgage rates, unemployment) | Implemented |
| HUD Fair Market Rents | Rent baselines for 8 target markets | Implemented |
| RentCast | Property-specific rent estimates | Implemented (with HUD fallback) |
| URL Parser | Import from Zillow/Redfin/Realtor URLs | Implemented |
| BLS | Employment data | Planned |
| Census/ACS | Demographics | Planned |

## Roadmap

- [x] Phase 1: Foundation (CLI, models, agents)
- [x] Phase 1.5: Web Application (FastAPI + Next.js)
- [x] Phase 2: Real Data Sources (Redfin DC, FRED, HUD FMR, RentCast)
- [x] Phase 2.5: URL-to-Deal Import (Zillow, Redfin, Realtor.com)
- [ ] Phase 3: Alerting & Monitoring
- [ ] Phase 4: PostgreSQL Persistence

## License

MIT
