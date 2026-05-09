"""FastAPI entrypoint.

FastAPI is declared in `backend/requirements.txt`. The calculation engine itself
does not depend on FastAPI so tests can run in dependency-light environments.
"""

from __future__ import annotations

import os

try:  # pragma: no cover - exercised when FastAPI is installed.
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
except ModuleNotFoundError:  # pragma: no cover
    FastAPI = None  # type: ignore[assignment]
    CORSMiddleware = None  # type: ignore[assignment]

from .engine import calculate_affordability
from .schemas import AffordabilityOutputs, Scenario
from .simulation import simulate_scenario


DEFAULT_CORS_ORIGINS = (
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
)


def _cors_origins() -> tuple[str, ...]:
    raw_origins = os.environ.get("CORS_ORIGINS")
    if not raw_origins:
        return DEFAULT_CORS_ORIGINS
    return tuple(origin.strip() for origin in raw_origins.split(",") if origin.strip())


def create_app():
    if FastAPI is None:
        raise RuntimeError(
            "FastAPI is not installed. Install backend requirements before serving the API."
        )

    app = FastAPI(
        title="Home Affordability API",
        version="0.1.0",
        description="Deterministic affordability, recast, stress, and Monte Carlo engine.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(_cors_origins()),
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
    )

    @app.get("/v1/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/v1/defaults", response_model=Scenario)
    def defaults() -> Scenario:
        return Scenario()

    @app.post("/v1/calculate", response_model=AffordabilityOutputs)
    def calculate(scenario: Scenario) -> AffordabilityOutputs:
        return calculate_affordability(scenario)

    @app.post("/v1/simulate")
    def simulate(scenario: Scenario):
        return simulate_scenario(scenario)

    @app.post("/v1/stress-tests")
    def stress_tests(scenario: Scenario):
        return {"stress_tests": calculate_affordability(scenario).stress_tests}

    @app.post("/v1/safe-purchase-price")
    def safe_purchase_price(scenario: Scenario):
        return {"safe_purchase_price": calculate_affordability(scenario).safe_purchase_price}

    @app.post("/v1/reports/summary")
    def report_summary(scenario: Scenario):
        outputs = calculate_affordability(scenario)
        return {
            "purchase": outputs.purchase,
            "recast": outputs.recast,
            "affordability_score": outputs.affordability_score,
            "safe_purchase_price": outputs.safe_purchase_price,
            "validation_checks": outputs.validation_checks,
            "year_30": outputs.projection[-1],
        }

    return app


app = create_app() if FastAPI is not None else None
