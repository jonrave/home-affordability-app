import { useState } from "react";
import type { Scenario } from "../lib/api";
import { displayInput, parseInput } from "../lib/formatters";
import {
  getScenarioPath,
  getScenarioValue,
  setScenarioPath,
  setScenarioValue
} from "../lib/scenarioPaths";

type FieldFormat = "currency" | "number" | "percent";

type InputField = {
  help: string;
  kind?: "number";
  label: string;
  path: string[];
  format: FieldFormat;
  unit: string;
};

type SelectField = {
  help: string;
  kind: "select";
  label: string;
  options: Array<{ label: string; value: string }>;
  path: string[];
};

type TextField = {
  help: string;
  kind: "text";
  label: string;
  maxLength?: number;
  path: string[];
  placeholder?: string;
};

type InputGroup = {
  badge: string;
  defaultOpen: boolean;
  description: string;
  title: string;
  fields: Array<InputField | SelectField | TextField>;
};

type ScenarioInputPanelProps = {
  canReset: boolean;
  draftChanged: boolean;
  loading: boolean;
  onCalculate: () => void;
  onReset: () => void;
  onScenarioChange: (scenario: Scenario) => void;
  scenario: Scenario | null;
};

const inputGroups: InputGroup[] = [
  {
    badge: "Core",
    defaultOpen: true,
    description: "The biggest drivers of long-term affordability are income, savings, price, and down payment.",
    title: "Household & Purchase",
    fields: [
      {
        help: "Annual household gross income before taxes and payroll deductions.",
        label: "Gross income",
        path: ["income", "gross_income"],
        format: "currency",
        unit: "$/yr"
      },
      {
        help: "Purchase price drives cash to close, mortgage size, and maintenance reserve.",
        label: "Purchase price",
        path: ["purchase", "purchase_price"],
        format: "currency",
        unit: "$"
      },
      {
        help: "Higher down payments reduce the mortgage but use more liquid assets up front.",
        label: "Down payment",
        path: ["purchase", "down_payment_pct"],
        format: "percent",
        unit: "%"
      },
      {
        help: "Starting portfolio before cash to close is deducted.",
        label: "Starting portfolio",
        path: ["savings", "starting_portfolio"],
        format: "currency",
        unit: "$"
      }
    ]
  },
  {
    badge: "Cash flow",
    defaultOpen: true,
    description: "Ongoing income, spending, and housing costs determine whether the plan adds or draws liquidity each year.",
    title: "Income, Mortgage & Monthly Burn",
    fields: [
      {
        help: "Recurring annual salary growth applied before part-time reductions or salary increases.",
        label: "Income growth",
        path: ["income", "income_growth"],
        format: "percent",
        unit: "%"
      },
      {
        help: "Annual salary increase beginning in the selected model year.",
        label: "Salary increase",
        path: ["income", "salary_step_increase_amount"],
        format: "currency",
        unit: "$/yr"
      },
      {
        help: "Model year when the salary increase begins. Year 0 is the purchase/start year.",
        label: "Salary bump starts",
        path: ["income", "salary_step_increase_year"],
        format: "number",
        unit: "model yr"
      },
      {
        help: "Fixed mortgage interest rate used for principal and interest.",
        label: "Mortgage rate",
        path: ["mortgage", "mortgage_rate"],
        format: "percent",
        unit: "%"
      },
      {
        help: "Non-housing spending before childcare, education, and housing costs.",
        label: "Living expenses",
        path: ["lifestyle", "monthly_living_expenses"],
        format: "currency",
        unit: "$/mo"
      },
      {
        help: "Monthly utilities included in ownership costs.",
        label: "Utilities",
        path: ["housing_costs", "utilities_monthly"],
        format: "currency",
        unit: "$/mo"
      }
    ]
  },
  {
    badge: "Advanced",
    defaultOpen: false,
    description: "These assumptions shape stress resilience, taxes, reserve targets, and recast tradeoffs.",
    title: "Risk, Taxes & Recast",
    fields: [
      {
        help: "Estimated mode is the app default. Manual mode is only a fallback for unsupported tax situations or payroll matching.",
        kind: "select",
        label: "Tax mode",
        options: [
          { label: "Estimate from filing status", value: "estimated" },
          { label: "Manual payroll override", value: "take_home_rate" }
        ],
        path: ["taxes", "tax_mode"]
      },
      {
        help: "Used by estimated tax mode for standard deductions, brackets, and payroll-tax thresholds.",
        kind: "select",
        label: "Filing status",
        options: [
          { label: "Married filing jointly", value: "married_filing_jointly" },
          { label: "Single", value: "single" },
          { label: "Head of household", value: "head_of_household" },
          { label: "Married filing separately", value: "married_filing_separately" }
        ],
        path: ["taxes", "filing_status"]
      },
      {
        help: "Used to infer supported tax jurisdiction. V1 recognizes NY and NYC ZIPs; unsupported ZIPs fall back to federal/FICA only.",
        kind: "text",
        label: "Residence ZIP",
        maxLength: 5,
        path: ["taxes", "residence_zip"],
        placeholder: "e.g. 10001"
      },
      {
        help: "Fallback only: used when Tax mode is set to Manual payroll override.",
        label: "Manual take-home override",
        path: ["income", "cash_take_home_rate"],
        format: "percent",
        unit: "%"
      },
      {
        help: "Model year when the household income reduction starts.",
        label: "Part-time starts",
        path: ["income", "base_part_time_switch_year"],
        format: "number",
        unit: "model yr"
      },
      {
        help: "Annual gross income reduction after the part-time switch begins.",
        label: "Part-time reduction",
        path: ["income", "part_time_gross_income_reduction"],
        format: "currency",
        unit: "$/yr"
      },
      {
        help: "Basis used by the current simplified property-tax calculation.",
        label: "Property tax basis",
        path: ["taxes", "property_tax_basis"],
        format: "currency",
        unit: "$"
      },
      {
        help: "Annual property-tax rate applied to the selected property-tax basis.",
        label: "Property tax rate",
        path: ["taxes", "property_tax_rate"],
        format: "percent",
        unit: "%"
      },
      {
        help: "Annual insurance assumption before insurance growth.",
        label: "Home insurance",
        path: ["housing_costs", "homeowners_insurance_annual"],
        format: "currency",
        unit: "$/yr"
      },
      {
        help: "Annual maintenance reserve as a percentage of purchase price.",
        label: "Maintenance reserve",
        path: ["housing_costs", "maintenance_reserve_pct"],
        format: "percent",
        unit: "%"
      },
      {
        help: "Cash cushion added on top of months-of-expense reserve.",
        label: "One-time cushion",
        path: ["lifestyle", "minimum_one_time_cushion"],
        format: "currency",
        unit: "$"
      },
      {
        help: "Number of months of required outflow targeted as an emergency reserve.",
        label: "Reserve months",
        path: ["lifestyle", "emergency_reserve_months"],
        format: "number",
        unit: "mo"
      },
      {
        help: "Principal paydown used for recast. Use $0 with recast month 0 for no recast.",
        label: "Recast paydown",
        path: ["recast", "one_time_principal_paydown"],
        format: "currency",
        unit: "$"
      },
      {
        help: "Calendar year when the recast occurs.",
        label: "Recast year",
        path: ["recast", "recast_year"],
        format: "number",
        unit: "calendar"
      },
      {
        help: "Month when the recast occurs. Month 0 with $0 paydown is treated as no recast.",
        label: "Recast month",
        path: ["recast", "recast_month"],
        format: "number",
        unit: "0-12"
      },
      {
        help: "Administrative fee included in the recast liquidity tradeoff.",
        label: "Recast fee",
        path: ["recast", "recast_fee"],
        format: "currency",
        unit: "$"
      }
    ]
  }
];

