"""
v0.3 Content Generation & Validation — Candidate Selection Strategies.

Implements the Strategy Pattern (GoF) for deciding which page candidates to generate:
- `CandidateSelectionStrategy`: Base abstract strategy interface.
- `NextBestStrategy`: (Option A) Selects the top unbuilt candidates ranked by composite SEO score.
- `SpecificClusterStrategy`: (Option B) Focuses exclusively on unbuilt candidates within a single topical cluster.
- `StrategyFactory`: Factory to resolve strategy by name/enum.
"""

from abc import ABC, abstractmethod
from dataclasses import asdict
from pathlib import Path
import json
import logging
from typing import Any, Dict, List, Optional, Set, Tuple

from phases.v03.models import (
    FirstWaveSelectionConfig,
    FirstWaveSelectionManifest,
    NormalizedPageCandidate,
    PageCandidatesManifest,
    PageScoringBreakdown,
    SelectedPage,
)

logger = logging.getLogger("v03.selection")

# Path constants
BASE_DIR = Path(__file__).resolve().parent.parent.parent
OUTPUTS_DIR = BASE_DIR / "outputs"
V03_OUTPUTS_DIR = OUTPUTS_DIR / "v03"
SELECTED_PAGES_PATH = V03_OUTPUTS_DIR / "selected_pages.json"


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
# FIRST-WAVE SELECTION ALGORITHM (ORIGINAL COMPLETE ALGO)
# ============================================================

def select_first_wave_pages(
    manifest: PageCandidatesManifest,
    config: Optional[FirstWaveSelectionConfig] = None,
) -> FirstWaveSelectionManifest:
    """Select optimal 10–20 pages for First Wave content generation."""
    cfg = config or FirstWaveSelectionConfig()
    logger.info("Executing First-Wave page selection algorithm...")

    candidates = manifest.candidates
    total_available = len(candidates)

    if total_available == 0:
        return FirstWaveSelectionManifest(
            config=asdict(cfg),
            summary={"total_candidates_evaluated": 0, "total_pages_selected": 0},
            selected_pages=[],
        )

    cluster_counts: Dict[str, int] = {}
    hub_candidates: List[NormalizedPageCandidate] = []
    content_candidates: List[NormalizedPageCandidate] = []

    for c in candidates:
        if cfg.allowed_intents and c.search_intent not in cfg.allowed_intents:
            continue
        if cfg.allowed_page_types and c.page_type not in cfg.allowed_page_types:
            continue

        if c.page_type == "cluster" and cfg.include_cluster_hubs:
            hub_candidates.append(c)
        else:
            content_candidates.append(c)

    scored_candidates: List[Tuple[float, NormalizedPageCandidate, PageScoringBreakdown, str]] = []

    for c in hub_candidates + content_candidates:
        score, breakdown, rationale = score_page_candidate(c, cfg, cluster_counts)
        scored_candidates.append((score, c, breakdown, rationale))

    scored_hubs = [item for item in scored_candidates if item[1].page_type == "cluster"]
    scored_content = [item for item in scored_candidates if item[1].page_type != "cluster"]

    scored_hubs.sort(key=lambda x: x[0], reverse=True)
    scored_content.sort(key=lambda x: x[0], reverse=True)

    if cfg.target_count is not None:
        target_size = min(total_available, max(cfg.min_pages, min(cfg.max_pages, cfg.target_count)))
    else:
        target_size = min(total_available, max(cfg.min_pages, min(cfg.max_pages, total_available)))

    chosen_items: List[Tuple[float, NormalizedPageCandidate, PageScoringBreakdown, str]] = []

    for item in scored_hubs:
        chosen_items.append(item)
        cluster_counts[item[1].cluster] = cluster_counts.get(item[1].cluster, 0) + 1

    remaining_quota = target_size - len(chosen_items)
    for item in scored_content[:remaining_quota]:
        chosen_items.append(item)
        cluster_counts[item[1].cluster] = cluster_counts.get(item[1].cluster, 0) + 1

    if len(chosen_items) < target_size and len(scored_content) > remaining_quota:
        extra_needed = target_size - len(chosen_items)
        chosen_items.extend(scored_content[remaining_quota : remaining_quota + extra_needed])

    chosen_items.sort(key=lambda x: x[0], reverse=True)

    selected_pages: List[SelectedPage] = []
    for rank, (score, cand, breakdown, rationale) in enumerate(chosen_items, start=1):
        target_links = [l.get("target_url") for l in cand.internal_linking.outbound_links if l.get("target_url")]
        selected = SelectedPage(
            rank=rank,
            candidate_id=cand.candidate_id,
            title=cand.title,
            slug=cand.slug,
            url=cand.url,
            page_type=cand.page_type,
            cluster=cand.cluster,
            primary_keyword=cand.keywords.primary_keyword,
            secondary_keywords=cand.keywords.secondary_keywords,
            search_intent=cand.search_intent,
            priority=cand.priority,
            score=score,
            score_breakdown=asdict(breakdown),
            selection_rationale=rationale,
            internal_link_targets=target_links,
            target_questions=cand.keywords.question_keywords,
        )
        selected_pages.append(selected)

    chosen_ids = {c.candidate_id for c in selected_pages}
    excluded = [
        {
            "candidate_id": item[1].candidate_id,
            "title": item[1].title,
            "url": item[1].url,
            "score": item[0],
            "reason": "Lower relative composite score in this wave",
        }
        for item in scored_candidates
        if item[1].candidate_id not in chosen_ids
    ]

    intent_dist: Dict[str, int] = {}
    type_dist: Dict[str, int] = {}
    for p in selected_pages:
        intent_dist[p.search_intent] = intent_dist.get(p.search_intent, 0) + 1
        type_dist[p.page_type] = type_dist.get(p.page_type, 0) + 1

    avg_score = round(sum(p.score for p in selected_pages) / len(selected_pages), 4) if selected_pages else 0.0

    summary = {
        "total_candidates_evaluated": total_available,
        "total_pages_selected": len(selected_pages),
        "cluster_pages_selected": sum(1 for p in selected_pages if p.page_type == "cluster"),
        "content_pages_selected": sum(1 for p in selected_pages if p.page_type != "cluster"),
        "average_selection_score": avg_score,
        "clusters_represented": list(cluster_counts.keys()),
        "intent_distribution": intent_dist,
        "page_type_distribution": type_dist,
    }

    selection_manifest = FirstWaveSelectionManifest(
        version="0.3",
        phase="first_wave_page_selection",
        config=asdict(cfg),
        summary=summary,
        selected_pages=selected_pages,
        excluded_candidates=excluded,
    )

    logger.info(
        f"First-Wave selection complete: {len(selected_pages)} pages selected (Average score: {avg_score})."
    )
    return selection_manifest


def save_selected_pages(
    manifest: FirstWaveSelectionManifest,
    output_path: Optional[Path] = None,
) -> Path:
    """Save First-Wave selected pages manifest to outputs/v03/selected_pages.json."""
    target_path = output_path or SELECTED_PAGES_PATH
    target_path.parent.mkdir(parents=True, exist_ok=True)

    manifest_dict = asdict(manifest)

    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(manifest_dict, f, indent=2, ensure_ascii=False)

    logger.info(f"Saved First-Wave selected pages to: {target_path}")
    return target_path


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
