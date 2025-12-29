# CLAUDE.md

Context for Claude Code when working on this project.

## Overview

Real estate investment analysis platform. Search live listings, analyze deals, save favorites.

**Stack:** Python 3.10+ / FastAPI / Next.js 14 / TypeScript / Tailwind / SQLite (dev) / Postgres (prod) / Electron

## Architecture

```
src/
├── models/              # Pydantic: Property, Financials, Market, Deal
├── agents/              # Business logic: MarketResearch, DealAnalyzer, Pipeline
├── data_sources/
│   ├── real_estate_providers/   # Pluggable API providers (US Real Estate Listings)
│   │   ├── base.py              # RealEstateProvider protocol, PropertyListing dataclass
│   │   ├── registry.py          # get_provider(), list_providers()
│   │   └── us_real_estate_listings.py  # RapidAPI implementation
│   ├── redfin.py        # Market metrics
│   ├── fred.py          # Macro data (rates)
│   ├── income_data.py   # Census income by ZIP
│   ├── rentcast.py      # Rent estimates (HUD fallback)
│   └── url_parser.py    # Parse Zillow/Redfin/Realtor URLs
├── db/
│   ├── sqlite_repository.py  # CRUD: markets, saved properties, cache
│   ├── models.py             # SQLAlchemy: MarketDB, SavedPropertyDB, SearchCacheDB
│   └── cache.py              # CacheManager with TTL
└── analysis/            # Ranking, sensitivity testing

api/
├── main.py              # FastAPI app, CORS, router registration
├── jobs/
│   ├── worker.py        # Background job worker (polling or run_once)
│   └── handlers.py      # Job handlers: enrich_market, enrich_property
└── routes/
    ├── markets.py       # GET /api/markets
    ├── deals.py         # GET /api/deals/search
    ├── properties.py    # GET /api/properties/search (live API)
    ├── import_property.py  # POST /api/import/url, /parsed, /income/{zip}
    ├── saved.py         # GET/POST /api/saved/properties, /markets
    ├── jobs.py          # Background job management, /api/jobs/process
    └── analysis.py      # POST /api/analysis/calculate

web/src/
├── app/                 # Next.js App Router
│   ├── page.tsx         # Dashboard
│   ├── markets/         # Market list and detail
│   ├── deals/           # Live search with sorting, load more
│   ├── import/          # URL import and property analysis
│   └── calculator/      # Manual entry calculator
├── components/
│   ├── Navigation.tsx
│   ├── ImageCarousel.tsx    # Property photo carousel
│   ├── ApiUsageIndicator.tsx
│   ├── ScoreGauge.tsx
│   └── LoadingSpinner.tsx
└── lib/
    ├── api.ts           # Typed API client
    ├── utils.ts         # Formatting helpers
    └── electron.ts      # Electron bridge

electron/
├── main.js              # Electron main process
├── preload.js           # IPC bridge
└── scraper.js           # Puppeteer scraper for Zillow/Redfin/Realtor
```

## Property Journey Architecture

Properties flow through three tiers of increasing data richness:

**Tier 1 - Quick Score (Search Results)**
- Basic metrics: price, beds/baths, sqft, days on market
- Quick CoC and cap rate estimates
- Displayed in search results and deal cards
- Data from: Live API search

**Tier 2 - Full Analysis (Deal Detail Page)**
- Complete financial analysis with expense breakdown
- Location insights: Walk Score, noise, schools, flood zone
- Market context and comparable properties
- Pros/cons/red flags evaluation
- Data fetched on-demand, not persisted

**Tier 3 - Enriched (Saved Properties)**
- All Tier 2 data, persisted to SQLite
- Location data cached to avoid repeated API calls
- Custom "What Should I Offer" scenarios
- User notes and tags
- Re-analyze capability with current market data

**Key Files:**
- `src/db/models.py` - `SavedPropertyDB` with JSON columns for location_data, custom_scenarios
- `api/routes/saved.py` - Enrichment endpoints: `/refresh-location`, `/reanalyze`, `/scenarios`
- `web/src/components/PropertyAnalysisView.tsx` - Shared UI component for Tier 2 & 3

**Adding New Location Data:**
1. Create data source in `src/data_sources/` (e.g., `fema_flood.py`)
2. Add endpoint in `api/routes/import_property.py` for on-demand fetching
3. Add to `location_data` JSON in `SavedPropertyDB` for persistence
4. Add cache TTL in `src/db/cache.py`
5. Display in `PropertyAnalysisView.tsx`

## Key Patterns

**Data Flow:** Frontend → api.ts → FastAPI routes → data_sources/db → external APIs

**Property Search:** `get_provider()` returns configured provider, `search_properties()` fetches from RapidAPI, results cached in SQLite

**Financial Analysis:** `Financials.calculate()` computes all metrics from price, rent, and assumptions

**Rent Estimates:** RentCast API → HUD FMR fallback (embedded data for 10 markets)

**Caching:** `CacheManager` with TTL per data type. Key TTLs:
- Listings: 1hr
- Income: 24hr
- Walk Score: 30 days
- Noise/Schools: 1 week
- Flood Zone: 1 year

## Background Jobs

DB-backed job queue for async tasks like market/property enrichment.

**Job Types:**
- `enrich_market` - Fetch data from Redfin, BLS, Census, HUD for a market
- `enrich_property` - Geocode, get Walk Score, flood zone, run analysis

**Key Endpoints:**
- `POST /api/jobs/enqueue-markets` - Queue enrichment for favorite markets
- `POST /api/jobs/enqueue-property` - Create property + queue enrichment
- `POST /api/jobs/process?limit=10` - Process pending jobs (for cron)
- `GET /api/jobs` - List jobs with status
- `GET /api/jobs/stats` - Queue statistics

