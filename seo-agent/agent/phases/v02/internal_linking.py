"""Compatibility imports for the v0.2 internal-linking stage package."""

from .internal_linking_stage.graph import build_summary, remove_duplicate_links, validate_links
from .internal_linking_stage.link_builder import create_cluster_links, create_link, create_related_links
from .internal_linking_stage.page_data import extract_pages, get_anchor_text
from .internal_linking_stage.relevance import (
    calculate_page_similarity,
    keyword_similarity,
    keyword_tokens,
    normalize_text,
)
from .internal_linking_stage.service import main
from .internal_linking_stage.storage import load_json, save_json

__all__ = [
    "build_summary",
    "calculate_page_similarity",
    "create_cluster_links",
    "create_link",
    "create_related_links",
    "extract_pages",
    "get_anchor_text",
    "keyword_similarity",
    "keyword_tokens",
    "load_json",
    "main",
    "normalize_text",
    "remove_duplicate_links",
    "save_json",
    "validate_links",
]


if __name__ == "__main__":
    main()
