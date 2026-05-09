import type { AffordabilityOutputs } from "../lib/api";
import { money, percent, signedMoney } from "../lib/formatters";

type RiskOverviewProps = {
  outputs: AffordabilityOutputs;
};

function stressCounts(outputs: AffordabilityOutputs) {
  const zero = outputs.stress_tests.filter((item) => item.falls_below_zero).length;
  const reserve = outputs.stress_tests.filter((item) => item.falls_below_reserve).length;
  return { reserve, total: outputs.stress_tests.length, zero };
}

function highInflationPath(outputs: AffordabilityOutputs) {
  return (
    outputs.stress_tests.find((item) => item.scenario === "High inflation" && item.path === "recast") ??
    outputs.stress_tests.find((item) => item.scenario === "High inflation")
  );
}

export function RiskOverview({ outputs }: RiskOverviewProps) {
  const counts = stressCounts(outputs);
  const highInflation = highInflationPath(outputs);
  const stressTone = counts.zero > 0 ? "bad" : counts.reserve > 0 ? "warn" : "good";

  return (
    <section className="panel risk-panel">
      <div className="section-heading">
        <div>
          <h2>Risk Snapshot</h2>
          <p>These are the main ways the plan can become fragile: cash flow, reserve depth, and inflation stress.</p>
        </div>
      </div>
      <div className="risk-grid">
        <article>
          <span>Monthly pressure</span>
          <strong>{signedMoney(outputs.recast.worst_monthly_cash_flow_recast)}</strong>
          <p>Worst modeled monthly cash-flow result after the current recast setting.</p>
        </article>
        <article className={`risk-${stressTone}`}>
          <span>Stress survival</span>
          <strong>
            {counts.reserve}/{counts.total}
          </strong>
          <p>Stress paths that breach the reserve floor; {counts.zero} deplete taxable liquidity.</p>
        </article>
        <article>
          <span>Inflation sensitivity</span>
          <strong>{highInflation ? money(highInflation.minimum_liquid_assets) : "--"}</strong>
          <p>Minimum liquid assets under the high-inflation stress path.</p>
        </article>
        <article>
          <span>Score guardrail</span>
          <strong>{percent.format(outputs.affordability_score.score / 100)}</strong>
          <p>Composite score from cash flow, liquidity, runway, and stress survival.</p>
        </article>
      </div>
    </section>
  );
}
