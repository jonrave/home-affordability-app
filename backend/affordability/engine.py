"""Deterministic financial engine for the home affordability app."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from math import isfinite

from .schemas import (
    AffordabilityOutputs,
    AffordabilityScore,
    CalculationMetadata,
    ProjectionYear,
    PurchaseOutputs,
    RecastComparisonOutputs,
    RecastOutputs,
    Scenario,
    StressTestResult,
    TaxSummary,
    ValidationCheck,
)

FEDERAL_STANDARD_DEDUCTION_2026 = {
    "single": 16_100.0,
    "married_filing_jointly": 32_200.0,
    "married_filing_separately": 16_100.0,
    "head_of_household": 24_150.0,
}

FEDERAL_BRACKETS_2026 = {
    "single": [
        (0.10, 0.0, 12_400.0),
        (0.12, 12_400.0, 50_400.0),
        (0.22, 50_400.0, 105_700.0),
        (0.24, 105_700.0, 201_775.0),
        (0.32, 201_775.0, 256_225.0),
        (0.35, 256_225.0, 640_600.0),
        (0.37, 640_600.0, None),
    ],
    "married_filing_jointly": [
        (0.10, 0.0, 24_800.0),
        (0.12, 24_800.0, 100_800.0),
        (0.22, 100_800.0, 211_400.0),
        (0.24, 211_400.0, 403_550.0),
        (0.32, 403_550.0, 512_450.0),
        (0.35, 512_450.0, 768_700.0),
        (0.37, 768_700.0, None),
    ],
    "married_filing_separately": [
        (0.10, 0.0, 12_400.0),
        (0.12, 12_400.0, 50_400.0),
        (0.22, 50_400.0, 105_700.0),
        (0.24, 105_700.0, 201_775.0),
        (0.32, 201_775.0, 256_225.0),
        (0.35, 256_225.0, 384_350.0),
        (0.37, 384_350.0, None),
    ],
    "head_of_household": [
        (0.10, 0.0, 17_700.0),
        (0.12, 17_700.0, 67_450.0),
        (0.22, 67_450.0, 108_650.0),
        (0.24, 108_650.0, 201_775.0),
        (0.32, 201_775.0, 256_200.0),
        (0.35, 256_200.0, 640_600.0),
        (0.37, 640_600.0, None),
    ],
}

ADDITIONAL_MEDICARE_THRESHOLDS = {
    "single": 200_000.0,
    "married_filing_jointly": 250_000.0,
    "married_filing_separately": 125_000.0,
    "head_of_household": 200_000.0,
}

SOCIAL_SECURITY_WAGE_BASE_2026 = 184_500.0

NY_STANDARD_DEDUCTION = {
    "single": 8_000.0,
    "married_filing_jointly": 16_050.0,
    "married_filing_separately": 8_000.0,
    "head_of_household": 11_200.0,
}

# V1 state/local support intentionally covers NY/NYC because local taxes are
# especially material there. Other jurisdictions should remain in manual mode
# until their bracket tables are added and tested.
NY_STATE_BRACKETS = {
    "single": [
        (0.04, 0.0, 8_500.0),
        (0.045, 8_500.0, 11_700.0),
        (0.0525, 11_700.0, 13_900.0),
        (0.055, 13_900.0, 80_650.0),
        (0.06, 80_650.0, 215_400.0),
        (0.0685, 215_400.0, 1_077_550.0),
        (0.0965, 1_077_550.0, 5_000_000.0),
        (0.103, 5_000_000.0, 25_000_000.0),
        (0.109, 25_000_000.0, None),
    ],
    "married_filing_jointly": [
        (0.04, 0.0, 17_150.0),
        (0.045, 17_150.0, 23_600.0),
        (0.0525, 23_600.0, 27_900.0),
        (0.055, 27_900.0, 161_550.0),
        (0.06, 161_550.0, 323_200.0),
        (0.0685, 323_200.0, 2_155_350.0),
        (0.0965, 2_155_350.0, 5_000_000.0),
        (0.103, 5_000_000.0, 25_000_000.0),
        (0.109, 25_000_000.0, None),
    ],
    "married_filing_separately": [
        (0.04, 0.0, 8_500.0),
        (0.045, 8_500.0, 11_700.0),
        (0.0525, 11_700.0, 13_900.0),
        (0.055, 13_900.0, 80_650.0),
        (0.06, 80_650.0, 215_400.0),
        (0.0685, 215_400.0, 1_077_550.0),
        (0.0965, 1_077_550.0, 5_000_000.0),
        (0.103, 5_000_000.0, 25_000_000.0),
        (0.109, 25_000_000.0, None),
    ],
    "head_of_household": [
        (0.04, 0.0, 12_800.0),
        (0.045, 12_800.0, 17_650.0),
        (0.0525, 17_650.0, 20_900.0),
        (0.055, 20_900.0, 107_650.0),
        (0.06, 107_650.0, 269_300.0),
        (0.0685, 269_300.0, 1_616_450.0),
        (0.0965, 1_616_450.0, 5_000_000.0),
        (0.103, 5_000_000.0, 25_000_000.0),
        (0.109, 25_000_000.0, None),
    ],
}

NYC_BRACKETS = {
    "single": [
        (0.03078, 0.0, 12_000.0),
        (0.03762, 12_000.0, 25_000.0),
        (0.03819, 25_000.0, 50_000.0),
        (0.03876, 50_000.0, None),
    ],
    "married_filing_jointly": [
        (0.03078, 0.0, 21_600.0),
        (0.03762, 21_600.0, 45_000.0),
        (0.03819, 45_000.0, 90_000.0),
        (0.03876, 90_000.0, None),
    ],
    "married_filing_separately": [
        (0.03078, 0.0, 12_000.0),
        (0.03762, 12_000.0, 25_000.0),
        (0.03819, 25_000.0, 50_000.0),
        (0.03876, 50_000.0, None),
    ],
    "head_of_household": [
        (0.03078, 0.0, 14_400.0),
        (0.03762, 14_400.0, 30_000.0),
        (0.03819, 30_000.0, 60_000.0),
        (0.03876, 60_000.0, None),
    ],
}


NYC_ZIP_RANGES = (
    (10001, 10282),  # Manhattan
    (10301, 10314),  # Staten Island
    (10451, 10475),  # Bronx
    (11004, 11005),  # Queens ZIPs with Long Island postal city names
    (11101, 11109),  # Queens
    (11201, 11256),  # Brooklyn
    (11351, 11385),  # Queens
    (11411, 11436),  # Queens
    (11691, 11697),  # Queens / Rockaway
)
NY_SPECIAL_ZIPS = {501, 544, 6390}


def clamp(value: float, lower: float = 0.0, upper: float = 100.0) -> float:
    return max(lower, min(upper, value))


def compound(rate: float, year: int) -> float:
    return (1.0 + rate) ** year


def pmt(periodic_rate: float, periods: int, principal: float) -> float:
    """Return the positive fixed payment for a loan.

    This mirrors Excel's `PMT(rate, nper, -principal)` convention used by the
    workbook, including a zero-rate guard.
    """

    if periods <= 0:
        raise ValueError("periods must be positive")
    if principal < 0:
        raise ValueError("principal must be nonnegative")
    if periodic_rate == 0:
        return principal / periods
    growth = (1.0 + periodic_rate) ** periods
    return principal * periodic_rate * growth / (growth - 1.0)


def mortgage_balance_after_payments(
    principal: float, periodic_rate: float, monthly_payment: float, elapsed_months: int
) -> float:
    """Closed-form remaining principal after elapsed mortgage payments."""

    if elapsed_months <= 0:
        return principal
    if periodic_rate == 0:
        return max(0.0, principal - monthly_payment * elapsed_months)
    growth = (1.0 + periodic_rate) ** elapsed_months
    balance = principal * growth - monthly_payment * ((growth - 1.0) / periodic_rate)
    return max(0.0, balance)


def _progressive_tax(taxable_income: float, brackets: list[tuple[float, float, float | None]]) -> float:
    tax = 0.0
    for rate, lower, upper in brackets:
        if taxable_income <= lower:
            break
        taxable_slice = min(taxable_income, upper if upper is not None else taxable_income) - lower
        tax += taxable_slice * rate
        if upper is None or taxable_income <= upper:
            break
    return max(0.0, tax)


def _marginal_rate(taxable_income: float, brackets: list[tuple[float, float, float | None]]) -> float:
    if taxable_income <= 0:
        return 0.0
    for rate, lower, upper in brackets:
        if taxable_income > lower and (upper is None or taxable_income <= upper):
            return rate
    return brackets[-1][0] if brackets else 0.0


def _effective_rate(tax_amount: float, gross_income: float) -> float:
    return tax_amount / gross_income if gross_income > 0 else 0.0


def _payroll_marginal_rate(gross_income: float, filing_status: str) -> float:
    if gross_income <= 0:
        return 0.0
    rate = 0.0145
    if gross_income < SOCIAL_SECURITY_WAGE_BASE_2026:
        rate += 0.062
    if gross_income >= ADDITIONAL_MEDICARE_THRESHOLDS[filing_status]:
        rate += 0.009
    return rate


def _parse_zip(zip_code: str) -> int | None:
    raw = (zip_code or "").strip()
    if len(raw) != 5 or not raw.isdigit():
        return None
    return int(raw)


def _zip_in_ranges(zip_value: int, ranges: tuple[tuple[int, int], ...]) -> bool:
    return any(start <= zip_value <= end for start, end in ranges)


def infer_tax_jurisdiction_from_zip(zip_code: str) -> tuple[str, str, str]:
    """Infer the supported tax jurisdiction from a five-digit residence ZIP.

    The engine currently supports federal/FICA plus NY/NYC. ZIPs outside that
    coverage intentionally map to no state/city tax instead of guessing.
    """

    zip_value = _parse_zip(zip_code)
    if zip_value is None:
        return "none", "none", "none"
    if _zip_in_ranges(zip_value, NYC_ZIP_RANGES):
        return "NY", "NYC", "zip"
    if (100 <= zip_value // 100 <= 149) or zip_value in NY_SPECIAL_ZIPS:
        return "NY", "none", "zip"
    return "none", "none", "zip"


def _tax_jurisdiction(scenario: Scenario) -> tuple[str, str, str]:
    inferred_state, inferred_city, source = infer_tax_jurisdiction_from_zip(
        scenario.taxes.residence_zip
    )
    if source == "zip":
        return inferred_state, inferred_city, source
    if (
        scenario.taxes.tax_residence_state != "none"
        or scenario.taxes.tax_residence_city != "none"
    ):
        return (
            scenario.taxes.tax_residence_state,
            scenario.taxes.tax_residence_city,
            "manual",
        )
    return "none", "none", "none"


def estimate_income_taxes(
    scenario: Scenario,
    gross_income: float,
    income_tax_wages: float,
) -> TaxSummary:
    taxes = scenario.taxes
    filing_status = taxes.filing_status
    residence_state, residence_city, jurisdiction_source = _tax_jurisdiction(scenario)
    notes = [
        "Estimated mode includes 2026 federal brackets, 2026 employee FICA, and v1 NY/NYC local support only.",
        "NY/NYC estimates are directional bracket estimates, not a full resident-return worksheet calculation.",
        "It excludes credits, AMT, NIIT, SALT limits, investment tax drag, and employer-side payroll taxes.",
    ]
    if jurisdiction_source == "zip":
        notes.append(
            f"Tax jurisdiction inferred from residence ZIP {taxes.residence_zip}; ZIP inference is approximate near boundaries and special-use ZIPs."
        )
        if residence_state == "none":
            notes.append(
                "Residence ZIP is outside v1 state/local support, so only federal income tax and employee payroll tax are modeled."
            )
    deduction = max(
        taxes.itemized_deductions,
        FEDERAL_STANDARD_DEDUCTION_2026[filing_status],
    )
    federal_taxable = max(0.0, income_tax_wages + taxes.additional_taxable_income - deduction)
    federal_income_tax = _progressive_tax(
        federal_taxable, FEDERAL_BRACKETS_2026[filing_status]
    )
    social_security_tax = min(gross_income, SOCIAL_SECURITY_WAGE_BASE_2026) * 0.062
    medicare_tax = gross_income * 0.0145
    additional_medicare = max(
        0.0, gross_income - ADDITIONAL_MEDICARE_THRESHOLDS[filing_status]
    ) * 0.009
    payroll_tax = social_security_tax + medicare_tax + additional_medicare

    state_income_tax = 0.0
    city_income_tax = 0.0
    ny_taxable = 0.0
    if residence_state == "NY":
        ny_taxable = max(
            0.0,
            income_tax_wages
            + taxes.additional_taxable_income
            - max(taxes.itemized_deductions, NY_STANDARD_DEDUCTION[filing_status]),
        )
        state_income_tax = _progressive_tax(ny_taxable, NY_STATE_BRACKETS[filing_status])
        if residence_city == "NYC":
            city_income_tax = _progressive_tax(ny_taxable, NYC_BRACKETS[filing_status])
        notes.append(
            "New York state/local estimates do not apply high-income tax computation worksheets or recapture calculations."
        )
    elif residence_city == "NYC":
        notes.append("NYC local tax is only applied when tax residence state is New York.")

    total_tax = federal_income_tax + payroll_tax + state_income_tax + city_income_tax
    after_tax_wages = max(0.0, income_tax_wages - total_tax)
    effective_take_home_rate = after_tax_wages / gross_income if gross_income > 0 else 0.0
    total_effective_tax_rate = _effective_rate(total_tax, gross_income)
    tax_rate_details = [
        {
            "label": "Federal income",
            "tax_amount": federal_income_tax,
            "taxable_income": federal_taxable,
            "effective_rate": _effective_rate(federal_income_tax, gross_income),
            "marginal_rate": _marginal_rate(
                federal_taxable, FEDERAL_BRACKETS_2026[filing_status]
            ),
            "note": "2026 federal ordinary income brackets after the selected standard or itemized deduction.",
        },
        {
            "label": "Employee payroll",
            "tax_amount": payroll_tax,
            "taxable_income": gross_income,
            "effective_rate": _effective_rate(payroll_tax, gross_income),
            "marginal_rate": _payroll_marginal_rate(gross_income, filing_status),
            "note": "Employee Social Security and Medicare, including additional Medicare above the filing-status threshold.",
        },
    ]
    if residence_state == "NY":
        tax_rate_details.append(
            {
                "label": "NY state income",
                "tax_amount": state_income_tax,
                "taxable_income": ny_taxable,
                "effective_rate": _effective_rate(state_income_tax, gross_income),
                "marginal_rate": _marginal_rate(
                    ny_taxable, NY_STATE_BRACKETS[filing_status]
                ),
                "note": "New York resident income-tax brackets after the modeled NY deduction.",
            }
        )
    if residence_city == "NYC":
        tax_rate_details.append(
            {
                "label": "NYC resident income",
                "tax_amount": city_income_tax,
                "taxable_income": ny_taxable,
                "effective_rate": _effective_rate(city_income_tax, gross_income),
                "marginal_rate": _marginal_rate(ny_taxable, NYC_BRACKETS[filing_status]),
                "note": "New York City resident income-tax brackets applied to modeled NY taxable income.",
            }
        )

    return TaxSummary(
        tax_mode="estimated",
        filing_status=filing_status,
        residence_zip=taxes.residence_zip,
        tax_residence_state=residence_state,
        tax_residence_city=residence_city,
        jurisdiction_source=jurisdiction_source,
        effective_take_home_rate=effective_take_home_rate,
        estimated_total_tax=total_tax,
        federal_income_tax=federal_income_tax,
        payroll_tax=payroll_tax,
        state_income_tax=state_income_tax,
        city_income_tax=city_income_tax,
        taxable_income_for_estimate=federal_taxable,
        total_effective_tax_rate=total_effective_tax_rate,
        tax_rate_details=tax_rate_details,
        notes=notes,
    )


def calculate_tax_summary(
    scenario: Scenario,
    gross_income: float | None = None,
    income_tax_wages: float | None = None,
) -> TaxSummary:
    income = scenario.income
    gross = income.gross_income if gross_income is None else gross_income
    wages = gross if income_tax_wages is None else income_tax_wages
    residence_state, residence_city, jurisdiction_source = _tax_jurisdiction(scenario)
    if scenario.taxes.tax_mode == "take_home_rate":
        estimated_tax = max(0.0, wages * (1.0 - income.cash_take_home_rate))
        manual_tax_rate = 1.0 - income.cash_take_home_rate
        return TaxSummary(
            tax_mode="take_home_rate",
            filing_status=scenario.taxes.filing_status,
            residence_zip=scenario.taxes.residence_zip,
            tax_residence_state=residence_state,
            tax_residence_city=residence_city,
            jurisdiction_source=jurisdiction_source,
            effective_take_home_rate=income.cash_take_home_rate,
            estimated_total_tax=estimated_tax,
            federal_income_tax=0.0,
            payroll_tax=0.0,
            state_income_tax=0.0,
            city_income_tax=0.0,
            taxable_income_for_estimate=max(0.0, wages),
            total_effective_tax_rate=manual_tax_rate,
            tax_rate_details=[
                {
                    "label": "Manual take-home override",
                    "tax_amount": estimated_tax,
                    "taxable_income": max(0.0, wages),
                    "effective_rate": manual_tax_rate,
                    "marginal_rate": manual_tax_rate,
                    "note": "Manual mode treats the entered take-home percentage as the full payroll/tax haircut.",
                }
            ],
            notes=["Manual mode uses the take-home rate entered in assumptions."],
        )
    return estimate_income_taxes(scenario, gross, wages)


def calculate_purchase_outputs(scenario: Scenario) -> PurchaseOutputs:
    household = scenario.household
    purchase = scenario.purchase
    mortgage = scenario.mortgage
    taxes = scenario.taxes
    housing = scenario.housing_costs
    lifestyle = scenario.lifestyle
    savings = scenario.savings

    months = household.months_per_year
    down_payment = purchase.purchase_price * purchase.down_payment_pct
    mortgage_principal = purchase.purchase_price - down_payment
    closing_costs = purchase.purchase_price * purchase.buyer_closing_cost_pct
    transfer_tax = purchase.purchase_price * taxes.buyer_paid_transfer_tax_pct
    gross_upfront_cash = (
        down_payment
        + closing_costs
        + purchase.renovation_move_in_costs
        + purchase.points_rate_buydown
        + purchase.legal_appraisal_extras
        + transfer_tax
    )
    family_loan_used = min(purchase.family_loan_amount, gross_upfront_cash)
    net_cash_from_portfolio = gross_upfront_cash - family_loan_used
    portfolio_after_closing = savings.starting_portfolio - net_cash_from_portfolio
    starting_liquid = portfolio_after_closing * savings.liquid_share_of_portfolio
    starting_retirement = portfolio_after_closing * (1.0 - savings.liquid_share_of_portfolio)

    monthly_rate = mortgage.mortgage_rate / months
    term_months = mortgage.mortgage_term_years * months
    monthly_pi = pmt(monthly_rate, term_months, mortgage_principal)
    monthly_property_tax = taxes.property_tax_basis * taxes.property_tax_rate / months
    monthly_insurance = housing.homeowners_insurance_annual / months
    monthly_maintenance = purchase.purchase_price * housing.maintenance_reserve_pct / months
    monthly_capex = purchase.purchase_price * housing.capex_reserve_pct / months
    family_loan_service = (
        purchase.family_loan_principal_repayment
        + family_loan_used * purchase.family_loan_interest_rate / months
    )
    monthly_ownership_cost = (
        monthly_pi
        + monthly_property_tax
        + monthly_insurance
        + monthly_maintenance
        + monthly_capex
        + family_loan_service
        + housing.utilities_monthly
        + housing.hoa_monthly
        + housing.pmi_monthly
    )
    monthly_nonhousing = lifestyle.monthly_living_expenses + lifestyle.monthly_debt_payments
    required_outflow = monthly_ownership_cost + monthly_nonhousing
    reserve_target = (
        required_outflow * lifestyle.emergency_reserve_months + lifestyle.minimum_one_time_cushion
    )

    return PurchaseOutputs(
        down_payment_amount=down_payment,
        mortgage_principal=mortgage_principal,
        buyer_closing_costs=closing_costs,
        buyer_transfer_tax=transfer_tax,
        gross_upfront_cash=gross_upfront_cash,
        family_loan_used=family_loan_used,
        net_cash_from_portfolio=net_cash_from_portfolio,
        portfolio_after_closing=portfolio_after_closing,
        starting_liquid_investments=starting_liquid,
        starting_retirement_nonliquid=starting_retirement,
        monthly_mortgage_pi=monthly_pi,
        monthly_property_tax=monthly_property_tax,
        monthly_insurance=monthly_insurance,
        monthly_maintenance=monthly_maintenance,
        monthly_capex=monthly_capex,
        family_loan_monthly_service=family_loan_service,
        monthly_ownership_cost=monthly_ownership_cost,
        annual_ownership_cost=monthly_ownership_cost * months,
        monthly_nonhousing_burn=monthly_nonhousing,
        monthly_required_outflow=required_outflow,
        liquidity_reserve_target=reserve_target,
    )


def _part_time_reduction(scenario: Scenario, year: int, switch_year: int) -> float:
    income = scenario.income
    if not income.part_time_switch_active or year < switch_year:
        return 0.0
    return income.part_time_gross_income_reduction * compound(
        income.income_growth, year - switch_year
    )


def _salary_step_increase(scenario: Scenario, year: int, income_growth: float) -> float:
    income = scenario.income
    if income.salary_step_increase_amount <= 0 or year < income.salary_step_increase_year:
        return 0.0
    return income.salary_step_increase_amount * compound(
        income_growth, year - income.salary_step_increase_year
    )


def _employee_contribution_reduction(scenario: Scenario, year: int, switch_year: int) -> float:
    income = scenario.income
    if not income.part_time_switch_active or year < switch_year:
        return 0.0
    return income.part_time_employee_contrib_reduction * compound(
        income.retirement_contribution_growth, year - switch_year
    )


def _employer_match_reduction(scenario: Scenario, year: int, switch_year: int) -> float:
    income = scenario.income
    if not income.part_time_switch_active or year < switch_year:
        return 0.0
    return income.part_time_employer_match_reduction * compound(
        income.retirement_contribution_growth, year - switch_year
    )


def _childcare_education_cost(scenario: Scenario, year: int, spending_growth: float) -> float:
    childcare = scenario.childcare_education
    annual_cost = childcare.monthly_childcare * scenario.household.months_per_year
    annual_cost += childcare.annual_education_cost
    if annual_cost == 0:
        return 0.0
    if childcare.end_year == 0:
        active = year >= childcare.start_year
    else:
        active = childcare.start_year <= year <= childcare.end_year
    if not active:
        return 0.0
    return annual_cost * compound(spending_growth, max(0, year - childcare.start_year))


def _annual_spendable_cash(
    scenario: Scenario,
    *,
    gross_income: float,
    pre_tax_after_reduction: float,
    other_pre_tax: float,
    roth_after_tax: float,
    espp_after_tax: float,
) -> float:
    income = scenario.income
    taxable_wages = max(0.0, gross_income - pre_tax_after_reduction - other_pre_tax)
    if scenario.taxes.tax_mode == "estimated":
        tax_summary = estimate_income_taxes(scenario, gross_income, taxable_wages)
        return (
            taxable_wages
            - tax_summary.estimated_total_tax
            + income.annual_after_tax_bonus
            - roth_after_tax
            - espp_after_tax
        )
    return (
        taxable_wages * income.cash_take_home_rate
        + income.annual_after_tax_bonus
        - roth_after_tax
        - espp_after_tax
    )


def build_projection(
    scenario: Scenario,
    purchase_outputs: PurchaseOutputs | None = None,
    *,
    part_time_switch_year: int | None = None,
    spending_inflation_override: float | None = None,
    income_growth_override: float | None = None,
    extra_income_reduction_start_year: int | None = None,
    extra_income_reduction: float = 0.0,
    extra_expense_shock_year: int | None = None,
    extra_expense_shock: float = 0.0,
    return_series: list[float] | None = None,
) -> list[ProjectionYear]:
    """Build the deterministic annual projection used by the workbook."""

    purchase = purchase_outputs or calculate_purchase_outputs(scenario)
    household = scenario.household
    income = scenario.income
    lifestyle = scenario.lifestyle
    taxes = scenario.taxes
    housing = scenario.housing_costs
    savings = scenario.savings
    months = household.months_per_year
    horizon = household.horizon_years
    switch_year = part_time_switch_year
    if switch_year is None:
        switch_year = income.base_part_time_switch_year
    spending_growth = (
        lifestyle.spending_inflation
        if spending_inflation_override is None
        else spending_inflation_override
    )
    income_growth = income.income_growth if income_growth_override is None else income_growth_override

    rows: list[ProjectionYear] = []
    liquid = purchase.starting_liquid_investments
    retirement = purchase.starting_retirement_nonliquid

    for year in range(horizon + 1):
        gross_income = max(
            0.0,
            income.gross_income * compound(income_growth, year)
            + _salary_step_increase(scenario, year, income_growth)
            - _part_time_reduction(scenario, year, switch_year),
        )
        if extra_income_reduction_start_year is not None and year >= extra_income_reduction_start_year:
            gross_income = max(
                0.0,
                gross_income
                - extra_income_reduction * compound(income_growth, year - extra_income_reduction_start_year),
            )

        pre_tax_base = (
            income.employee_pre_tax_retirement + income.hsa_payroll_contribution
        ) * compound(income.retirement_contribution_growth, year)
        pre_tax_reduction = min(
            _employee_contribution_reduction(scenario, year, switch_year), pre_tax_base
        )
        pre_tax_after_reduction = max(0.0, pre_tax_base - pre_tax_reduction)
        other_pre_tax = income.other_pre_tax_payroll_deductions * compound(
            spending_growth, year
        )
        roth_after_tax = income.employee_roth_after_tax_retirement * compound(
            income.retirement_contribution_growth, year
        )
        espp_after_tax = income.espp_or_other_after_tax_deductions * compound(
            spending_growth, year
        )
        annual_spendable = _annual_spendable_cash(
            scenario,
            gross_income=gross_income,
            pre_tax_after_reduction=pre_tax_after_reduction,
            other_pre_tax=other_pre_tax,
            roth_after_tax=roth_after_tax,
            espp_after_tax=espp_after_tax,
        )

        employee_retirement = max(
            0.0,
            (
                income.employee_pre_tax_retirement
                + income.employee_roth_after_tax_retirement
                + income.hsa_payroll_contribution
            )
            * compound(income.retirement_contribution_growth, year)
            - _employee_contribution_reduction(scenario, year, switch_year),
        )
        employer_match = max(
            0.0,
            income.employer_retirement_match
            * compound(income.retirement_contribution_growth, year)
            - _employer_match_reduction(scenario, year, switch_year),
        )
        total_retirement = employee_retirement + employer_match

        annual_ownership = (
            purchase.monthly_mortgage_pi * months
            + purchase.monthly_property_tax * months * compound(taxes.property_tax_growth, year)
            + purchase.monthly_insurance * months * compound(housing.insurance_growth, year)
            + housing.utilities_monthly * months * compound(spending_growth, year)
            + (purchase.monthly_maintenance + purchase.monthly_capex)
            * months
            * compound(housing.maintenance_capex_growth, year)
            + (
                housing.hoa_monthly
                + housing.pmi_monthly
                + purchase.family_loan_monthly_service
            )
            * months
        )
        annual_nonhousing = (
            (lifestyle.monthly_living_expenses + lifestyle.monthly_debt_payments)
            * months
            * compound(spending_growth, year)
        )
        annual_nonhousing += _childcare_education_cost(scenario, year, spending_growth)
        if extra_expense_shock_year is not None and year == extra_expense_shock_year:
            annual_nonhousing += extra_expense_shock

        taxable_savings_target = (
            lifestyle.target_monthly_taxable_savings
            * months
            * compound(spending_growth, year)
        )
        annual_liquid_contribution = annual_spendable - annual_ownership - annual_nonhousing

        if year > 0:
            annual_return = (
                savings.portfolio_expected_return
                if return_series is None
                else return_series[min(year, len(return_series) - 1)]
            )
            liquid = max(0.0, liquid * (1.0 + annual_return) + annual_liquid_contribution)
            retirement = max(0.0, retirement * (1.0 + annual_return) + total_retirement)

        inflation_factor = compound(savings.expected_inflation, year)
        total_assets = liquid + retirement
        required_monthly_outflow = (annual_ownership + annual_nonhousing) / months
        reserve_target = (
            required_monthly_outflow * lifestyle.emergency_reserve_months
            + lifestyle.minimum_one_time_cushion
        )
        runway_months = liquid / required_monthly_outflow if required_monthly_outflow > 0 else 0.0

        rows.append(
            ProjectionYear(
                year=year,
                annual_spendable_cash_before_housing=annual_spendable,
                annual_employee_retirement_hsa_savings=employee_retirement,
                annual_employer_match=employer_match,
                total_retirement_savings=total_retirement,
                annual_ownership_cost=annual_ownership,
                annual_nonhousing_burn=annual_nonhousing,
                annual_taxable_savings_target=taxable_savings_target,
                annual_liquid_contribution_draw=annual_liquid_contribution,
                liquid_investments=liquid,
                retirement_nonliquid_investments=retirement,
                total_investable_assets=total_assets,
                inflation_factor=inflation_factor,
                liquid_real=liquid / inflation_factor,
                retirement_nonliquid_real=retirement / inflation_factor,
                total_real=total_assets / inflation_factor,
                required_monthly_outflow=required_monthly_outflow,
                liquidity_reserve_target=reserve_target,
                runway_months=runway_months,
            )
        )

    return rows


@dataclass(frozen=True)
class RecastForecast:
    no_recast_cash_flow: list[float]
    recast_cash_flow: list[float]
    recast_outflow: list[float]
    liquid_no_recast: list[float]
    liquid_recast: list[float]
    total_no_recast: list[float]
    total_recast: list[float]


def calculate_recast_outputs(
    scenario: Scenario,
    purchase: PurchaseOutputs,
    projection: list[ProjectionYear],
) -> RecastOutputs:
    household = scenario.household
    recast = scenario.recast
    mortgage = scenario.mortgage
    months = household.months_per_year
    original_loan = purchase.mortgage_principal
    monthly_rate = mortgage.mortgage_rate / months
    term_months = mortgage.mortgage_term_years * months
    original_pi = purchase.monthly_mortgage_pi
    recast_model_year = max(0, recast.recast_year - household.model_start_year)
    months_elapsed = max(0, recast_model_year * months + recast.recast_month - 1)
    remaining_term = (
        max(1, term_months - months_elapsed)
        if recast.loan_term_stays_same_after_recast
        else term_months
    )
    balance_before = mortgage_balance_after_payments(
        original_loan, monthly_rate, original_pi, months_elapsed
    )
    starting_liquid_before = (
        recast.starting_liquid_before_recast_override
        if recast.starting_liquid_before_recast_override is not None
        else purchase.starting_liquid_investments
    )
    recast_requested = (
        recast.enable_recast
        and recast.recast_month > 0
        and recast.one_time_principal_paydown > 0
    )
    principal_paydown = (
        min(
            recast.one_time_principal_paydown,
            balance_before,
            max(0.0, starting_liquid_before - recast.recast_fee),
        )
        if recast_requested
        else 0.0
    )
    recast_active = recast_requested and principal_paydown > 0
    applied_fee = recast.recast_fee if recast_active else 0.0
    balance_after = max(0.0, balance_before - principal_paydown)
    if recast_active and recast.payment_recalculated_after_recast:
        new_pi = (
            balance_after / remaining_term
            if monthly_rate == 0
            else pmt(monthly_rate, remaining_term, balance_after)
        )
    else:
        new_pi = original_pi
    monthly_reduction = max(0.0, original_pi - new_pi)
    annual_improvement = monthly_reduction * months
    breakeven = (
        (principal_paydown + recast.recast_fee) / annual_improvement
        if annual_improvement > 0
        else 0.0
    )
    starting_liquid_after = (
        recast.starting_liquid_after_recast_override
        if recast.starting_liquid_after_recast_override is not None
        else starting_liquid_before - principal_paydown - applied_fee
    )

    no_recast_cash_flows = [row.annual_liquid_contribution_draw for row in projection]
    recast_cash_flows = []
    for row in projection:
        year = row.year
        if year < recast_model_year:
            savings = 0.0
        elif year == recast_model_year:
            savings = monthly_reduction * (months + 1 - recast.recast_month)
        else:
            savings = annual_improvement
        recast_cash_flows.append(row.annual_liquid_contribution_draw + savings)

    horizon_slice = slice(min(recast_model_year, len(projection) - 1), None)
    worst_no_recast = min(no_recast_cash_flows[horizon_slice]) / months
    worst_recast = min(recast_cash_flows[horizon_slice]) / months

    return RecastOutputs(
        active=recast_active,
        recast_model_year=recast_model_year,
        months_elapsed_pre_recast=months_elapsed,
        remaining_term_months=remaining_term,
        mortgage_balance_before_recast=balance_before,
        principal_paydown_requested=recast.one_time_principal_paydown,
        principal_paydown_applied=principal_paydown,
        recast_fee=applied_fee,
        mortgage_balance_after_recast=balance_after,
        original_monthly_pi=original_pi,
        new_monthly_pi_after_recast=new_pi,
        monthly_payment_reduction=monthly_reduction,
        annual_cash_flow_improvement=annual_improvement,
        breakeven_years=breakeven,
        starting_liquid_before_recast=starting_liquid_before,
        starting_liquid_after_recast=starting_liquid_after,
        adequate_liquidity_after_recast=(
            starting_liquid_after >= recast.minimum_desired_liquid_reserve_floor
        ),
        worst_monthly_cash_flow_no_recast=worst_no_recast,
        worst_monthly_cash_flow_recast=worst_recast,
        cash_flow_positive_after_recast=worst_recast > 0,
    )


def build_recast_forecast(
    scenario: Scenario,
    projection: list[ProjectionYear],
    recast: RecastOutputs,
) -> RecastForecast:
    expected_return = scenario.savings.portfolio_expected_return
    no_recast_cash_flow = [row.annual_liquid_contribution_draw for row in projection]
    recast_cash_flow: list[float] = []
    recast_outflow: list[float] = []
    liquid_no_recast: list[float] = []
    liquid_recast: list[float] = []
    total_no_recast: list[float] = []
    total_recast: list[float] = []

    for row in projection:
        if row.year < recast.recast_model_year:
            improvement = 0.0
        elif row.year == recast.recast_model_year:
            improvement = recast.monthly_payment_reduction * (
                scenario.household.months_per_year + 1 - scenario.recast.recast_month
            )
        else:
            improvement = recast.annual_cash_flow_improvement
        recast_cash_flow.append(row.annual_liquid_contribution_draw + improvement)
        recast_outflow.append(
            recast.principal_paydown_applied + recast.recast_fee
            if row.year == recast.recast_model_year
            else 0.0
        )

    for index, row in enumerate(projection):
        if index == 0:
            liquid_no_recast.append(recast.starting_liquid_before_recast)
            liquid_recast.append(recast.starting_liquid_before_recast)
        else:
            liquid_no_recast.append(
                liquid_no_recast[-1] * (1.0 + expected_return) + no_recast_cash_flow[index]
            )
            liquid_recast.append(
                (liquid_recast[-1] - recast_outflow[index]) * (1.0 + expected_return)
                + recast_cash_flow[index]
            )
        total_no_recast.append(liquid_no_recast[-1] + row.retirement_nonliquid_investments)
        total_recast.append(liquid_recast[-1] + row.retirement_nonliquid_investments)

    return RecastForecast(
        no_recast_cash_flow=no_recast_cash_flow,
        recast_cash_flow=recast_cash_flow,
        recast_outflow=recast_outflow,
        liquid_no_recast=liquid_no_recast,
        liquid_recast=liquid_recast,
        total_no_recast=total_no_recast,
        total_recast=total_recast,
    )


def build_recast_comparison(
    scenario: Scenario,
    projection: list[ProjectionYear],
    recast: RecastOutputs,
    recast_forecast: RecastForecast,
) -> RecastComparisonOutputs:
    year_30 = min(scenario.household.horizon_years, len(projection) - 1)
    inflation_factor = projection[year_30].inflation_factor
    return RecastComparisonOutputs(
        no_recast_monthly_pi=recast.original_monthly_pi,
        recast_monthly_pi=recast.new_monthly_pi_after_recast,
        no_recast_worst_monthly_cash_flow=recast.worst_monthly_cash_flow_no_recast,
        recast_worst_monthly_cash_flow=recast.worst_monthly_cash_flow_recast,
        no_recast_starting_liquid_assets=recast.starting_liquid_before_recast,
        recast_starting_liquid_assets=recast.starting_liquid_after_recast,
        no_recast_year_30_liquid_real=projection[year_30].liquid_real,
        recast_year_30_liquid_real=recast_forecast.liquid_recast[year_30] / inflation_factor,
    )


def _roll_forward_liquid(
    starting_liquid: float,
    cash_flows: list[float],
    returns: list[float],
    outflows: list[float] | None = None,
    *,
    clip_at_zero: bool = False,
) -> list[float]:
    balances = [starting_liquid]
    outflows = outflows or [0.0 for _ in cash_flows]
    for year in range(1, len(cash_flows)):
        value = (balances[-1] - outflows[year]) * (1.0 + returns[year]) + cash_flows[year]
        balances.append(max(0.0, value) if clip_at_zero else value)
    return balances


def _roll_forward_retirement(
    starting_retirement: float,
    contributions: list[float],
    returns: list[float],
) -> list[float]:
    balances = [starting_retirement]
    for year in range(1, len(contributions)):
        balances.append(max(0.0, balances[-1] * (1.0 + returns[year]) + contributions[year]))
    return balances


def _stress_summary(
    scenario: Scenario,
    name: str,
    path: str,
    liquid: list[float],
    retirement: list[float],
    cash_flow_positive: bool,
) -> StressTestResult:
    reserve = scenario.stress_tests.reserve_threshold_500k
    year_30_liquid = liquid[min(scenario.household.horizon_years, len(liquid) - 1)]
    min_liquid = min(liquid)
    year_30_total = year_30_liquid + retirement[min(scenario.household.horizon_years, len(retirement) - 1)]
    below_zero = min_liquid < 0
    below_reserve = min_liquid < reserve
    if below_zero:
        takeaway = "Depletes taxable liquidity"
    elif below_reserve:
        takeaway = "Stays above zero but breaches reserve floor"
    else:
        takeaway = "Stays above reserve floor"
    return StressTestResult(
        scenario=name,
        path=path,  # type: ignore[arg-type]
        year_30_liquid_assets=year_30_liquid,
        minimum_liquid_assets=min_liquid,
        year_30_total_investable_assets=year_30_total,
        falls_below_zero=below_zero,
        falls_below_reserve=below_reserve,
        cash_flow_positive_after_recast=cash_flow_positive,
        takeaway=takeaway,
    )


def calculate_stress_tests(
    scenario: Scenario,
    purchase: PurchaseOutputs,
    projection: list[ProjectionYear],
    recast: RecastOutputs,
    recast_forecast: RecastForecast,
) -> list[StressTestResult]:
    horizon = scenario.household.horizon_years
    expected = scenario.savings.portfolio_expected_return
    base_returns = [expected for _ in range(horizon + 1)]
    contributions = [row.total_retirement_savings for row in projection]
    retirement_base = [row.retirement_nonliquid_investments for row in projection]
    results: list[StressTestResult] = []

    results.append(
        _stress_summary(
            scenario,
            "Base expected return",
            "no_recast",
            recast_forecast.liquid_no_recast,
            retirement_base,
            recast.cash_flow_positive_after_recast,
        )
    )
    results.append(
        _stress_summary(
            scenario,
            "Base expected return",
            "recast",
            recast_forecast.liquid_recast,
            retirement_base,
            recast.cash_flow_positive_after_recast,
        )
    )

    stress_defs: list[tuple[str, list[float], list[ProjectionYear]]] = []
    immediate = base_returns.copy()
    if horizon >= 1:
        immediate[1] = scenario.stress_tests.immediate_bear_market_drop_2027
    stress_defs.append(("Immediate bear market", immediate, projection))

    two_year = base_returns.copy()
    if horizon >= 1:
        two_year[1] = scenario.stress_tests.two_year_bear_market_drop_y1
    if horizon >= 2:
        two_year[2] = scenario.stress_tests.two_year_bear_market_drop_y2
    stress_defs.append(("Two-year bear market", two_year, projection))

    flat_decade = base_returns.copy()
    for year in range(1, min(10, horizon) + 1):
        flat_decade[year] = (
            scenario.savings.expected_inflation + scenario.stress_tests.flat_decade_real_return
        )
    stress_defs.append(("Flat decade", flat_decade, projection))

    stress_defs.append(("High inflation", base_returns, projection))

    income_reduction_projection = build_projection(
        scenario,
        purchase,
        extra_income_reduction_start_year=5,
        extra_income_reduction=scenario.stress_tests.income_reduction_y5,
    )
    stress_defs.append(("Income reduction in year 5", base_returns, income_reduction_projection))

    for name, shock in [
        ("Unexpected expense shock - $50k", scenario.stress_tests.expense_shock_low),
        ("Unexpected expense shock - $100k", scenario.stress_tests.expense_shock_medium),
        ("Unexpected expense shock - $150k", scenario.stress_tests.expense_shock_severe),
    ]:
        shock_projection = build_projection(
            scenario,
            purchase,
            extra_expense_shock_year=recast.recast_model_year,
            extra_expense_shock=shock,
        )
        stress_defs.append((name, base_returns, shock_projection))

    for name, returns, stress_projection in stress_defs:
        if name == "High inflation":
            stress_cash_flows = [
                row.annual_liquid_contribution_draw
                - row.annual_nonhousing_burn
                * (compound(scenario.stress_tests.high_inflation_extra_spend_growth, row.year) - 1.0)
                for row in stress_projection
            ]
        else:
            stress_cash_flows = [row.annual_liquid_contribution_draw for row in stress_projection]
        stress_retirement = _roll_forward_retirement(
            purchase.starting_retirement_nonliquid,
            [row.total_retirement_savings for row in stress_projection],
            returns,
        )
        no_recast_liquid = _roll_forward_liquid(
            purchase.starting_liquid_investments, stress_cash_flows, returns
        )
        recast_cash_flows = []
        for index, row in enumerate(stress_projection):
            if row.year < recast.recast_model_year:
                improvement = 0.0
            elif row.year == recast.recast_model_year:
                improvement = recast.monthly_payment_reduction * (
                    scenario.household.months_per_year + 1 - scenario.recast.recast_month
                )
            else:
                improvement = recast.annual_cash_flow_improvement
            recast_cash_flows.append(stress_cash_flows[index] + improvement)
        recast_outflows = [
            recast.principal_paydown_applied + recast.recast_fee
            if row.year == recast.recast_model_year
            else 0.0
            for row in stress_projection
        ]
        recast_liquid = _roll_forward_liquid(
            purchase.starting_liquid_investments, recast_cash_flows, returns, recast_outflows
        )
        results.append(
            _stress_summary(
                scenario,
                name,
                "no_recast",
                no_recast_liquid,
                stress_retirement,
                recast.cash_flow_positive_after_recast,
            )
        )
        results.append(
            _stress_summary(
                scenario,
                name,
                "recast",
                recast_liquid,
                stress_retirement,
                recast.cash_flow_positive_after_recast,
            )
        )

    return results


def calculate_affordability_score(
    scenario: Scenario,
    projection: list[ProjectionYear],
    recast: RecastOutputs,
    recast_forecast: RecastForecast,
    stress_tests: list[StressTestResult],
) -> AffordabilityScore:
    months = scenario.household.months_per_year
    reserve_floor = scenario.recast.minimum_desired_liquid_reserve_floor
    score_path = "recast" if recast.active else "no_recast"
    cash_flows = (
        recast_forecast.recast_cash_flow
        if recast.active
        else recast_forecast.no_recast_cash_flow
    )
    liquid_assets = (
        recast_forecast.liquid_recast
        if recast.active
        else recast_forecast.liquid_no_recast
    )
    runways: list[float] = []
    for index, row in enumerate(projection):
        cash_flow_improvement = cash_flows[index] - row.annual_liquid_contribution_draw
        required_monthly_outflow = max(
            0.0,
            row.required_monthly_outflow - cash_flow_improvement / months,
        )
        runways.append(
            liquid_assets[index] / required_monthly_outflow
            if required_monthly_outflow > 0
            else 0.0
        )
    worst_monthly_cash_flow = min(cash_flows) / months
    min_liquid = min(liquid_assets)
    min_runway = min(runways)
    relevant_stress_tests = [item for item in stress_tests if item.path == score_path]
    stress_failures = sum(1 for item in relevant_stress_tests if item.falls_below_zero)
    stress_reserve_reviews = sum(
        1 for item in relevant_stress_tests if item.falls_below_reserve
    )

    cash_flow_component = clamp(50.0 + (worst_monthly_cash_flow / 2_000.0) * 50.0)
    liquidity_component = clamp((min_liquid / reserve_floor) * 100.0 if reserve_floor else 100.0)
    runway_component = clamp((min_runway / 36.0) * 100.0)
    stress_component = clamp(100.0 - 25.0 * stress_failures - 8.0 * stress_reserve_reviews)
    score = (
        cash_flow_component * 0.30
        + liquidity_component * 0.30
        + runway_component * 0.20
        + stress_component * 0.20
    )
    if score >= 85:
        label = "strong"
    elif score >= 70:
        label = "workable"
    elif score >= 50:
        label = "fragile"
    else:
        label = "unsafe"
    return AffordabilityScore(
        score=score,
        cash_flow_component=cash_flow_component,
        liquidity_component=liquidity_component,
        runway_component=runway_component,
        stress_component=stress_component,
        label=label,  # type: ignore[arg-type]
    )


def validate_scenario(
    scenario: Scenario,
    purchase: PurchaseOutputs,
    recast: RecastOutputs,
) -> list[ValidationCheck]:
    checks: list[ValidationCheck] = []

    def add(code: str, severity: str, message: str, field: str | None = None, value=None) -> None:
        checks.append(
            ValidationCheck(
                code=code,
                severity=severity,  # type: ignore[arg-type]
                message=message,
                field=field,
                value=value,
            )
        )

    add("schema_valid", "ok", "Scenario passed typed schema validation.")
    if purchase.portfolio_after_closing < 0:
        add(
            "portfolio_after_closing_negative",
            "error",
            "Cash-to-close exceeds starting portfolio plus modeled family loan.",
            "purchase.purchase_price",
            purchase.portfolio_after_closing,
        )
    else:
        add("portfolio_after_closing_nonnegative", "ok", "Portfolio remains nonnegative after closing.")
    if recast.principal_paydown_applied > recast.mortgage_balance_before_recast + 1e-6:
        add("recast_exceeds_balance", "error", "Recast paydown exceeds mortgage balance.")
    else:
        add("recast_principal_cap", "ok", "Recast paydown is capped by outstanding principal.")
    if recast.starting_liquid_after_recast < scenario.recast.minimum_desired_liquid_reserve_floor:
        add(
            "recast_liquidity_below_floor",
            "warning",
            "After-recast liquidity is below the desired reserve floor.",
            "recast.minimum_desired_liquid_reserve_floor",
            recast.starting_liquid_after_recast,
        )
    else:
        add("recast_liquidity_floor", "ok", "After-recast liquidity meets the desired reserve floor.")
    if scenario.monte_carlo.paths < 1_000:
        add(
            "mc_path_count_directional",
            "warning",
            "Monte Carlo path count is suitable for directional analysis, not tail precision.",
            "monte_carlo.paths",
            scenario.monte_carlo.paths,
        )
    if scenario.taxes.tax_mode == "estimated":
        add(
            "estimated_tax_scope",
            "warning",
            "Estimated tax mode covers federal/FICA and v1 NY/NYC local tax support; review assumptions before relying on after-tax cash flow.",
            "taxes.tax_mode",
            scenario.taxes.tax_mode,
        )
        residence_state, residence_city, jurisdiction_source = _tax_jurisdiction(scenario)
        if jurisdiction_source == "zip" and residence_state == "none":
            add(
                "zip_tax_jurisdiction_unsupported",
                "warning",
                "Residence ZIP is outside v1 state/local support, so estimated taxes include federal/FICA only.",
                "taxes.residence_zip",
                scenario.taxes.residence_zip,
            )
        if jurisdiction_source == "none" and not scenario.taxes.residence_zip:
            add(
                "zip_tax_jurisdiction_missing",
                "warning",
                "Enter a residence ZIP to infer supported state/local taxes; otherwise estimated taxes include federal/FICA unless manual jurisdiction fields are set.",
                "taxes.residence_zip",
                scenario.taxes.residence_zip,
            )
        if residence_city == "NYC" and residence_state != "NY":
            add(
                "nyc_requires_ny_state",
                "warning",
                "NYC local tax is only applied when New York is selected as the tax residence state.",
                "taxes.tax_residence_city",
                residence_city,
            )
        if residence_state == "NY":
            add(
                "ny_tax_directional",
                "warning",
                "NY/NYC tax is a directional bracket estimate and does not apply all resident-return worksheet mechanics.",
                "taxes.tax_residence_state",
                residence_state,
            )
    if not isfinite(purchase.monthly_mortgage_pi):
        add("mortgage_payment_invalid", "error", "Mortgage payment is not finite.")
    return checks


def _calculate_without_safe_price(scenario: Scenario) -> tuple[
    PurchaseOutputs,
    list[ProjectionYear],
    RecastOutputs,
    RecastForecast,
    list[StressTestResult],
    AffordabilityScore,
    list[ValidationCheck],
]:
    purchase = calculate_purchase_outputs(scenario)
    projection = build_projection(scenario, purchase)
    recast = calculate_recast_outputs(scenario, purchase, projection)
    recast_forecast = build_recast_forecast(scenario, projection, recast)
    stress_tests = calculate_stress_tests(scenario, purchase, projection, recast, recast_forecast)
    score = calculate_affordability_score(
        scenario, projection, recast, recast_forecast, stress_tests
    )
    checks = validate_scenario(scenario, purchase, recast)
    return purchase, projection, recast, recast_forecast, stress_tests, score, checks


def _year_zero_income_tax_wages(scenario: Scenario) -> tuple[float, float]:
    income = scenario.income
    gross_income = income.gross_income + _salary_step_increase(scenario, 0, income.income_growth)
    gross_income -= _part_time_reduction(scenario, 0, income.base_part_time_switch_year)
    gross_income = max(0.0, gross_income)
    pre_tax = income.employee_pre_tax_retirement + income.hsa_payroll_contribution
    other_pre_tax = income.other_pre_tax_payroll_deductions
    return gross_income, max(0.0, gross_income - pre_tax - other_pre_tax)


def _scenario_for_purchase_price(scenario: Scenario, purchase_price: float) -> Scenario:
    purchase = scenario.purchase.model_copy(update={"purchase_price": purchase_price})
    tax_updates: dict[str, float] = {}
    if scenario.purchase.purchase_price > 0 and scenario.taxes.property_tax_basis > 0:
        tax_basis_ratio = scenario.taxes.property_tax_basis / scenario.purchase.purchase_price
        tax_updates["property_tax_basis"] = purchase_price * tax_basis_ratio
    taxes = (
        scenario.taxes.model_copy(update=tax_updates)
        if tax_updates
        else scenario.taxes
    )
    return scenario.model_copy(
        update={
            "purchase": purchase,
            "taxes": taxes,
        },
        deep=True,
    )


def _scenario_clears_safe_price_threshold(
    scenario: Scenario,
    *,
    minimum_score: float,
) -> bool:
    _, _, _, _, _, score, checks = _calculate_without_safe_price(scenario)
    has_error = any(check.severity == "error" for check in checks)
    return not has_error and score.score >= minimum_score


def solve_safe_purchase_price(
    scenario: Scenario,
    *,
    minimum_score: float = 70.0,
    iterations: int = 36,
    max_search_price: float = 100_000_000.0,
) -> float:
    """Binary-search a safe purchase price under the current assumptions."""

    low = 0.0
    best = 0.0
    high = max(1.0, scenario.purchase.purchase_price)
    if _scenario_clears_safe_price_threshold(
        _scenario_for_purchase_price(scenario, high),
        minimum_score=minimum_score,
    ):
        best = high
        low = high
        while high < max_search_price:
            high = min(max_search_price, high * 2.0)
            if not _scenario_clears_safe_price_threshold(
                _scenario_for_purchase_price(scenario, high),
                minimum_score=minimum_score,
            ):
                break
            best = high
            low = high
            if high == max_search_price:
                return best

    for _ in range(iterations):
        mid = (low + high) / 2.0
        candidate = _scenario_for_purchase_price(scenario, mid)
        if _scenario_clears_safe_price_threshold(
            candidate,
            minimum_score=minimum_score,
        ):
            best = mid
            low = mid
        else:
            high = mid
    return best


def calculate_affordability(scenario: Scenario | None = None) -> AffordabilityOutputs:
    scenario = scenario or Scenario()
    purchase, projection, recast, recast_forecast, stress_tests, score, checks = (
        _calculate_without_safe_price(scenario)
    )
    safe_price = solve_safe_purchase_price(scenario)
    year_zero_gross, year_zero_tax_wages = _year_zero_income_tax_wages(scenario)
    tax_summary = calculate_tax_summary(scenario, year_zero_gross, year_zero_tax_wages)
    return AffordabilityOutputs(
        purchase=purchase,
        projection=projection,
        recast=recast,
        recast_comparison=build_recast_comparison(
            scenario, projection, recast, recast_forecast
        ),
        stress_tests=stress_tests,
        affordability_score=score,
        safe_purchase_price=safe_price,
        tax_summary=tax_summary,
        validation_checks=checks,
        metadata=CalculationMetadata(
            engine_version="0.1.0",
            calculated_at=datetime.now(timezone.utc).isoformat(),
            workbook_reconciliation_status="deterministic_reconciled",
        ),
    )
