"""Determine URL strategy and summarize generated routes."""

from typing import Any


def determine_url_strategy(architecture: dict[str, Any]) -> str:
    """Select flat URLs for new sites and preservation URLs otherwise."""
    return "flat_root_level" if architecture.get("site_status") == "brand_new" else "existing_site_preservation"


def build_url_summary(records: list[dict[str, Any]]) -> dict[str, int]:
    """Count total, cluster, and indexable URLs."""
    cluster_count = sum(record.get("page_type") == "cluster" for record in records)
    indexable_count = sum(record.get("indexable", True) for record in records)
    return {
        "total_urls": len(records),
        "cluster_urls": cluster_count,
        "content_urls": len(records) - cluster_count,
        "indexable_urls": indexable_count,
        "non_indexable_urls": len(records) - indexable_count,
    }
