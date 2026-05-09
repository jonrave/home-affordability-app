"""Typed domain models for the affordability engine.

The defaults intentionally mirror the reviewed workbook so reconciliation tests can
compare deterministic outputs before product-specific defaults evolve.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    """Base model that rejects silent schema drift."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class HouseholdAssumptions(StrictModel):
    months_per_year: int = Field(12, ge=1, le=24, description="Months per year")
    model_start_year: int = Field(2026, ge=1900, le=2200)
    horizon_years: int = Field(30, ge=1, le=80)


class IncomeAssumptions(StrictModel):
    gross_income: float = Field(425_000.0, ge=0, description="Annual gross income")
    cash_take_home_rate: float = Field(
        0.62,
        ge=0,
        le=1,
        description="After-tax cash take-home rate before elective savings",
    )
    annual_after_tax_bonus: float = Field(0.0, ge=0)
    employee_pre_tax_retirement: float = Field(0.0, ge=0)
    employee_roth_after_tax_retirement: float = Field(0.0, ge=0)
    employer_retirement_match: float = Field(0.0, ge=0)
    hsa_payroll_contribution: float = Field(0.0, ge=0)
    other_pre_tax_payroll_deductions: float = Field(0.0, ge=0)
    espp_or_other_after_tax_deductions: float = Field(0.0, ge=0)
    retirement_contribution_growth: float = Field(0.025, ge=-0.5, le=1)
    income_growth: float = Field(0.028, ge=-0.5, le=1)
    salary_step_increase_year: int = Field(0, ge=0, le=80)
    salary_step_increase_amount: float = Field(0.0, ge=0)
    part_time_switch_active: bool = True
    base_part_time_switch_year: int = Field(3, ge=0, le=80)
    alt_part_time_switch_year: int = Field(5, ge=0, le=80)
    part_time_gross_income_reduction: float = Field(40_000.0, ge=0)
    part_time_employee_contrib_reduction: float = Field(0.0, ge=0)
    part_time_employer_match_reduction: float = Field(0.0, ge=0)


class TaxAssumptions(StrictModel):
    tax_mode: Literal["take_home_rate", "estimated"] = "take_home_rate"
    filing_status: Literal[
        "single",
        "married_filing_jointly",
        "married_filing_separately",
        "head_of_household",
    ] = "married_filing_jointly"
    residence_zip: str = Field("", pattern=r"^\d{0,5}$")
    tax_residence_state: Literal["none", "NY"] = "none"
    tax_residence_city: Literal["none", "NYC"] = "none"
    itemized_deductions: float = Field(0.0, ge=0)
    additional_taxable_income: float = Field(0.0, ge=0)
    property_tax_basis: float = Field(1_000_000.0, ge=0)
    property_tax_rate: float = Field(0.03, ge=0, le=0.2)
    property_tax_growth: float = Field(0.03, ge=-0.5, le=1)
    buyer_paid_transfer_tax_pct: float = Field(0.0, ge=0, le=0.2)


class HomePurchaseAssumptions(StrictModel):
    purchase_price: float = Field(1_975_000.0, ge=0)
    down_payment_pct: float = Field(0.40, ge=0, le=1)
    buyer_closing_cost_pct: float = Field(0.025, ge=0, le=0.2)
    renovation_move_in_costs: float = Field(0.0, ge=0)
    points_rate_buydown: float = Field(0.0, ge=0)
    legal_appraisal_extras: float = Field(0.0, ge=0)
    family_loan_amount: float = Field(0.0, ge=0)
    family_loan_interest_rate: float = Field(0.0, ge=0, le=1)
    family_loan_principal_repayment: float = Field(0.0, ge=0)
    home_value_growth: float = Field(0.025, ge=-0.5, le=1)


class MortgageAssumptions(StrictModel):
    mortgage_rate: float = Field(0.045, ge=0, le=1)
    mortgage_term_years: int = Field(30, ge=1, le=50)


class RecurringHousingCosts(StrictModel):
    homeowners_insurance_annual: float = Field(4_200.0, ge=0)
    utilities_monthly: float = Field(1_000.0, ge=0)
    maintenance_reserve_pct: float = Field(0.008, ge=0, le=0.2)
    capex_reserve_pct: float = Field(0.0, ge=0, le=0.2)
    hoa_monthly: float = Field(0.0, ge=0)
    pmi_monthly: float = Field(0.0, ge=0)
    insurance_growth: float = Field(0.04, ge=-0.5, le=1)
    maintenance_capex_growth: float = Field(0.03, ge=-0.5, le=1)


