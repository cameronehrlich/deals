# Repository Guidelines

## Project Structure & Module Organization
The repo pairs a FastAPI backend (`api/`), multi-agent Python core (`src/`), Next.js frontend (`web/`), and shared configs/tests. Use `src/agents/*` for pipeline logic, `src/data_sources/*` for Redfin/FRED/HUD integrations, `src/analysis/*` for scoring, and `api/routes/*.py` for HTTP handlers. UI lives in `web/src/app` (routes), `web/src/components` (shared UI), and `web/src/lib` (client utils). Persistent settings, like target markets and strategy weights, live under `config/`. Keep fixtures in `data/` and unit tests in `tests/`. Electron helpers for scraping are isolated in `electron/`.

## Build, Test, and Development Commands
Run `make install` once to install Python (editable with extras) and frontend deps. `make dev` launches both API (`uvicorn api.main:app --reload`) and web (`npm run dev`) with live reload. Use `make api` or `make web` when iterating on a single service. For Docker parity, `docker compose up --build` mirrors prod networking. The CLI is available with `python -m src.cli search --markets indianapolis_in`.

## Coding Style & Naming Conventions
Python modules follow Black defaults (4-space indent, double quotes ok) and Ruff linting; run `make format` or `make lint` before committing. Prefer snake_case for functions/vars, PascalCase for classes/agents (e.g., `DealAnalyzer`). Frontend is TypeScript + Next 14 with ESLint (`npm run lint`); React components stay PascalCase under `web/src/components`, hooks/utilities use camelCase filenames (`useDeals.ts`). Keep configs in YAML using kebab-case keys to match existing files.

## Testing Guidelines
Pytests live in `tests/` and mirror module layout (`test_agents.py`, `test_data_sources.py`). Run `make test` (pytest -v) locally; use `make test-cov` to ensure critical flows hit `src/agents`, `src/analysis`, and `api/routes`. When adding adapters, provide fixture-driven tests that mock network responses. Frontend changes must at least run `npm run lint`; snapshot or Playwright tests are optional but document manual steps for UI-heavy changes.

## Commit & Pull Request Guidelines
Git history favors short, imperative subject lines (“Fix Electron title bar…”). Reference the component touched and avoid trailing punctuation; squash noisy work-in-progress commits. PRs should include: 1) summary of behavior change, 2) linked issue or context, 3) verification notes (pytest, lint, `docker compose up`, screenshots for UI diffs). Mention config or data migrations explicitly so reviewers can replicate.
