# Real Estate Deal Sourcing & Analysis Platform

An automated system to source, analyze, and rank residential real estate investment opportunities in target U.S. markets.

## Features

- **Live Property Search**: Search active listings via US Real Estate API (RapidAPI)
- **Property Analysis**: Full financial modeling with cash-on-cash returns, cap rates, and cash flow
- **Market Research**: Analyze metro areas for investment potential
- **URL Import**: Import listings from Zillow, Redfin, or Realtor.com
- **Offer Calculator**: Interactive slider to model different offer prices
- **Sensitivity Analysis**: Stress test deals against rate changes, vacancy, and rent decreases
- **SQLite Persistence**: Save and track properties with favorites
- **Desktop App**: Electron app with local Puppeteer scraping (avoids IP blocking)

## Quick Start

### Web Development

```bash
# Terminal 1: Start API server
pip install -e .
uvicorn api.main:app --reload

# Terminal 2: Start frontend
cd web && npm install && npm run dev

# Open http://localhost:3000
```

### Electron Desktop App

```bash
# Terminals 1 & 2: Start API and web (as above)

# Terminal 3: Start Electron
cd electron && npm install && npm run dev
```

### Docker

```bash
docker compose up --build
# API: http://localhost:8000
# Web: http://localhost:3000
```

## Project Structure

```
deals/
├── api/                    # FastAPI REST API
│   └── routes/             # Endpoints: markets, deals, properties, import, saved
├── web/                    # Next.js 14 frontend
│   └── src/app/            # Pages: dashboard, markets, deals, import, calculator
├── src/
│   ├── models/             # Pydantic models (Property, Financials, Market, Deal)
│   ├── agents/             # Business logic (MarketResearch, DealAnalyzer, Pipeline)
│   ├── data_sources/       # External APIs
│   │   ├── real_estate_providers/  # Pluggable property data providers
│   │   ├── redfin.py       # Market metrics from Redfin Data Center
│   │   ├── fred.py         # Macro data (mortgage rates, unemployment)
│   │   ├── income_data.py  # Census income data by ZIP
│   │   └── rentcast.py     # Rent estimates with HUD FMR fallback
│   ├── db/                 # SQLite persistence layer
│   │   ├── sqlite_repository.py  # CRUD operations
│   │   ├── models.py       # SQLAlchemy models
│   │   └── cache.py        # Response caching
│   └── analysis/           # Ranking and sensitivity analysis
├── electron/               # Desktop app with local scraping
├── config/                 # Strategy and market configs
└── tests/                  # Test suite
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/properties/search` | Search live property listings |
| GET | `/api/properties/usage` | Check API usage stats |
| GET | `/api/markets` | List and rank markets |
| GET | `/api/markets/{id}` | Market details |
| GET | `/api/deals/search` | Search analyzed deals |
| POST | `/api/analysis/calculate` | Calculate financials |
| POST | `/api/import/url` | Import from listing URL |
| POST | `/api/import/parsed` | Analyze pre-parsed property |
| GET | `/api/import/income/{zip}` | Get income data by ZIP |
| GET | `/api/saved/properties` | List saved properties |
| POST | `/api/saved/properties` | Save a property |
| GET | `/api/health` | Health check |

## Environment Variables

**Required for live property search:**
```bash
RAPIDAPI_KEY=your_key_here  # US Real Estate API via RapidAPI
```

**Optional:**
```bash
FRED_API_KEY=xxx            # Live macro data (rates, unemployment)
RENTCAST_API_KEY=xxx        # Property-specific rent estimates
LOG_LEVEL=INFO              # Logging level
```

## Data Sources

| Source | Purpose | Status |
|--------|---------|--------|
| US Real Estate API | Live property listings & search | Active |
| Redfin Data Center | Market metrics (prices, inventory) | Active |
| FRED | Mortgage rates, unemployment | Active |
| HUD Fair Market Rents | Rent baselines by market | Active |
| RentCast | Property rent estimates | Active (with fallback) |
| Census ACS | Income data by ZIP code | Active |
| URL Parser | Zillow/Redfin/Realtor import | Active (Electron only) |

## Target Markets

| Market | Key Strengths |
|--------|---------------|
| Indianapolis, IN | High rent-to-price, landlord friendly |
| Cleveland, OH | Excellent cash flow, low entry |
| Memphis, TN | Good cash flow, FedEx hub |
| Birmingham, AL | Lowest taxes, affordable |
| Kansas City, MO | Balanced growth + cash flow |
| Tampa, FL | Population growth, appreciation |
| Phoenix, AZ | Strong growth |
| Austin, TX | Tech hub, high growth |
| Miami, FL | International demand |
| Houston, TX | Energy sector, diverse economy |

## Financial Defaults

| Parameter | Default |
|-----------|---------|
| Down Payment | 20% |
| Interest Rate | Current 30yr (from FRED) |
| Loan Term | 30 years |
| Closing Costs | 3% |
| Property Tax | 1.2%/year |
| Insurance | 0.5%/year |
| Vacancy | 8% |
| Maintenance | 1%/year |
| Property Mgmt | 10% of rent |
| CapEx Reserve | 1%/year |

## Investment Strategies

| Strategy | Min CoC | Focus |
|----------|---------|-------|
| Cash Flow | 8% | Immediate positive cash flow |
| Appreciation | 2% | Growth markets |
| Value-Add | 10% | Renovation potential |
| Distressed | 12% | Deep discounts |

## API Rate Limits

The US Real Estate API (RapidAPI) has tiered limits:

| Tier | Requests/Month | Cost |
|------|----------------|------|
| Free | 100 | $0 |
| Pro | 5,000 | $9 |
| Ultra | 40,000 | $29 |

The platform tracks usage and shows warnings at 80% capacity. When limits are reached, use the Calculator for manual analysis.

## Development

```bash
# Run tests
pytest tests/ -v

# Type check frontend
cd web && npx tsc --noEmit

# Lint
make lint
```

## Deployment

**Vercel (Current):**
- Frontend: Deployed from `web/` directory
- API: Deployed as Python serverless functions

**Fly.io (Alternative):**
```bash
fly deploy
```

## Roadmap

- [x] Phase 1: Foundation (CLI, models, agents)
- [x] Phase 2: Web Application (FastAPI + Next.js)
- [x] Phase 3: Live Data Integration (US Real Estate API, income data)
- [x] Phase 4: Persistence (SQLite, saved properties, market favorites)
- [ ] Phase 5: Enhanced Analysis (comp analysis, neighborhood scoring)
- [ ] Phase 6: Alerts & Monitoring (new listing notifications)

## License

MIT
