import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from affordability.schemas import Scenario  # noqa: E402


class ApiContractTests(unittest.TestCase):
    def test_default_scenario_serializes(self):
        payload = Scenario().model_dump()
        self.assertIn("income", payload)
        self.assertIn("purchase", payload)
        self.assertIn("monte_carlo", payload)

    def test_api_module_imports_without_fastapi_installed(self):
        from affordability import api  # noqa: WPS433

        self.assertTrue(hasattr(api, "create_app"))

    def test_create_app_configures_local_cors(self):
        from affordability import api  # noqa: WPS433

        if api.FastAPI is None:
            self.skipTest("FastAPI is not installed")

        app = api.create_app()
        middleware_names = [middleware.cls.__name__ for middleware in app.user_middleware]
        self.assertIn("CORSMiddleware", middleware_names)


if __name__ == "__main__":
    unittest.main()
