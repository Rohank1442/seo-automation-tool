"""Compatibility imports for the v0.2 site foundation package."""

from pathlib import Path

from .site_foundation_stage.inference import (
    _collect_cluster_text,
    _collect_project_text,
    build_site_profile,
    infer_primary_entities,
    infer_site_model,
)
from .site_foundation_stage.research import load_v01_research, validate_v01_research
from .site_foundation_stage.service import run_v02_site_foundation
from .site_foundation_stage.storage import save_site_profile

# Keep the previous default paths available for existing scripts.
V01_OUTPUT_PATH = "outputs/page_opportunities.json"
V02_OUTPUT_DIR = "outputs/v02"
SITE_PROFILE_PATH = "outputs/v02/site_profile.json"


def ensure_v02_output_directory(output_dir=V02_OUTPUT_DIR):
    """Create the v0.2 output directory when called by legacy integrations."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)


__all__ = [
    "SITE_PROFILE_PATH",
    "V01_OUTPUT_PATH",
    "V02_OUTPUT_DIR",
    "_collect_cluster_text",
    "_collect_project_text",
    "build_site_profile",
    "ensure_v02_output_directory",
    "infer_primary_entities",
    "infer_site_model",
    "load_v01_research",
    "run_v02_site_foundation",
    "save_site_profile",
    "validate_v01_research",
]


if __name__ == "__main__":
    run_v02_site_foundation()
