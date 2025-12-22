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
| URL Parser | Import from Zillow/Redfin/Realtor URLs | Implemented (blocked by cloud IPs) |
| **US Real Estate API** | **Live property listings & search** | **Phase 3 - In Progress** |
| BLS | Employment data | Planned |
| Census/ACS | Demographics | Planned |

---

## US Real Estate API Integration (Phase 3)

### Overview

The [US Real Estate API](https://rapidapi.com/datascraper/api/us-real-estate) on RapidAPI provides direct access to property listings from Zillow, Redfin, Realtor, and OpenDoor. This replaces the unreliable URL scraping approach which gets blocked by cloud provider IPs.

### API Credentials

```
Provider: RapidAPI
API: US Real Estate (by datascraper)
Base URL: https://us-real-estate.p.rapidapi.com
```

**Environment Variables:**
```bash
RAPIDAPI_KEY=your_api_key_here          # Required
RAPIDAPI_HOST=us-real-estate.p.rapidapi.com
```

### Rate Limits & Tiers

| Tier | Price | Requests/Month | Cost/Request |
|------|-------|----------------|--------------|
| **Free** | $0 | **300** | - |
| Pro | $9 | 5,000 | $0.002 |
| Ultra | $29 | 40,000 | $0.0007 |
| Mega | $99 | 200,000 | $0.0005 |

**Current Tier: FREE (300 requests/month)**

### Rate Limit Strategy

Since we're on the free tier, we MUST be conservative:

1. **Track Usage**: Store request count in localStorage (frontend) and environment/file (backend)
2. **Cache Aggressively**: Cache all API responses for 24 hours minimum
3. **UI Feedback**:
   - Show remaining requests in UI header/footer
   - Warning banner at 80% usage (240 requests)
   - Error state at 100% with "Upgrade" CTA
4. **Graceful Degradation**: Fall back to manual entry when limit hit
5. **Batch Requests**: Prefer bulk endpoints over multiple single calls

### Key Endpoints to Integrate

#### Priority 1: Property Search (Core Feature)
```
GET /v3/for-sale
Parameters:
  - state_code: "IN", "OH", "TN", etc.
  - city: "Indianapolis", "Cleveland", etc.
  - offset: 0 (pagination)
  - limit: 50 (max per request)
  - price_min, price_max: Filter by price
  - beds_min, baths_min: Filter by beds/baths
  - property_type: "single_family", "multi_family", "condo", "townhouse"
  - sort: "newest", "price_low", "price_high"

Returns: Array of properties with address, price, beds, baths, sqft, photos, listing_id
Cost: 1 request per search
```

#### Priority 2: Property Detail
```
GET /v3/property-detail
Parameters:
  - property_id: From search results

Returns: Full property details including:
  - Price history
  - Tax history
  - Property features
  - Neighborhood info
  - Schools nearby
  - Similar homes

Cost: 1 request per property
```

#### Priority 3: Home Value Estimate
```
GET /for-sale/home-estimate-value
Parameters:
  - property_id: From search or URL

Returns: Estimated value (like Zestimate)
Cost: 1 request
```

#### Priority 4: Rental Comps
```
GET /v3/for-rent
Parameters:
  - state_code, city, postal_code
  - beds_min, beds_max
  - price_min, price_max

Returns: Active rental listings for rent estimate validation
Cost: 1 request per search
```

#### Priority 5: Recently Sold (Market Analysis)
```
GET /sold-homes
Parameters:
  - state_code, city
  - max_sold_days: 90 (last 3 months)

Returns: Recent sales for market trend analysis
Cost: 1 request per search
```

### Implementation Plan

#### Backend: `src/data_sources/us_real_estate.py`

```python
class USRealEstateClient:
    """
    US Real Estate API client via RapidAPI.

    Features:
    - Request tracking and rate limit enforcement
    - Response caching (24hr TTL)
    - Graceful error handling
    """

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://us-real-estate.p.rapidapi.com"
        self.headers = {
            "X-RapidAPI-Key": api_key,
            "X-RapidAPI-Host": "us-real-estate.p.rapidapi.com"
        }
        self._request_count = 0
        self._cache = {}  # In-memory cache, consider Redis for production

    async def search_properties(
        self,
        city: str,
        state_code: str,
        max_price: int = None,
        min_beds: int = None,
        property_type: str = None,
        limit: int = 20
    ) -> list[Property]:
        """Search for-sale properties in a market."""
        pass

    async def get_property_detail(self, property_id: str) -> PropertyDetail:
        """Get full property details."""
        pass

    async def get_home_estimate(self, property_id: str) -> float:
        """Get estimated home value."""
        pass

    async def search_rentals(
        self,
        city: str,
        state_code: str,
        beds: int = None
    ) -> list[Rental]:
        """Search rental listings for rent comps."""
        pass

    async def get_sold_homes(
        self,
        city: str,
        state_code: str,
        days: int = 90
    ) -> list[SoldProperty]:
        """Get recently sold properties."""
        pass

    def get_usage(self) -> dict:
        """Return current usage stats."""
        return {
            "requests_used": self._request_count,
            "requests_limit": 300,  # Free tier
            "requests_remaining": 300 - self._request_count,
            "percent_used": (self._request_count / 300) * 100
        }
```

#### Backend: New API Endpoint

```
GET /api/properties/search
Parameters:
  - market: "indianapolis_in" (market ID)
  - max_price: 300000
  - min_beds: 3
  - property_type: "single_family"
  - limit: 20

Response:
{
  "properties": [...],
  "total_count": 150,
  "api_usage": {
    "requests_used": 45,
    "requests_remaining": 255,
    "warning": null | "Approaching limit" | "Limit reached"
  }
}
```

#### Frontend: UI Components

1. **API Usage Indicator** (in Navigation or Footer)
   ```
   [====----] 45/300 API calls used
   ```

2. **Warning Banner** (at 80%+ usage)
   ```
   ⚠️ API limit almost reached (240/300). Upgrade for more searches.
   ```

3. **Limit Reached State**
   ```
   🚫 Monthly API limit reached. Use Calculator for manual analysis.
   [Upgrade Plan] [Use Calculator]
   ```

4. **Property Search Page** (`/deals` enhancement)
   - Replace mock data with live API results
   - Show "Live Data" badge on API-sourced properties
   - Loading states with "Searching properties..." feedback

### Integration with Existing Features

| Feature | Current | With US Real Estate API |
|---------|---------|-------------------------|
| **Deal Search** | Mock data only | Live property listings |
| **Import URL** | Scraping (blocked on cloud) | API lookup by address |
| **Property Detail** | Limited data | Full details, photos, history |
| **Rent Estimate** | RentCast + HUD fallback | + Rental comps from API |
| **Market Analysis** | Redfin Data Center stats | + Live sold data |

### Caching Strategy

```python
CACHE_TTL = {
    "property_search": 3600,      # 1 hour - listings change often
    "property_detail": 86400,     # 24 hours - details stable
    "home_estimate": 86400,       # 24 hours - estimates stable
    "sold_homes": 86400,          # 24 hours - historical data
    "rentals": 3600,              # 1 hour - rental market moves fast
}
```

### Error Handling

| Error | UI Response |
|-------|-------------|
| 429 Rate Limited | "API limit reached. Try again next month or upgrade." |
| 401 Unauthorized | "API key invalid. Check configuration." |
| 404 Not Found | "Property not found. Try a different search." |
| 500 Server Error | "Service temporarily unavailable. Using cached data." |
| Network Error | "Connection failed. Check your internet." |

### Testing Strategy

1. **Unit Tests**: Mock API responses, test parsing and caching
2. **Integration Tests**: Use 5-10 requests from free tier for real API tests
3. **E2E Tests**: Mock API at network level to avoid burning quota

### Files to Create/Modify

**New Files:**
- `src/data_sources/us_real_estate.py` - API client
- `api/routes/properties.py` - New search endpoint
- `web/src/components/ApiUsageIndicator.tsx` - Usage UI
- `tests/test_us_real_estate.py` - Tests

**Modified Files:**
- `src/data_sources/__init__.py` - Export new client
- `src/data_sources/aggregator.py` - Integrate as data source
- `api/main.py` - Register new router
- `web/src/app/deals/page.tsx` - Use live API for search
- `web/src/lib/api.ts` - Add new API methods
- `web/src/components/Navigation.tsx` - Add usage indicator

---

## Roadmap

- [x] Phase 1: Foundation (CLI, models, agents)
- [x] Phase 1.5: Web Application (FastAPI + Next.js)
- [x] Phase 2: Real Data Sources (Redfin DC, FRED, HUD FMR, RentCast)
- [x] Phase 2.5: URL-to-Deal Import (Zillow, Redfin, Realtor.com)
- [ ] **Phase 3: US Real Estate API Integration** ← Current
  - [ ] Create `USRealEstateClient` with caching & rate limiting
  - [ ] Add `/api/properties/search` endpoint
  - [ ] Build API usage indicator component
  - [ ] Integrate with Deal Search page
  - [ ] Add warning/error states for rate limits
- [ ] Phase 4: Alerting & Monitoring
- [ ] Phase 5: PostgreSQL Persistence

## License

MIT
