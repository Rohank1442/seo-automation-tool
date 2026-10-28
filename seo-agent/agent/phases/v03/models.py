"""
v0.3 Content Generation & Validation — Domain Models and Data Structures.

Defines all type-safe dataclasses for:
- Pipeline input artifacts (v0.1 & v0.2 data)
- Keyword containers and audit findings
- Page candidates, technical SEO rules, and content strategy specifications
- First-wave and multi-wave selection manifests
- Execution page contexts and generation results
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


# ============================================================
# 1. INPUT ARTIFACT CONTAINERS
# ============================================================

@dataclass
class LoadedArtifacts:
    """Container for all loaded v0.1 research and v0.2 architecture artifacts."""

    research_report_md: str
    site_architecture: Dict[str, Any]
    keyword_groups: Dict[str, Any]
    group_audit: Dict[str, Any]
    url_architecture: Dict[str, Any]
    internal_linking: Dict[str, Any]
    technical_seo: Dict[str, Any]
    loaded_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


# ============================================================
# 2. KEYWORD & AUDIT MODELS
# ============================================================

@dataclass
class KeywordDetail:
    """Detailed keyword metadata with search volume and intent."""

    keyword: str
    intent: str = "informational"
    is_question: bool = False
    volume: Optional[int] = None
    competition: Optional[float] = None
    competition_level: Optional[str] = None
    cpc: Optional[float] = None


@dataclass
class KeywordsContainer:
    """Normalized keyword package for an individual page candidate."""

    primary_keyword: Optional[str]
    secondary_keywords: List[str] = field(default_factory=list)
    all_keyword_details: List[Dict[str, Any]] = field(default_factory=list)
    question_keywords: List[str] = field(default_factory=list)


@dataclass
class GroupAuditSummary:
    """Audit findings and recommendations for the page's keyword group."""

    group_id: Optional[str]
    status: str = "approved"
    confidence: float = 1.0
    intent_consistent: bool = True
    topic_coherent: bool = True
    potential_outliers: List[str] = field(default_factory=list)
    issues: List[str] = field(default_factory=list)
    recommendation: str = "Approved for content generation."


# ============================================================
# 3. INTERNAL LINKING & TECHNICAL SEO
# ============================================================

@dataclass
class InternalLinkSpec:
    """Specification for an inbound or outbound internal link."""

    source_page_id: str
    source_url: str
    target_page_id: str
    target_url: str
    anchor_text: str
    relationship: str
    reason: str
    priority: str = "medium"


@dataclass
class InternalLinkingContainer:
    """Aggregated inbound and outbound internal links for a candidate page."""

    outbound_links: List[Dict[str, Any]] = field(default_factory=list)
    inbound_links: List[Dict[str, Any]] = field(default_factory=list)
    outbound_count: int = 0
    inbound_count: int = 0


@dataclass
class TechnicalSeoRules:
    """On-page technical SEO directives and constraints."""

    robots: str = "index, follow"
    canonical_url: str = ""
    schema_type: str = "Article"
    max_title_length: int = 60
    max_meta_description_length: int = 160
    protocol: str = "https"
    canonical_domain: str = "https://example.com"


@dataclass
class ContentStrategySpec:
    """Content creation guidance derived from audience research and content gaps."""

    target_audience: str
    site_purpose: str
    content_gaps: List[Dict[str, Any]] = field(default_factory=list)
    relevant_faqs: List[str] = field(default_factory=list)
    recommended_word_count: int = 1200
    suggested_sections: List[str] = field(default_factory=list)


# ============================================================
# 4. NORMALIZED PAGE CANDIDATE
# ============================================================

@dataclass
class NormalizedPageCandidate:
    """
    Unified, fully-normalized candidate model for an SEO page.
    Combines architecture, keyword research, internal links, and technical rules.
    """

    candidate_id: str
    title: str
    slug: str
    url: str
    canonical_url: str
    page_type: str
    cluster: str
    parent_page_id: Optional[str]
    search_intent: str
    priority: str
    indexable: bool
    content_status: str
    readiness_status: str
    keywords: KeywordsContainer
    keyword_audit: GroupAuditSummary
    internal_linking: InternalLinkingContainer
    technical_seo: TechnicalSeoRules
    content_strategy: ContentStrategySpec


@dataclass
class PageCandidatesManifest:
    """Top-level container for all normalized page candidates."""

    version: str = "0.3"
    phase: str = "page_candidates_preparation"
    generated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    site_profile: Dict[str, Any] = field(default_factory=dict)
    summary: Dict[str, Any] = field(default_factory=dict)
    global_technical_seo: Dict[str, Any] = field(default_factory=dict)
    candidates: List[NormalizedPageCandidate] = field(default_factory=list)


# ============================================================
# 5. SELECTION & SCORING MODELS
# ============================================================

