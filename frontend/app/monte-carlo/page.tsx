"use client";

import { useEffect, useMemo, useState } from "react";
import { AppHeader } from "../../components/AppHeader";
import { MetricCard } from "../../components/MetricCard";
import {
  MonteCarloScenarioKey,
  Scenario,
  SimulationOutputs,
  fetchDefaults,
  simulateScenario
} from "../../lib/api";
import { decimal, money, percent } from "../../lib/formatters";
import { loadStoredScenario } from "../../lib/scenarioStorage";

type LoadState = {
  scenario: Scenario | null;
  simulation: SimulationOutputs | null;
  error: string | null;
  loading: boolean;
};

const scenarioColumns: Array<{ key: MonteCarloScenarioKey; label: string }> = [
  { key: "no_recast", label: "No recast" },
  { key: "recast", label: "$200k recast" }
];

const percentileRows = [
  { key: "p5", label: "P5" },
  { key: "p10", label: "P10" },
  { key: "p15", label: "P15" },
  { key: "p25", label: "P25" },
  { key: "p50", label: "P50" },
  { key: "p75", label: "P75" },
  { key: "p85", label: "P85" },
  { key: "p90", label: "P90" },
  { key: "p95", label: "P95" }
];

const breachRows = [
  { key: "probability_ever_at_or_below_zero", label: "At or below $0" },
  { key: "probability_ever_below_250k", label: "Below $250k" },
  { key: "probability_ever_below_500k", label: "Below $500k" },
  { key: "probability_ever_below_750k", label: "Below $750k" }
] as const;

