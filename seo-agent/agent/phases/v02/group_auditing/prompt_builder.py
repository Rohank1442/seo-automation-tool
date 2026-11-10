"""Build the model prompt for auditing one topic cluster."""

import json
from typing import Any


def build_audit_prompt(cluster: dict[str, Any]) -> str:
    """Serialize only the keyword-group details relevant to the audit."""
    groups = []
    for group in cluster.get("groups", []):
        groups.append({
            "group_id": group.get("group_id"),
            "primary_keyword": group.get("primary_keyword"),
            "secondary_keywords": group.get("secondary_keywords", []),
            "page_type": group.get("page_type"),
            "reasoning": group.get("reasoning"),
            "keywords": [
                {key: item.get(key) for key in ("keyword", "intent", "is_question")}
                for item in group.get("keywords", [])
            ],
        })
    cluster_name = cluster.get("cluster", "Unknown")
    return (
        "Audit the proposed SEO keyword groups for the following topic cluster:\n\n"
        f"{cluster_name}\n\nPROPOSED GROUPS:\n"
        f"{json.dumps(groups, indent=2, ensure_ascii=False)}\n\n"
        "Critically evaluate every group."
    )
