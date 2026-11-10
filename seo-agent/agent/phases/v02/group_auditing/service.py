"""Orchestrate the group-audit stage from input artifact to saved result."""

from pathlib import Path
from typing import Any

from .auditor import audit_cluster
from .storage import load_json, save_json
from .summary import calculate_summary


DEFAULT_INPUT_PATH = Path("outputs/v02/keyword_groups.json")
DEFAULT_OUTPUT_PATH = Path("outputs/v02/keyword_group_audit.json")


def run_audit(data: dict[str, Any]) -> dict[str, Any]:
    """Audit all keyword groups and return the established artifact shape."""
    output_clusters = []
    clusters = data.get("clusters", [])
    for index, cluster in enumerate(clusters, start=1):
        name = cluster.get("cluster", "Unknown")
        print(f"\n[Cluster {index}/{len(clusters)}] Auditing '{name}'...")
        audits = audit_cluster(cluster)
        for audit in audits:
            print(f"  • {audit['group_id']}: {audit['status']} ({audit['confidence']:.2f})")
            outliers = audit.get("potential_outliers")
            if outliers:
                print("    Outliers: " + ", ".join(outliers))
        output_clusters.append({"cluster": name, "audits": audits})
    return {
        "version": "0.2",
        "audit_method": "gemini_group_critic",
        "summary": calculate_summary(output_clusters),
        "clusters": output_clusters,
    }


def main(input_path: str | Path = DEFAULT_INPUT_PATH,
         output_path: str | Path = DEFAULT_OUTPUT_PATH) -> dict[str, Any]:
    """Load keyword groups, audit them, and persist the output artifact."""
    print("\n" + "=" * 60 + "\n        V0.2 — KEYWORD GROUP AUDIT\n" + "=" * 60)
    print("\n[Step 1] Loading keyword groups...")
    data = load_json(input_path)
    print("  ✓ Keyword groups loaded\n\n[Step 2] Auditing groups...")
    result = run_audit(data)
    summary = result["summary"]
    print("\n[Step 3] Audit summary...")
    for label in ("total_groups", "approved", "review", "split"):
        print(f"  • {label.replace('_', ' ').title()}: {summary[label]}")
    print("\n[Step 4] Saving audit...")
    save_json(output_path, result)
    print(f"  ✓ Saved: {output_path}")
    print("\n" + "=" * 60 + "\n        GROUP AUDIT COMPLETE\n" + "=" * 60)
    return result
