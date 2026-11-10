"""Normalize and extract keyword records from v0.1 cluster research."""

import re
from typing import Any


def normalize_keyword(keyword: str) -> str:
    """Normalize case and whitespace for exact keyword membership checks."""
    return re.sub(r"\s+", " ", str(keyword).strip().lower())


def extract_cluster_keywords(cluster: dict[str, Any]) -> list[dict[str, Any]]:
    """Return usable keyword records from a research cluster."""
    raw_keywords = cluster.get("keywords", [])
    if not isinstance(raw_keywords, list):
        return []
    return [item for item in raw_keywords if isinstance(item, dict) and item.get("keyword")]


def build_keyword_lookup(keywords: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Index the original research records by normalized keyword."""
    return {
        normalize_keyword(item["keyword"]): item
        for item in keywords
        if item.get("keyword")
    }
