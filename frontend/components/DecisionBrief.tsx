import type { AffordabilityOutputs } from "../lib/api";
import { decimal, money, signedMoney } from "../lib/formatters";
import {
  mainRisk,
  reserveStatus,
  safePurchaseConfidenceNote,
  safePurchasePriceExplanation,
  summaryInterpretation
} from "../lib/viewModel";

type DecisionBriefProps = {
  autoUpdating: boolean;
  draftChanged: boolean;
  loading: boolean;
  onCalculate: () => void;
  outputs: AffordabilityOutputs;
};

function statusTone(label: string) {
  if (label === "strong" || label === "workable") return "good";
  if (label === "fragile") return "warn";
  return "bad";
}

function weakestRunway(outputs: AffordabilityOutputs) {
  return outputs.projection.reduce((weakest, row) =>
    row.runway_months < weakest.runway_months ? row : weakest
  );
}

export function DecisionBrief({
  autoUpdating,
  draftChanged,
  loading,
  onCalculate,
  outputs
}: DecisionBriefProps) {
  const runway = weakestRunway(outputs);
  const tone = statusTone(outputs.affordability_score.label);

  return (
    <section className={`decision-panel decision-${tone}`}>
      <div className="decision-copy">
        <span>Affordability conclusion</span>
        <strong>{outputs.affordability_score.label}</strong>
        <p>{summaryInterpretation(outputs)}</p>
        {draftChanged ? (
          <div className="draft-callout">
            <div>
              <strong>{autoUpdating ? "Updating results" : "Assumptions changed"}</strong>
              <p>
                {autoUpdating
                  ? "The overview is recalculating after your slider change."
                  : "Outputs still reflect the last calculated scenario. Recalculate to update the decision read."}
              </p>
            </div>
            {autoUpdating ? null : (
              <button onClick={onCalculate} disabled={loading} type="button">
                {loading ? "Calculating" : "Update results"}
              </button>
            )}
          </div>
        ) : null}
      </div>

      <div className="decision-metrics">
        <article className={outputs.recast.worst_monthly_cash_flow_recast >= 0 ? "decision-item item-good" : "decision-item item-warn"}>
          <span>Cash-flow resilience</span>
          <strong>{signedMoney(outputs.recast.worst_monthly_cash_flow_recast)}</strong>
          <p>Weakest monthly surplus or deficit on the modeled path.</p>
        </article>
        <article className="decision-item">
          <span>{outputs.recast.active ? "Liquid reserve after recast" : "Liquid reserve"}</span>
          <strong>{reserveStatus(outputs)}</strong>
          <p>Starting taxable liquidity after purchase and recast choices.</p>
        </article>
        <article className="decision-item">
          <span>Weakest runway</span>
          <strong>{decimal(runway.runway_months)} mo</strong>
          <p>Lowest modeled months of required outflow covered by liquid assets, in year {runway.year}.</p>
        </article>
        <article className="decision-item item-warn decision-item-wide">
          <span>Main risk</span>
          <strong>{mainRisk(outputs)}</strong>
          <p>Use this as the first assumption to audit before relying on the result.</p>
        </article>
        <article className="decision-item">
          <span>Max workable price</span>
          <strong>{money(outputs.safe_purchase_price)}</strong>
          <p>{safePurchasePriceExplanation(outputs)}</p>
          <p className="confidence-note">{safePurchaseConfidenceNote()}</p>
        </article>
      </div>
    </section>
  );
}