class LifestyleExpenses(StrictModel):
    monthly_living_expenses: float = Field(10_800.0, ge=0)
    monthly_debt_payments: float = Field(0.0, ge=0)
    target_monthly_taxable_savings: float = Field(0.0, ge=0)
    spending_inflation: float = Field(0.028, ge=-0.5, le=1)
    emergency_reserve_months: float = Field(12.0, ge=0, le=120)
    minimum_one_time_cushion: float = Field(100_000.0, ge=0)


class ChildcareEducationAssumptions(StrictModel):
    monthly_childcare: float = Field(0.0, ge=0)
    annual_education_cost: float = Field(0.0, ge=0)
    start_year: int = Field(0, ge=0, le=80)
    end_year: int = Field(0, ge=0, le=80)


class SavingsInvestments(StrictModel):
    starting_portfolio: float = Field(2_050_000.0, ge=0)
    liquid_share_of_portfolio: float = Field(0.85, ge=0, le=1)
    portfolio_expected_return: float = Field(0.065, ge=-0.95, le=2)
    annual_market_volatility: float = Field(0.15, ge=0, le=2)
    expected_inflation: float = Field(0.025, ge=-0.5, le=1)


class RecastAssumptions(StrictModel):
    enable_recast: bool = True
    recast_year: int = Field(2027, ge=1900, le=2200)
    recast_month: int = Field(1, ge=0, le=12)
    one_time_principal_paydown: float = Field(200_000.0, ge=0)
    recast_fee: float = Field(500.0, ge=0)
    payment_recalculated_after_recast: bool = True
    loan_term_stays_same_after_recast: bool = True
    enable_dynamic_recast: bool = False
    dynamic_recast_threshold_monthly_cash_flow: float = -2_000.0
    starting_liquid_before_recast_override: float | None = Field(None, ge=0)
    starting_liquid_after_recast_override: float | None = Field(None, ge=0)
    minimum_desired_liquid_reserve_floor: float = Field(500_000.0, ge=0)
    claim_test_remaining_liquidity: float = Field(800_000.0, ge=0)


class StressTestAssumptions(StrictModel):
    immediate_bear_market_drop_2027: float = Field(-0.25, ge=-1, le=1)
    two_year_bear_market_drop_y1: float = Field(-0.20, ge=-1, le=1)
    two_year_bear_market_drop_y2: float = Field(-0.10, ge=-1, le=1)
    flat_decade_real_return: float = Field(0.0, ge=-1, le=1)
    high_inflation_extra_spend_growth: float = Field(0.025, ge=0, le=1)
    high_inflation_income_growth_haircut: float = Field(0.01, ge=0, le=1)
    income_reduction_y5: float = Field(40_000.0, ge=0)
    expense_shock_low: float = Field(50_000.0, ge=0)
    expense_shock_medium: float = Field(100_000.0, ge=0)
    expense_shock_severe: float = Field(150_000.0, ge=0)
    reserve_threshold_250k: float = Field(250_000.0, ge=0)
    reserve_threshold_500k: float = Field(500_000.0, ge=0)
    reserve_threshold_750k: float = Field(750_000.0, ge=0)


class MonteCarloAssumptions(StrictModel):
    paths: int = Field(500, ge=1, le=1_000_000)
    seed: int = Field(20260508, ge=0)
    percentiles: tuple[float, ...] = (0.05, 0.10, 0.15, 0.25, 0.50, 0.75, 0.85, 0.90, 0.95)
    clip_at_zero: bool = True


class Scenario(StrictModel):
    household: HouseholdAssumptions = Field(default_factory=HouseholdAssumptions)
    income: IncomeAssumptions = Field(default_factory=IncomeAssumptions)
    taxes: TaxAssumptions = Field(default_factory=TaxAssumptions)
    purchase: HomePurchaseAssumptions = Field(default_factory=HomePurchaseAssumptions)
    mortgage: MortgageAssumptions = Field(default_factory=MortgageAssumptions)
    housing_costs: RecurringHousingCosts = Field(default_factory=RecurringHousingCosts)
    lifestyle: LifestyleExpenses = Field(default_factory=LifestyleExpenses)
    childcare_education: ChildcareEducationAssumptions = Field(
        default_factory=ChildcareEducationAssumptions
    )
    savings: SavingsInvestments = Field(default_factory=SavingsInvestments)
    recast: RecastAssumptions = Field(default_factory=RecastAssumptions)
    stress_tests: StressTestAssumptions = Field(default_factory=StressTestAssumptions)
    monte_carlo: MonteCarloAssumptions = Field(default_factory=MonteCarloAssumptions)


class ValidationCheck(StrictModel):
    code: str
    severity: Literal["ok", "warning", "error"]
    message: str
    field: str | None = None
    value: float | str | bool | None = None


