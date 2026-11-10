"""Deduplicate and validate the generated internal-link graph and summarize it."""

from typing import Any


def remove_duplicate_links(links: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep the first recommendation for each directed source-target pair."""
    unique = {}
    for link in links:
        key = (link["source_page_id"], link["target_page_id"])
        unique.setdefault(key, link)
    return list(unique.values())


def validate_links(links: list[dict[str, Any]], pages: list[dict[str, Any]]) -> None:
    """Raise when a link references an unknown page or links a page to itself."""
    page_ids = {page.get("id", page.get("page_id")) for page in pages}
    page_urls = {page.get("url") for page in pages}
    for link in links:
        source_id, target_id = link.get("source_page_id"), link.get("target_page_id")
        if source_id not in page_ids:
            raise ValueError(f"Invalid source page: {source_id}")
        if target_id not in page_ids:
            raise ValueError(f"Invalid target page: {target_id}")
        if source_id == target_id:
            raise ValueError(f"Self-link detected: {source_id}")
        if link.get("target_url") not in page_urls:
            raise ValueError(f"Invalid target URL for page {target_id}: {link.get('target_url')}")


def build_summary(pages: list[dict[str, Any]], links: list[dict[str, Any]]) -> dict[str, Any]:
    """Return page, link, and graph-connectivity counts for the artifact."""
    cluster_count = sum(page.get("page_type") == "cluster" for page in pages)
    inbound = {page.get("id", page.get("page_id")): 0 for page in pages}
    outbound = dict.fromkeys(inbound, 0)
    for link in links:
        outbound[link["source_page_id"]] += 1
        inbound[link["target_page_id"]] += 1
    return {
        "total_pages": len(pages),
        "cluster_pages": cluster_count,
        "content_pages": len(pages) - cluster_count,
        "total_links": len(links),
        "average_links_per_page": round(len(links) / len(pages), 2) if pages else 0,
        "pages_without_outbound_links": [page_id for page_id, count in outbound.items() if count == 0],
        "pages_without_inbound_links": [page_id for page_id, count in inbound.items() if count == 0],
    }
