"""
v0.3 Content Generation & Validation — Candidate Selection Strategies.

Implements the Strategy Pattern (GoF) for deciding which page candidates to generate:
- `CandidateSelectionStrategy`: Base abstract strategy interface.
- `NextBestStrategy`: (Option A) Selects the top unbuilt candidates ranked by composite SEO score.
- `SpecificClusterStrategy`: (Option B) Focuses exclusively on unbuilt candidates within a single topical cluster.
- `StrategyFactory`: Factory to resolve strategy by name/enum.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Set, Tuple

from phases.v03.models import (
    FirstWaveSelectionConfig,
    NormalizedPageCandidate,
    PageScoringBreakdown,
)


def score_page_candidate(
    candidate: NormalizedPageCandidate,
    config: Optional[FirstWaveSelectionConfig] = None,
    cluster_representation_counts: Optional[Dict[str, int]] = None,
) -> Tuple[float, PageScoringBreakdown, str]:
    """Calculate multi-criteria SEO composite score for a page candidate."""
    cfg = config or FirstWaveSelectionConfig()
    counts = cluster_representation_counts or {}
    reasons: List[str] = []

    # 1. Keyword Audit Score
    audit = candidate.keyword_audit
    if candidate.page_type == "cluster":
        audit_score = 1.0
        reasons.append("Cluster hub page (full audit alignment)")
    elif audit.status == "approved":
        audit_score = 0.85 + (audit.confidence * 0.15)
        reasons.append(f"Approved keyword group (confidence: {audit.confidence:.2f})")
    elif audit.status == "review":
        audit_score = 0.60 + (audit.confidence * 0.15)
        reasons.append("Group in review status")
    else:
        audit_score = 0.50
        reasons.append("Resolved split group")

    # 2. Long-Tail Opportunity
    p_kw = candidate.keywords.primary_keyword or ""
    p_kw_words = len(p_kw.split()) if p_kw else 0
    q_count = len(candidate.keywords.question_keywords)

    if p_kw_words >= 5:
        long_tail_score = 0.95
        reasons.append(f"Deep long-tail primary query ({p_kw_words} words)")
    elif p_kw_words >= 4:
        long_tail_score = 0.85
        reasons.append(f"Strong long-tail primary query ({p_kw_words} words)")
    elif p_kw_words == 3:
        long_tail_score = 0.70
        reasons.append("Medium-tail primary keyword")
    elif candidate.page_type == "cluster":
        long_tail_score = 0.65
        reasons.append("Broad cluster hub keyword scope")
    else:
        long_tail_score = 0.50

    if q_count > 0:
        long_tail_score = min(1.0, long_tail_score + 0.10)
        reasons.append(f"Addresses {q_count} target question queries")

    # 3. Low Competition / Early Domain Rankability
    comp_scores = [
        kw.get("competition") for kw in candidate.keywords.all_keyword_details
        if kw.get("competition") is not None
    ]
    if comp_scores:
        avg_comp = sum(comp_scores) / len(comp_scores)
        low_competition_score = max(0.2, 1.0 - avg_comp)
        reasons.append(f"DataForSEO competition score: {avg_comp:.2f}")
    else:
        if candidate.search_intent == "informational" or candidate.page_type in ["guide", "informational"]:
            low_competition_score = 0.85
            reasons.append("Informational / how-to intent (high early rankability)")
        elif candidate.search_intent == "commercial" or candidate.page_type == "listicle":
            low_competition_score = 0.75
            reasons.append("Commercial listicle intent")
        else:
            low_competition_score = 0.65

    # 4. Content-Gap Match & Priority
    content_gap_score = 0.50
    p_kw_lower = p_kw.lower()
    title_lower = candidate.title.lower()

    for gap in candidate.content_strategy.content_gaps:
        gap_topic = gap.get("topic", "").lower()
        gap_ideas = [k.lower() for k in gap.get("keyword_ideas", [])]
        gap_priority = gap.get("priority", "medium")

        if (
            (p_kw_lower and p_kw_lower in gap_ideas)
            or any(k in title_lower for k in gap_ideas)
            or any(w in gap_topic for w in title_lower.split() if len(w) > 4)
        ):
            if gap_priority == "high":
                content_gap_score = 1.0
                reasons.append(f"Solves high-priority competitor gap: '{gap.get('topic')[:40]}...'")
                break
            else:
                content_gap_score = max(content_gap_score, 0.80)
                reasons.append(f"Solves competitor gap: '{gap.get('topic')[:40]}...'")

    if candidate.priority == "high" and content_gap_score < 0.8:
        content_gap_score = max(content_gap_score, 0.85)
        reasons.append("High architectural priority")

    # 5. Search Intent Clarity
    if candidate.search_intent in ["informational", "commercial", "transactional"]:
        intent_clarity_score = 0.95
        reasons.append(f"Definitive {candidate.search_intent} intent")
    elif candidate.search_intent == "mixed" and candidate.page_type == "cluster":
        intent_clarity_score = 0.80
        reasons.append("Cluster hub mixed navigational/informational intent")
    else:
        intent_clarity_score = 0.60

    # 6. Cluster Diversity Score
    cluster_count = counts.get(candidate.cluster, 0)
    cluster_diversity_score = 1.0 / (1.0 + (cluster_count * 0.15))
    if cluster_count == 0:
        reasons.append(f"Initial anchor representative for cluster '{candidate.cluster}'")

    total_score = (
        (audit_score * cfg.audit_weight)
        + (long_tail_score * cfg.long_tail_weight)
        + (low_competition_score * cfg.low_competition_weight)
        + (content_gap_score * cfg.content_gap_weight)
        + (intent_clarity_score * cfg.intent_clarity_weight)
        + (cluster_diversity_score * cfg.cluster_diversity_weight)
    )

    breakdown = PageScoringBreakdown(
        audit_score=round(audit_score, 3),
        long_tail_score=round(long_tail_score, 3),
        low_competition_score=round(low_competition_score, 3),
        content_gap_score=round(content_gap_score, 3),
        intent_clarity_score=round(intent_clarity_score, 3),
        cluster_diversity_score=round(cluster_diversity_score, 3),
        total_score=round(total_score, 4),
        reasons=reasons,
    )

    rationale = "; ".join(reasons[:3])
    return round(total_score, 4), breakdown, rationale


# ============================================================
# STRATEGY PATTERN INTERFACE
# ============================================================

class CandidateSelectionStrategy(ABC):
    """
    Abstract Strategy Interface for choosing which page candidates
    to generate in a wave, filtering out previously generated slugs.
    """

    @abstractmethod
    def select(
        self,
        candidates: List[NormalizedPageCandidate],
        existing_slugs: Set[str],
        batch_size: int = 25,
        **kwargs,
    ) -> List[NormalizedPageCandidate]:
        """Filter and rank candidate pages according to the strategy rules."""
        pass


class NextBestStrategy(CandidateSelectionStrategy):
    """
    Option A: Selection Strategy for the top unbuilt candidates across all clusters.
    Ranks candidates by composite SEO score (low competition, long-tail, intent clarity).
    """

    def select(
        self,
        candidates: List[NormalizedPageCandidate],
        existing_slugs: Set[str],
        batch_size: int = 25,
        **kwargs,
    ) -> List[NormalizedPageCandidate]:
        unbuilt = [c for c in candidates if c.slug not in existing_slugs]
        scored: List[Tuple[float, NormalizedPageCandidate]] = []
        for c in unbuilt:
            score, _, _ = score_page_candidate(c)
            scored.append((score, c))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [c for _, c in scored[:batch_size]]


class SpecificClusterStrategy(CandidateSelectionStrategy):
    """
    Option B: Selection Strategy targeting candidates belonging to a single topical cluster.
    Enables dedicated topical authority expansion in one cluster.
    """

    def select(
        self,
        candidates: List[NormalizedPageCandidate],
        existing_slugs: Set[str],
        batch_size: int = 25,
        cluster_name: str = "",
        **kwargs,
    ) -> List[NormalizedPageCandidate]:
        target_cluster = (cluster_name or "").strip().lower()
        unbuilt = [
            c for c in candidates
            if c.slug not in existing_slugs and c.cluster.strip().lower() == target_cluster
        ]
        scored: List[Tuple[float, NormalizedPageCandidate]] = []
        for c in unbuilt:
            score, _, _ = score_page_candidate(c)
            scored.append((score, c))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [c for _, c in scored[:batch_size]]


class StrategyFactory:
    """Factory to instantiate the appropriate selection strategy."""

    _registry = {
        "next_best": NextBestStrategy,
        "specific_cluster": SpecificClusterStrategy,
    }

    @classmethod
    def get(cls, strategy_name: str) -> CandidateSelectionStrategy:
        strategy_cls = cls._registry.get(strategy_name.lower())
        if not strategy_cls:
            valid = list(cls._registry.keys())
            raise ValueError(f"Unknown strategy '{strategy_name}'. Must be one of: {valid}")
        return strategy_cls()