@dataclass
class FirstWaveSelectionConfig:
    """Configurable weights and thresholds for First-Wave page selection."""

    min_pages: int = 10
    max_pages: int = 20
    target_count: Optional[int] = None
    include_cluster_hubs: bool = True
    audit_weight: float = 0.25
    long_tail_weight: float = 0.20
    low_competition_weight: float = 0.15
    content_gap_weight: float = 0.20
    intent_clarity_weight: float = 0.10
    cluster_diversity_weight: float = 0.10
    min_score_threshold: float = 0.0
    allowed_intents: Optional[List[str]] = None
    allowed_page_types: Optional[List[str]] = None


@dataclass
class PageScoringBreakdown:
    """Detailed score breakdown across all selection dimensions."""

    audit_score: float
    long_tail_score: float
    low_competition_score: float
    content_gap_score: float
    intent_clarity_score: float
    cluster_diversity_score: float
    total_score: float
    reasons: List[str] = field(default_factory=list)


@dataclass
class SelectedPage:
    """Specification of an approved page selection with score rationale."""

    rank: int
    candidate_id: str
    title: str
    slug: str
    url: str
    page_type: str
    cluster: str
    primary_keyword: Optional[str]
    secondary_keywords: List[str]
    search_intent: str
    priority: str
    score: float
    score_breakdown: Dict[str, Any]
    selection_rationale: str
    internal_link_targets: List[str] = field(default_factory=list)
    target_questions: List[str] = field(default_factory=list)


@dataclass
class FirstWaveSelectionManifest:
    """Top-level output artifact for First-Wave page selection."""

    version: str = "0.3"
    phase: str = "first_wave_page_selection"
    generated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    config: Dict[str, Any] = field(default_factory=dict)
    summary: Dict[str, Any] = field(default_factory=dict)
    selected_pages: List[SelectedPage] = field(default_factory=list)
    excluded_candidates: List[Dict[str, Any]] = field(default_factory=list)


# ============================================================
# 6. PIPELINE CONTEXT & EXECUTION OUTCOME
# ============================================================

@dataclass
class PageContext:
    """Context wrapper for executing single-page brief and content generation."""

    candidate: NormalizedPageCandidate

    @property
    def page_id(self) -> str:
        return self.candidate.candidate_id

    @property
    def title(self) -> str:
        return self.candidate.title

    @property
    def slug(self) -> str:
        return self.candidate.slug

    @property
    def url(self) -> str:
        return self.candidate.url

    @property
    def canonical_url(self) -> str:
        return self.candidate.canonical_url

    @property
    def page_type(self) -> str:
        return self.candidate.page_type

    @property
    def cluster(self) -> str:
        return self.candidate.cluster

    @property
    def parent_page_id(self) -> Optional[str]:
        return self.candidate.parent_page_id

    @property
    def primary_keyword(self) -> Optional[str]:
        return self.candidate.keywords.primary_keyword

    @property
    def secondary_keywords(self) -> List[str]:
        return self.candidate.keywords.secondary_keywords

    @property
    def search_intent(self) -> str:
        return self.candidate.search_intent

    @property
    def priority(self) -> str:
        return self.candidate.priority

    @property
    def indexable(self) -> bool:
        return self.candidate.indexable

    @property
    def target_audience(self) -> str:
        return self.candidate.content_strategy.target_audience

    @property
    def site_purpose(self) -> str:
        return self.candidate.content_strategy.site_purpose

    @property
    def outbound_internal_links(self) -> List[Dict[str, Any]]:
        return self.candidate.internal_linking.outbound_links

    @property
    def inbound_internal_links(self) -> List[Dict[str, Any]]:
        return self.candidate.internal_linking.inbound_links

    @property
    def content_gaps(self) -> List[Dict[str, Any]]:
        return self.candidate.content_strategy.content_gaps

    @property
    def research_questions(self) -> List[str]:
        return self.candidate.content_strategy.relevant_faqs

    @property
    def keywords(self) -> KeywordsContainer:
        return self.candidate.keywords

    @property
    def question_keywords(self) -> List[str]:
        return self.candidate.keywords.question_keywords


@dataclass
class GeneratedPageResult:
    """Full generation outcome for a single page."""

    page_id: str
    slug: str
    url: str
    title: str
    page_type: str
    cluster: str
    primary_keyword: Optional[str]
    secondary_keywords: List[str]
    brief: Optional[Dict[str, Any]] = None
    markdown_content: str = ""
    metadata: Optional[Dict[str, Any]] = None
    faq: Optional[Dict[str, Any]] = None
    audit: Optional[Dict[str, Any]] = None
    word_count: int = 0
    embedded_internal_links: List[Dict[str, Any]] = field(default_factory=list)
    status: str = "pending"
    generated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    error: Optional[str] = None
