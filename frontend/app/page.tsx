"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { AppHeader } from "../components/AppHeader";
import { DecisionBrief } from "../components/DecisionBrief";
import { HowItWorks } from "../components/HowItWorks";
import { MetricCard } from "../components/MetricCard";
import { ProductIntro } from "../components/ProductIntro";
import { ProjectionChart } from "../components/ProjectionChart";
import { RiskOverview } from "../components/RiskOverview";
import { ScenarioInputPanel } from "../components/ScenarioInputPanel";
import { ScenarioTuner } from "../components/ScenarioTuner";
import { AffordabilityOutputs, Scenario, calculateScenario, fetchDefaults } from "../lib/api";
import { decimal, money, percent, signedMoney } from "../lib/formatters";
import {
  clearStoredScenario,
  hasStoredScenario,
  loadStoredScenario,
  saveStoredScenario
} from "../lib/scenarioStorage";
import {
  safePurchaseConfidenceNote,
  safePurchasePriceExplanation,
  scoreExplanation,
  trustItems
} from "../lib/viewModel";

function applyAppDefaults(defaults: Scenario): Scenario {
  const next = structuredClone(defaults);
  next.taxes.tax_mode = "estimated";
  return next;
}

function migrateLegacyTaxMode(scenario: Scenario): Scenario {
  const next = structuredClone(scenario);
  if (next.taxes.tax_mode === "take_home_rate" && next.income.cash_take_home_rate === 0.62) {
    next.taxes.tax_mode = "estimated";
  }
  return next;
}

function taxJurisdictionLabel(outputs: AffordabilityOutputs): string {
  const summary = outputs.tax_summary;
  if (summary.tax_residence_state === "NY" && summary.tax_residence_city === "NYC") {
    return "NY + NYC";
  }
  if (summary.tax_residence_state === "NY") {
    return "New York";
  }
  return "Federal/FICA only";
}

