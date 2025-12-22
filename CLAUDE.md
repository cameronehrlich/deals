# CLAUDE.md

This file provides context for Claude Code when working on this project.

## Project Overview

Real Estate Deal Sourcing & Analysis Platform - an automated system to source, analyze, and rank residential real estate investment opportunities in target U.S. markets.

**Tech Stack:**
- Backend: Python 3.10+, FastAPI, Pydantic
- Frontend: Next.js 14, React, TypeScript, Tailwind CSS
- Desktop: Electron 28, Puppeteer (local scraping)
- Data: httpx for async HTTP, pandas for data processing
- Testing: pytest, pytest-asyncio

## Architecture

### Backend Structure

```
src/
├── models/          # Pydantic data models
│   ├── property.py  # Property with pricing, location, details
│   ├── financials.py # Financial calculations (mortgage, cash flow, CoC)
│   ├── market.py    # Market metrics and scoring
│   └── deal.py      # Deal combining property + financials + market
├── agents/          # Business logic layer
│   ├── market_research.py  # Market analysis and ranking
│   ├── deal_analyzer.py    # Property analysis and quick screening
│   └── pipeline.py         # End-to-end deal sourcing workflow
├── data_sources/    # External data integrations
│   ├── redfin.py    # Redfin Data Center market metrics
│   ├── fred.py      # FRED API for macro data (rates, unemployment)
│   ├── hud_fmr.py   # HUD Fair Market Rents (embedded for 8 markets)
│   ├── rentcast.py  # RentCast API with HUD fallback
│   ├── url_parser.py # Parse Zillow/Redfin/Realtor listings
│   └── aggregator.py # Combines all data sources
├── analysis/        # Analysis engines
│   ├── ranking.py   # Score and rank deals
│   └── sensitivity.py # Stress testing
└── scrapers/        # Property scrapers (mock for now)

api/
├── main.py          # FastAPI app with CORS, routers
├── models.py        # API response models
└── routes/
    ├── markets.py   # Market endpoints
    ├── deals.py     # Deal search and detail
    ├── analysis.py  # Calculator endpoints
    └── import_property.py # URL import, rent estimates, macro data
```

### Frontend Structure

```
web/src/
├── app/             # Next.js App Router pages
│   ├── page.tsx     # Dashboard
│   ├── markets/     # Market list and detail
│   ├── deals/       # Deal search and detail
│   ├── import/      # URL import feature
│   └── calculator/  # Financial calculator
├── components/      # Reusable React components
│   ├── Navigation.tsx
│   ├── ScoreGauge.tsx
│   ├── DealCard.tsx
│   └── ...
└── lib/
    ├── api.ts       # API client with typed methods
    └── utils.ts     # Formatting, styling utilities
```

## Key Patterns

### Data Models
- All models use Pydantic for validation
- Models have `@property` methods for computed fields
- Financial calculations happen in `Financials.calculate()` class method

### Agents
- Agents are stateless classes with async methods
- Return `AgentResult` with success, data, message, errors
- Log operations using the `log()` helper

### Data Sources
- All external clients use httpx for async HTTP
- Graceful fallbacks when APIs unavailable (e.g., RentCast → HUD FMR)
- Mock data available when no API keys configured

### API
- FastAPI with typed request/response models
- CORS configured for localhost:3000 and production domains
- Routers organized by domain (markets, deals, analysis, import)

### Frontend
- Next.js 14 App Router with "use client" for interactive pages
- Tailwind CSS with custom component classes in globals.css
- API client in `lib/api.ts` handles all backend communication

## Running the Project

### Web Mode (Browser)

```bash
# Install Python dependencies
pip install -e .

# Run API (port 8000)
uvicorn api.main:app --reload

# Install frontend dependencies
cd web && npm install

# Run frontend (port 3000)
npm run dev

# Run tests
pytest tests/ -v

# Type check frontend
cd web && npx tsc --noEmit
```

### Electron Mac App (Local Development)

The Electron app provides a native Mac experience with local property scraping (avoids IP blocking on Vercel).

```bash
# Terminal 1: Start API server
uvicorn api.main:app --reload

# Terminal 2: Start Next.js dev server
cd web && npm run dev

# Terminal 3: Start Electron app
cd electron && npm run dev
```

The Electron app loads from `localhost:3000` in development and uses local Puppeteer for scraping.

### Electron Structure

```
electron/
├── main.js          # Main Electron process, window config, IPC handlers
├── preload.js       # Context bridge exposing electronAPI to renderer
├── scraper.js       # Puppeteer-based local scraping for Zillow/Redfin/Realtor
└── package.json     # Electron and Puppeteer dependencies
```

**Key Features:**
- Liquid Glass UI (macOS vibrancy effect)
- Hidden title bar with traffic lights
- Local scraping via Puppeteer (residential IP = no blocking)
- IPC bridge for secure communication between main/renderer

**Environment:**
- `NODE_ENV=development` - Loads from localhost:3000
- `NODE_ENV=production` - Loads from Vercel deployment
- `API_URL` - Override API URL (default: Vercel API)

## Common Tasks

### Adding a new API endpoint
1. Add route function in `api/routes/<domain>.py`
2. Add response model in `api/models.py` if needed
3. Router is already registered in `api/main.py`

### Adding a new data source
1. Create client in `src/data_sources/<source>.py`
2. Add to `DataAggregator` in `aggregator.py`
3. Export from `__init__.py`
4. Add tests in `tests/test_data_sources.py`

### Adding a new frontend page
1. Create `web/src/app/<page>/page.tsx`
2. Add to navigation in `web/src/components/Navigation.tsx`
3. Add API methods to `web/src/lib/api.ts` if needed

## Environment Variables

**API:**
- `FRED_API_KEY` - Optional, enables live FRED data
- `RENTCAST_API_KEY` - Optional, enables RentCast rent estimates
- `LOG_LEVEL` - Logging level (default: INFO)

**Frontend:**
- `API_URL` - Backend URL (default: http://localhost:8000)

## Target Markets

The platform focuses on 8 markets with embedded HUD FMR data:
- Indianapolis, IN (primary)
- Cleveland, OH
- Memphis, TN
- Birmingham, AL
- Kansas City, MO
- Tampa, FL
- Phoenix, AZ
- Austin, TX

## Investment Strategies

- **Cash Flow**: 8%+ CoC, prioritizes rent-to-price ratio
- **Appreciation**: 2%+ CoC, prioritizes market growth
- **Value-Add**: 10%+ CoC, renovation potential
- **Distressed**: 12%+ CoC, deep discounts

## Testing

- 45 tests covering models, agents, analysis, and data sources
- Use `pytest tests/ -v` to run all tests
- Tests use sample/mock data, no external API calls
