import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from affordability.engine import (  # noqa: E402
    build_projection,
    calculate_affordability,
    calculate_purchase_outputs,
    calculate_recast_outputs,
    mortgage_balance_after_payments,
    pmt,
    solve_safe_purchase_price,
)
from affordability.schemas import Scenario  # noqa: E402


class EngineTests(unittest.TestCase):
    def assertClose(self, actual, expected, places=6):
        self.assertTrue(
            math.isclose(actual, expected, rel_tol=0, abs_tol=10 ** (-places)),
            f"{actual!r} != {expected!r}",
        )

    def test_pmt_matches_workbook(self):
        monthly_rate = 0.045 / 12
        payment = pmt(monthly_rate, 360, 1_185_000)
        self.assertClose(payment, 6004.220921436686)

    def test_zero_rate_payment_and_balance(self):
        self.assertEqual(pmt(0, 360, 360_000), 1_000)
        self.assertEqual(mortgage_balance_after_payments(360_000, 0, 1_000, 12), 348_000)

    def test_purchase_reconciliation_targets(self):
        purchase = calculate_purchase_outputs(Scenario())
        self.assertClose(purchase.down_payment_amount, 790_000)
        self.assertClose(purchase.mortgage_principal, 1_185_000)
        self.assertClose(purchase.buyer_closing_costs, 49_375)
        self.assertClose(purchase.gross_upfront_cash, 839_375)
        self.assertClose(purchase.net_cash_from_portfolio, 839_375)
        self.assertClose(purchase.portfolio_after_closing, 1_210_625)
        self.assertClose(purchase.starting_liquid_investments, 1_029_031.25)
        self.assertClose(purchase.starting_retirement_nonliquid, 181_593.75)
        self.assertClose(purchase.monthly_mortgage_pi, 6004.220921436686)
        self.assertClose(purchase.monthly_ownership_cost, 11170.887588103351)
        self.assertClose(purchase.monthly_required_outflow, 21970.887588103353)
        self.assertClose(purchase.liquidity_reserve_target, 363650.6510572402)

    def test_projection_reconciliation_targets(self):
        scenario = Scenario()
        purchase = calculate_purchase_outputs(scenario)
        projection = build_projection(scenario, purchase)
        self.assertClose(projection[0].annual_spendable_cash_before_housing, 263_500)
        self.assertClose(projection[3].annual_liquid_contribution_draw, -19_192.99170844024)
        self.assertClose(projection[30].liquid_real, 3_118_276.084415098)
        self.assertClose(projection[30].retirement_nonliquid_real, 572_628.7760156414)
        self.assertClose(projection[30].runway_months, 150.63026527859915)

    def test_salary_step_increase_starts_in_selected_year(self):
        base = Scenario()
        scenario = base.model_copy(
            update={
                "income": base.income.model_copy(
                    update={
                        "income_growth": 0.0,
                        "part_time_switch_active": False,
                        "salary_step_increase_year": 5,
                        "salary_step_increase_amount": 50_000.0,
                    }
                )
            },
            deep=True,
        )
        base_projection = build_projection(
            base.model_copy(
                update={
                    "income": base.income.model_copy(
                        update={"income_growth": 0.0, "part_time_switch_active": False}
                    )
                },
                deep=True,
            )
        )
        projection = build_projection(scenario)

        self.assertClose(
            projection[4].annual_spendable_cash_before_housing,
            base_projection[4].annual_spendable_cash_before_housing,
        )
        self.assertClose(
            projection[5].annual_spendable_cash_before_housing,
            base_projection[5].annual_spendable_cash_before_housing + 31_000,
        )
        self.assertClose(
            projection[6].annual_spendable_cash_before_housing,
            base_projection[6].annual_spendable_cash_before_housing + 31_000,
        )

    def test_recast_reconciliation_targets(self):
        scenario = Scenario()
        purchase = calculate_purchase_outputs(scenario)
        projection = build_projection(scenario, purchase)
        recast = calculate_recast_outputs(scenario, purchase, projection)
        self.assertEqual(recast.recast_model_year, 1)
        self.assertEqual(recast.months_elapsed_pre_recast, 12)
        self.assertEqual(recast.remaining_term_months, 348)
        self.assertClose(recast.mortgage_balance_before_recast, 1165883.263703539)
        self.assertClose(recast.principal_paydown_applied, 200_000)
        self.assertClose(recast.new_monthly_pi_after_recast, 4974.234282403256)
        self.assertClose(recast.monthly_payment_reduction, 1029.98663903343)
        self.assertClose(recast.annual_cash_flow_improvement, 12359.83966840116)
        self.assertClose(recast.breakeven_years, 16.2218932752496)
        self.assertClose(recast.starting_liquid_after_recast, 828531.25)
        self.assertClose(recast.worst_monthly_cash_flow_recast, -569.4293366699225)
        self.assertFalse(recast.cash_flow_positive_after_recast)

    def test_recast_comparison_reconciliation_targets(self):
        outputs = calculate_affordability(Scenario())
        comparison = outputs.recast_comparison
        self.assertClose(comparison.no_recast_monthly_pi, 6004.220921436686)
        self.assertClose(comparison.recast_monthly_pi, 4974.234282403256)
        self.assertClose(comparison.no_recast_worst_monthly_cash_flow, -1599.4159757033533)
        self.assertClose(comparison.recast_worst_monthly_cash_flow, -569.4293366699225)
        self.assertClose(comparison.no_recast_starting_liquid_assets, 1_029_031.25)
        self.assertClose(comparison.recast_starting_liquid_assets, 828_531.25)
        self.assertClose(comparison.no_recast_year_30_liquid_real, 3_118_276.084415098)
        self.assertClose(comparison.recast_year_30_liquid_real, 2_994_989.9756525327)

    def test_affordability_score_uses_selected_recast_path(self):
        outputs = calculate_affordability(Scenario())
        expected_cash_flow_component = max(
            0.0,
            min(100.0, 50.0 + (outputs.recast.worst_monthly_cash_flow_recast / 2_000.0) * 50.0),
        )

        self.assertTrue(outputs.recast.active)
        self.assertClose(
            outputs.affordability_score.cash_flow_component,
            expected_cash_flow_component,
        )

    def test_zero_recast_month_and_zero_paydown_match_no_recast(self):
        base = Scenario()
        scenario = base.model_copy(
            update={
                "recast": base.recast.model_copy(
                    update={"recast_month": 0, "one_time_principal_paydown": 0.0}
                )
            },
            deep=True,
        )
        outputs = calculate_affordability(scenario)

        self.assertFalse(outputs.recast.active)
        self.assertClose(outputs.recast.principal_paydown_applied, 0.0)
        self.assertClose(outputs.recast.recast_fee, 0.0)
        self.assertClose(outputs.recast.new_monthly_pi_after_recast, outputs.recast.original_monthly_pi)
        self.assertClose(outputs.recast.monthly_payment_reduction, 0.0)
        self.assertClose(
            outputs.recast.starting_liquid_after_recast,
            outputs.recast.starting_liquid_before_recast,
        )
        comparison = outputs.recast_comparison
        self.assertClose(comparison.recast_monthly_pi, comparison.no_recast_monthly_pi)
        self.assertClose(
            comparison.recast_starting_liquid_assets,
            comparison.no_recast_starting_liquid_assets,
        )
        self.assertClose(
            comparison.recast_year_30_liquid_real,
            comparison.no_recast_year_30_liquid_real,
        )

    def test_safe_purchase_price_expands_beyond_legacy_static_bound(self):
        base = Scenario()
        scenario = base.model_copy(
            update={
                "income": base.income.model_copy(
                    update={"gross_income": 5_000_000.0, "part_time_switch_active": False}
                ),
                "savings": base.savings.model_copy(update={"starting_portfolio": 3_000_000.0}),
            },
            deep=True,
        )
        legacy_static_bound = max(
            scenario.purchase.purchase_price * 2.0,
            scenario.savings.starting_portfolio * 1.5,
        )

        self.assertGreater(solve_safe_purchase_price(scenario), legacy_static_bound)

    def test_safe_purchase_price_scales_property_tax_basis(self):
        base = Scenario()
        scenario = base.model_copy(
            update={
                "income": base.income.model_copy(
                    update={"gross_income": 2_000_000.0, "part_time_switch_active": False}
                ),
                "savings": base.savings.model_copy(update={"starting_portfolio": 10_000_000.0}),
            },
            deep=True,
        )
        zero_property_tax = scenario.model_copy(
            update={"taxes": scenario.taxes.model_copy(update={"property_tax_basis": 0.0})},
            deep=True,
        )
        high_property_tax = scenario.model_copy(
            update={"taxes": scenario.taxes.model_copy(update={"property_tax_rate": 0.10})},
            deep=True,
        )

        self.assertLess(
            solve_safe_purchase_price(high_property_tax),
            solve_safe_purchase_price(zero_property_tax),
        )

    def test_calculate_affordability_shape(self):
        outputs = calculate_affordability(Scenario())
        self.assertEqual(len(outputs.projection), 31)
        self.assertGreater(len(outputs.stress_tests), 1)
        self.assertGreater(outputs.safe_purchase_price, 0)
        self.assertEqual(outputs.tax_summary.tax_mode, "take_home_rate")
        self.assertEqual(outputs.tax_summary.jurisdiction_source, "none")
        self.assertClose(outputs.tax_summary.effective_take_home_rate, 0.62)
        self.assertClose(outputs.tax_summary.total_effective_tax_rate, 0.38)
        self.assertEqual(outputs.tax_summary.tax_rate_details[0].label, "Manual take-home override")
        self.assertTrue(any(check.code == "schema_valid" for check in outputs.validation_checks))
        self.assertEqual(outputs.metadata.engine_version, "0.1.0")
        self.assertEqual(
            outputs.metadata.workbook_reconciliation_status, "deterministic_reconciled"
        )

    def test_estimated_tax_mode_changes_take_home_rate_by_residence(self):
        base = Scenario()
        federal_only = base.model_copy(
            update={
                "taxes": base.taxes.model_copy(
                    update={"tax_mode": "estimated", "tax_residence_state": "none"}
                )
            },
            deep=True,
        )
        nyc = base.model_copy(
            update={
                "taxes": base.taxes.model_copy(
                    update={
                        "tax_mode": "estimated",
                        "tax_residence_state": "NY",
                        "tax_residence_city": "NYC",
                    }
                )
            },
            deep=True,
        )
        federal_outputs = calculate_affordability(federal_only)
        nyc_outputs = calculate_affordability(nyc)

        self.assertEqual(federal_outputs.tax_summary.tax_mode, "estimated")
        self.assertGreater(federal_outputs.tax_summary.federal_income_tax, 0)
        self.assertGreater(federal_outputs.tax_summary.payroll_tax, 0)
        self.assertEqual(federal_outputs.tax_summary.state_income_tax, 0)
        self.assertGreater(federal_outputs.tax_summary.total_effective_tax_rate, 0)
        self.assertLess(federal_outputs.tax_summary.total_effective_tax_rate, 1)
        federal_rates = {
            detail.label: detail for detail in federal_outputs.tax_summary.tax_rate_details
        }
        self.assertIn("Federal income", federal_rates)
        self.assertIn("Employee payroll", federal_rates)
        self.assertGreater(federal_rates["Federal income"].marginal_rate, 0)
        self.assertGreater(federal_rates["Employee payroll"].effective_rate, 0)
        self.assertGreater(nyc_outputs.tax_summary.state_income_tax, 0)
        self.assertGreater(nyc_outputs.tax_summary.city_income_tax, 0)
        nyc_rates = {detail.label: detail for detail in nyc_outputs.tax_summary.tax_rate_details}
        self.assertIn("NY state income", nyc_rates)
        self.assertIn("NYC resident income", nyc_rates)
        self.assertGreater(nyc_rates["NY state income"].marginal_rate, 0)
        self.assertGreater(nyc_rates["NYC resident income"].marginal_rate, 0)
        self.assertLess(
            nyc_outputs.tax_summary.effective_take_home_rate,
            federal_outputs.tax_summary.effective_take_home_rate,
        )
        self.assertTrue(
            any(check.code == "estimated_tax_scope" for check in nyc_outputs.validation_checks)
        )

    def test_estimated_tax_mode_infers_tax_jurisdiction_from_zip(self):
        base = Scenario()
        nyc = base.model_copy(
            update={
                "taxes": base.taxes.model_copy(
                    update={"tax_mode": "estimated", "residence_zip": "10001"}
                )
            },
            deep=True,
        )
        ny_state = base.model_copy(
            update={
                "taxes": base.taxes.model_copy(
                    update={"tax_mode": "estimated", "residence_zip": "14604"}
                )
            },
            deep=True,
        )
        unsupported = base.model_copy(
            update={
                "taxes": base.taxes.model_copy(
                    update={"tax_mode": "estimated", "residence_zip": "90210"}
                )
            },
            deep=True,
        )

        nyc_outputs = calculate_affordability(nyc)
        ny_state_outputs = calculate_affordability(ny_state)
        unsupported_outputs = calculate_affordability(unsupported)

        self.assertEqual(nyc_outputs.tax_summary.tax_residence_state, "NY")
        self.assertEqual(nyc_outputs.tax_summary.tax_residence_city, "NYC")
        self.assertEqual(nyc_outputs.tax_summary.jurisdiction_source, "zip")
        self.assertGreater(nyc_outputs.tax_summary.city_income_tax, 0)
        self.assertEqual(ny_state_outputs.tax_summary.tax_residence_state, "NY")
        self.assertEqual(ny_state_outputs.tax_summary.tax_residence_city, "none")
        self.assertGreater(ny_state_outputs.tax_summary.state_income_tax, 0)
        self.assertEqual(ny_state_outputs.tax_summary.city_income_tax, 0)
        self.assertEqual(unsupported_outputs.tax_summary.tax_residence_state, "none")
        self.assertEqual(unsupported_outputs.tax_summary.jurisdiction_source, "zip")
        self.assertEqual(unsupported_outputs.tax_summary.state_income_tax, 0)
        self.assertTrue(
            any(
                check.code == "zip_tax_jurisdiction_unsupported"
                for check in unsupported_outputs.validation_checks
            )
        )

    def test_high_inflation_stress_reconciliation_targets(self):
        outputs = calculate_affordability(Scenario())
        high_inflation = {
            result.path: result
            for result in outputs.stress_tests
            if result.scenario == "High inflation"
        }
        self.assertClose(high_inflation["no_recast"].year_30_liquid_assets, 222048.5253629369)
        self.assertClose(high_inflation["recast"].year_30_liquid_assets, -36552.419328572985)
        self.assertFalse(high_inflation["no_recast"].falls_below_zero)
        self.assertTrue(high_inflation["recast"].falls_below_zero)


if __name__ == "__main__":
    unittest.main()