**Local Development:**
```bash
# Run worker continuously (polls every 2s)
python -m api.jobs.worker
```

**Production (Vercel):**
The worker can't run continuously on serverless. Use cron to call `/api/jobs/process`:

```json
// vercel.json
{
  "crons": [
    {
      "path": "/api/jobs/process",
      "schedule": "*/5 * * * *"
    }
  ]
}
```

Note: Vercel Cron requires Pro plan. Alternatively, use external cron service (cron-job.org).

## Running Locally

```bash
# API (port 8000)
uvicorn api.main:app --reload

# Web (port 3000)
cd web && npm run dev

# Electron (optional, for local scraping)
cd electron && npm run dev
```

## Environment Variables

```bash
RAPIDAPI_KEY=xxx          # Required for live property search
WALKSCORE_API_KEY=xxx     # Required for Walk Score (official API)
FRED_API_KEY=xxx          # Optional, macro data
RENTCAST_API_KEY=xxx      # Optional, rent estimates
BLS_API_KEY=xxx           # Optional, metro employment data (get free at data.bls.gov/registrationEngine)
```

## Key Files by Feature

| Feature | Files |
|---------|-------|
| Live property search | `api/routes/properties.py`, `src/data_sources/real_estate_providers/` |
| Property analysis | `api/routes/import_property.py`, `src/models/financials.py` |
| Saved properties | `api/routes/saved.py`, `src/db/sqlite_repository.py` |
| Market favorites | `api/routes/saved.py`, `web/src/app/markets/page.tsx` |
| Background jobs | `api/routes/jobs.py`, `api/jobs/worker.py`, `api/jobs/handlers.py` |
| Market enrichment | `src/data_sources/aggregator.py`, `api/jobs/handlers.py` |
| Income data | `src/data_sources/income_data.py`, `api/routes/import_property.py` |
| URL scraping | `electron/scraper.js`, `src/data_sources/url_parser.py` |
| Image carousel | `web/src/components/ImageCarousel.tsx` |
| Sorting/filtering | `web/src/app/deals/page.tsx` (SORT_OPTIONS, client-side) |
| Property analysis UI | `web/src/components/PropertyAnalysisView.tsx` (shared for deals/saved) |
| Walk Score | `src/data_sources/walkscore.py`, `api/routes/import_property.py` |
| Flood zone | `src/data_sources/fema_flood.py`, `api/routes/import_property.py` |
| Geocoding | `src/data_sources/geocoder.py` (Census Geocoder API, free, no key required) |
| Location enrichment | `api/routes/saved.py` (`/refresh-location`, `/reanalyze`) |

## Common Tasks

**Add API endpoint:** Create route in `api/routes/`, register in `api/main.py`

**Add data source:** Implement in `src/data_sources/`, export from `__init__.py`

**Add frontend page:** Create in `web/src/app/`, add to Navigation.tsx, add API methods to `lib/api.ts`

**Add provider:** Implement `RealEstateProvider` protocol in `real_estate_providers/`, register in `registry.py`

## Current State

- Live property search: Working (US Real Estate Listings API via RapidAPI)
- SQLite persistence: Working (saved properties, market favorites, caching)
- Electron scraping: Working (local Puppeteer avoids IP blocking)
- API rate limiting: 100 req/month free tier, tracked in `.api_usage_listings.json`
- Frontend: Next.js 14 with image carousel, sorting, progressive loading

## Target Markets

Phoenix AZ, Tampa FL, Austin TX, Miami FL, Indianapolis IN, Cleveland OH, Memphis TN, Birmingham AL, Kansas City MO, Houston TX

## Testing

**Run all tests:**
```bash
pytest tests/ -v              # All tests with verbose output
pytest tests/ -q              # Quick summary
pytest tests/ --tb=short      # Shorter tracebacks
```

**Run specific test suites:**
```bash
pytest tests/test_repository.py   # Database CRUD operations
pytest tests/test_cache.py        # Cache manager with TTL
pytest tests/test_api_routes.py   # API endpoint tests
pytest tests/test_scoring.py      # Market/deal scoring logic
pytest tests/test_integration.py  # End-to-end flows
pytest tests/test_financing.py    # Loan products and calculations
```

**Test Suite Overview (~200+ tests):**

| File | Tests | Description |
|------|-------|-------------|
| `test_repository.py` | ~50 | SQLite repository CRUD: deals, markets, saved properties, jobs |
| `test_cache.py` | ~25 | CacheManager: TTL, invalidation, income cache, stats |
| `test_api_routes.py` | ~40 | FastAPI routes: health, deals, markets, saved, jobs |
| `test_scoring.py` | ~35 | MarketMetrics and DealScore calculations |
| `test_integration.py` | ~20 | Full flows: deal lifecycle, market enrichment, caching |
| `test_financing.py` | ~25 | Loan products CRUD, scenario calculations |

**Test Isolation:**
- Tests use temporary SQLite databases created via `tempfile.NamedTemporaryFile`
- Each test gets a fresh database that's auto-deleted after the test
- Your real `deals.db` is never touched by tests

**Key Fixtures (conftest.py):**
- `repository` - Isolated SQLiteRepository with temp database
- `sample_deal`, `sample_property`, `sample_market` - Pre-built test data
- `test_session` - Raw SQLAlchemy session for direct DB access
- `api_client` - FastAPI TestClient for route testing

**Frontend type checking:**
```bash
cd web && npx tsc --noEmit
```
