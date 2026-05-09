# Home Affordability Web App

This repository contains the extracted home affordability calculation engine, a FastAPI API, and a Next.js MVP frontend for local review.

## Project Layout

- `backend/affordability/`: Python schemas, deterministic calculation engine, simulation helpers, and FastAPI routes.
- `frontend/`: Next.js app that calls the backend through a local proxy by default.
- `tests/`: Python `unittest` coverage for the engine, simulation invariants, and API contract.
- `docs/`: Workbook extraction notes, architecture notes, and local runbook.

## Local Development

Backend:

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install -r backend/requirements.txt
python -m unittest discover -s tests -v
uvicorn affordability.api:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```

Frontend:

```sh
cd frontend
cp .env.local.example .env.local
npm install
npm run dev
```

Open `http://localhost:3000`. See `docs/runbook.md` for CORS, proxy, and smoke-test details.

## Public Deployment

The repo includes a Render blueprint for the FastAPI backend and Vercel config for the Next.js frontend:

- `render.yaml`
- `frontend/vercel.json`
- `frontend/.env.production.example`

See `docs/deployment.md` for the exact Render + Vercel deployment steps and production environment variables.
