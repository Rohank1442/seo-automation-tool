"""Read and write technical SEO JSON artifacts."""

import json
from pathlib import Path
from typing import Any


def load_json(file_path: Path) -> dict[str, Any]:
    """Load a JSON object from a required artifact path."""
    if not file_path.is_file():
        raise FileNotFoundError(f"Required file not found: {file_path}")
    with file_path.open("r", encoding="utf-8") as source:
        data = json.load(source)
    if not isinstance(data, dict):
        raise ValueError(f"Expected a JSON object in: {file_path}")
    return data


def save_json(data: dict[str, Any], file_path: Path) -> None:
    """Persist formatted JSON, creating parent directories when required."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with file_path.open("w", encoding="utf-8") as destination:
        json.dump(data, destination, indent=2, ensure_ascii=False)
