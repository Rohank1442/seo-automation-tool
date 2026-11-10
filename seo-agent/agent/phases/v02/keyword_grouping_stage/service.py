"""Run the project-scoped v0.2 semantic keyword grouping stage."""

from pathlib import Path
from typing import Any

from .grouping import build_keyword_groups
from .keywords import extract_cluster_keywords
from .storage import load_json_file, save_keyword_groups


def run_v02_keyword_grouping(outputs_root: Path | None = None) -> dict[str, Any]:
    """Load a project's v0.1 research, group keywords, and save its artifact."""
    root = Path(outputs_root) if outputs_root is not None else Path("outputs")
    research_path = root / "page_opportunities.json"
    groups_path = root / "v02" / "keyword_groups.json"
    print("\n" + "=" * 60 + "\n        V0.2 — SEMANTIC KEYWORD GROUPING\n" + "=" * 60)
    print("\n[Step 1] Loading v0.1 research...")
    research = load_json_file(research_path)
    print("  ✓ Research loaded\n\n[Step 2] Grouping keywords by search intent...")
    result = build_keyword_groups(research)
    total_groups = sum(len(cluster.get("groups", [])) for cluster in result["clusters"])
    total_keywords = sum(len(extract_cluster_keywords(cluster)) for cluster in research.get("clusters", []))
    print(f"\n  ✓ Total keywords processed: {total_keywords}")
    print(f"  ✓ Total page groups: {total_groups}\n\n[Step 3] Saving keyword groups...")
    save_keyword_groups(result, groups_path)
    print(f"  ✓ Saved: {groups_path}\n" + "=" * 60 + "\n        SEMANTIC GROUPING COMPLETE\n" + "=" * 60)
    return result
