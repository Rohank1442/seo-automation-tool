"""Summarize v0.1 research outputs for pipeline responses and logs."""

from typing import Any, Dict, List


def build_research_summary(saved_clusters, all_cluster_keywords, competitor_data, content_gaps) -> Dict[str, Any]:
    """Return aggregate counts and a recommended cluster with page-level opportunities."""
    page_gaps = [
        (cluster_name, gap)
        for cluster_name, gaps in content_gaps.items()
        for gap in gaps
        if str(gap.get("scope", "page")).lower() == "page"
    ]
    counts = {
        cluster["name"]: {
            "page": 0,
            "high_priority": 0,
        }
        for cluster in saved_clusters
    }
    for cluster_name, gap in page_gaps:
        counts.setdefault(cluster_name, {"page": 0, "high_priority": 0})
        counts[cluster_name]["page"] += 1
        if str(gap.get("priority", "medium")).lower() == "high":
            counts[cluster_name]["high_priority"] += 1

    recommended = max(
        (name for name, values in counts.items() if values["page"]),
        key=lambda name: (counts[name]["high_priority"], counts[name]["page"]),
        default=None,
    )
    return {
        "clusters": len(saved_clusters),
        "keywords": sum(len(all_cluster_keywords.get(c["name"], [])) for c in saved_clusters),
        "competitors": sum(len(competitor_data.get(c["name"], [])) for c in saved_clusters),
        "content_gaps": sum(len(gaps) for gaps in content_gaps.values()),
        "high_priority_gaps": sum(
            1 for gaps in content_gaps.values()
            for gap in gaps
            if str(gap.get("priority", "")).lower() == "high"
        ),
        "page_opportunities": len(page_gaps),
        "recommended_cluster": recommended,
    }
