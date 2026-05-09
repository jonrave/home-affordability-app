const configuredBase = process.env.SMOKE_API_BASE ?? process.env.NEXT_PUBLIC_API_BASE;
const baseUrl =
  configuredBase && !configuredBase.startsWith("/")
    ? configuredBase.replace(/\/$/, "")
    : "http://127.0.0.1:8000";

async function getJson(path) {
  const response = await fetch(`${baseUrl}${path}`);
  if (!response.ok) {
    throw new Error(`${path} failed with HTTP ${response.status}: ${await response.text()}`);
  }
  return response.json();
}

async function postJson(path, body) {
  const response = await fetch(`${baseUrl}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });
  if (!response.ok) {
    throw new Error(`${path} failed with HTTP ${response.status}: ${await response.text()}`);
  }
  return response.json();
}

const health = await getJson("/v1/health");
if (health.status !== "ok") {
  throw new Error(`Unexpected health response: ${JSON.stringify(health)}`);
}

const defaults = await getJson("/v1/defaults");
const outputs = await postJson("/v1/calculate", defaults);
const simulation = await postJson("/v1/simulate", defaults);
const salaryAndNoRecastScenario = structuredClone(defaults);
salaryAndNoRecastScenario.income.salary_step_increase_year = 5;
salaryAndNoRecastScenario.income.salary_step_increase_amount = 50_000;
salaryAndNoRecastScenario.recast.one_time_principal_paydown = 0;
salaryAndNoRecastScenario.recast.recast_month = 0;
const salaryAndNoRecastOutputs = await postJson("/v1/calculate", salaryAndNoRecastScenario);

if (!outputs.purchase?.monthly_mortgage_pi || !Array.isArray(outputs.projection)) {
  throw new Error("Calculation response is missing expected affordability fields.");
}

if (!outputs.recast_comparison?.recast_year_30_liquid_real) {
  throw new Error("Calculation response is missing recast comparison fields used by the UI.");
}

if (!outputs.metadata?.engine_version || !outputs.metadata?.calculated_at) {
  throw new Error("Calculation response is missing trust/audit metadata used by the UI.");
}

if (!simulation.no_recast?.percentiles_real?.p50 || !simulation.recast?.percentiles_real?.p50) {
  throw new Error("Simulation response is missing Monte Carlo percentile fields used by the UI.");
}

if (simulation.no_recast.paths !== defaults.monte_carlo.paths || simulation.recast.paths !== defaults.monte_carlo.paths) {
  throw new Error("Simulation response is missing expected path-count metadata for the UI paths.");
}

if (!Object.hasOwn(defaults.income, "salary_step_increase_amount")) {
  throw new Error("Defaults are missing salary step-up fields used by the UI.");
}

if (salaryAndNoRecastOutputs.projection[5].annual_spendable_cash_before_housing <= outputs.projection[5].annual_spendable_cash_before_housing) {
  throw new Error("Salary step-up scenario did not increase spendable cash in the selected year.");
}

if (
  salaryAndNoRecastOutputs.recast.active ||
  salaryAndNoRecastOutputs.recast_comparison.recast_monthly_pi !== salaryAndNoRecastOutputs.recast_comparison.no_recast_monthly_pi
) {
  throw new Error("Zero paydown and recast month 0 should behave as no recast.");
}

console.log(
  `API smoke OK: ${baseUrl} returned ${outputs.projection.length} projection rows, ${simulation.no_recast.paths} MC paths, monthly P&I ${outputs.purchase.monthly_mortgage_pi.toFixed(2)}, and engine v${outputs.metadata.engine_version}.`
);
