"""Validate URL uniqueness, parent references, and cluster root rules."""

from typing import Any


def validate_unique_urls(records: list[dict[str, Any]]) -> None:
    """Raise when multiple pages resolve to the same URL."""
    seen = {}
    for record in records:
        url, page_id = record["url"], record["page_id"]
        if url in seen:
            raise ValueError(f"Duplicate URL detected: {url} used by '{seen[url]}' and '{page_id}'.")
        seen[url] = page_id


def validate_unique_slugs(records: list[dict[str, Any]]) -> None:
    """Raise when multiple pages use the same slug."""
    seen = {}
    for record in records:
        slug, page_id = record["slug"], record["page_id"]
        if slug in seen:
            raise ValueError(f"Duplicate slug detected: '{slug}' used by '{seen[slug]}' and '{page_id}'.")
        seen[slug] = page_id


def validate_parent_relationships(records: list[dict[str, Any]]) -> None:
    """Ensure every non-null parent reference points to a page in the graph."""
    page_ids = {record["page_id"] for record in records}
    for record in records:
        parent_id = record.get("parent_page_id")
        if parent_id is not None and parent_id not in page_ids:
            raise ValueError(f"Page '{record['page_id']}' references missing parent '{parent_id}'.")


def validate_cluster_roots(records: list[dict[str, Any]]) -> None:
    """Require cluster pages to be indexable roots without a parent."""
    for record in records:
        if record.get("page_type") != "cluster":
            continue
        if record.get("parent_page_id") is not None:
            raise ValueError(f"Cluster page '{record['page_id']}' must not have a parent.")
        if not record.get("indexable", True):
            raise ValueError(f"Cluster page '{record['page_id']}' must be indexable.")


def validate_url_architecture(url_architecture: dict[str, Any]) -> None:
    """Run all final checks against the generated URL architecture object."""
    records = url_architecture.get("urls", [])
    if not records:
        raise ValueError("URL architecture contains no URLs.")
    validate_unique_urls(records)
    validate_unique_slugs(records)
    validate_parent_relationships(records)
    validate_cluster_roots(records)
