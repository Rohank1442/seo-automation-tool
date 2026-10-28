"""
Backward-compatibility facade for phases.v03_content_generation.
All modular implementations now live inside the `phases.v03` package.
"""

from phases.v03 import (
    generate_additional_wave,
    run_content_generation_phase,
    main,
)
from phases.v03.candidate_loader import (
    build_unified_page_candidates,
    load_all_pipeline_inputs,
    save_page_candidates,
    extract_research_questions,
    extract_content_gaps,
    determine_recommended_schema_type,
)
from phases.v03.models import (
    FirstWaveSelectionConfig,
    FirstWaveSelectionManifest,
    GeneratedPageResult,
    LoadedArtifacts,
    NormalizedPageCandidate,
    PageCandidatesManifest,
    PageContext,
    SelectedPage,
    PageScoringBreakdown,
    KeywordDetail,
    KeywordsContainer,
    GroupAuditSummary,
    InternalLinkSpec,
    InternalLinkingContainer,
    TechnicalSeoRules,
    ContentStrategySpec,
)
from phases.v03.pipeline import (
    create_default_generation_pipeline,
    generate_structured_content_brief,
    generate_all_content_briefs,
    process_single_page_from_brief,
)
from phases.v03.selection import (
    CandidateSelectionStrategy,
    NextBestStrategy,
    SpecificClusterStrategy,
    StrategyFactory,
    score_page_candidate,
    select_first_wave_pages,
    save_selected_pages,
)
from phases.v03.validator import (
    perform_full_content_validation,
    validate_single_page_content,
    export_generated_content_json,
    generate_v03_summary_report,
    export_content_manifest,
    extract_markdown_links,
)

__all__ = [
    "run_content_generation_phase",
    "generate_additional_wave",
    "main",
    "load_all_pipeline_inputs",
    "build_unified_page_candidates",
    "save_page_candidates",
    "extract_research_questions",
    "extract_content_gaps",
    "determine_recommended_schema_type",
    "FirstWaveSelectionConfig",
    "FirstWaveSelectionManifest",
    "GeneratedPageResult",
    "LoadedArtifacts",
    "NormalizedPageCandidate",
    "PageCandidatesManifest",
    "PageContext",
    "SelectedPage",
    "PageScoringBreakdown",
    "KeywordDetail",
    "KeywordsContainer",
    "GroupAuditSummary",
    "InternalLinkSpec",
    "InternalLinkingContainer",
    "TechnicalSeoRules",
    "ContentStrategySpec",
    "CandidateSelectionStrategy",
    "NextBestStrategy",
    "SpecificClusterStrategy",
    "StrategyFactory",
    "score_page_candidate",
    "select_first_wave_pages",
    "save_selected_pages",
    "create_default_generation_pipeline",
    "generate_structured_content_brief",
    "generate_all_content_briefs",
    "process_single_page_from_brief",
    "validate_single_page_content",
    "perform_full_content_validation",
    "export_generated_content_json",
    "generate_v03_summary_report",
    "export_content_manifest",
    "extract_markdown_links",
]

if __name__ == "__main__":
    main()
