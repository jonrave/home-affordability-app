import { AffordabilityOutputs } from "./api";
import { money, signedMoney } from "./formatters";

export function mainRisk(outputs: AffordabilityOutputs) {
  const zeroBreach = outputs.stress_tests.find((item) => item.falls_below_zero);
  if (zeroBreach) {
    return `${zeroBreach.scenario}, ${zeroBreach.path.replace("_", " ")} path depletes taxable liquidity.`;
  }
  const reserveBreach = outputs.stress_tests.find((item) => item.falls_below_reserve);
  if (reserveBreach) {
    return `${reserveBreach.scenario}, ${reserveBreach.path.replace("_", " ")} path breaches the reserve floor.`;
  }
  return "No deterministic stress case breaches the modeled reserve floor.";
}

export function summaryInterpretation(outputs: AffordabilityOutputs) {
  const label = outputs.affordability_score.label;
  const worstCashFlow = outputs.recast.worst_monthly_cash_flow_recast;
  const pathLabel = outputs.recast.active ? "modeled recast path" : "no-recast path";
  if (label === "unsafe") {
    return `The purchase does not clear the current guardrails. The ${pathLabel} still reaches ${signedMoney(worstCashFlow)} per month at its weakest point.`;
  }
  if (label === "fragile") {
    return `The purchase is possible on paper, but the cushion is thin. The ${pathLabel} still reaches ${signedMoney(worstCashFlow)} per month at its weakest point.`;
  }
  if (label === "workable") {
    return `The purchase is workable under base assumptions, but stress cases should drive the decision. The weakest ${pathLabel} month is ${signedMoney(worstCashFlow)}.`;
  }
  return `The purchase has a strong base-case cushion. The weakest ${pathLabel} month is ${signedMoney(worstCashFlow)}.`;
}

export function scoreExplanation(outputs: AffordabilityOutputs) {
  const components = [
    { label: "Cash flow", value: outputs.affordability_score.cash_flow_component },
    { label: "Liquidity", value: outputs.affordability_score.liquidity_component },
    { label: "Runway", value: outputs.affordability_score.runway_component },
    { label: "Stress survival", value: outputs.affordability_score.stress_component }
  ];
  const weakest = [...components].sort((a, b) => a.value - b.value)[0];
  return {
    components,
    explanation: `${weakest.label} is the weakest score component, so it is doing most of the work in keeping the overall status at ${outputs.affordability_score.label}.`
  };
}

export function safePurchasePriceExplanation(outputs: AffordabilityOutputs) {
  const components = [
    { label: "cash flow", value: outputs.affordability_score.cash_flow_component },
    { label: "liquidity", value: outputs.affordability_score.liquidity_component },
    { label: "runway", value: outputs.affordability_score.runway_component },
    { label: "stress survival", value: outputs.affordability_score.stress_component }
  ];
  const weakest = [...components].sort((a, b) => a.value - b.value)[0];
  return `Modeled max price that still reaches a 70+ workable score. The current constraint is ${weakest.label}, so higher income alone may not raise this if liquidity, runway, or stress tests remain tight.`;
}

export function safePurchaseConfidenceNote() {
  return "Confidence basis: this price must clear the model's cash-flow, liquidity, runway, and stress-test guardrails. It is a planning signal, not a guarantee; review taxes, job stability, spending, and market risk before deciding.";
}

export function trustItems(outputs: AffordabilityOutputs) {
  const calculatedAt = new Date(outputs.metadata.calculated_at);
  return [
    {
      label: "Workbook tie-out",
      value: "Deterministic outputs reconciled",
      detail: "Purchase, projection, recast, and stress outputs are covered by workbook reconciliation tests."
    },
    {
      label: "Tax model",
      value: "Simplified",
      detail: "Estimated mode covers federal/FICA and directional NY/NYC bracket estimates; it is not a full tax return calculation."
    },
    {
      label: "Monte Carlo",
      value: "Seeded app simulation",
      detail: "Excel RAND paths are intentionally not reproduced exactly; stochastic tests use seeded invariants."
    },
    {
      label: "Engine",
      value: `v${outputs.metadata.engine_version}`,
      detail: `Calculated ${calculatedAt.toLocaleString()}`
    },
    {
      label: "Use",
      value: "Planning aid",
      detail: "This is not financial advice; assumptions and results should be reviewed before a major purchase decision."
    }
  ];
}

export function reserveStatus(outputs: AffordabilityOutputs) {
  if (!outputs.recast.active) {
    return `${money(outputs.recast.starting_liquid_after_recast)} without recast`;
  }
  return `${money(outputs.recast.starting_liquid_after_recast)} after modeled recast`;
}
