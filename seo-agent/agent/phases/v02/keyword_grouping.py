"""Compatibility imports for the v0.2 semantic keyword-grouping package."""

from .keyword_grouping_stage.grouping import build_keyword_groups, group_cluster_keywords
from .keyword_grouping_stage.keywords import (
    build_keyword_lookup,
    extract_cluster_keywords,
    normalize_keyword,
)
from .keyword_grouping_stage.prompt_builder import build_grouping_prompt
from .keyword_grouping_stage.service import run_v02_keyword_grouping
from .keyword_grouping_stage.storage import load_json_file, save_keyword_groups
from .keyword_grouping_stage.validation import enrich_groups, validate_grouping

# Keep the previous public helper available to scripts importing this module.
def load_v01_research(research_path="outputs/page_opportunities.json"):
    """Load structured v0.1 research using the shared artifact reader."""
    return load_json_file(research_path)


__all__ = [
    "build_grouping_prompt",
    "build_keyword_groups",
    "build_keyword_lookup",
    "enrich_groups",
    "extract_cluster_keywords",
    "group_cluster_keywords",
    "load_json_file",
    "load_v01_research",
    "normalize_keyword",
    "run_v02_keyword_grouping",
    "save_keyword_groups",
    "validate_grouping",
]


if __name__ == "__main__":
    run_v02_keyword_grouping()