class PurchaseOutputs(StrictModel):
    down_payment_amount: float
    mortgage_principal: float
    buyer_closing_costs: float
    buyer_transfer_tax: float
    gross_upfront_cash: float
    family_loan_used: float
    net_cash_from_portfolio: float
    portfolio_after_closing: float
    starting_liquid_investments: float
    starting_retirement_nonliquid: float
    monthly_mortgage_pi: float
    monthly_property_tax: float
    monthly_insurance: float
    monthly_maintenance: float
    monthly_capex: float
    family_loan_monthly_service: float
    monthly_ownership_cost: float
    annual_ownership_cost: float
    monthly_nonhousing_burn: float
    monthly_required_outflow: float
    liquidity_reserve_target: float


class ProjectionYear(StrictModel):
    year: int
    annual_spendable_cash_before_housing: float
    annual_employee_retirement_hsa_savings: float
    annual_employer_match: float
    total_retirement_savings: float
    annual_ownership_cost: float
    annual_nonhousing_burn: float
    annual_taxable_savings_target: float
    annual_liquid_contribution_draw: float
    liquid_investments: float
    retirement_nonliquid_investments: float
    total_investable_assets: float
    inflation_factor: float
    liquid_real: float
    retirement_nonliquid_real: float
    total_real: float
    required_monthly_outflow: float
    liquidity_reserve_target: float
    runway_months: float


class RecastOutputs(StrictModel):
    active: bool
    recast_model_year: int
    months_elapsed_pre_recast: int
    remaining_term_months: int
    mortgage_balance_before_recast: float
    principal_paydown_requested: float
    principal_paydown_applied: float
    recast_fee: float
    mortgage_balance_after_recast: float
    original_monthly_pi: float
    new_monthly_pi_after_recast: float
    monthly_payment_reduction: float
    annual_cash_flow_improvement: float
    breakeven_years: float
    starting_liquid_before_recast: float
    starting_liquid_after_recast: float
    adequate_liquidity_after_recast: bool
    worst_monthly_cash_flow_no_recast: float
    worst_monthly_cash_flow_recast: float
    cash_flow_positive_after_recast: bool


class RecastComparisonOutputs(StrictModel):
    no_recast_monthly_pi: float
    recast_monthly_pi: float
    no_recast_worst_monthly_cash_flow: float
    recast_worst_monthly_cash_flow: float
    no_recast_starting_liquid_assets: float
    recast_starting_liquid_assets: float
    no_recast_year_30_liquid_real: float
    recast_year_30_liquid_real: float


class StressTestResult(StrictModel):
    scenario: str
    path: Literal["no_recast", "recast"]
    year_30_liquid_assets: float
    minimum_liquid_assets: float
    year_30_total_investable_assets: float
    falls_below_zero: bool
    falls_below_reserve: bool
    cash_flow_positive_after_recast: bool
    takeaway: str


class MonteCarloSummary(StrictModel):
    percentiles_real: dict[str, float]
    probability_ever_at_or_below_zero: float
    probability_ever_below_250k: float
    probability_ever_below_500k: float
    probability_ever_below_750k: float
    average_shortfall_when_depleted: float
    max_shortfall: float
    seed: int
    paths: int


class AffordabilityScore(StrictModel):
    score: float = Field(ge=0, le=100)
    cash_flow_component: float = Field(ge=0, le=100)
    liquidity_component: float = Field(ge=0, le=100)
    runway_component: float = Field(ge=0, le=100)
    stress_component: float = Field(ge=0, le=100)
    label: Literal["strong", "workable", "fragile", "unsafe"]


class CalculationMetadata(StrictModel):
    engine_version: str
    calculated_at: str
    workbook_reconciliation_status: Literal["deterministic_reconciled"]


class TaxRateDetail(StrictModel):
    label: str
    tax_amount: float
    taxable_income: float
    effective_rate: float = Field(ge=0, le=1)
    marginal_rate: float = Field(ge=0, le=1)
    note: str


class TaxSummary(StrictModel):
    tax_mode: Literal["take_home_rate", "estimated"]
    filing_status: str
    residence_zip: str
    tax_residence_state: str
    tax_residence_city: str
    jurisdiction_source: Literal["zip", "manual", "none"]
    effective_take_home_rate: float = Field(ge=0, le=1)
    estimated_total_tax: float
    federal_income_tax: float
    payroll_tax: float
    state_income_tax: float
    city_income_tax: float
    taxable_income_for_estimate: float
    total_effective_tax_rate: float = Field(ge=0, le=1)
    tax_rate_details: list[TaxRateDetail]
    notes: list[str]


class AffordabilityOutputs(StrictModel):
    purchase: PurchaseOutputs
    projection: list[ProjectionYear]
    recast: RecastOutputs
    recast_comparison: RecastComparisonOutputs
    stress_tests: list[StressTestResult]
    affordability_score: AffordabilityScore
    safe_purchase_price: float
    tax_summary: TaxSummary
    validation_checks: list[ValidationCheck]
    metadata: CalculationMetadata
