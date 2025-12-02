# Repository Guidelines

## Project Structure & Module Organization
- `backend/app` hosts the FastAPI services (routers in `api/`, persistence in `models.py`, middleware/auth helpers in `middleware.py` and `mock_auth.py`).
- `backend/tests` mirrors API modules; add fixtures next to the feature you cover so pytest auto-discovers them via `test_*.py`.
- `frontend/src` contains the Vue 3 PWA: route definitions in `router/`, global stores in `store/`, shared composables in `utils/`, and Material You assets under `assets/`.
- End-to-end and component tests live in `frontend/cypress` and `scripts/test-component.js`; static assets for deployment belong in `frontend/public`.

## Build, Test, and Development Commands
- `docker-compose up -d postgres` starts the local PostgreSQL expected by both tiers.
- `cd backend && python -m uvicorn app.main:app --reload --port 8090` runs the API with live reload.
- `cd frontend && npm run serve` launches the Vue dev server on port 5000; `npm run build` produces the production bundle.
- `cd backend && pytest` executes backend unit/integration tests defined under `backend/tests`.
- `cd frontend && npm run test:unit` (Jest) and `npm run test:e2e` (Cypress) cover UI logic and workflows; open Cypress interactively with `npm run cypress:open` when debugging.

## Coding Style & Naming Conventions
- Python: 4-space indentation, fully type-annotate FastAPI endpoints, and keep business logic in services or utils to preserve thin routers.
- Vue: follow Composition API with `script setup`, components in `PascalCase.vue`, stores named `featureStore.js`, and folders in `kebab-case` per `best-practices.md`.
- Run Prettier (frontend) and `ruff`/`black` equivalents if added; match existing lint configs before committing.

## Testing Guidelines
- Name backend tests `test_<feature>.py`; rely on pytest fixtures for database setup and prefer the mock auth helpers during local runs.
- UI specs belong in `frontend/tests/unit` (Jest) and scenarios in `frontend/cypress/e2e`. Keep coverage high for chore assignment flows, log rollbacks, and offline sync paths.

## Commit & Pull Request Guidelines
- Follow Conventional Commits as seen in history (`feat:`, `fix:`, `chore:`). Scope optional but encouraged (e.g., `feat(auth): add mock login`).
- Each PR should describe behavior changes, reference related issues, and attach screenshots or GIFs for UI work. Include test evidence (`pytest`, `npm run test:unit`, `npm run test:e2e`) in the description.

## Security & Configuration Tips
- Store secrets via environment variables; never commit credentials from `README.md` examples. Use the mock auth flow described in `AUTH_README.md` for local testing.
- Keep `init-db.sql` and Alembic migrations in sync—run migrations before seeding data.
