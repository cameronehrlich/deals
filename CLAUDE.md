# CLAUDE.md

Context for Claude Code when working on this project.

## Overview

Real estate investment analysis platform. Search live listings, analyze deals, save favorites.

**Stack:** Python 3.10+ / FastAPI / Next.js 14 / TypeScript / Tailwind / SQLite / Electron

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
└── routes/
    ├── markets.py       # GET /api/markets
    ├── deals.py         # GET /api/deals/search
    ├── properties.py    # GET /api/properties/search (live API)
    ├── import_property.py  # POST /api/import/url, /parsed, /income/{zip}
    ├── saved.py         # GET/POST /api/saved/properties, /markets
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
```

## Key Files by Feature

| Feature | Files |
|---------|-------|
| Live property search | `api/routes/properties.py`, `src/data_sources/real_estate_providers/` |
| Property analysis | `api/routes/import_property.py`, `src/models/financials.py` |
| Saved properties | `api/routes/saved.py`, `src/db/sqlite_repository.py` |
| Market favorites | `api/routes/saved.py`, `web/src/app/markets/page.tsx` |
| Income data | `src/data_sources/income_data.py`, `api/routes/import_property.py` |
| URL scraping | `electron/scraper.js`, `src/data_sources/url_parser.py` |
| Image carousel | `web/src/components/ImageCarousel.tsx` |
| Sorting/filtering | `web/src/app/deals/page.tsx` (SORT_OPTIONS, client-side) |
| Property analysis UI | `web/src/components/PropertyAnalysisView.tsx` (shared for deals/saved) |
| Walk Score | `src/data_sources/walkscore.py`, `api/routes/import_property.py` |
| Flood zone | `src/data_sources/fema_flood.py`, `api/routes/import_property.py` |
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

```bash
pytest tests/ -v
cd web && npx tsc --noEmit
```
