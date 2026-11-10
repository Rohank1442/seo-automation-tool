"""Lightweight deterministic keyword and page relevance scoring."""

import re
from typing import Any


STOP_WORDS = {
    "the", "a", "an", "to", "for", "of", "in", "on", "and", "or", "is", "are",
    "what", "how", "where", "can", "you", "with", "online", "best", "app", "apps",
}


def normalize_text(text: str) -> str:
    """Lowercase text and remove punctuation for lexical comparison."""
    normalized = re.sub(r"[^a-z0-9\s-]", " ", (text or "").lower())
    return re.sub(r"\s+", " ", normalized).strip()


def keyword_tokens(keyword: str) -> set[str]:
    """Return meaningful words after removing short and common terms."""
    return {word for word in normalize_text(keyword).split() if len(word) > 2 and word not in STOP_WORDS}


def keyword_similarity(keyword_a: str, keyword_b: str) -> float:
    """Return Jaccard similarity for two keyword token sets."""
    tokens_a, tokens_b = keyword_tokens(keyword_a), keyword_tokens(keyword_b)
    union = tokens_a | tokens_b
    return len(tokens_a & tokens_b) / len(union) if union else 0.0


def calculate_page_similarity(page_a: dict[str, Any], page_b: dict[str, Any]) -> float:
    """Score primary/secondary keyword overlap, with a small intent bonus."""
    score = keyword_similarity(page_a.get("primary_keyword", ""), page_b.get("primary_keyword", ""))
    secondary_scores = [
        keyword_similarity(keyword_a, keyword_b)
        for keyword_a in page_a.get("secondary_keywords", [])
        for keyword_b in page_b.get("secondary_keywords", [])
    ]
    if secondary_scores:
        score = max(score, max(secondary_scores))
    intent_a, intent_b = page_a.get("intent"), page_b.get("intent")
    if intent_a and intent_b and intent_a == intent_b:
        score += 0.10
    return min(score, 1.0)
