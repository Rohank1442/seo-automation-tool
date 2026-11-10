"""Read and write URL architecture JSON artifacts."""

import json
from pathlib import Path
from typing import Any


def load_json_file(path: Path) -> dict[str, Any]:
    """Load a JSON object from a required path."""
    if not path.is_file():
        raise FileNotFoundError(f"Required file not found: {path}")
    with path.open("r", encoding="utf-8") as source:
        data = json.load(source)
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object in: {path}")
    return data


def save_json_file(path: Path, data: dict[str, Any]) -> None:
    """Save formatted JSON and create the destination directory."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as destination:
        json.dump(data, destination, indent=2, ensure_ascii=False)
