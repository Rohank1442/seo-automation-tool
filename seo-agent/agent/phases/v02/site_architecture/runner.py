"""Load project artifacts, build and validate the architecture, then save it."""

from pathlib import Path
from typing import Any, Dict, Optional

from .builder import build_site_architecture
from .inputs import (
    load_group_audit,
    load_keyword_groups,
    load_site_profile,
    load_v01_research,
    save_json_file,
)
from .validation import validate_architecture, validate_keyword_coverage


def run_v02_architecture(outputs_root: Optional[Path] = None) -> Dict[str, Any]:
    """
    Execute the complete final architecture stage.

    Pipeline:

        load v0.1 research
                ↓
        load SiteProfile
                ↓
        load semantic groups
                ↓
        load group audits
                ↓
        resolve split groups
                ↓
        build final pages
                ↓
        validate
                ↓
        save architecture

    Returns:
        Final architecture dictionary.
    """

    print(
        "\n" + "=" * 60
    )

    print(
        "        V0.2 — FINAL SITE ARCHITECTURE"
    )

    print(
        "=" * 60
    )

    print(
        "\n[Step 1] Loading v0.1 research..."
    )

    root = Path(outputs_root) if outputs_root else Path("outputs")
    v02_dir = root / "v02"
    research_path = str(root / "page_opportunities.json")
    profile_path = str(v02_dir / "site_profile.json")
    groups_path = str(v02_dir / "keyword_groups.json")
    audit_path = str(v02_dir / "keyword_group_audit.json")
    architecture_path = str(v02_dir / "site_architecture.json")
    research = load_v01_research(research_path)

    print(
        "  ✓ Research loaded"
    )

    print(
        "\n[Step 2] Loading SiteProfile..."
    )

    site_profile = load_site_profile(profile_path)

    print(
        f"  ✓ Site model: "
        f"{site_profile.get('site_model')}"
    )

    print(
        "\n[Step 3] Loading semantic keyword groups..."
    )

    keyword_groups = load_keyword_groups(groups_path)

    total_groups = sum(
        len(
            cluster.get(
                "groups",
                [],
            )
        )
        for cluster in keyword_groups.get(
            "clusters",
            [],
        )
    )

    print(
        f"  ✓ Loaded {total_groups} semantic groups"
    )

    print(
        "\n[Step 4] Loading group audit..."
    )

    audit_data = load_group_audit(audit_path)

    audit_counts = {
        "approved": 0,
        "review": 0,
        "split": 0,
    }

    for cluster in audit_data.get(
        "clusters",
        [],
    ):
        for audit in cluster.get(
            "audits",
            [],
        ):
            status = audit.get(
                "status"
            )

            if status in audit_counts:
                audit_counts[
                    status
                ] += 1

    print(
        f"  ✓ Approved: {audit_counts['approved']}"
    )

    print(
        f"  ✓ Review: {audit_counts['review']}"
    )

    print(
        f"  ✓ Split: {audit_counts['split']}"
    )

    print(
        "\n[Step 5] Building final page architecture..."
    )

    architecture = build_site_architecture(
        research,
        site_profile,
        keyword_groups,
        audit_data,
        source_files={
            "research": research_path,
            "keyword_groups": groups_path,
            "group_audit": audit_path,
        },
        split_cache_dir=v02_dir / "checkpoints" / "split_groups",
    )

    print(
        f"\n  ✓ Generated "
        f"{architecture['page_count']} final pages"
    )

    print(
        "\n[Step 6] Validating architecture..."
    )

    validate_architecture(
        architecture
    )

    validate_keyword_coverage(
        keyword_groups,
        architecture,
    )

    print(
        "  ✓ Architecture is valid"
    )

    print(
        "\n[Step 7] Saving architecture..."
    )

    save_json_file(architecture_path, architecture)

    print(
        f"  ✓ Saved: {architecture_path}"
    )

    print(
        "\n" + "=" * 60
    )

    print(
        "        V0.2 ARCHITECTURE COMPLETE"
    )

    print(
        "=" * 60
    )

    return architecture
