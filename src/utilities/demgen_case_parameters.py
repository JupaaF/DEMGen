import json
from pathlib import Path
from typing import Any


def load_case_parameters(parameters_path: str | Path) -> dict[str, Any]:
    """Load the effective DEMGen settings for one generated case."""
    with Path(parameters_path).open(encoding="utf-8") as parameters_file:
        return json.load(parameters_file)
