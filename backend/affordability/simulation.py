"""Seeded Monte Carlo simulation for liquidity risk."""

from __future__ import annotations

import numpy as np

from .engine import (
    build_recast_forecast,
    calculate_purchase_outputs,
    calculate_recast_outputs,
    build_projection,
)
from .schemas import MonteCarloSummary, Scenario


def _annual_returns(
    rng: np.random.Generator,
    *,
    paths: int,
    horizon_years: int,
    expected_return: float,
    volatility: float,
    force_year_one_return: float | None = None,
) -> np.ndarray:
    """Generate lognormal annual returns with optional first-year override."""

    if volatility == 0:
        returns = np.full((paths, horizon_years + 1), expected_return, dtype=float)
    else:
        drift = np.log1p(expected_return) - 0.5 * volatility**2
        shocks = rng.normal(0.0, 1.0, size=(paths, horizon_years + 1))
        returns = np.exp(drift + volatility * shocks) - 1.0
    returns[:, 0] = 0.0
    if force_year_one_return is not None and horizon_years >= 1:
        returns[:, 1] = force_year_one_return
    return returns


def _simulate_paths(
    scenario: Scenario,
    *,
    use_recast: bool,
    force_year_one_return: float | None = None,
) -> np.ndarray:
    purchase = calculate_purchase_outputs(scenario)
    projection = build_projection(scenario, purchase)
    recast = calculate_recast_outputs(scenario, purchase, projection)
    recast_forecast = build_recast_forecast(scenario, projection, recast)
    horizon = scenario.household.horizon_years
    paths = scenario.monte_carlo.paths
    rng = np.random.default_rng(scenario.monte_carlo.seed + (101 if use_recast else 0))
    returns = _annual_returns(
        rng,
        paths=paths,
        horizon_years=horizon,
        expected_return=scenario.savings.portfolio_expected_return,
        volatility=scenario.savings.annual_market_volatility,
        force_year_one_return=force_year_one_return,
    )
    cash_flows = np.array(
        recast_forecast.recast_cash_flow if use_recast else recast_forecast.no_recast_cash_flow,
        dtype=float,
    )
    outflows = np.array(recast_forecast.recast_outflow if use_recast else [0.0] * len(cash_flows))
    balances = np.zeros((paths, horizon + 1), dtype=float)
    shortfalls = np.zeros((paths, horizon + 1), dtype=float)
    balances[:, 0] = purchase.starting_liquid_investments

    for year in range(1, horizon + 1):
        raw = (balances[:, year - 1] - outflows[year]) * (1.0 + returns[:, year])
        raw += cash_flows[year]
        shortfalls[:, year] = np.maximum(0.0, -raw)
        balances[:, year] = np.maximum(0.0, raw) if scenario.monte_carlo.clip_at_zero else raw

    return np.stack([balances, shortfalls], axis=0)


def summarize_paths(
    scenario: Scenario,
    paths_and_shortfalls: np.ndarray,
) -> MonteCarloSummary:
    balances = paths_and_shortfalls[0]
    shortfalls = paths_and_shortfalls[1]
    horizon = scenario.household.horizon_years
    inflation = np.array(
        [(1.0 + scenario.savings.expected_inflation) ** year for year in range(horizon + 1)],
        dtype=float,
    )
    real_balances = balances / inflation
    ending_real = real_balances[:, -1]
    min_real = real_balances.min(axis=1)
    percentiles = {
        f"p{int(p * 100)}": float(np.percentile(ending_real, p * 100.0))
        for p in scenario.monte_carlo.percentiles
    }
    depleted = shortfalls.max(axis=1) > 0
    depleted_shortfalls = shortfalls[depleted]
    average_shortfall = float(depleted_shortfalls.mean()) if depleted_shortfalls.size else 0.0

    return MonteCarloSummary(
        percentiles_real=percentiles,
        probability_ever_at_or_below_zero=float(np.mean(min_real <= 0.0)),
        probability_ever_below_250k=float(np.mean(min_real <= scenario.stress_tests.reserve_threshold_250k)),
        probability_ever_below_500k=float(np.mean(min_real <= scenario.stress_tests.reserve_threshold_500k)),
        probability_ever_below_750k=float(np.mean(min_real <= scenario.stress_tests.reserve_threshold_750k)),
        average_shortfall_when_depleted=average_shortfall,
        max_shortfall=float(shortfalls.max()),
        seed=scenario.monte_carlo.seed,
        paths=scenario.monte_carlo.paths,
    )


def simulate_scenario(scenario: Scenario | None = None) -> dict[str, MonteCarloSummary]:
    scenario = scenario or Scenario()
    no_recast = _simulate_paths(scenario, use_recast=False)
    recast = _simulate_paths(scenario, use_recast=True)
    bear_no_recast = _simulate_paths(
        scenario,
        use_recast=False,
        force_year_one_return=scenario.stress_tests.immediate_bear_market_drop_2027,
    )
    bear_recast = _simulate_paths(
        scenario,
        use_recast=True,
        force_year_one_return=scenario.stress_tests.immediate_bear_market_drop_2027,
    )
    return {
        "no_recast": summarize_paths(scenario, no_recast),
        "recast": summarize_paths(scenario, recast),
        "bear_no_recast": summarize_paths(scenario, bear_no_recast),
        "bear_recast": summarize_paths(scenario, bear_recast),
    }
