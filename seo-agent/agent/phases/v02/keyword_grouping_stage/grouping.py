"""Coordinate model-based grouping and validation for each research cluster."""

from typing import Any

from core.llm import generate_json
from prompts.v02_prompts import KEYWORD_GROUPING_SYSTEM_PROMPT, KeywordGroupingResponse

from .keywords import extract_cluster_keywords
from .prompt_builder import build_grouping_prompt
from .validation import (
    enrich_groups,
    remove_unresearched_keywords,
    validate_grouping,
)


def group_cluster_keywords(cluster: dict[str, Any]) -> dict[str, Any]:
    """Group one cluster's keywords and return the model's proposed groups."""
    keywords = extract_cluster_keywords(cluster)
    if not keywords:
        return {"cluster": cluster.get("name", ""), "groups": []}
    response = generate_json(
        prompt=build_grouping_prompt(cluster, keywords),
        response_schema=KeywordGroupingResponse,
        system_instruction=KEYWORD_GROUPING_SYSTEM_PROMPT,
    )
    return {"cluster": cluster.get("name", ""), "groups": [group.model_dump() for group in response.groups]}


def build_keyword_groups(research: dict[str, Any]) -> dict[str, Any]:
    """Group each research cluster independently into page-level keyword sets."""
    clusters = research.get("clusters", [])
    results = []
    for index, cluster in enumerate(clusters, start=1):
        if not isinstance(cluster, dict):
            continue
        name = cluster.get("name", "Unknown")
        print(f"\n[Cluster {index}/{len(clusters)}] Grouping keywords for '{name}'...")
        keywords = extract_cluster_keywords(cluster)
        print(f"  • Keywords supplied: {len(keywords)}")
        if not keywords:
            print("  • No keywords found. Skipping.")
            results.append({"cluster": name, "groups": []})
            continue
        try:
            grouping = group_cluster_keywords(cluster)
            grouping, removed_keywords, dropped_groups, promoted_primaries = (
                remove_unresearched_keywords(keywords, grouping)
            )
            if removed_keywords:
                print(
                    f"  ⚠ Removed {len(removed_keywords)} unresearched keyword(s): "
                    + ", ".join(f"'{keyword}'" for keyword in removed_keywords)
                )
            if promoted_primaries:
                print(
                    f"  ⚠ Promoted a researched secondary keyword to primary in "
                    f"{promoted_primaries} group(s)."
                )
            if dropped_groups:
                print(
                    f"  ⚠ Dropped {dropped_groups} group(s) with no researched keywords."
                )
            validate_grouping(keywords, grouping)
            enriched = enrich_groups(grouping, keywords)
            print(f"  ✓ Generated {len(enriched['groups'])} page groups")
            results.append(enriched)
        except Exception as exc:
            print(f"  ✗ Keyword grouping failed: {exc}")
            raise
    return {"version": "0.2", "grouping_method": "gemini_search_intent", "clusters": results}
