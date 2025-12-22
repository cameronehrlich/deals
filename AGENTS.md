# Repository Guidelines

## Project Structure
FastAPI backend (`api/`), Python core (`src/`), Next.js frontend (`web/`), Electron desktop (`electron/`).

- `src/agents/` - Business logic (MarketResearch, DealAnalyzer, Pipeline)
- `src/data_sources/` - External APIs (Redfin, FRED, HUD, RentCast, US Real Estate)
- `src/data_sources/real_estate_providers/` - Pluggable property data providers
- `src/db/` - SQLite persistence (sqlite_repository.py, models.py, cache.py)
- `src/analysis/` - Scoring and sensitivity analysis
- `api/routes/` - HTTP handlers (markets, deals, properties, import, saved)
- `web/src/app/` - Next.js pages
- `web/src/components/` - React components
- `web/src/lib/` - API client and utilities
- `electron/` - Desktop app with Puppeteer scraping
- `config/` - Strategy and market configs
- `tests/` - Test suite

## Development Commands
```bash
# Install
pip install -e . && cd web && npm install

# Run API + Web
uvicorn api.main:app --reload  # Terminal 1
cd web && npm run dev          # Terminal 2

# Run Electron (optional)
cd electron && npm run dev     # Terminal 3

# Tests
pytest tests/ -v
cd web && npx tsc --noEmit
```

## Coding Style
- Python: Black defaults, snake_case functions/vars, PascalCase classes
- TypeScript: ESLint, PascalCase components, camelCase utilities
- Run `make lint` before committing

## Commits
Short imperative subject lines. Reference component touched. Squash WIP commits.

Example: "Add image carousel to property cards"

## Pull Requests
Include: 1) Summary of change, 2) Context/issue, 3) Verification steps (pytest, lint, screenshots for UI)
