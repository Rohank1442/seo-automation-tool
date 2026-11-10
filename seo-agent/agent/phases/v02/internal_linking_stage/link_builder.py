"""Create hub-and-spoke and contextual related-page link recommendations."""

from typing import Any

from .page_data import get_anchor_text
from .relevance import calculate_page_similarity


def create_link(source_page: dict[str, Any], target_page: dict[str, Any], anchor_text: str,
                relationship: str, reason: str, priority: str) -> dict[str, Any]:
    """Build one link record in the established v0.2 artifact format."""
    return {
        "source_page_id": source_page.get("id", source_page.get("page_id")),
        "source_url": source_page["url"],
        "target_page_id": target_page.get("id", target_page.get("page_id")),
        "target_url": target_page["url"],
        "anchor_text": anchor_text,
        "relationship": relationship,
        "reason": reason,
        "priority": priority,
    }


def create_cluster_links(pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Link each cluster hub to its child pages and each child back to the hub."""
    links = []
    clusters = [page for page in pages if page.get("page_type") == "cluster"]
    for cluster in clusters:
        children = [page for page in pages if page.get("parent_page_id") == cluster.get("id", cluster.get("page_id"))]
        for child in children:
            links.append(create_link(child, cluster, cluster["title"], "cluster_parent",
                                     "The content page belongs to this topical cluster and should link back to its cluster hub.", "high"))
            links.append(create_link(cluster, child, get_anchor_text(child), "cluster_child",
                                     "The cluster page acts as a topical hub and should link to its supporting content pages.", "high"))
    return links


def create_related_links(pages: list[dict[str, Any]], minimum_similarity: float = 0.20) -> list[dict[str, Any]]:
    """Create bidirectional links for sufficiently similar pages in one cluster."""
    links = []
    content_pages = [page for page in pages if page.get("page_type") != "cluster"]
    for index, source in enumerate(content_pages):
        for target in content_pages[index + 1:]:
            if source.get("cluster") != target.get("cluster"):
                continue
            if calculate_page_similarity(source, target) < minimum_similarity:
                continue
            reason = "The pages have overlapping topical or search-intent signals and can provide useful contextual navigation for users."
            links.append(create_link(source, target, get_anchor_text(target), "related_content", reason, "medium"))
            links.append(create_link(target, source, get_anchor_text(source), "related_content", reason, "medium"))
    return links
