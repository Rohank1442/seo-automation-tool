"""Construct the per-cluster prompt supplied to the grouping model."""

import json
from typing import Any


def build_grouping_prompt(cluster: dict[str, Any], keywords: list[dict[str, Any]]) -> str:
    """Send only research fields already available from v0.1 to the model."""
    keyword_payload = [
        {
            "keyword": item.get("keyword"),
            "volume": item.get("volume"),
            "competition": item.get("competition"),
            "competition_level": item.get("competition_level"),
            "intent": item.get("intent"),
            "is_question": item.get("is_question"),
        }
        for item in keywords
    ]
    return (
        f"Topic cluster:\n{cluster.get('name', '')}\n\n"
        f"Cluster description:\n{cluster.get('description', '')}\n\n"
        "Keywords discovered by v0.1:\n"
        f"{json.dumps(keyword_payload, indent=2, ensure_ascii=False)}\n\n"
        "Group these keywords into SEO pages based on search intent."
    )
