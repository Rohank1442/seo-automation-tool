"""Build cluster and page records, then assemble the final site architecture."""

import re
from typing import Any, Dict, List, Optional

from .group_splitting import resolve_split_group
from .inputs import (
    V01_OUTPUT_PATH,
    KEYWORD_GROUPS_PATH,
    GROUP_AUDIT_PATH,
)
from .keywords import (
    build_audit_lookup,
    build_keyword_lookup,
    determine_page_priority,
    normalize_keyword,
)


def slugify(
    value: str,
) -> str:
    """
    Convert human-readable text into a URL-safe slug.

    Example:

        "What Is Virtual Try On"
        ->
        "what-is-virtual-try-on"
    """

    value = value.lower().strip()

    value = re.sub(
        r"[^a-z0-9\s-]",
        "",
        value,
    )

    value = re.sub(
        r"\s+",
        "-",
        value,
    )

    value = re.sub(
        r"-+",
        "-",
        value,
    )

    return value.strip("-")


def create_cluster_root_page(
    cluster_name: str,
) -> Dict[str, Any]:
    """
    Create the root page for a topic cluster.

    The website is assumed to be brand new, so this page is
    planned as part of the future site rather than representing
    an existing URL.
    """

    slug = slugify(
        cluster_name
    )

    return {
        "id": f"cluster:{slug}",
        "title": cluster_name,
        "slug": slug,
        "url": f"/{slug}/",
        "page_type": "cluster",
        "cluster": cluster_name,
        "parent_page_id": None,
        "primary_keyword": None,
        "secondary_keywords": [],
        "intent": "mixed",
        "priority": "high",
        "indexable": True,
        "content_status": "planned",
    }


def create_final_page(
    group: Dict[str, Any],
    cluster_name: str,
    parent_page_id: str,
    audit: Dict[str, Any],
    keyword_lookup: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Create one final page from one validated semantic keyword group.
    """

    primary_keyword = str(
        group.get(
            "primary_keyword",
            "",
        )
    ).strip()

    if not primary_keyword:
        raise ValueError(
            "Final keyword group has no primary keyword."
        )

    slug = slugify(
        primary_keyword
    )

    group_id = str(
        group.get(
            "group_id",
            slug,
        )
    )

    intent = keyword_lookup.get(
        normalize_keyword(
            primary_keyword
        ),
        {},
    ).get(
        "intent"
    )

    return {
        "id": f"page:{group_id}",
        "title": primary_keyword.title(),
        "slug": slug,
        "url": f"/{slug}/",
        "page_type": group.get(
            "page_type",
            "guide",
        ),
        "cluster": cluster_name,
        "parent_page_id": parent_page_id,
        "primary_keyword": primary_keyword,
        "secondary_keywords": group.get(
            "secondary_keywords",
            [],
        ),
        "intent": intent,
        "priority": determine_page_priority(
            primary_keyword,
            keyword_lookup,
        ),
        "indexable": True,
        "content_status": "planned",

        # Information used by later phases.
        "source_group_id": group_id,
        "audit_status": audit.get(
            "status"
        ),
        "audit_confidence": audit.get(
            "confidence"
        ),
        "group_reasoning": group.get(
            "reasoning",
            "",
        ),
    }


def build_cluster_architecture(
    cluster_name: str,
    groups: List[Dict[str, Any]],
    audit_lookup: Dict[str, Dict[str, Any]],
    keyword_lookup: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Build the final page hierarchy for one topic cluster.

    The hierarchy is:

        Cluster root
            ├── Semantic page
            ├── Semantic page
            └── Semantic page

    Approved and review groups become one page.

    Split groups are sent through Gemini again so they can be
    divided into multiple coherent final pages.
    """

    cluster_page = create_cluster_root_page(
        cluster_name
    )

    pages = [
        cluster_page
    ]

    final_groups: List[Dict[str, Any]] = []

    for group in groups:
        group_id = group.get(
            "group_id"
        )

        if not group_id:
            continue

        audit = audit_lookup.get(
            group_id,
            {},
        )

        status = audit.get(
            "status",
            "review",
        )

        if status == "split":
            print(
                f"  • Splitting group: {group_id}"
            )

            resolved_groups = resolve_split_group(
                cluster_name,
                group,
                audit,
            )

            print(
                f"    ✓ Split into "
                f"{len(resolved_groups)} final groups"
            )

            final_groups.extend(
                resolved_groups
            )

        else:
            final_groups.append(
                {
                    "group_id": group_id,
                    "primary_keyword": group.get(
                        "primary_keyword"
                    ),
                    "secondary_keywords": group.get(
                        "secondary_keywords",
                        [],
                    ),
                    "page_type": group.get(
                        "page_type",
                        "guide",
                    ),
                    "reasoning": group.get(
                        "reasoning",
                        "",
                    ),
                }
            )

    for group in final_groups:
        group_id = group.get(
            "group_id"
        )

        original_audit = audit_lookup.get(
            group_id,
            {},
        )

        # A split group receives its original audit if the final
        # group ID starts with the original group ID.
        if not original_audit:
            for original_id, audit in audit_lookup.items():
                if group_id.startswith(
                    original_id
                ):
                    original_audit = audit
                    break

        page = create_final_page(
            group,
            cluster_name,
            cluster_page["id"],
            original_audit,
            keyword_lookup,
        )

        pages.append(
            page
        )

    return {
        "cluster": cluster_page,
        "pages": pages,
    }


def build_site_architecture(
    research: Dict[str, Any],
    site_profile: Dict[str, Any],
    keyword_groups: Dict[str, Any],
    audit_data: Dict[str, Any],
    source_files: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Build the final SEO architecture using the outputs of the
    semantic grouping and audit stages.

    This is the key change from the previous implementation:

    The architecture is no longer built one keyword at a time.

    Instead:

        keywords
            ↓
        semantic groups
            ↓
        audit
            ↓
        final pages
    """

    keyword_lookup = build_keyword_lookup(
        research
    )

    audit_lookup = build_audit_lookup(
        audit_data
    )

    grouped_clusters = keyword_groups.get(
        "clusters",
        [],
    )

    all_pages: List[Dict[str, Any]] = []
    cluster_architectures: List[Dict[str, Any]] = []

    for cluster in grouped_clusters:
        if not isinstance(
            cluster,
            dict,
        ):
            continue

        cluster_name = str(
            cluster.get(
                "cluster",
                "",
            )
        ).strip()

        if not cluster_name:
            continue

        print(
            f"\nBuilding final architecture for "
            f"'{cluster_name}'..."
        )

        architecture = build_cluster_architecture(
            cluster_name,
            cluster.get(
                "groups",
                [],
            ),
            audit_lookup,
            keyword_lookup,
        )

        cluster_architectures.append(
            architecture
        )

        all_pages.extend(
            architecture["pages"]
        )

    return {
        "version": "0.2",
        "architecture_method": "semantic_groups_plus_audit",
        "site_status": "brand_new",
        "site_profile": site_profile,
        "clusters": cluster_architectures,
        "pages": all_pages,
        "page_count": len(all_pages),
        "source_files": source_files or {
            "research": V01_OUTPUT_PATH,
            "keyword_groups": KEYWORD_GROUPS_PATH,
            "group_audit": GROUP_AUDIT_PATH,
        },
    }
