"""Load and validate the v0.1 research contract required by v0.2."""

import json
from pathlib import Path
from typing import Any


def load_v01_research(research_path: str | Path = "outputs/page_opportunities.json") -> dict[str, Any]:
    """Read the v0.1 JSON object, reporting missing or malformed research clearly."""
    source_path = Path(research_path)
    if not source_path.is_file():
        raise FileNotFoundError(
            f"v0.1 output was not found: {source_path}\nRun v0.1 research before starting v0.2."
        )
    try:
        with source_path.open("r", encoding="utf-8") as source:
            data = json.load(source)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in v0.1 output: {source_path}") from exc
    if not isinstance(data, dict):
        raise ValueError("v0.1 page_opportunities.json must contain a JSON object.")
    return data


def validate_v01_research(research: dict[str, Any]) -> None:
    """Check the minimum project and cluster data needed for site setup."""
    for field in ("project", "clusters"):
        if field not in research:
            raise ValueError(f"Required v0.1 field is missing: '{field}'")
    if not isinstance(research["project"], dict):
        raise ValueError("v0.1 'project' field must be an object.")
    clusters = research["clusters"]
    if not isinstance(clusters, list):
        raise ValueError("v0.1 'clusters' field must be a list.")
    if not clusters:
        raise ValueError("v0.1 contains no topic clusters. v0.2 cannot build a site architecture without clusters.")
