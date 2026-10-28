"""
Backward-compatibility facade for phases.v03_content_generation.
All modular implementations now live inside the `phases.v03` package.
"""

from phases.v03 import (
    generate_additional_wave,
    run_content_generation_phase,
)
from phases.v03.candidate_loader import (
    build_unified_page_candidates,
    load_all_pipeline_inputs,
    save_page_candidates,
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
)
from phases.v03.pipeline import create_default_generation_pipeline
from phases.v03.selection import (
    CandidateSelectionStrategy,
    NextBestStrategy,
    SpecificClusterStrategy,
    StrategyFactory,
    score_page_candidate,
)
from phases.v03.validator import (
    perform_full_content_validation,
    validate_single_page_content,
)

__all__ = [
    "run_content_generation_phase",
    "generate_additional_wave",
    "load_all_pipeline_inputs",
    "build_unified_page_candidates",
    "save_page_candidates",
    "FirstWaveSelectionConfig",
    "FirstWaveSelectionManifest",
    "GeneratedPageResult",
    "LoadedArtifacts",
    "NormalizedPageCandidate",
    "PageCandidatesManifest",
    "PageContext",
    "SelectedPage",
    "CandidateSelectionStrategy",
    "NextBestStrategy",
    "SpecificClusterStrategy",
    "StrategyFactory",
    "score_page_candidate",
    "create_default_generation_pipeline",
    "validate_single_page_content",
    "perform_full_content_validation",
]
