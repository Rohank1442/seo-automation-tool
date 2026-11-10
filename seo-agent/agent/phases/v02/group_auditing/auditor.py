"""Call the configured language model and validate one cluster's audit."""

from typing import Any

from core.llm import generate_json
from prompts.v02_audit_prompts import GROUP_AUDIT_SYSTEM_PROMPT, GroupAuditResponse

from .prompt_builder import build_audit_prompt
from .validation import validate_audits


def audit_cluster(cluster: dict[str, Any]) -> list[dict[str, Any]]:
    """Return validated audit records for all groups in a cluster."""
    if not cluster.get("groups"):
        return []
    response = generate_json(
        prompt=build_audit_prompt(cluster),
        response_schema=GroupAuditResponse,
        system_instruction=GROUP_AUDIT_SYSTEM_PROMPT,
    )
    validate_audits(cluster, response)
    return [audit.model_dump() for audit in response.audits]
