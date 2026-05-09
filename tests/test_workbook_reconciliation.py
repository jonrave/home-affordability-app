import json
import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from affordability.engine import calculate_affordability  # noqa: E402
from affordability.schemas import Scenario  # noqa: E402


FIXTURE_PATH = ROOT / "tests" / "fixtures" / "workbook_reconciliation_targets.json"

COUNTER_FIELDS = {
    "year",
    "recast_model_year",
    "months_elapsed_pre_recast",
    "remaining_term_months",
}
MONTH_FIELDS = {"runway_months"}
YEAR_FIELDS = {"breakeven_years"}
FACTOR_FIELDS = {"inflation_factor"}


class WorkbookReconciliationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.targets = json.loads(FIXTURE_PATH.read_text())
        cls.outputs = calculate_affordability(Scenario())
        cls.tolerances = cls.targets["tolerances"]

    def assertCloseTarget(self, actual, expected, field):
        if field in FACTOR_FIELDS:
            tolerance = self.tolerances["factor_abs"]
        elif field in COUNTER_FIELDS or field in MONTH_FIELDS:
            tolerance = self.tolerances["months_abs"]
        elif field in YEAR_FIELDS:
            tolerance = self.tolerances["years_abs"]
        else:
            tolerance = self.tolerances["currency_abs"]

        self.assertTrue(
            math.isclose(float(actual), float(expected), rel_tol=0, abs_tol=tolerance),
            f"{field}: app={actual!r}, workbook={expected!r}, tolerance={tolerance}",
        )

    def test_purchase_outputs_reconcile_to_workbook(self):
        actual = self.outputs.purchase.model_dump()
        for field, expected in self.targets["purchase"].items():
            self.assertCloseTarget(actual[field], expected, field)

    def test_year_by_year_projection_reconciles_to_workbook(self):
        actual_rows = [row.model_dump() for row in self.outputs.projection]
        expected_rows = self.targets["projection"]

        self.assertEqual(len(actual_rows), len(expected_rows))
        for index, expected_row in enumerate(expected_rows):
            actual_row = actual_rows[index]
            for field, expected in expected_row.items():
                self.assertCloseTarget(actual_row[field], expected, field)

    def test_recast_outputs_reconcile_to_workbook(self):
        actual = self.outputs.recast.model_dump()
        for field, expected in self.targets["recast"].items():
            if isinstance(expected, bool):
                self.assertEqual(actual[field], expected, field)
            else:
                self.assertCloseTarget(actual[field], expected, field)

    def test_deterministic_stress_outputs_reconcile_to_workbook(self):
        actual = {
            (item.scenario, item.path): item.model_dump()
            for item in self.outputs.stress_tests
        }
        expected = {
            (item["scenario"], item["path"]): item
            for item in self.targets["stress_tests"]
        }

        self.assertEqual(set(actual), set(expected))
        for key, expected_item in expected.items():
            actual_item = actual[key]
            for field, expected_value in expected_item.items():
                if field in {"scenario", "path", "takeaway"}:
                    self.assertEqual(actual_item[field], expected_value, field)
                elif isinstance(expected_value, bool):
                    self.assertEqual(actual_item[field], expected_value, field)
                else:
                    self.assertCloseTarget(actual_item[field], expected_value, field)


if __name__ == "__main__":
    unittest.main()
