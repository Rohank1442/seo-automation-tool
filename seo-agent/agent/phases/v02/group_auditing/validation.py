"""Validate model output against the proposed keyword groups."""

from typing import Any


VALID_STATUSES = {"approved", "review", "split"}


def validate_audits(cluster: dict[str, Any], response: Any) -> None:
    """Require exactly one valid model audit for every input group."""
    expected_ids = {group.get("group_id") for group in cluster.get("groups", [])}
    if None in expected_ids:
        raise ValueError("A proposed keyword group is missing group_id.")
    actual_ids = [audit.group_id for audit in response.audits]
    if len(set(actual_ids)) != len(actual_ids):
        raise ValueError("Gemini returned duplicate audits for one or more groups.")
    actual_set = set(actual_ids)
    missing = expected_ids - actual_set
    unknown = actual_set - expected_ids
    if missing:
        raise ValueError("Missing audits for groups: " + ", ".join(sorted(missing)))
    if unknown:
        raise ValueError("Gemini returned audits for unknown groups: " + ", ".join(sorted(unknown)))
    for audit in response.audits:
        if audit.status not in VALID_STATUSES:
            raise ValueError(f"Invalid audit status '{audit.status}' for group '{audit.group_id}'.")
        if not 0 <= audit.confidence <= 1:
            raise ValueError(f"Invalid confidence for group '{audit.group_id}': {audit.confidence}")