export default function Page() {
  const [defaultScenario, setDefaultScenario] = useState<Scenario | null>(null);
  const [scenario, setScenario] = useState<Scenario | null>(null);
  const [calculatedScenario, setCalculatedScenario] = useState<Scenario | null>(null);
  const [outputs, setOutputs] = useState<AffordabilityOutputs | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [autoUpdating, setAutoUpdating] = useState(false);
  const [pendingAutoScenario, setPendingAutoScenario] = useState<Scenario | null>(null);
  const calculationId = useRef(0);

  useEffect(() => {
    let active = true;
    fetchDefaults()
      .then(async (defaults) => {
        if (!active) return;
        const appDefaults = applyAppDefaults(defaults);
        const initialScenario = hasStoredScenario()
          ? migrateLegacyTaxMode(loadStoredScenario(appDefaults))
          : appDefaults;
        setDefaultScenario(appDefaults);
        setScenario(initialScenario);
        setCalculatedScenario(initialScenario);
        setOutputs(await calculateScenario(initialScenario));
      })
      .catch((err: Error) => {
        if (active) setError(err.message);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  const year30 = useMemo(() => outputs?.projection.at(-1), [outputs]);
  const score = useMemo(() => (outputs ? scoreExplanation(outputs) : null), [outputs]);
  const draftChanged = useMemo(
    () =>
      Boolean(
        scenario &&
          calculatedScenario &&
          JSON.stringify(scenario) !== JSON.stringify(calculatedScenario)
      ),
    [calculatedScenario, scenario]
  );
  const recastPathLabel = useMemo(() => {
    if (!outputs) return "Recast path";
    if (!outputs.recast.active) return "No recast path";
    return `${money(outputs.recast.principal_paydown_applied)} recast`;
  }, [outputs]);

  useEffect(() => {
    if (!pendingAutoScenario) return;
    const timer = window.setTimeout(() => {
      void submit(pendingAutoScenario);
    }, 500);
    return () => window.clearTimeout(timer);
  }, [pendingAutoScenario]);

  async function submit(nextScenario = scenario) {
    if (!nextScenario) return;
    const requestId = calculationId.current + 1;
    calculationId.current = requestId;
    setPendingAutoScenario(null);
    setLoading(true);
    setError(null);
    try {
      saveStoredScenario(nextScenario);
      const nextOutputs = await calculateScenario(nextScenario);
      if (requestId !== calculationId.current) return;
      setOutputs(nextOutputs);
      setCalculatedScenario(nextScenario);
      setPendingAutoScenario(null);
    } catch (err) {
      if (requestId === calculationId.current) {
        setError(err instanceof Error ? err.message : "Calculation failed");
      }
    } finally {
      if (requestId === calculationId.current) {
        setLoading(false);
        setAutoUpdating(false);
      }
    }
  }

  async function resetDefaults() {
    if (!defaultScenario) return;
    const resetScenario = structuredClone(defaultScenario);
    clearStoredScenario();
    setAutoUpdating(false);
    setPendingAutoScenario(null);
    setScenario(resetScenario);
    await submit(resetScenario);
    clearStoredScenario();
  }

  function updateScenario(nextScenario: Scenario, options: { autoCalculate?: boolean } = {}) {
    setScenario(nextScenario);
    saveStoredScenario(nextScenario);
    if (options.autoCalculate) {
      setAutoUpdating(true);
      setPendingAutoScenario(nextScenario);
    } else {
      setAutoUpdating(false);
      setPendingAutoScenario(null);
    }
  }

  return (
    <main>
      <AppHeader
        active="overview"
        eyebrow="Household Finance"
        title="Home Affordability Planner"
      />

      {error ? <div className="status status-error">{error}</div> : null}

      <section className="shell">
        <ProductIntro />

        {outputs ? (
          <DecisionBrief
            autoUpdating={autoUpdating}
            draftChanged={draftChanged}
            loading={loading}
            onCalculate={() => submit()}
            outputs={outputs}
          />
        ) : (
          <section className="decision-panel">
            <div className="skeleton skeleton-large" />
          </section>
        )}

        <ScenarioTuner
          autoUpdating={autoUpdating}
          loading={loading}
          onScenarioChange={(nextScenario) => updateScenario(nextScenario, { autoCalculate: true })}
          outputs={outputs}
          scenario={scenario}
        />

        <HowItWorks />

        <section className="workspace">
          <section className="output-panel" aria-label="Affordability outputs">
            {outputs ? (
              <>
                <RiskOverview outputs={outputs} />

                <section className="score-layout">
                  <div className="score-band">
                    <span>Affordability score</span>
                    <strong>{decimal(outputs.affordability_score.score)}</strong>
                    <em>{outputs.affordability_score.label}</em>
                  </div>
                  <div className="score-explanation panel">
                    <div className="section-heading">
                      <div>
                        <h2>Why The Score Looks This Way</h2>
                        <p>{score?.explanation}</p>
                      </div>
                    </div>
                    <div className="score-components">
                      {score?.components.map((component) => (
                        <div className="score-component" key={component.label}>
                          <span>{component.label}</span>
                          <strong>{decimal(component.value)}</strong>
                          <div className="meter">
                            <i style={{ width: `${Math.max(0, Math.min(100, component.value))}%` }} />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </section>

                <section className="section-heading output-heading">
                  <div>
                    <h2>Decision Metrics</h2>
                    <p>Use these as the first-pass read on payment burden, liquidity cushion, and long-term flexibility.</p>
                  </div>
                </section>

                <div className="metrics-grid">
                  <MetricCard label="Monthly P&I" value={money(outputs.purchase.monthly_mortgage_pi)} hint="Principal and interest only." />
                  <MetricCard label="Monthly outflow" value={money(outputs.purchase.monthly_required_outflow)} hint="Housing plus baseline living costs." />
                  <MetricCard
                    label="Effective take-home"
                    value={percent.format(outputs.tax_summary.effective_take_home_rate)}
                    hint={
                      outputs.tax_summary.tax_mode === "estimated"
                        ? `Estimated from ${outputs.tax_summary.filing_status.replaceAll("_", " ")} and ${
                            outputs.tax_summary.jurisdiction_source === "zip"
                              ? `ZIP ${outputs.tax_summary.residence_zip}`
                              : "available residence data"
                          }.`
                        : "Manual take-home rate from assumptions."
                    }
                  />
                  <MetricCard label="Reserve target" value={money(outputs.purchase.liquidity_reserve_target)} hint="Emergency reserve plus one-time cushion." />
                  <MetricCard
                    label="Max workable price"
                    value={money(outputs.safe_purchase_price)}
                    tone="good"
                    hint={safePurchasePriceExplanation(outputs)}
                  />
                  <MetricCard label="Year-30 liquid real" value={year30 ? money(year30.liquid_real) : "--"} hint="Liquid assets after inflation." />
                  <MetricCard label="Year-30 total real" value={year30 ? money(year30.total_real) : "--"} hint="Liquid plus retirement/non-liquid assets." />
                  <MetricCard label="Year-30 runway" value={year30 ? `${decimal(year30.runway_months)} mo` : "--"} hint="Months covered by liquid assets." />
                  <MetricCard
                    label="Recast breakeven"
                    value={outputs.recast.active ? `${decimal(outputs.recast.breakeven_years)} yr` : "No recast"}
                    hint="Years of lower payments to recover cash used."
                  />
                </div>

                <section className="panel confidence-panel">
                  <div>
                    <h2>Why You Can Use The Max Workable Price</h2>
                    <p>{safePurchaseConfidenceNote()}</p>
                  </div>
                  <div>
                    <h2>Why It Still Needs Judgment</h2>
                    <p>
                      The threshold is model-based and depends on current assumptions. It does not replace a full tax
                      review, lender underwriting, or household-specific risk judgment.
                    </p>
                  </div>
                </section>

                <section className="panel tax-panel">
                  <div className="section-heading">
                    <div>
                      <h2>Take-Home Estimate</h2>
                      <p>
                        {outputs.tax_summary.tax_mode === "estimated"
                          ? "Estimated mode calculates federal income tax, employee payroll tax, and directional supported state/city tax from filing status and residence ZIP."
                          : "Manual mode uses the take-home percentage entered in assumptions."}
                      </p>
                    </div>
                  </div>
                  <div className="tax-grid">
                    <article>
                      <span>Jurisdiction</span>
                      <strong>{taxJurisdictionLabel(outputs)}</strong>
                    </article>
                    <article>
                      <span>ZIP source</span>
                      <strong>
                        {outputs.tax_summary.jurisdiction_source === "zip"
                          ? outputs.tax_summary.residence_zip
                          : outputs.tax_summary.jurisdiction_source === "manual"
                            ? "Manual fallback"
                            : "Not set"}
                      </strong>
                    </article>
                    <article>
                      <span>Effective take-home</span>
                      <strong>{percent.format(outputs.tax_summary.effective_take_home_rate)}</strong>
                    </article>
                    <article>
                      <span>All-in tax rate</span>
                      <strong>{percent.format(outputs.tax_summary.total_effective_tax_rate)}</strong>
                    </article>
                    <article>
                      <span>Federal taxable income</span>
                      <strong>{money(outputs.tax_summary.taxable_income_for_estimate)}</strong>
                    </article>
                    <article>
                      <span>Estimated total tax</span>
                      <strong>{money(outputs.tax_summary.estimated_total_tax)}</strong>
                    </article>
                    <article>
                      <span>Federal income tax</span>
                      <strong>{money(outputs.tax_summary.federal_income_tax)}</strong>
                    </article>
                    <article>
                      <span>Payroll tax</span>
                      <strong>{money(outputs.tax_summary.payroll_tax)}</strong>
                    </article>
                    <article>
                      <span>State tax</span>
                      <strong>{money(outputs.tax_summary.state_income_tax)}</strong>
                    </article>
                    <article>
                      <span>City tax</span>
                      <strong>{money(outputs.tax_summary.city_income_tax)}</strong>
                    </article>
                  </div>
                  <div className="tax-rate-audit">
                    <div>
                      <h3>Rate audit</h3>
                      <p>
                        Effective rate is each tax divided by gross income. Marginal rate is the modeled rate applied to
                        the next taxable dollar in that category.
                      </p>
                    </div>
                    <div className="tax-rate-table">
                      <div className="tax-rate-row tax-rate-head">
                        <span>Tax</span>
                        <span>Taxable base</span>
                        <span>Tax</span>
                        <span>Effective</span>
                        <span>Marginal</span>
                      </div>
                      {outputs.tax_summary.tax_rate_details.map((detail) => (
                        <div className="tax-rate-row" key={detail.label}>
                          <span>
                            <strong>{detail.label}</strong>
                            <small>{detail.note}</small>
                          </span>
                          <span>{money(detail.taxable_income)}</span>
                          <span>{money(detail.tax_amount)}</span>
                          <span>{percent.format(detail.effective_rate)}</span>
                          <span>{percent.format(detail.marginal_rate)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                  <div className="tax-notes">
                    {outputs.tax_summary.notes.map((note) => (
                      <p key={note}>{note}</p>
                    ))}
                  </div>
                </section>

                <ProjectionChart
                  description="The key question is whether liquid assets stay comfortably above the reserve target while real purchasing power remains healthy."
                  rows={outputs.projection}
                />

                <section className="panel scenario-panel">
                  <div className="section-heading">
                    <div>
                      <h2>Recast Scenario Comparison</h2>
                      <p>
                        {outputs.recast.active
                          ? "A recast lowers monthly payment pressure but trades away liquid cash up front."
                          : "No recast is selected, so the recast path ties to the no-recast path."}
                      </p>
                    </div>
                  </div>

                  <div className="scenario-cards">
                    <article>
                      <span>No recast</span>
                      <strong>{money(outputs.recast_comparison.no_recast_monthly_pi)}</strong>
                      <p>Monthly P&I with liquidity preserved.</p>
                      <dl>
                        <div>
                          <dt>Worst monthly cash flow</dt>
                          <dd>{signedMoney(outputs.recast_comparison.no_recast_worst_monthly_cash_flow)}</dd>
                        </div>
                        <div>
                          <dt>Year-30 liquid real</dt>
                          <dd>{money(outputs.recast_comparison.no_recast_year_30_liquid_real)}</dd>
                        </div>
                      </dl>
                    </article>
                    <article>
                      <span>{recastPathLabel}</span>
                      <strong>{money(outputs.recast_comparison.recast_monthly_pi)}</strong>
                      <p>Monthly P&I after applying the modeled recast choice.</p>
                      <dl>
                        <div>
                          <dt>Worst monthly cash flow</dt>
                          <dd>{signedMoney(outputs.recast_comparison.recast_worst_monthly_cash_flow)}</dd>
                        </div>
                        <div>
                          <dt>Year-30 liquid real</dt>
                          <dd>{money(outputs.recast_comparison.recast_year_30_liquid_real)}</dd>
                        </div>
                      </dl>
                    </article>
                  </div>

                  <div className="table comparison-table">
                    <div className="table-row table-head">
                      <span>Metric</span>
                      <span>No recast</span>
                      <span>{recastPathLabel}</span>
                    </div>
                    <div className="table-row">
                      <span>Monthly P&I</span>
                      <span>{money(outputs.recast_comparison.no_recast_monthly_pi)}</span>
                      <span>{money(outputs.recast_comparison.recast_monthly_pi)}</span>
                    </div>
                    <div className="table-row">
                      <span>Worst monthly cash flow</span>
                      <span>{signedMoney(outputs.recast_comparison.no_recast_worst_monthly_cash_flow)}</span>
                      <span>{signedMoney(outputs.recast_comparison.recast_worst_monthly_cash_flow)}</span>
                    </div>
                    <div className="table-row">
                      <span>Starting liquid assets</span>
                      <span>{money(outputs.recast_comparison.no_recast_starting_liquid_assets)}</span>
                      <span>{money(outputs.recast_comparison.recast_starting_liquid_assets)}</span>
                    </div>
                    <div className="table-row">
                      <span>Year-30 liquid real</span>
                      <span>{money(outputs.recast_comparison.no_recast_year_30_liquid_real)}</span>
                      <span>{money(outputs.recast_comparison.recast_year_30_liquid_real)}</span>
                    </div>
                  </div>
                </section>

                <section className="panel stress-table">
                  <div className="section-heading">
                    <div>
                      <h2>Stress Tests</h2>
                      <p>Shows whether deterministic downside cases breach zero liquidity or the modeled reserve floor.</p>
                    </div>
                  </div>
                  <div className="table">
                    <div className="table-row table-head">
                      <span>Scenario</span>
                      <span>Path</span>
                      <span>Minimum liquid</span>
                      <span>Reserve breach</span>
                    </div>
                    {outputs.stress_tests.map((item) => (
                      <div className="table-row" key={`${item.scenario}-${item.path}`}>
                        <span>{item.scenario}</span>
                        <span>{item.path.replace("_", " ")}</span>
                        <span>{money(item.minimum_liquid_assets)}</span>
                        <span>{item.falls_below_reserve ? "Yes" : "No"}</span>
                      </div>
                    ))}
                  </div>
                </section>

                <section className="panel validation-list">
                  <div className="section-heading">
                    <div>
                      <h2>Checks</h2>
                      <p>Validation messages flag assumptions or outputs that deserve review before interpreting the scenario.</p>
                    </div>
                  </div>
                  {outputs.validation_checks.map((check) => (
                    <div className={`check check-${check.severity}`} key={check.code}>
                      <span>{check.severity}</span>
                      <p>{check.message}</p>
                    </div>
                  ))}
                </section>

                <section className="panel trust-panel">
                  <div className="section-heading">
                    <div>
                      <h2>Trust & Audit</h2>
                      <p>Read this before relying on the result; it separates reconciled logic from known simplifications.</p>
                    </div>
                  </div>
                  <div className="trust-grid">
                    {trustItems(outputs).map((item) => (
                      <article key={item.label}>
                        <span>{item.label}</span>
                        <strong>{item.value}</strong>
                        <p>{item.detail}</p>
                      </article>
                    ))}
                  </div>
                </section>
              </>
            ) : (
              Array.from({ length: 8 }).map((_, index) => <div className="skeleton" key={index} />)
            )}
          </section>

          <ScenarioInputPanel
            canReset={Boolean(defaultScenario)}
            draftChanged={draftChanged}
            loading={loading}
            onCalculate={() => submit()}
            onReset={resetDefaults}
            onScenarioChange={updateScenario}
            scenario={scenario}
          />
        </section>
      </section>
    </main>
  );
}
