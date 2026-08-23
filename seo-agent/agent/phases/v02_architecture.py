"""
v0.2 — Final Site Architecture Planner.

This module converts the research and semantic keyword analysis
produced by v0.1 and v0.2 into the final SEO site architecture.

Pipeline:

    v0.1 research
          ↓
    SiteProfile
          ↓
    semantic keyword groups
          ↓
    keyword group audit
          ↓
    resolve split groups
          ↓
    final page architecture
          ↓
    validation
          ↓
    site_architecture.json

Important:

- This module is designed for a brand-new website.
- It does NOT require an existing website.
- It does NOT generate page content.
- It does NOT build the frontend.
- It decides which pages the future website should contain.
"""


import json
import os
import re
from typing import Any, Dict, List

from pydantic import BaseModel, Field

from core.llm import generate_json


# ============================================================
# PATHS
# ============================================================

V01_OUTPUT_PATH = os.path.join(
    "outputs",
    "page_opportunities.json",
)

V02_OUTPUT_DIR = os.path.join(
    "outputs",
    "v02",
)

SITE_PROFILE_PATH = os.path.join(
    V02_OUTPUT_DIR,
    "site_profile.json",
)

KEYWORD_GROUPS_PATH = os.path.join(
    V02_OUTPUT_DIR,
    "keyword_groups.json",
)

GROUP_AUDIT_PATH = os.path.join(
    V02_OUTPUT_DIR,
    "keyword_group_audit.json",
)

ARCHITECTURE_PATH = os.path.join(
    V02_OUTPUT_DIR,
    "site_architecture.json",
)


# ============================================================
# PYDANTIC SCHEMAS
# ============================================================


class FinalKeywordGroup(BaseModel):
    """
    Represents one final page group produced when a proposed
    semantic group needs to be split into multiple pages.
    """

    group_id: str = Field(
        description="Unique ID for the final page group."
    )

    primary_keyword: str = Field(
        description="Primary keyword targeted by this page."
    )

    secondary_keywords: List[str] = Field(
        default_factory=list,
        description="Closely related keywords targeted by the page."
    )

    page_type: str = Field(
        description="Recommended page type."
    )

    reasoning: str = Field(
        description="Why these keywords belong on one page."
    )


class FinalKeywordGroupResponse(BaseModel):
    """
    Structured response containing the final groups after
    resolving a group marked as split.
    """

    groups: List[FinalKeywordGroup] = Field(
        default_factory=list
    )


# ============================================================
# PROMPT
# ============================================================

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


# ============================================================
# FILE HELPERS
# ============================================================


def load_json_file(
    path: str,
) -> Dict[str, Any]:
    """
    Load a JSON object from disk.

    Args:
        path:
            Path to the JSON file.

    Returns:
        Parsed JSON dictionary.

    Raises:
        FileNotFoundError:
            If the file does not exist.

        ValueError:
            If the file does not contain a JSON object.
    """

    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Required file was not found: {path}"
        )

    try:
        with open(
            path,
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Invalid JSON file: {path}"
        ) from exc

    if not isinstance(data, dict):
        raise ValueError(
            f"Expected a JSON object in: {path}"
        )

    return data


