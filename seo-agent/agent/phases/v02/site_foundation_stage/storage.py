"""Persist the v0.2 SiteProfile artifact."""

import json
from pathlib import Path
from typing import Any


def save_site_profile(profile: dict[str, Any], output_path: str | Path = "outputs/v02/site_profile.json") -> None:
    """Write a formatted UTF-8 profile and create its parent directory."""
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8") as output:
        json.dump(profile, output, indent=2, ensure_ascii=False)
