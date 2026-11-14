"""Validate model groupings and attach source-of-truth keyword metrics."""

from typing import Any

from .keywords import build_keyword_lookup, normalize_keyword


def clean_keyword_grouping(
    keywords: list[dict[str, Any]], grouping: dict[str, Any]
) -> tuple[dict[str, Any], list[str], int, int, list[dict[str, Any]]]:
    """Remove invented and duplicate assignments while retaining researched terms."""
    supplied = {normalize_keyword(item["keyword"]) for item in keywords if item.get("keyword")}
    removed_keywords = []
    occurrences_by_keyword: dict[str, list[dict[str, Any]]] = {}
    occurrences_by_group: dict[int, list[dict[str, Any]]] = {}
    occurrence_id = 0

    for group_index, group in enumerate(grouping.get("groups", [])):
        occurrences_by_group[group_index] = []
        secondary_keywords = group.get("secondary_keywords", [])
        if not isinstance(secondary_keywords, list):
            secondary_keywords = []
        candidates = [("primary", 0, group.get("primary_keyword"))]
        candidates.extend(
            ("secondary", index, keyword)
            for index, keyword in enumerate(secondary_keywords)
        )

        for role, position, keyword in candidates:
            normalized = normalize_keyword(keyword) if keyword else ""
            if not normalized or normalized not in supplied:
                if keyword:
                    removed_keywords.append(keyword)
                continue

            occurrence = {
                "id": occurrence_id,
                "group_index": group_index,
                "role": role,
                "position": position,
                "keyword": keyword,
                "normalized": normalized,
            }
            occurrence_id += 1
            occurrences_by_keyword.setdefault(normalized, []).append(occurrence)
            occurrences_by_group[group_index].append(occurrence)

    # Prefer a primary assignment. For ties, keep the first group in Gemini's output.
    owners: dict[str, int] = {}
    resolved_duplicates = []
    for occurrences in occurrences_by_keyword.values():
        winner = min(
            occurrences,
            key=lambda item: (
                0 if item["role"] == "primary" else 1,
                item["group_index"],
                item["position"],
            ),
        )
        owners[winner["normalized"]] = winner["id"]
        if len(occurrences) > 1:
            winner_group = grouping["groups"][winner["group_index"]]
            resolved_duplicates.append({
                "keyword": winner["keyword"],
                "kept_group": winner_group.get("group_id") or f"group {winner['group_index'] + 1}",
                "removed_assignments": len(occurrences) - 1,
            })

    cleaned_groups = []
    dropped_groups = 0
    promoted_primaries = 0

    for group_index, group in enumerate(grouping.get("groups", [])):
        owned = [
            item
            for item in occurrences_by_group[group_index]
            if owners[item["normalized"]] == item["id"]
        ]
        primary_occurrence = next(
            (item for item in owned if item["role"] == "primary"), None
        )

        if primary_occurrence:
            primary = primary_occurrence["keyword"]
            secondary_keywords = [
                item["keyword"] for item in owned if item["role"] == "secondary"
            ]
        elif owned:
            # A duplicate or invented primary may have been removed; retain this
            # group's researched terms by promoting its first remaining secondary.
            primary = owned[0]["keyword"]
            secondary_keywords = [item["keyword"] for item in owned[1:]]
            promoted_primaries += 1
        else:
            dropped_groups += 1
            continue

        cleaned_group = dict(group)
        cleaned_group["primary_keyword"] = primary
        cleaned_group["secondary_keywords"] = secondary_keywords
        cleaned_groups.append(cleaned_group)

    cleaned_grouping = dict(grouping)
    cleaned_grouping["groups"] = cleaned_groups
    return (
        cleaned_grouping,
        removed_keywords,
        dropped_groups,
        promoted_primaries,
        resolved_duplicates,
    )


def validate_grouping(keywords: list[dict[str, Any]], grouping: dict[str, Any]) -> None:
    """Require each supplied keyword exactly once after cleanup."""
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
