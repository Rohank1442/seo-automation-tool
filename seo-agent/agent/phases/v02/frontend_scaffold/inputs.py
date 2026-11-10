"""Load the v0.2 artifacts required to build a static site scaffold."""

import json
from pathlib import Path


REQUIRED_ARTIFACTS = (
    "site_architecture.json",
    "url_architecture.json",
    "internal_linking.json",
    "technical_seo.json",
)


def load_inputs(project_outputs: Path) -> dict:
    """Read validated v0.2 input artifacts from one project's output tree."""
    v02_dir = Path(project_outputs) / "v02"
    loaded = {}
    for filename in REQUIRED_ARTIFACTS:
        path = v02_dir / filename
        if not path.is_file():
            raise FileNotFoundError(f"Required v0.2 artifact not found: {path}")
        with path.open("r", encoding="utf-8") as source:
            loaded[filename.removesuffix(".json")] = json.load(source)
    return loaded
