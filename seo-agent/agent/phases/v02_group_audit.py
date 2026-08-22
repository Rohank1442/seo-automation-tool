"""
v0.2 — Keyword Group Audit.

This phase audits the semantic keyword groups produced by
v02_keyword_grouping.py.

Pipeline:

    keyword_groups.json
            ↓
      Gemini group audit
            ↓
       Python validation
            ↓
      keyword_group_audit.json

The audit does NOT modify the original groups.
It provides evidence for the final page architecture stage.
"""

import json
import os
from typing import Any, Dict, List

from core.llm import generate_json

from prompts.v02_audit_prompts import (
    GroupAuditResponse,
    GROUP_AUDIT_SYSTEM_PROMPT,
)


# ============================================================
# PATHS
# ============================================================

INPUT_PATH = os.path.join(
    "outputs",
    "v02",
    "keyword_groups.json",
)

OUTPUT_PATH = os.path.join(
    "outputs",
    "v02",
    "keyword_group_audit.json",
)


# ============================================================
# FILE HELPERS
# ============================================================


def load_json(path: str) -> Dict[str, Any]:
    """
    Load a JSON file from disk.
    """

    if not os.path.exists(path):
        raise FileNotFoundError(
            f"File not found: {path}"
        )

    with open(
        path,
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def save_json(
    path: str,
    data: Dict[str, Any],
) -> None:
    """
    Save a dictionary as formatted JSON.
    """

    os.makedirs(
        os.path.dirname(path),
        exist_ok=True,
    )

    with open(
        path,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            data,
            file,
            indent=2,
            ensure_ascii=False,
        )


# ============================================================
# PROMPT BUILDING
# ============================================================


def build_audit_prompt(
    cluster: Dict[str, Any],
) -> str:
    """
    Build the Gemini audit prompt for one cluster.

    The complete proposed grouping is supplied so Gemini can
    evaluate the relationships between the groups.
    """

    groups = []

    for group in cluster.get(
        "groups",
        [],
    ):
        groups.append(
            {
                "group_id": group.get(
                    "group_id"
                ),
                "primary_keyword": group.get(
                    "primary_keyword"
                ),
                "secondary_keywords": group.get(
                    "secondary_keywords",
                    [],
                ),
                "page_type": group.get(
                    "page_type"
                ),
                "reasoning": group.get(
                    "reasoning"
                ),
                "keywords": [
                    {
                        "keyword": item.get(
                            "keyword"
                        ),
                        "intent": item.get(
                            "intent"
                        ),
                        "is_question": item.get(
                            "is_question"
                        ),
                    }
                    for item in group.get(
                        "keywords",
                        [],
                    )
                ],
            }
        )

    return (
        f"Audit the proposed SEO keyword groups for the following "
        f"topic cluster:\n\n"
        f"{cluster.get('cluster')}\n\n"
        f"PROPOSED GROUPS:\n"
        f"{json.dumps(groups, indent=2)}\n\n"
        f"Critically evaluate every group."
    )


# ============================================================
# VALIDATION
# ============================================================


def validate_audits(
    cluster: Dict[str, Any],
    response: GroupAuditResponse,
) -> None:
    """
    Validate Gemini's audit response.

    Ensures that:

    - Every existing group is audited.
    - No unknown group is introduced.
    - Status values are valid.
    - Confidence values are within range.
    """

    expected_ids = {
        group.get("group_id")
        for group in cluster.get(
            "groups",
            [],
        )
    }

    actual_ids = {
        audit.group_id
        for audit in response.audits
    }

    if len(actual_ids) != len(response.audits):
        raise ValueError(
            "Gemini returned duplicate audits for one or more groups."
        )

    missing = expected_ids - actual_ids

    if missing:
        raise ValueError(
            "Missing audits for groups: "
            + ", ".join(sorted(missing))
        )

    unknown = actual_ids - expected_ids

    if unknown:
        raise ValueError(
            "Gemini returned audits for unknown groups: "
            + ", ".join(sorted(unknown))
        )

    valid_statuses = {
        "approved",
        "review",
        "split",
    }

    for audit in response.audits:

        if audit.status not in valid_statuses:
            raise ValueError(
                f"Invalid audit status '{audit.status}' "
                f"for group '{audit.group_id}'."
            )

        if not 0 <= audit.confidence <= 1:
            raise ValueError(
                f"Invalid confidence for group "
                f"'{audit.group_id}': {audit.confidence}"
            )


# ============================================================
# AUDIT ONE CLUSTER
# ============================================================


def audit_cluster(
    cluster: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Ask Gemini to audit every keyword group in one cluster.
    """

    if not cluster.get(
        "groups"
    ):
        return []

    prompt = build_audit_prompt(
        cluster
    )

    response = generate_json(
        prompt=prompt,
        response_schema=GroupAuditResponse,
        system_instruction=GROUP_AUDIT_SYSTEM_PROMPT,
    )

    validate_audits(
        cluster,
        response,
    )

    return [
        audit.model_dump()
        for audit in response.audits
    ]


# ============================================================
# SUMMARY
# ============================================================


def calculate_summary(
    clusters: List[Dict[str, Any]],
) -> Dict[str, int]:
    """
    Calculate overall audit statistics.
    """

    summary = {
        "total_groups": 0,
        "approved": 0,
        "review": 0,
        "split": 0,
    }

    for cluster in clusters:

        for audit in cluster.get(
            "audits",
            [],
        ):
            summary[
                "total_groups"
            ] += 1

            status = audit.get(
                "status"
            )

            if status in summary:
                summary[
                    status
                ] += 1

    return summary


# ============================================================
# PIPELINE
# ============================================================


def run_audit(
    data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Audit all keyword groups across all topic clusters.
    """

    output_clusters = []

    clusters = data.get(
        "clusters",
        [],
    )

    for index, cluster in enumerate(
        clusters,
        start=1,
    ):

        cluster_name = cluster.get(
            "cluster",
            "Unknown",
        )

        print(
            f"\n[Cluster {index}/{len(clusters)}] "
            f"Auditing '{cluster_name}'..."
        )

        audits = audit_cluster(
            cluster
        )

        for audit in audits:

            print(
                f"  • {audit['group_id']}: "
                f"{audit['status']} "
                f"({audit['confidence']:.2f})"
            )

            if audit.get(
                "potential_outliers"
            ):
                print(
                    "    Outliers: "
                    + ", ".join(
                        audit[
                            "potential_outliers"
                        ]
                    )
                )

        output_clusters.append(
            {
                "cluster": cluster_name,
                "audits": audits,
            }
        )

    summary = calculate_summary(
        output_clusters
    )

    return {
        "version": "0.2",
        "audit_method": "gemini_group_critic",
        "summary": summary,
        "clusters": output_clusters,
    }


# ============================================================
# ENTRY POINT
# ============================================================


def main() -> None:
    """
    Execute the complete keyword group audit pipeline.
    """

    print("\n" + "=" * 60)
    print("        V0.2 — KEYWORD GROUP AUDIT")
    print("=" * 60)

    print(
        "\n[Step 1] Loading keyword groups..."
    )

    data = load_json(
        INPUT_PATH
    )

    print(
        "  ✓ Keyword groups loaded"
    )

    print(
        "\n[Step 2] Auditing groups..."
    )

    result = run_audit(
        data
    )

    print(
        "\n[Step 3] Audit summary..."
    )

    summary = result[
        "summary"
    ]

    print(
        f"  • Total groups: {summary['total_groups']}"
    )

    print(
        f"  • Approved: {summary['approved']}"
    )

    print(
        f"  • Review: {summary['review']}"
    )

    print(
        f"  • Split: {summary['split']}"
    )

    print(
        "\n[Step 4] Saving audit..."
    )

    save_json(
        OUTPUT_PATH,
        result,
    )

    print(
        f"  ✓ Saved: {OUTPUT_PATH}"
    )

    print("\n" + "=" * 60)
    print("        GROUP AUDIT COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()