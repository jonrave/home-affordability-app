# Local Runbook

## Backend

Create a local virtual environment and install the backend dependencies:

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install -r backend/requirements.txt
```

Run the deterministic engine and backend tests:

```sh
PYTHONPATH=backend python backend/run_calculation.py
python -m unittest discover -s tests -v
```

Start the FastAPI API:

```sh
uvicorn affordability.api:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```

The API enables local-development CORS for `localhost` and `127.0.0.1` on ports `3000` and `3001`. Override the allow-list with a comma-separated `CORS_ORIGINS` value if needed.

## Frontend

The frontend is a Next.js app in `frontend/`. By default it calls the backend through the Next.js proxy at `/api/backend`, which forwards to `BACKEND_API_URL`.

```sh
cd frontend
cp .env.local.example .env.local
npm install
npm run dev
```

Default local environment:

```sh
NEXT_PUBLIC_API_BASE=/api/backend
BACKEND_API_URL=http://127.0.0.1:8000
```

If you prefer direct browser calls to FastAPI, set `NEXT_PUBLIC_API_BASE=http://127.0.0.1:8000`. FastAPI CORS must allow the frontend origin.

## Smoke Tests

With FastAPI running, verify the backend contract used by the frontend:

```sh
cd frontend
npm run smoke:api
```

To verify the Next.js proxy after both servers are running:

```sh
cd frontend
SMOKE_API_BASE=http://localhost:3000/api/backend npm run smoke:api
```

Manual frontend check: open `http://localhost:3000`, confirm the dashboard loads defaults without an error banner, then click `Calculate` and confirm metrics refresh.

## Current Verification

The checked-in tests use Python `unittest` rather than `pytest` so they can run before optional developer dependencies are installed.
