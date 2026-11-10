"""Compatibility imports for the v0.2 URL architecture package."""

from .url_architecture_stage.service import (
    ARCHITECTURE_PATH,
    BASE_DIR,
    URL_ARCHITECTURE_PATH,
    build_url_architecture,
    run_v02_url_architecture,
)
from .url_architecture_stage.storage import load_json_file, save_json_file
from .url_architecture_stage.summary import build_url_summary, determine_url_strategy
from .url_architecture_stage.url_records import (
    build_url_record,
    build_url_records,
    normalize_url,
    validate_slug,
)
from .url_architecture_stage.validation import (
    validate_cluster_roots,
    validate_parent_relationships,
    validate_unique_slugs,
    validate_unique_urls,
    validate_url_architecture,
)

__all__ = [
    "ARCHITECTURE_PATH",
    "BASE_DIR",
    "URL_ARCHITECTURE_PATH",
    "build_url_architecture",
    "build_url_record",
    "build_url_records",
    "build_url_summary",
    "determine_url_strategy",
    "load_json_file",
    "normalize_url",
    "run_v02_url_architecture",
    "save_json_file",
    "validate_cluster_roots",
    "validate_parent_relationships",
    "validate_slug",
    "validate_unique_slugs",
    "validate_unique_urls",
    "validate_url_architecture",
]


if __name__ == "__main__":
    run_v02_url_architecture()
