"""Read and write the JSON artifacts used by the group-audit stage."""

import json
from pathlib import Path
from typing import Any


def load_json(path: str | Path) -> dict[str, Any]:
    """Load a JSON object, reporting a clear error for missing files."""
    source_path = Path(path)
    if not source_path.is_file():
        raise FileNotFoundError(f"File not found: {source_path}")
    with source_path.open("r", encoding="utf-8") as source:
        data = json.load(source)
    if not isinstance(data, dict):
        raise ValueError(f"Expected a JSON object in {source_path}")
    return data


def save_json(path: str | Path, data: dict[str, Any]) -> None:
    """Save a JSON object and create its parent directory if needed."""
    target_path = Path(path)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    with target_path.open("w", encoding="utf-8") as target:
        json.dump(data, target, indent=2, ensure_ascii=False)
