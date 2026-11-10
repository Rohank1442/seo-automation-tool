"""Orchestrate project-scoped v0.1 loading and v0.2 profile generation."""

from pathlib import Path
from typing import Any

from .inference import build_site_profile
from .research import load_v01_research, validate_v01_research
from .storage import save_site_profile


def run_v02_site_foundation(outputs_root: Path | None = None) -> dict[str, Any]:
    """Load a project's v0.1 research, infer its profile, and save it under v0.2."""
    root = Path(outputs_root) if outputs_root is not None else Path("outputs")
    research_path = root / "page_opportunities.json"
    profile_path = root / "v02" / "site_profile.json"
    print("\n" + "=" * 60 + "\n        SEO AUTOMATION AGENT — v0.2\n        SITE FOUNDATION\n" + "=" * 60)
    print("\n[Step 1] Loading v0.1 research...")
    research = load_v01_research(research_path)
    print(f"  ✓ Loaded {research_path}\n\n[Step 2] Validating v0.1 research...")
    validate_v01_research(research)
    print("  ✓ v0.1 research is valid\n\n[Step 3] Inferring website profile...")
    profile = build_site_profile(research)
    print(f"  ✓ Site model: {profile['site_model']}")
    print(f"  ✓ Primary topic: {profile['primary_topic']}")
    print(f"  ✓ Clusters: {profile['cluster_count']}\n\n[Step 4] Saving v0.2 site profile...")
    save_site_profile(profile, profile_path)
    print(f"  ✓ Saved: {profile_path}\n\n" + "=" * 60 + "\n        V0.2 FOUNDATION COMPLETE\n" + "=" * 60)
    return profile
