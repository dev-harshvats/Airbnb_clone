# Airbnb Clone

A full-stack clone of Airbnb: browse and search stays across India, book date ranges, manage trips and wishlists, and host your own listings.

> **Status:** in development. Sections marked _(coming)_ are filled in as features land.

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 16 (App Router), React 19, TypeScript (strict), Tailwind CSS v4 |
| Backend | Python 3.11+, FastAPI, SQLAlchemy 2, Alembic, Pydantic v2 |
| Auth | JWT access tokens + rotating refresh tokens (HttpOnly cookie), bcrypt |
| Database | SQLite (WAL mode, foreign keys enforced) |
| Quality | pytest, ruff, import-linter (architecture contracts), ESLint, GitHub Actions |

## Quick start

Requires **Python 3.11+**, **Node.js 20+** and, on Windows, **Git for Windows**. From the repo root:

```bash
./start.sh        # macOS / Linux / Git Bash
```

```powershell
.\start.cmd       # Windows PowerShell or cmd
```

On the first run it creates the virtualenv, installs the backend and frontend dependencies, creates `.env` files from the examples, applies migrations and seeds demo data. Then it starts both servers:

- App: http://localhost:3000
- API docs: http://localhost:8000/api/docs

On first start it also seeds demo data: 58 listings across 20 Indian destinations, bookings, reviews and
wishlists. Log in with `guest@example.com` or `host@example.com` (password `Password123`).

Press `Ctrl+C` to stop both servers. Use `--skip-install` to skip the dependency check. Override the ports with `BACKEND_PORT` / `FRONTEND_PORT`.

## Local setup (manual)

### Backend (http://localhost:8000)

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate        # Windows; use `source .venv/bin/activate` on macOS/Linux
pip install -e ".[dev]"
cp .env.example .env
uvicorn app.main:create_app --factory --reload --no-access-log --no-proxy-headers
```

API docs: http://localhost:8000/api/docs · Health: http://localhost:8000/api/v1/health

### Frontend (http://localhost:3000)

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

The frontend proxies `/api/*` and `/media/*` to the backend (`API_ORIGIN`), so the browser only talks to one origin.

### Checks

```bash
# backend
ruff check . && ruff format --check . && lint-imports && pytest
# frontend
npm run lint && npm run typecheck && npm run build
```

## Project structure

```
backend/   FastAPI app: api (HTTP) → services (use cases) → domain (pure rules) + ports ← adapters
frontend/  Next.js app: app routes, components, lib/api, hooks, store
```

## Architecture, database schema, API overview, demo accounts _(coming)_
