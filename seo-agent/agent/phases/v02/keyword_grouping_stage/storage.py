"""Read and write the research and grouping JSON artifacts."""

import json
from pathlib import Path
from typing import Any


def load_json_file(path: str | Path) -> dict[str, Any]:
    """Load a JSON object and report missing, malformed, or wrong-shaped data."""
    source_path = Path(path)
    if not source_path.is_file():
        raise FileNotFoundError(f"Required file not found: {source_path}")
    try:
        with source_path.open("r", encoding="utf-8") as source:
            data = json.load(source)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON file: {source_path}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"Expected a JSON object in: {source_path}")
    return data


def save_keyword_groups(data: dict[str, Any], output_path: str | Path) -> None:
    """Persist grouping results as formatted UTF-8 JSON."""
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8") as output:
        json.dump(data, output, indent=2, ensure_ascii=False)