export default function MonteCarloPage() {
  const [{ scenario, simulation, error, loading }, setState] = useState<LoadState>({
    scenario: null,
    simulation: null,
    error: null,
    loading: true
  });

  useEffect(() => {
    let active = true;
    fetchDefaults()
      .then(async (defaults) => {
        const activeScenario = loadStoredScenario(defaults);
        return {
          scenario: activeScenario,
          simulation: await simulateScenario(activeScenario)
        };
      })
      .then(({ scenario: nextScenario, simulation: nextSimulation }) => {
        if (active) setState({ scenario: nextScenario, simulation: nextSimulation, error: null, loading: false });
      })
      .catch((err: Error) => {
        if (active) setState({ scenario: null, simulation: null, error: err.message, loading: false });
      });
    return () => {
      active = false;
    };
  }, []);

  const highestReserveRisk = useMemo(() => {
    if (!simulation) return null;
    return scenarioColumns.reduce((highest, item) => {
      const risk = simulation[item.key].probability_ever_below_500k;
      return risk > highest.risk ? { label: item.label, risk } : highest;
    }, { label: scenarioColumns[0].label, risk: simulation[scenarioColumns[0].key].probability_ever_below_500k });
  }, [simulation]);

  return (
    <main>
      <AppHeader active="monte-carlo" title="Monte Carlo Detail" />

      {error ? <div className="status status-error">{error}</div> : null}

      <section className="shell detail-shell">
        {loading || !simulation || !scenario ? (
          <>
            <div className="skeleton skeleton-large" />
            <div className="skeleton skeleton-large" />
            <div className="skeleton skeleton-large" />
          </>
        ) : (
          <>
            <section className="panel detail-intro">
              <div>
                <h2>Monte Carlo Detail</h2>
                <p>
                  This page shows distribution risk: where year-30 liquid assets land across seeded paths, and how often
                  liquidity touches key reserve thresholds.
                </p>
              </div>
            </section>

            <section className="metrics-grid">
              <MetricCard label="Paths" value={decimal(simulation.no_recast.paths)} hint="Number of simulated return paths." />
              <MetricCard label="Seed" value={decimal(simulation.no_recast.seed)} hint="Makes simulation results reproducible." />
              <MetricCard label="No recast P50 real" value={money(simulation.no_recast.percentiles_real.p50)} hint="Median ending liquid assets." />
              <MetricCard label="$200k recast P50 real" value={money(simulation.recast.percentiles_real.p50)} hint="Median ending liquidity after recast." />
              <MetricCard label="No recast P5 real" tone="warn" value={money(simulation.no_recast.percentiles_real.p5)} hint="Low-end market path already sampled by MC." />
              <MetricCard label="$200k recast P5 real" tone="warn" value={money(simulation.recast.percentiles_real.p5)} hint="Low-end result after the modeled recast." />
              <MetricCard
                label="Highest $500k breach risk"
                tone="warn"
                value={highestReserveRisk ? `${percent.format(highestReserveRisk.risk)} ${highestReserveRisk.label}` : "--"}
                hint="Worst modeled chance of crossing the reserve line."
              />
              <MetricCard
                label="No recast depletion risk"
                value={percent.format(simulation.no_recast.probability_ever_at_or_below_zero)}
                hint="Chance liquid assets hit zero."
              />
              <MetricCard
                label="Recast depletion risk"
                value={percent.format(simulation.recast.probability_ever_at_or_below_zero)}
                hint="Same risk after modeled recast."
              />
            </section>

            <section className="panel audit-panel">
              <div className="section-heading">
                <div>
                  <h2>Market Downside Handling</h2>
                  <p>
                    The primary Monte Carlo view does not need separate bear-market columns because downside market
                    paths are already sampled through annual volatility. Use P5/P10 outcomes and breach probabilities
                    to audit market risk without duplicating the same signal.
                  </p>
                </div>
              </div>
              <div className="audit-grid">
                <article>
                  <span>Expected return</span>
                  <strong>{percent.format(scenario.savings.portfolio_expected_return)}</strong>
                  <p>Central annual return assumption used by the seeded simulation.</p>
                </article>
                <article>
                  <span>Annual volatility</span>
                  <strong>{percent.format(scenario.savings.annual_market_volatility)}</strong>
                  <p>Creates upside and downside return paths, including bear-like market years.</p>
                </article>
                <article>
                  <span>Real-dollar lens</span>
                  <strong>{percent.format(scenario.savings.expected_inflation)}</strong>
                  <p>Ending balances are converted to real dollars with expected inflation.</p>
                </article>
                <article>
                  <span>Separate stress test</span>
                  <strong>{percent.format(scenario.stress_tests.immediate_bear_market_drop_2027)}</strong>
                  <p>An exact first-year shock is still covered in deterministic stress tests, not duplicated here.</p>
                </article>
              </div>
              <div className="audit-notes">
                <div>
                  <strong>Included</strong>
                  <p>
                    Random liquid-portfolio return paths, annual cash-flow draws or additions, recast outflow when
                    selected, lower post-recast P&I, and cumulative liquidity threshold checks.
                  </p>
                </div>
                <div>
                  <strong>Kept out of this view</strong>
                  <p>
                    Forced one-year bear columns, job-loss assumptions, home-value declines, refinance changes, tax-law
                    changes, forced sale costs, and extra expense inflation.
                  </p>
                </div>
              </div>
            </section>

            <section className="panel detail-table-panel">
              <div className="section-heading">
                <div>
                  <h2>Ending Real Liquid Percentiles</h2>
                  <p>Higher percentiles are better outcomes; lower percentiles show the downside tail to plan around.</p>
                </div>
              </div>
              <div className="table-scroll">
                <div className="table monte-table">
                  <div className="table-row table-head">
                    <span>Percentile</span>
                    {scenarioColumns.map((item) => (
                      <span key={item.key}>{item.label}</span>
                    ))}
                  </div>
                  {percentileRows.map((row) => (
                    <div className="table-row" key={row.key}>
                      <span>{row.label}</span>
                      {scenarioColumns.map((item) => (
                        <span key={item.key}>{money(simulation[item.key].percentiles_real[row.key] ?? 0)}</span>
                      ))}
                    </div>
                  ))}
                </div>
              </div>
            </section>

            <section className="panel detail-table-panel">
              <div className="section-heading">
                <div>
                  <h2>Liquidity Breach Probabilities</h2>
                  <p>These are cumulative warnings: a path counts if it crosses the threshold at any point in 30 years.</p>
                </div>
              </div>
              <div className="table-scroll">
                <div className="table monte-table">
                  <div className="table-row table-head">
                    <span>Threshold</span>
                    {scenarioColumns.map((item) => (
                      <span key={item.key}>{item.label}</span>
                    ))}
                  </div>
                  {breachRows.map((row) => (
                    <div className="table-row" key={row.key}>
                      <span>{row.label}</span>
                      {scenarioColumns.map((item) => (
                        <span key={item.key}>{percent.format(simulation[item.key][row.key])}</span>
                      ))}
                    </div>
                  ))}
                </div>
              </div>
            </section>

            <section className="panel detail-table-panel">
              <div className="section-heading">
                <div>
                  <h2>Shortfall Severity</h2>
                  <p>Shortfall depth helps separate a brief depletion from a severe liquidity gap.</p>
                </div>
              </div>
              <div className="table-scroll">
                <div className="table monte-table">
                  <div className="table-row table-head">
                    <span>Metric</span>
                    {scenarioColumns.map((item) => (
                      <span key={item.key}>{item.label}</span>
                    ))}
                  </div>
                  <div className="table-row">
                    <span>Average shortfall when depleted</span>
                    {scenarioColumns.map((item) => (
                      <span key={item.key}>{money(simulation[item.key].average_shortfall_when_depleted)}</span>
                    ))}
                  </div>
                  <div className="table-row">
                    <span>Maximum shortfall</span>
                    {scenarioColumns.map((item) => (
                      <span key={item.key}>{money(simulation[item.key].max_shortfall)}</span>
                    ))}
                  </div>
                </div>
              </div>
            </section>
          </>
        )}
      </section>
    </main>
  );
}
