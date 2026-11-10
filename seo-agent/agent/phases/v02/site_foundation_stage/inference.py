"""Apply deterministic heuristics to infer the high-level SiteProfile."""

from typing import Any


def _collect_project_text(research: dict[str, Any]) -> str:
    """Combine project-level descriptive fields for model classification."""
    project = research.get("project", {})
    values = [project.get(key, "") for key in (
        "core_topic", "target_audience", "site_goal", "geo_scope", "constraints",
    )]
    return " ".join(str(value) for value in values if value).lower()


def _collect_cluster_text(research: dict[str, Any]) -> str:
    """Combine cluster names and descriptions for classification signals."""
    values = []
    for cluster in research.get("clusters", []):
        if isinstance(cluster, dict):
            values.extend((str(cluster.get("name", "")), str(cluster.get("description", ""))))
    return " ".join(values).lower()


def infer_site_model(research: dict[str, Any]) -> str:
    """Classify the website as content, ecommerce, marketplace, social, SaaS, or hybrid."""
    text = _collect_project_text(research) + " " + _collect_cluster_text(research)
    signals = {
        "ecommerce": ("shop", "shopping", "product", "products", "buy", "store", "clothing", "fashion"),
        "social": ("social", "community", "creator", "creators", "followers", "following", "profile", "post", "posts", "reels", "user-generated"),
        "marketplace": ("marketplace", "seller", "sellers", "buyers", "vendors", "listing", "listings"),
        "saas": ("software", "platform", "subscription", "dashboard", "workflow", "automation", "tool", "tools"),
        "content": ("blog", "guide", "guides", "article", "articles", "content", "information", "education"),
    }
    scores = {model: sum(term in text for term in terms) for model, terms in signals.items()}
    if (scores["social"] >= 2 and scores["ecommerce"] >= 2) or (
        scores["marketplace"] >= 2 and scores["social"] >= 2
    ):
        return "hybrid"
    highest_model = max(scores, key=scores.get)
    return "content" if scores[highest_model] == 0 else highest_model


def infer_primary_entities(research: dict[str, Any]) -> list[str]:
    """Use distinct research cluster names as the initial primary entities."""
    entities = []
    for cluster in research.get("clusters", []):
        if not isinstance(cluster, dict) or not cluster.get("name"):
            continue
        name = str(cluster["name"]).strip()
        if name and name not in entities:
            entities.append(name)
    return entities


def build_site_profile(research: dict[str, Any]) -> dict[str, Any]:
    """Build the JSON-serializable profile consumed by later v0.2 stages."""
    project = research.get("project", {})
    return {
        "site_model": infer_site_model(research),
        "primary_purpose": project.get("site_goal", ""),
        "target_audience": project.get("target_audience", ""),
        "primary_topic": project.get("core_topic", ""),
        "geo_scope": project.get("geo_scope", ""),
        "constraints": project.get("constraints", ""),
        "primary_entities": infer_primary_entities(research),
        "cluster_count": len(research.get("clusters", [])),
        "source": "v01/page_opportunities.json",
        "version": "0.2",
    }
