import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from affordability.schemas import Scenario  # noqa: E402
from affordability.simulation import simulate_scenario  # noqa: E402


class SimulationTests(unittest.TestCase):
    def test_simulation_is_seed_reproducible(self):
        first = simulate_scenario(Scenario())
        second = simulate_scenario(Scenario())
        self.assertEqual(
            first["no_recast"].percentiles_real,
            second["no_recast"].percentiles_real,
        )

    def test_percentiles_are_ordered(self):
        result = simulate_scenario(Scenario())["no_recast"].percentiles_real
        ordered_keys = ["p5", "p10", "p15", "p25", "p50", "p75", "p85", "p90", "p95"]
        values = [result[key] for key in ordered_keys]
        self.assertEqual(values, sorted(values))

    def test_breach_probabilities_are_probabilities(self):
        summary = simulate_scenario(Scenario())["recast"]
        for value in [
            summary.probability_ever_at_or_below_zero,
            summary.probability_ever_below_250k,
            summary.probability_ever_below_500k,
            summary.probability_ever_below_750k,
        ]:
            self.assertGreaterEqual(value, 0)
            self.assertLessEqual(value, 1)


if __name__ == "__main__":
    unittest.main()