def save_json_file(
    path: str,
    data: Dict[str, Any],
) -> None:
    """
    Save a JSON object to disk.

    Args:
        path:
            Destination file path.

        data:
            Dictionary to serialize.
    """

    directory = os.path.dirname(path)

    if directory:
        os.makedirs(
            directory,
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
# SLUGGING
# ============================================================


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


# ============================================================
# NORMALIZATION
# ============================================================


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


# ============================================================
# DATA LOADERS
# ============================================================


def load_v01_research() -> Dict[str, Any]:
    """
    Load the keyword/page opportunity research produced by v0.1.
    """

    return load_json_file(
        V01_OUTPUT_PATH
    )


def load_site_profile() -> Dict[str, Any]:
    """
    Load the SiteProfile produced during the v0.2 foundation stage.
    """

    return load_json_file(
        SITE_PROFILE_PATH
    )


def load_keyword_groups() -> Dict[str, Any]:
    """
    Load the semantic keyword groups produced by v0.2 grouping.
    """

    return load_json_file(
        KEYWORD_GROUPS_PATH
    )


def load_group_audit() -> Dict[str, Any]:
    """
    Load the keyword group audit produced by the audit stage.
    """

    return load_json_file(
        GROUP_AUDIT_PATH
    )


# ============================================================
# V0.1 KEYWORD LOOKUP
# ============================================================


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


# ============================================================
# PRIORITY
# ============================================================


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


# ============================================================
# CLUSTER ROOT PAGE
# ============================================================


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


# ============================================================
# GROUP HELPERS
# ============================================================


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


# ============================================================
# SPLIT GROUP RESOLUTION
# ============================================================


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

    response = generate_json(
        prompt=prompt,
        response_schema=FinalKeywordGroupResponse,
        system_instruction=SPLIT_GROUP_SYSTEM_PROMPT,
    )

    validate_split_groups(
        group,
        response,
    )

    return [
        item.model_dump()
        for item in response.groups
    ]


# ============================================================
# FINAL PAGE CREATION
# ============================================================


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


# ============================================================
# CLUSTER ARCHITECTURE
# ============================================================


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


# ============================================================
# FINAL ARCHITECTURE
# ============================================================


def build_site_architecture(
    research: Dict[str, Any],
    site_profile: Dict[str, Any],
    keyword_groups: Dict[str, Any],
    audit_data: Dict[str, Any],
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
        "source_files": {
            "research": V01_OUTPUT_PATH,
            "keyword_groups": KEYWORD_GROUPS_PATH,
            "group_audit": GROUP_AUDIT_PATH,
        },
    }


# ============================================================
# VALIDATION
# ============================================================


def validate_architecture(
    architecture: Dict[str, Any],
) -> None:
    """
    Validate the final architecture.

    Checks:

    - page IDs are unique
    - URLs are unique
    - every page has a URL
    - every child references an existing parent
    - every non-cluster page has a primary keyword
    - every page is indexable only when it has a valid URL
    """

    pages = architecture.get(
        "pages",
        [],
    )

    page_ids = set()
    urls = set()

    for page in pages:
        page_id = page.get(
            "id"
        )

        url = page.get(
            "url"
        )

        if not page_id:
            raise ValueError(
                "Architecture contains a page without an ID."
            )

        if page_id in page_ids:
            raise ValueError(
                f"Duplicate page ID: {page_id}"
            )

        page_ids.add(
            page_id
        )

        if not url:
            raise ValueError(
                f"Page has no URL: {page_id}"
            )

        if url in urls:
            raise ValueError(
                f"Duplicate URL: {url}"
            )

        urls.add(
            url
        )

        if page.get(
            "page_type"
        ) != "cluster":

            if not page.get(
                "primary_keyword"
            ):
                raise ValueError(
                    f"Non-cluster page has no primary keyword: "
                    f"{page_id}"
                )

    for page in pages:
        parent_id = page.get(
            "parent_page_id"
        )

        if parent_id is not None:
            if parent_id not in page_ids:
                raise ValueError(
                    f"Page '{page['id']}' references "
                    f"missing parent '{parent_id}'."
                )


# ============================================================
# COVERAGE VALIDATION
# ============================================================


def validate_keyword_coverage(
    keyword_groups: Dict[str, Any],
    architecture: Dict[str, Any],
) -> None:
    """
    Validate that every keyword from the final semantic groups is
    represented by at least one architecture page.

    This protects against accidental keyword loss during the
    architecture transformation.
    """

    expected = set()

    for cluster in keyword_groups.get(
        "clusters",
        [],
    ):
        for group in cluster.get(
            "groups",
            [],
        ):
            for keyword in collect_group_keywords(
                group
            ):
                expected.add(
                    normalize_keyword(
                        keyword
                    )
                )

    actual = set()

    for page in architecture.get(
        "pages",
        [],
    ):
        primary = page.get(
            "primary_keyword"
        )

        if primary:
            actual.add(
                normalize_keyword(
                    primary
                )
            )

        for keyword in page.get(
            "secondary_keywords",
            [],
        ):
            actual.add(
                normalize_keyword(
                    keyword
                )
            )

    missing = expected - actual

    if missing:
        raise ValueError(
            "Final architecture lost keywords: "
            + ", ".join(
                sorted(missing)
            )
        )


# ============================================================
# ENTRY POINT
# ============================================================


def run_v02_architecture() -> Dict[str, Any]:
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

    research = load_v01_research()

    print(
        "  ✓ Research loaded"
    )

    print(
        "\n[Step 2] Loading SiteProfile..."
    )

    site_profile = load_site_profile()

    print(
        f"  ✓ Site model: "
        f"{site_profile.get('site_model')}"
    )

    print(
        "\n[Step 3] Loading semantic keyword groups..."
    )

    keyword_groups = load_keyword_groups()

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

    audit_data = load_group_audit()

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

    save_json_file(
        ARCHITECTURE_PATH,
        architecture,
    )

    print(
        f"  ✓ Saved: {ARCHITECTURE_PATH}"
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


if __name__ == "__main__":
    run_v02_architecture()