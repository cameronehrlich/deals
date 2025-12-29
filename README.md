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
│   └── src/app/            # Pages: dashboard, markets, deals, import, saved, pipeline, financing
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
| US Real Estate API | Live property listings, search, agent profiles | Active |
| Redfin Data Center | Market metrics (prices, inventory) | Active |
| FRED | Mortgage rates, unemployment | Active |
| HUD Fair Market Rents | Rent baselines by market | Active |
| RentCast | Property rent estimates | Active (with fallback) |
| Census ACS | Income data by ZIP code | Active |
| Census Geocoder | Address geocoding (lat/lng) | Active |
| Walk Score API | Walkability, transit, bike scores | Active |
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

The platform tracks usage and shows warnings at 80% capacity. When limits are reached, import properties via URL on the Import page.

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
- [ ] Phase 5: Transaction Pipeline (financing, outreach, offers) ← **Next**
- [ ] Phase 6: Enhanced Analysis (comp analysis, neighborhood scoring)
- [ ] Phase 7: Alerts & Monitoring (new listing notifications)

---

## Phase 5: Transaction Pipeline

The platform currently helps find and analyze deals. The next layer turns "interesting property" into "under contract" by adding two parallel capabilities: **Financing Desk** and **Outreach & Offers**.

### The Deal Execution Flow

```
Find Property → Analyze → Save to Pipeline
                              ↓
              ┌───────────────┴───────────────┐
              ↓                               ↓
        Line Up Financing              Make Contact
        (Loan scenarios,               (Agent/seller,
         lender quotes)                 templates)
              ↓                               ↓
              └───────────────┬───────────────┘
                              ↓
                        Submit Offer
                              ↓
                      Due Diligence
                              ↓
                          Close
```

### Build Phases (Each Delivers Value Independently)

#### 5.1 Financing Scenarios

**Goal:** Compare different loan options on any saved property to see which financing makes a deal work.

**What it does:**
- Add multiple financing scenarios to a saved property
- Compare how different loans affect CoC return, monthly cash flow, and DSCR
- Quick presets: "Conventional 25% down", "DSCR 20% down", "Hard money", etc.
- See break-even points: "What rate kills this deal?" "What down payment do I need for 8% CoC?"

**Why first:** You already have saved properties with analysis. This extends existing functionality and directly impacts buy/no-buy decisions.

#### 5.2 Contact & Outreach

**Goal:** Track communications with agents/sellers and reduce friction in reaching out.

**What it does:**
- Contact tracker tied to properties (not a standalone CRM)
- Auto-fetch listing agent info via API when saving a property
- Communication timeline per property: calls, emails, notes, next follow-up
- Email templates that auto-fill property details (address, your offer terms, etc.)
- One-click "copy to clipboard" for quick sending via your email client

**Agent Data Integration (US Real Estate API):**

The US Real Estate API we already use includes agent endpoints at no extra cost:

| Endpoint | Use Case |
|----------|----------|
| `/agents/agents-search` | Find agents by city/state |
| `/agents/agents-search-by-zipcode` | Find agents by ZIP |
| `/agents/agent-profile` | Get agent details (name, phone, email, brokerage, photo) |
| `/agents/agent-listings` | See agent's other listings |

When a property is saved, we auto-fetch the listing agent's profile and attach it as a Contact. This gives you agent name, phone, email, and brokerage without manual data entry.

**Templates to include:**
- Initial inquiry (listed property)
- FSBO/off-market outreach
- Follow-up (Day 1, Day 3, Day 7)
- Offer submission cover
- Request for disclosures/rent roll

**Future: Skip Tracing (Off-Market)**

For off-market outreach where you need to find property owners directly:
- Tracerfy API: $0.009/record, finds phone/email for property owners
- BatchData: Pierces LLC/trust ownership to find actual decision-makers
- These would only be added if/when off-market sourcing becomes a priority

#### 5.3 Financing Desk

**Goal:** Standardize the lending process so getting quotes is repeatable, not chaotic.

**What it does:**
- **Borrower Profile** (one-time setup): Income, assets, credit score range, entity info
- **Proof Stack Vault:** Upload/link to common docs (pay stubs, bank statements, tax returns, entity docs)
- **Deal Packet Generator:** One-page property summary with financials, rent estimate, DSCR, your exit strategy - ready to send to lenders
- **Lender Directory:** Track lenders you've worked with or researched, with notes on rates, requirements, responsiveness, and markets served
- **Quote Comparison Grid:** When you get quotes back, enter them in a normalized format to compare: rate, points, term, prepay penalty, DSCR requirement, close timeline

**No lender marketplace integration:** Investment property lending is relationship-based with too much variability for API integration. This is a user-maintained system that gets more valuable as you collect data.

**Mortgage Rate Baseline (Optional):**

Conventional mortgage rate APIs exist (Zillow Mortgage API, US Mortgage Rates API) and could provide a "market baseline" to compare your lender quotes against. However, DSCR/investment property rates are typically 1-1.5% higher than conventional and vary significantly by lender, so these are reference points only - not actionable quotes.

#### 5.4 Offers & Pipeline

**Goal:** Track where each deal stands and generate professional offer packages.

**What it does:**
- **Deal Stages:** Researching → Contacted → Offer Submitted → Under Contract → Due Diligence → Closed (or Lost)
- **Offer Generator:** Create offer package with: cover letter, terms summary, proof of funds, lender pre-qual letter
- **Offer Tracker:** Track multiple active offers, counteroffers, deadlines
- **Due Diligence Checklist:** Per-property checklist (inspection, appraisal, title, insurance quote, rent roll, disclosures)
- **Follow-up Reminders:** Simple task system for next actions with dates

#### 5.5 Deal Room (Optional/Future)

**Goal:** Reduce "where is that PDF?" tax to zero.

**What it does:**
- Shareable link per property (permissioned)
- Contains: deal summary, all docs, communication timeline, current status, key contacts
- Useful when working with partners, lenders, or property managers

### Data Model Extensions

| Entity | Purpose |
|--------|---------|
| FinancingScenario | Loan terms tied to a saved property |
| LoanProduct | Reusable loan templates (presets) |
| Contact | Agent/seller/lender with properties linked |
| Communication | Log entry (call, email, note) tied to contact + property |
| Offer | Terms, status, dates for a property |
| BorrowerProfile | User's financial snapshot (single record) |
| Lender | Lender info with notes and quote history |
| LenderQuote | Specific quote for a property |

### UI Additions

| Page | Purpose |
|------|---------|
| `/financing` | Borrower profile setup, loan presets, lender directory |
| `/pipeline` | Kanban or list view of deals by stage |
| `/saved/{id}` (enhanced) | Add tabs: Financing Scenarios, Contacts, Offers, Documents |

### What This Doesn't Include (Yet)

- **Automated email sending:** Generate emails, but user sends via their own client
- **SMS/calling integration:** Log calls manually, no Twilio integration initially
- **Doc storage:** Links to external storage (Google Drive, Dropbox), not built-in file hosting
- **Lender API integration:** No rate APIs; investment property lending is too variable
- **Automated follow-ups:** Manual reminders, not automated drip campaigns

### Success Criteria

After Phase 5, you should be able to:
1. Save a property and immediately model 3 financing options to find the best structure
2. See at a glance: "I've contacted 5 properties, have 2 offers out, 1 in due diligence"
3. Generate a lender-ready deal packet in under 2 minutes
4. Compare 3 lender quotes side-by-side and pick the best one
5. Never lose track of a follow-up or deadline

---

## License

MIT
