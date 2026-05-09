"""Run the default deterministic calculation and print JSON.

This script is useful before FastAPI dependencies are installed:

    python backend/run_calculation.py
"""

from __future__ import annotations

import json

from affordability.engine import calculate_affordability
from affordability.schemas import Scenario


if __name__ == "__main__":
    outputs = calculate_affordability(Scenario())
    print(json.dumps(outputs.model_dump(), indent=2))
