import type { AffordabilityOutputs, Scenario } from "../lib/api";
import { decimal, money, percent, signedMoney } from "../lib/formatters";
import { getScenarioValue, setScenarioValue } from "../lib/scenarioPaths";

type SliderFormat = "currency" | "currencyMonthly" | "percent" | "number";

type SliderControl = {
  description: string;
  format: SliderFormat;
  label: string;
  max: number;
  min: number;
  path: string[];
  step: number;
};

type ScenarioTunerProps = {
  autoUpdating: boolean;
  loading: boolean;
  onScenarioChange: (scenario: Scenario) => void;
  outputs: AffordabilityOutputs | null;
  scenario: Scenario | null;
};

const controls: SliderControl[] = [
  {
    description: "Income drives spendable cash and is usually the first affordability lever to audit.",
    format: "currency",
    label: "Gross income",
    max: 1_000_000,
    min: 150_000,
    path: ["income", "gross_income"],
    step: 5_000
  },
  {
    description: "Higher prices increase cash to close, mortgage principal, and maintenance reserve.",
    format: "currency",
    label: "Purchase price",
    max: 3_000_000,
    min: 1_000_000,
    path: ["purchase", "purchase_price"],
    step: 25_000
  },
  {
    description: "More down payment lowers the loan, but uses more liquid cash up front.",
    format: "percent",
    label: "Down payment",
    max: 0.8,
    min: 0.05,
    path: ["purchase", "down_payment_pct"],
    step: 0.01
  },
  {
    description: "Rate changes flow directly into monthly principal and interest.",
    format: "percent",
    label: "Mortgage rate",
    max: 0.08,
    min: 0.02,
    path: ["mortgage", "mortgage_rate"],
    step: 0.001
  },
  {
    description: "Portfolio size determines post-close liquidity and long-term runway.",
    format: "currency",
    label: "Starting portfolio",
    max: 5_000_000,
    min: 500_000,
    path: ["savings", "starting_portfolio"],
    step: 50_000
  },
  {
    description: "Lifestyle burn is one of the fastest ways to change cash-flow resilience.",
    format: "currencyMonthly",
    label: "Living expenses",
    max: 25_000,
    min: 5_000,
    path: ["lifestyle", "monthly_living_expenses"],
    step: 100
  },
  {
    description: "Recast lowers payment pressure, but sacrifices liquid reserves.",
    format: "currency",
    label: "Recast paydown",
    max: 500_000,
    min: 0,
    path: ["recast", "one_time_principal_paydown"],
    step: 25_000
  },
  {
    description: "Moves the modeled part-time income reduction earlier or later.",
    format: "number",
    label: "Part-time starts",
    max: 10,
    min: 0,
    path: ["income", "base_part_time_switch_year"],
    step: 1
  }
];

function formatValue(value: number, format: SliderFormat) {
  if (format === "currency") return money(value);
  if (format === "currencyMonthly") return `${money(value)}/mo`;
  if (format === "percent") return percent.format(value);
  return `Year ${decimal(value)}`;
}

export function ScenarioTuner({
  autoUpdating,
  loading,
  onScenarioChange,
  outputs,
  scenario
}: ScenarioTunerProps) {
  return (
    <section className="panel tuner-panel">
      <div className="section-heading">
        <div>
          <h2>Scenario Tuner</h2>
          <p>
            Move the highest-impact assumptions and the overview recalculates after you pause. Detailed
            assumptions remain available below for audit.
          </p>
        </div>
        <span className={`tuner-status ${autoUpdating || loading ? "tuner-status-active" : ""}`}>
          {autoUpdating || loading ? "Updating" : "Auto-updates on pause"}
        </span>
      </div>

      {outputs ? (
        <div className="tuner-impact" aria-label="Current scenario impact">
          <article>
            <span>Monthly P&I</span>
            <strong>{money(outputs.purchase.monthly_mortgage_pi)}</strong>
          </article>
          <article>
            <span>Worst cash flow</span>
            <strong>{signedMoney(outputs.recast.worst_monthly_cash_flow_recast)}</strong>
          </article>
          <article>
            <span>Reserve target</span>
            <strong>{money(outputs.purchase.liquidity_reserve_target)}</strong>
          </article>
        </div>
      ) : null}

      <div className="tuner-grid">
        {scenario
          ? controls.map((control) => {
              const value = getScenarioValue(scenario, control.path);
              return (
                <label className="slider-control" key={control.path.join(".")}>
                  <span>
                    <strong>{control.label}</strong>
                    <em>{formatValue(value, control.format)}</em>
                  </span>
                  <input
                    aria-label={control.label}
                    max={control.max}
                    min={control.min}
                    onChange={(event) =>
                      onScenarioChange(setScenarioValue(scenario, control.path, Number(event.target.value)))
                    }
                    step={control.step}
                    type="range"
                    value={value}
                  />
                  <div className="slider-scale">
                    <small>{formatValue(control.min, control.format)}</small>
                    <small>{formatValue(control.max, control.format)}</small>
                  </div>
                  <p>{control.description}</p>
                </label>
              );
            })
          : Array.from({ length: 6 }).map((_, index) => <div className="skeleton" key={index} />)}
      </div>
    </section>
  );
}
