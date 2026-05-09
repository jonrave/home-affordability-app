"use client";

import { useEffect, useMemo, useState } from "react";
import { AppHeader } from "../../components/AppHeader";
import { MetricCard } from "../../components/MetricCard";
import { ProjectionChart } from "../../components/ProjectionChart";
import { AffordabilityOutputs, calculateScenario, fetchDefaults } from "../../lib/api";
import { decimal, money, signedMoney } from "../../lib/formatters";
import { loadStoredScenario } from "../../lib/scenarioStorage";

type LoadState = {
  outputs: AffordabilityOutputs | null;
  error: string | null;
  loading: boolean;
};

function minimumBy<T>(items: T[], selector: (item: T) => number): T | null {
  if (!items.length) return null;
  return items.reduce((best, item) => (selector(item) < selector(best) ? item : best), items[0]);
}

export default function LiquidityPage() {
  const [{ outputs, error, loading }, setState] = useState<LoadState>({
    outputs: null,
    error: null,
    loading: true
  });

  useEffect(() => {
    let active = true;
    fetchDefaults()
      .then((defaults) => calculateScenario(loadStoredScenario(defaults)))
      .then((nextOutputs) => {
        if (active) setState({ outputs: nextOutputs, error: null, loading: false });
      })
      .catch((err: Error) => {
        if (active) setState({ outputs: null, error: err.message, loading: false });
      });
    return () => {
      active = false;
    };
  }, []);

  const year30 = useMemo(() => outputs?.projection.at(-1), [outputs]);
  const weakestRunwayYear = useMemo(
    () => (outputs ? minimumBy(outputs.projection, (row) => row.runway_months) : null),
    [outputs]
  );
  const largestDrawYear = useMemo(
    () => (outputs ? minimumBy(outputs.projection, (row) => row.annual_liquid_contribution_draw) : null),
    [outputs]
  );

  return (
    <main>
      <AppHeader active="liquidity" title="Liquidity Detail" />

      {error ? <div className="status status-error">{error}</div> : null}

      <section className="shell detail-shell">
        {loading || !outputs ? (
          <>
            <div className="skeleton skeleton-large" />
            <div className="skeleton skeleton-large" />
            <div className="skeleton skeleton-large" />
          </>
        ) : (
          <>
            <section className="panel detail-intro">
              <div>
                <h2>Liquidity_30Y Detail</h2>
                <p>
                  This page answers where cash is added or drawn each year, and whether liquid assets stay ahead of the
                  reserve target in nominal and real dollars.
                </p>
              </div>
            </section>

            <section className="metrics-grid">
              <MetricCard label="Starting liquid" value={money(outputs.purchase.starting_liquid_investments)} hint="Liquid portfolio after modeled cash to close." />
              <MetricCard label="Year-30 liquid real" value={year30 ? money(year30.liquid_real) : "--"} hint="Ending liquid assets after inflation." />
              <MetricCard
                label="Year-30 retirement real"
                value={year30 ? money(year30.retirement_nonliquid_real) : "--"}
                hint="Retirement/non-liquid bucket after inflation."
              />
              <MetricCard
                label="Weakest runway"
                tone="warn"
                value={weakestRunwayYear ? `${decimal(weakestRunwayYear.runway_months)} mo, Y${weakestRunwayYear.year}` : "--"}
                hint="Lowest modeled months of expenses covered."
              />
              <MetricCard
                label="Largest annual draw"
                tone="warn"
                value={largestDrawYear ? `${signedMoney(largestDrawYear.annual_liquid_contribution_draw)}, Y${largestDrawYear.year}` : "--"}
                hint="Most negative annual liquid cash flow."
              />
              <MetricCard label="Reserve target" value={money(outputs.purchase.liquidity_reserve_target)} hint="Current cushion target from expenses." />
              <MetricCard label="Annual ownership cost" value={money(outputs.purchase.annual_ownership_cost)} hint="Mortgage, taxes, insurance, utilities, and upkeep." />
              <MetricCard label="Monthly required outflow" value={money(outputs.purchase.monthly_required_outflow)} hint="Ownership plus non-housing burn." />
            </section>

            <ProjectionChart
              description="Use the chart to spot when liquid assets drift toward the reserve target, and how inflation changes the picture."
              rows={outputs.projection}
            />

            <section className="panel detail-table-panel">
              <div className="section-heading">
                <div>
                  <h2>Annual Liquidity Projection</h2>
                  <p>Negative liquid contribution/draw means the portfolio is funding that year; positive means cash is being added.</p>
                </div>
              </div>
              <div className="table-scroll">
                <div className="table liquidity-table">
                  <div className="table-row table-head">
                    <span>Year</span>
                    <span>Spendable cash</span>
                    <span>Ownership cost</span>
                    <span>Non-housing burn</span>
                    <span>Liquid contribution/draw</span>
                    <span>Liquid nominal</span>
                    <span>Liquid real</span>
                    <span>Retirement/non-liquid</span>
                    <span>Reserve target</span>
                    <span>Runway</span>
                  </div>
                  {outputs.projection.map((row) => (
                    <div className="table-row" key={row.year}>
                      <span>Y{row.year}</span>
                      <span>{money(row.annual_spendable_cash_before_housing)}</span>
                      <span>{money(row.annual_ownership_cost)}</span>
                      <span>{money(row.annual_nonhousing_burn)}</span>
                      <span>{signedMoney(row.annual_liquid_contribution_draw)}</span>
                      <span>{money(row.liquid_investments)}</span>
                      <span>{money(row.liquid_real)}</span>
                      <span>{money(row.retirement_nonliquid_investments)}</span>
                      <span>{money(row.liquidity_reserve_target)}</span>
                      <span>{decimal(row.runway_months)} mo</span>
                    </div>
                  ))}
                </div>
              </div>
            </section>
          </>
        )}
      </section>
    </main>
  );
}
