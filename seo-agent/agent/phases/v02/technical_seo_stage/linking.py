"""Summarize inbound and outbound link participation for each URL."""

from typing import Any


def build_internal_linking_checks(internal_linking: dict[str, Any], pages: list[dict[str, Any]]) -> dict[str, Any]:
    """Count links per URL page and flag isolated pages in either direction."""
    links = internal_linking.get("links", [])
    inbound = {page["page_id"]: 0 for page in pages}
    outbound = {page["page_id"]: 0 for page in pages}
    for link in links:
        source, target = link.get("source_page_id"), link.get("target_page_id")
        if source in outbound:
            outbound[source] += 1
        if target in inbound:
            inbound[target] += 1
    return {
        "total_links": len(links),
        "pages_without_inbound_links": [page_id for page_id, count in inbound.items() if count == 0],
        "pages_without_outbound_links": [page_id for page_id, count in outbound.items() if count == 0],
        "graph_valid": all(inbound.values()) and all(outbound.values()),
    }
