export type Scenario = Record<string, any>;

export type AffordabilityOutputs = {
  purchase: {
    monthly_mortgage_pi: number;
    monthly_ownership_cost: number;
    annual_ownership_cost: number;
    monthly_required_outflow: number;
    liquidity_reserve_target: number;
    starting_liquid_investments: number;
  };
  recast: {
    active: boolean;
    principal_paydown_applied: number;
    recast_fee: number;
    original_monthly_pi: number;
    new_monthly_pi_after_recast: number;
    monthly_payment_reduction: number;
    breakeven_years: number;
    starting_liquid_before_recast: number;
    starting_liquid_after_recast: number;
    worst_monthly_cash_flow_no_recast: number;
    worst_monthly_cash_flow_recast: number;
    cash_flow_positive_after_recast: boolean;
  };
  recast_comparison: {
    no_recast_monthly_pi: number;
    recast_monthly_pi: number;
    no_recast_worst_monthly_cash_flow: number;
    recast_worst_monthly_cash_flow: number;
    no_recast_starting_liquid_assets: number;
    recast_starting_liquid_assets: number;
    no_recast_year_30_liquid_real: number;
    recast_year_30_liquid_real: number;
  };
  projection: Array<{
    year: number;
    annual_spendable_cash_before_housing: number;
    annual_employee_retirement_hsa_savings: number;
    annual_employer_match: number;
    total_retirement_savings: number;
    annual_ownership_cost: number;
    annual_nonhousing_burn: number;
    annual_taxable_savings_target: number;
    liquid_investments: number;
    liquid_real: number;
    retirement_nonliquid_real: number;
    retirement_nonliquid_investments: number;
    total_investable_assets: number;
    inflation_factor: number;
    total_real: number;
    required_monthly_outflow: number;
    liquidity_reserve_target: number;
    runway_months: number;
    annual_liquid_contribution_draw: number;
  }>;
  stress_tests: Array<{
    scenario: string;
    path: "no_recast" | "recast";
    year_30_liquid_assets: number;
    minimum_liquid_assets: number;
    year_30_total_investable_assets: number;
    falls_below_zero: boolean;
    falls_below_reserve: boolean;
    cash_flow_positive_after_recast: boolean;
    takeaway: string;
  }>;
  affordability_score: {
    score: number;
    cash_flow_component: number;
    liquidity_component: number;
    runway_component: number;
    stress_component: number;
    label: string;
  };
  safe_purchase_price: number;
  tax_summary: {
    tax_mode: "take_home_rate" | "estimated";
    filing_status: string;
    residence_zip: string;
    tax_residence_state: string;
    tax_residence_city: string;
    jurisdiction_source: "zip" | "manual" | "none";
    effective_take_home_rate: number;
    estimated_total_tax: number;
    federal_income_tax: number;
    payroll_tax: number;
    state_income_tax: number;
    city_income_tax: number;
    taxable_income_for_estimate: number;
    total_effective_tax_rate: number;
    tax_rate_details: Array<{
      label: string;
      tax_amount: number;
      taxable_income: number;
      effective_rate: number;
      marginal_rate: number;
      note: string;
    }>;
    notes: string[];
  };
  validation_checks: Array<{
    code: string;
    severity: "ok" | "warning" | "error";
    message: string;
  }>;
  metadata: {
    engine_version: string;
    calculated_at: string;
    workbook_reconciliation_status: "deterministic_reconciled";
  };
};

export type MonteCarloScenarioKey = "no_recast" | "recast";

export type MonteCarloSummary = {
  percentiles_real: Record<string, number>;
  probability_ever_at_or_below_zero: number;
  probability_ever_below_250k: number;
  probability_ever_below_500k: number;
  probability_ever_below_750k: number;
  average_shortfall_when_depleted: number;
  max_shortfall: number;
  seed: number;
  paths: number;
};

export type SimulationOutputs = Record<MonteCarloScenarioKey, MonteCarloSummary> &
  Partial<Record<"bear_no_recast" | "bear_recast", MonteCarloSummary>>;

const API_BASE = (process.env.NEXT_PUBLIC_API_BASE ?? "/api/backend").replace(/\/$/, "");

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {})
    }
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export function fetchDefaults(): Promise<Scenario> {
  return request<Scenario>("/v1/defaults");
}

export function calculateScenario(scenario: Scenario): Promise<AffordabilityOutputs> {
  return request<AffordabilityOutputs>("/v1/calculate", {
    method: "POST",
    body: JSON.stringify(scenario)
  });
}

export function simulateScenario(scenario: Scenario): Promise<SimulationOutputs> {
  return request<SimulationOutputs>("/v1/simulate", {
    method: "POST",
    body: JSON.stringify(scenario)
  });
}
