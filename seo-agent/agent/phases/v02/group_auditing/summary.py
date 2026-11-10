"""Summarize the audit outcomes across clusters."""

from typing import Any


def calculate_summary(clusters: list[dict[str, Any]]) -> dict[str, int]:
    """Count total audits and each supported audit status."""
    summary = {"total_groups": 0, "approved": 0, "review": 0, "split": 0}
    for cluster in clusters:
        for audit in cluster.get("audits", []):
            summary["total_groups"] += 1
            status = audit.get("status")
            if status in summary:
                summary[status] += 1
    return summary
