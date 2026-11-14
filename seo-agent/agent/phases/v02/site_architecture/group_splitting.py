"""Prompt, resolve, and validate audited keyword groups marked for splitting."""

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, List

from pydantic import BaseModel, Field

from core.llm import generate_json
from prompts.v02_prompts import FinalKeywordGroup
from .keywords import collect_group_keywords, normalize_keyword


class FinalKeywordGroupResponse(BaseModel):
    """
    Structured response containing the final groups after
    resolving a group marked as split.
    """

    groups: List[FinalKeywordGroup] = Field(
        default_factory=list
    )

SPLIT_GROUP_SYSTEM_PROMPT = """
You are an expert SEO information architect.

A previous semantic keyword grouping system created a keyword
group and an audit system determined that the group should be
SPLIT because it contains multiple distinct search intents.

Your job is to divide ONLY that supplied group into coherent
final page groups.

Rules:

1. Do not invent keywords.
2. Every supplied keyword must belong to exactly one final group.
3. Do not silently discard keywords.
4. Keywords with the same underlying search intent should stay
   together.
5. Different user goals should become different pages.
6. Search intent matters more than wording similarity.
7. Do not create a separate page merely because a keyword is
   longer or shorter.
8. Each final group must represent one clear page/searcher
   expectation.
9. Use the original keywords exactly as supplied.
10. Choose one primary keyword per final group.
11. The primary keyword must come from the supplied keywords.
12. Secondary keywords must also come from the supplied keywords.
13. Keep the number of pages as small as reasonably possible while
    preserving distinct search intent.
14. Do not create a page solely for a weak isolated variation unless
    its search intent is genuinely different.
"""


def build_split_group_prompt(
    cluster_name: str,
    group: Dict[str, Any],
    audit: Dict[str, Any],
) -> str:
    """
    Build the Gemini prompt used to split a group that failed
    the semantic audit.
    """

    payload = {
        "cluster": cluster_name,
        "group": {
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
            "keywords": [
                item.get(
                    "keyword"
                )
                for item in group.get(
                    "keywords",
                    []
                )
                if isinstance(
                    item,
                    dict,
                )
                and item.get(
                    "keyword"
                )
            ],
        },
        "audit": {
            "status": audit.get(
                "status"
            ),
            "confidence": audit.get(
                "confidence"
            ),
            "potential_outliers": audit.get(
                "potential_outliers",
                [],
            ),
            "issues": audit.get(
                "issues",
                [],
            ),
            "recommendation": audit.get(
                "recommendation"
            ),
        },
    }

    return (
        "Split the following audited SEO keyword group "
        "into its final page groups.\n\n"
        f"{json.dumps(payload, indent=2)}"
    )


def validate_split_groups(
    original_group: Dict[str, Any],
    response: FinalKeywordGroupResponse,
) -> None:
    """
    Validate the result of Gemini's split operation.

    Every original keyword must appear exactly once across the
    final groups.
    """

    original_keywords = {
        normalize_keyword(keyword)
        for keyword in collect_group_keywords(
            original_group
        )
    }

    assigned_keywords: List[str] = []

    for group in response.groups:
        assigned_keywords.append(
            normalize_keyword(
                group.primary_keyword
            )
        )

        for keyword in group.secondary_keywords:
            assigned_keywords.append(
                normalize_keyword(
                    keyword
                )
            )

    assigned_set = set(
        assigned_keywords
    )

    missing = (
        original_keywords
        - assigned_set
    )

    unknown = (
        assigned_set
        - original_keywords
    )

    if missing:
        raise ValueError(
            "Split operation lost keywords: "
            + ", ".join(
                sorted(missing)
            )
        )

    if unknown:
        raise ValueError(
            "Split operation invented keywords: "
            + ", ".join(
                sorted(unknown)
            )
        )

    if len(assigned_keywords) != len(
        original_keywords
    ):
        raise ValueError(
            "Split operation assigned one or more keywords "
            "more than once."
        )

    if not response.groups:
        raise ValueError(
            "Split operation returned no final groups."
        )


def resolve_split_group(
    cluster_name: str,
    group: Dict[str, Any],
    audit: Dict[str, Any],
    cache_dir: Path | None = None,
) -> List[Dict[str, Any]]:
    """
    Ask Gemini to split a group that the audit stage marked as
    requiring multiple pages.

    Returns:
        List of final semantic page groups.
    """

    prompt = build_split_group_prompt(
        cluster_name,
        group,
        audit,
    )

    cache_path = None
    if cache_dir is not None:
        cache_key = hashlib.sha256(
            f"{SPLIT_GROUP_SYSTEM_PROMPT}\n{prompt}".encode("utf-8")
        ).hexdigest()[:16]
        safe_group_id = re.sub(
            r"[^a-z0-9-]+",
            "-",
            str(group.get("group_id", "group")).lower(),
        ).strip("-") or "group"
        cache_path = Path(cache_dir) / f"{safe_group_id}-{cache_key}.json"

        if cache_path.is_file():
            try:
                cached_data = json.loads(cache_path.read_text(encoding="utf-8"))
                cached_response = FinalKeywordGroupResponse.model_validate(cached_data)
                validate_split_groups(group, cached_response)
                print(f"    Reusing cached split for '{group.get('group_id')}'.")
                return [item.model_dump() for item in cached_response.groups]
            except Exception as exc:
                print(
                    f"    Cached split for '{group.get('group_id')}' is invalid; "
                    f"regenerating it ({exc})."
                )

    response = generate_json(
        prompt=prompt,
        response_schema=FinalKeywordGroupResponse,
        system_instruction=SPLIT_GROUP_SYSTEM_PROMPT,
    )

    validate_split_groups(
        group,
        response,
    )

    if cache_path is not None:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = cache_path.with_suffix(".tmp")
        temporary_path.write_text(
            json.dumps(response.model_dump(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        temporary_path.replace(cache_path)

    return [
        item.model_dump()
        for item in response.groups
    ]
