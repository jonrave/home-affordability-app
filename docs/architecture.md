# Home Affordability App Architecture

## Decision

Use a backend-first architecture:

- **Frontend:** Next.js and React for scenario forms, dashboards, comparison views, and reports.
- **Backend API:** FastAPI with versioned endpoints.
- **Calculation engine:** Pure Python functions and Pydantic schemas.
- **Simulation engine:** NumPy-backed seeded Monte Carlo.
- **Validation layer:** Pydantic field validation plus financial validation checks returned with every result.
- **Persistence:** Deferred until deterministic engine reconciliation is complete.

The UI must not own financial assumptions or formulas. It requests defaults and calculations from the backend, then renders structured outputs.

## Backend Modules

- `affordability.schemas`: typed assumptions, scenarios, outputs, validation checks.
- `affordability.engine`: deterministic mortgage, purchase, cash-flow, projection, recast, stress, score, and safe-purchase-price logic.
- `affordability.simulation`: seeded Monte Carlo and percentile/breach summaries.
- `affordability.api`: FastAPI app and versioned HTTP routes.

## API Surface

- `GET /v1/defaults`: returns default scenario assumptions matching the workbook.
- `POST /v1/calculate`: deterministic affordability, projection, recast, score, and safe purchase price.
- `POST /v1/simulate`: seeded Monte Carlo summary.
- `POST /v1/stress-tests`: deterministic stress summaries.
- `POST /v1/reports/summary`: structured report payload; PDF/Excel export can be added later.

## Build Order

1. Lock down schemas and deterministic formulas.
2. Add reconciliation tests against workbook targets.
3. Add Monte Carlo with deterministic seeds and statistical tests.
4. Expose the engine through FastAPI.
5. Add the MVP UI after the engine and tests are stable.
6. Add import/export and persistence after model trust is established.

## Deferred Features

- Full federal/state/local tax engine.
- Tax drag and capital gains modeling.
- Full refinance decision engine and lender fee comparison.
- Account-level asset location and liquidity rules.
- Authentication and saved scenarios.
- Async simulation workers and persistent report history.