export function ScenarioInputPanel({
  canReset,
  draftChanged,
  loading,
  onCalculate,
  onReset,
  onScenarioChange,
  scenario
}: ScenarioInputPanelProps) {
  const [openGroups, setOpenGroups] = useState<Record<string, boolean>>(() =>
    Object.fromEntries(inputGroups.map((group) => [group.title, group.defaultOpen]))
  );

  return (
    <form className="input-panel" onSubmit={(event) => event.preventDefault()}>
      <div className="section-heading input-heading">
        <div>
          <h2>Scenario Assumptions</h2>
          <p>Start with core assumptions. Taxes are estimated automatically from the advanced tax profile.</p>
        </div>
      </div>

      <div className={`input-status ${draftChanged ? "input-status-dirty" : ""}`}>
        <strong>{draftChanged ? "Changes are ready to apply" : "Results match current assumptions"}</strong>
        <p>
          {draftChanged
            ? "Your edits are saved in this browser, but the decision outputs update only after recalculation."
            : "The decision brief and detail pages are using the assumptions shown here."}
        </p>
      </div>

      {scenario
        ? inputGroups.map((group) => {
            const isOpen = openGroups[group.title];
            return (
              <section className="input-group" key={group.title}>
                <button
                  aria-expanded={isOpen}
                  className="input-group-toggle"
                  onClick={() =>
                    setOpenGroups((current) => ({ ...current, [group.title]: !current[group.title] }))
                  }
                  type="button"
                >
                  <span>
                    <strong>{group.title}</strong>
                    <small>{group.description}</small>
                  </span>
                  <em>{group.badge}</em>
                </button>
                {isOpen ? (
                  <div className="field-grid">
                    {group.fields.map((field) => {
                      const fieldId = `${field.path.join("-")}-help`;
                      if (field.kind === "text") {
                        const value = getScenarioPath<string>(scenario, field.path) ?? "";
                        return (
                          <label key={field.path.join(".")}>
                            <span>{field.label}</span>
                            <input
                              aria-describedby={fieldId}
                              aria-label={field.label}
                              inputMode="numeric"
                              maxLength={field.maxLength}
                              onChange={(event) =>
                                onScenarioChange(
                                  setScenarioPath(
                                    scenario,
                                    field.path,
                                    event.target.value.replace(/\D/g, "").slice(0, field.maxLength ?? undefined)
                                  )
                                )
                              }
                              placeholder={field.placeholder}
                              value={value}
                            />
                            <p className="field-help" id={fieldId}>
                              {field.help}
                            </p>
                          </label>
                        );
                      }
                      if (field.kind === "select") {
                        const value = getScenarioPath<string>(scenario, field.path);
                        return (
                          <label key={field.path.join(".")}>
                            <span>{field.label}</span>
                            <select
                              aria-describedby={fieldId}
                              aria-label={field.label}
                              onChange={(event) =>
                                onScenarioChange(setScenarioPath(scenario, field.path, event.target.value))
                              }
                              value={value}
                            >
                              {field.options.map((option) => (
                                <option key={option.value} value={option.value}>
                                  {option.label}
                                </option>
                              ))}
                            </select>
                            <p className="field-help" id={fieldId}>
                              {field.help}
                            </p>
                          </label>
                        );
                      }
                      const value = getScenarioValue(scenario, field.path);
                      return (
                        <label key={field.path.join(".")}>
                          <span>{field.label}</span>
                          <div className="input-with-unit">
                            <input
                              aria-describedby={fieldId}
                              aria-label={field.label}
                              inputMode="decimal"
                              value={displayInput(value, field.format)}
                              onChange={(event) =>
                                onScenarioChange(
                                  setScenarioValue(scenario, field.path, parseInput(event.target.value, field.format))
                                )
                              }
                            />
                            <small>{field.unit}</small>
                          </div>
                          <p className="field-help" id={fieldId}>
                            {field.help}
                          </p>
                        </label>
                      );
                    })}
                  </div>
                ) : null}
              </section>
            );
          })
        : Array.from({ length: 8 }).map((_, index) => <div className="skeleton" key={index} />)}

      <div className="input-actions">
        <button onClick={onCalculate} disabled={!scenario || loading} type="button">
          {loading ? "Calculating" : "Calculate scenario"}
        </button>
        <button className="button-secondary" onClick={onReset} disabled={!canReset || loading} type="button">
          Reset app defaults
        </button>
      </div>
    </form>
  );
}
