"""Normalize and look up keyword, audit, and priority data for architecture."""

import re
from typing import Any, Dict, List


def normalize_keyword(
    keyword: str,
) -> str:
    """
    Normalize keyword text for comparisons.

    This prevents duplicate detection from being affected by
    capitalization or whitespace differences.
    """

    return re.sub(
        r"\s+",
        " ",
        keyword.lower().strip(),
    )


def build_keyword_lookup(
    research: Dict[str, Any],
) -> Dict[str, Dict[str, Any]]:
    """
    Build a normalized keyword lookup from v0.1 research.

    This lets the architecture stage recover metrics such as
    volume, competition, and intent for grouped keywords.
    """

    lookup: Dict[str, Dict[str, Any]] = {}

    for cluster in research.get(
        "clusters",
        [],
    ):
        if not isinstance(
            cluster,
            dict,
        ):
            continue

        for item in cluster.get(
            "keywords",
            [],
        ):
            if isinstance(
                item,
                str,
            ):
                keyword = item
                data = {
                    "keyword": item
                }

            elif isinstance(
                item,
                dict,
            ):
                keyword = item.get(
                    "keyword"
                )
                data = item

            else:
                continue

            if not keyword:
                continue

            lookup[
                normalize_keyword(
                    str(keyword)
                )
            ] = data

    return lookup


def determine_page_priority(
    primary_keyword: str,
    keyword_lookup: Dict[str, Dict[str, Any]],
) -> str:
    """
    Determine page priority using available v0.1 keyword metrics.

    The function remains conservative when metrics are unavailable.
    """

    data = keyword_lookup.get(
        normalize_keyword(
            primary_keyword
        ),
        {},
    )

    volume = data.get(
        "volume"
    )

    competition_level = str(
        data.get(
            "competition_level",
            "",
        )
    ).lower()

    if isinstance(
        volume,
        (int, float),
    ):
        if volume >= 1000:
            if competition_level in {
                "low",
                "medium",
            }:
                return "high"

        if volume >= 300:
            return "medium"

        return "low"

    return "medium"


def collect_group_keywords(
    group: Dict[str, Any],
) -> List[str]:
    """
    Collect every keyword explicitly assigned to a semantic group.

    The primary keyword and secondary keywords are combined with
    the detailed keyword records, then duplicates are removed.
    """

    keywords: List[str] = []

    primary = group.get(
        "primary_keyword"
    )

    if primary:
        keywords.append(
            str(primary)
        )

    for keyword in group.get(
        "secondary_keywords",
        [],
    ):
        if keyword:
            keywords.append(
                str(keyword)
            )

    for item in group.get(
        "keywords",
        [],
    ):
        if isinstance(
            item,
            dict,
        ):
            keyword = item.get(
                "keyword"
            )

            if keyword:
                keywords.append(
                    str(keyword)
                )

    seen = set()
    result = []

    for keyword in keywords:
        normalized = normalize_keyword(
            keyword
        )

        if normalized in seen:
            continue

        seen.add(
            normalized
        )

        result.append(
            keyword
        )

    return result


def build_audit_lookup(
    audit_data: Dict[str, Any],
) -> Dict[str, Dict[str, Any]]:
    """
    Create a lookup from group ID to its audit result.
    """

    lookup: Dict[str, Dict[str, Any]] = {}

    for cluster in audit_data.get(
        "clusters",
        [],
    ):
        if not isinstance(
            cluster,
            dict,
        ):
            continue

        for audit in cluster.get(
            "audits",
            [],
        ):
            if not isinstance(
                audit,
                dict,
            ):
                continue

            group_id = audit.get(
                "group_id"
            )

            if group_id:
                lookup[
                    group_id
                ] = audit

    return lookup
