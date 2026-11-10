"""Validate model groupings and attach source-of-truth keyword metrics."""

from typing import Any

from .keywords import build_keyword_lookup, normalize_keyword


def validate_grouping(keywords: list[dict[str, Any]], grouping: dict[str, Any]) -> None:
    """Require each supplied keyword exactly once and reject model inventions."""
    supplied = {normalize_keyword(item["keyword"]) for item in keywords if item.get("keyword")}
    grouped = []
    for group in grouping.get("groups", []):
        primary = group.get("primary_keyword")
        if not primary:
            raise ValueError("A keyword group is missing its primary keyword.")
        for keyword in [primary, *group.get("secondary_keywords", [])]:
            normalized = normalize_keyword(keyword)
            if normalized not in supplied:
                role = "primary" if keyword == primary else "secondary"
                raise ValueError(f"Gemini invented an unknown {role} keyword: '{keyword}'")
            grouped.append(normalized)
    duplicates = sorted({keyword for keyword in grouped if grouped.count(keyword) > 1})
    if duplicates:
        raise ValueError("Gemini assigned keywords to multiple groups: " + ", ".join(duplicates))
    missing = supplied - set(grouped)
    if missing:
        raise ValueError("Gemini did not assign these keywords to any group: " + ", ".join(sorted(missing)))


def enrich_groups(grouping: dict[str, Any], keywords: list[dict[str, Any]]) -> dict[str, Any]:
    """Copy original v0.1 metrics onto the model's semantic group decisions."""
    lookup = build_keyword_lookup(keywords)
    enriched_groups = []
    for group in grouping.get("groups", []):
        primary = group["primary_keyword"]
        assigned = [primary, *group.get("secondary_keywords", [])]
        keyword_records = []
        for keyword in assigned:
            source = lookup[normalize_keyword(keyword)]
            keyword_records.append({
                "keyword": source.get("keyword"),
                "volume": source.get("volume"),
                "competition": source.get("competition"),
                "competition_level": source.get("competition_level"),
                "cpc": source.get("cpc"),
                "intent": source.get("intent"),
                "is_question": source.get("is_question"),
            })
        enriched_groups.append({
            "group_id": group.get("group_id"),
            "primary_keyword": primary,
            "secondary_keywords": group.get("secondary_keywords", []),
            "page_type": group.get("page_type"),
            "reasoning": group.get("reasoning"),
            "keywords": keyword_records,
        })
    return {"cluster": grouping.get("cluster"), "groups": enriched_groups}
