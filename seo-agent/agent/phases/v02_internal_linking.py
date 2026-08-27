"""
v0.2 — Internal Linking Architecture.

This module creates an internal linking plan for a brand-new website.

The website does not need to exist yet. The module uses the URL
architecture and final page architecture generated earlier in v0.2
to determine which pages should link to each other.

The output is a structured internal_linking.json file that can later
be consumed by v0.3 during content generation.

Design principles:
    - Cluster pages act as topical hubs.
    - Content pages link back to their cluster page.
    - Related pages within the same cluster can link to each other.
    - Links should be contextually relevant.
    - Anchor text should be based on existing keywords.
    - The system should avoid unnecessary/random links.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any


# ---------------------------------------------------------------------
# PATH CONFIGURATION
# ---------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

V02_OUTPUT_DIR = BASE_DIR / "outputs" / "v02"

URL_ARCHITECTURE_FILE = (
    V02_OUTPUT_DIR / "url_architecture.json"
)

SITE_ARCHITECTURE_FILE = (
    V02_OUTPUT_DIR / "site_architecture.json"
)

OUTPUT_FILE = (
    V02_OUTPUT_DIR / "internal_linking.json"
)


# ---------------------------------------------------------------------
# FILE HELPERS
# ---------------------------------------------------------------------

def load_json(file_path: Path) -> Dict[str, Any]:
    """
    Load a JSON file from disk.

    Args:
        file_path: Path to the JSON file.

    Returns:
        Parsed JSON data as a dictionary.

    Raises:
        FileNotFoundError:
            If the requested file does not exist.

        json.JSONDecodeError:
            If the file does not contain valid JSON.
    """

    if not file_path.exists():
        raise FileNotFoundError(
            f"Required file not found: {file_path}"
        )

    with open(
        file_path,
        "r",
        encoding="utf-8"
    ) as file:
        return json.load(file)


def save_json(
    data: Dict[str, Any],
    file_path: Path
) -> None:
    """
    Save a dictionary as formatted JSON.

    Args:
        data: Data to save.
        file_path: Destination path.
    """

    file_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        file_path,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            data,
            file,
            indent=2,
            ensure_ascii=False
        )


# ---------------------------------------------------------------------
# TEXT / KEYWORD HELPERS
# ---------------------------------------------------------------------

def normalize_text(text: str) -> str:
    """
    Normalize text so it can be compared reliably.

    Lowercases the text and removes punctuation.

    Args:
        text: Input text.

    Returns:
        Normalized text.
    """

    if not text:
        return ""

    text = text.lower()

    text = re.sub(
        r"[^a-z0-9\s-]",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


def keyword_tokens(keyword: str) -> set:
    """
    Convert a keyword into a set of normalized words.

    Very short/common words are removed because they provide little
    evidence that two pages are topically related.

    Args:
        keyword: Keyword string.

    Returns:
        Set of meaningful keyword tokens.
    """

    stop_words = {
        "the",
        "a",
        "an",
        "to",
        "for",
        "of",
        "in",
        "on",
        "and",
        "or",
        "is",
        "are",
        "what",
        "how",
        "where",
        "can",
        "you",
        "with",
        "online",
        "best",
        "app",
        "apps",
    }

    normalized = normalize_text(keyword)

    return {
        word
        for word in normalized.split()
        if len(word) > 2
        and word not in stop_words
    }


def keyword_similarity(
    keyword_a: str,
    keyword_b: str
) -> float:
    """
    Calculate a simple lexical similarity between two keywords.

    This is intentionally lightweight and deterministic. It is used
    to identify obviously related pages without requiring an LLM.

    Args:
        keyword_a: First keyword.
        keyword_b: Second keyword.

    Returns:
        Similarity score between 0.0 and 1.0.
    """

    tokens_a = keyword_tokens(keyword_a)
    tokens_b = keyword_tokens(keyword_b)

    if not tokens_a or not tokens_b:
        return 0.0

    intersection = tokens_a.intersection(tokens_b)

    union = tokens_a.union(tokens_b)

    if not union:
        return 0.0

    return len(intersection) / len(union)


# ---------------------------------------------------------------------
# PAGE EXTRACTION
# ---------------------------------------------------------------------

def extract_pages(
    site_architecture: Dict[str, Any],
    url_architecture: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Extract and merge page information from the architecture files.

    The URL architecture provides canonical URL information while the
    site architecture provides semantic information such as secondary
    keywords and audit metadata.

    Args:
        site_architecture:
            Final site architecture data.

        url_architecture:
            URL architecture data.

    Returns:
        List of normalized page dictionaries.
    """

    site_pages = {
        page["id"]: page
        for page in site_architecture.get(
            "pages",
            []
        )
    }

    pages = []

    for url_page in url_architecture.get(
        "urls",
        []
    ):
        page_id = url_page["page_id"]

        semantic_page = site_pages.get(
            page_id,
            {}
        )

        merged_page = {
            **semantic_page,
            **url_page,
        }

        pages.append(merged_page)

    return pages


# ---------------------------------------------------------------------
# LINK CREATION
# ---------------------------------------------------------------------

def create_link(
    source_page: Dict[str, Any],
    target_page: Dict[str, Any],
    anchor_text: str,
    relationship: str,
    reason: str,
    priority: str
) -> Dict[str, Any]:
    """
    Create a single internal-link recommendation.

    Args:
        source_page:
            Page where the link will originate.

        target_page:
            Page the link will point to.

        anchor_text:
            Suggested anchor text.

        relationship:
            Type of relationship between the pages.

        reason:
            Explanation for why the link is useful.

        priority:
            Importance of the link.

    Returns:
        Structured internal-link recommendation.
    """

    return {
        "source_page_id": source_page["id"],
        "source_url": source_page["url"],
        "target_page_id": target_page["id"],
        "target_url": target_page["url"],
        "anchor_text": anchor_text,
        "relationship": relationship,
        "reason": reason,
        "priority": priority,
    }


def get_anchor_text(
    target_page: Dict[str, Any]
) -> str:
    """
    Determine the preferred anchor text for a target page.

    Primary keyword is preferred when available. Otherwise the page
    title is used.

    Args:
        target_page:
            Target page metadata.

    Returns:
        Suggested anchor text.
    """

    primary_keyword = target_page.get(
        "primary_keyword"
    )

    if primary_keyword:
        return primary_keyword

    return target_page.get(
        "title",
        target_page["slug"]
    )


# ---------------------------------------------------------------------
# CLUSTER LINKING
# ---------------------------------------------------------------------

def create_cluster_links(
    pages: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Create parent-child links between cluster pages and content pages.

    Every content page inside a cluster should link back to its cluster
    hub. The cluster hub should also link to its child pages.

    Args:
        pages:
            All pages in the architecture.

    Returns:
        List of cluster-based links.
    """

    links = []

    clusters = [
        page
        for page in pages
        if page.get("page_type") == "cluster"
    ]

    for cluster in clusters:

        child_pages = [
            page
            for page in pages
            if page.get("parent_page_id")
            == cluster["id"]
        ]

        # -------------------------------------------------------------
        # Child → Cluster
        # -------------------------------------------------------------

        for child in child_pages:

            links.append(
                create_link(
                    source_page=child,
                    target_page=cluster,
                    anchor_text=cluster["title"],
                    relationship="cluster_parent",
                    reason=(
                        "The content page belongs to this topical "
                        "cluster and should link back to the cluster "
                        "hub."
                    ),
                    priority="high",
                )
            )

        # -------------------------------------------------------------
        # Cluster → Child
        # -------------------------------------------------------------

        for child in child_pages:

            links.append(
                create_link(
                    source_page=cluster,
                    target_page=child,
                    anchor_text=get_anchor_text(child),
                    relationship="cluster_child",
                    reason=(
                        "The cluster page acts as a topical hub and "
                        "should provide navigation to its supporting "
                        "content pages."
                    ),
                    priority="high",
                )
            )

    return links


# ---------------------------------------------------------------------
# RELATED PAGE LINKING
# ---------------------------------------------------------------------

def calculate_page_similarity(
    page_a: Dict[str, Any],
    page_b: Dict[str, Any]
) -> float:
    """
    Calculate topical similarity between two content pages.

    The calculation considers:
        - Primary keywords
        - Secondary keywords
        - Search intent
        - Page type

    Args:
        page_a:
            First page.

        page_b:
            Second page.

    Returns:
        Similarity score between 0.0 and 1.0.
    """

    primary_a = page_a.get(
        "primary_keyword",
        ""
    )

    primary_b = page_b.get(
        "primary_keyword",
        ""
    )

    score = keyword_similarity(
        primary_a,
        primary_b
    )

    secondary_a = page_a.get(
        "secondary_keywords",
        []
    )

    secondary_b = page_b.get(
        "secondary_keywords",
        []
    )

    secondary_scores = []

    for keyword_a in secondary_a:

        for keyword_b in secondary_b:

            similarity = keyword_similarity(
                keyword_a,
                keyword_b
            )

            if similarity > 0:
                secondary_scores.append(
                    similarity
                )

    if secondary_scores:

        score = max(
            score,
            max(secondary_scores)
        )

    # Same search intent is a useful relevance signal.
    intent_a = page_a.get("intent")
    intent_b = page_b.get("intent")

    if (
        intent_a
        and intent_b
        and intent_a == intent_b
    ):
        score += 0.10

    # Keep score bounded.
    return min(
        score,
        1.0
    )


def create_related_links(
    pages: List[Dict[str, Any]],
    minimum_similarity: float = 0.20
) -> List[Dict[str, Any]]:
    """
    Create contextual links between related content pages.

    Only pages within the same cluster are compared. Cluster pages
    themselves are handled separately.

    Args:
        pages:
            All pages in the architecture.

        minimum_similarity:
            Minimum similarity required before creating a link.

    Returns:
        List of related-page links.
    """

    links = []

    content_pages = [
        page
        for page in pages
        if page.get("page_type") != "cluster"
    ]

    for index, source_page in enumerate(content_pages):

        for target_page in content_pages[index + 1:]:

            # ---------------------------------------------------------
            # Only compare pages within the same cluster.
            # ---------------------------------------------------------

            if (
                source_page.get("cluster")
                != target_page.get("cluster")
            ):
                continue

            similarity = calculate_page_similarity(
                source_page,
                target_page
            )

            if similarity < minimum_similarity:
                continue

            # ---------------------------------------------------------
            # Create bidirectional contextual links.
            # ---------------------------------------------------------

            links.append(
                create_link(
                    source_page=source_page,
                    target_page=target_page,
                    anchor_text=get_anchor_text(
                        target_page
                    ),
                    relationship="related_content",
                    reason=(
                        "The pages have overlapping topical or "
                        "search-intent signals and can provide useful "
                        "contextual navigation for users."
                    ),
                    priority="medium",
                )
            )

            links.append(
                create_link(
                    source_page=target_page,
                    target_page=source_page,
                    anchor_text=get_anchor_text(
                        source_page
                    ),
                    relationship="related_content",
                    reason=(
                        "The pages have overlapping topical or "
                        "search-intent signals and can provide useful "
                        "contextual navigation for users."
                    ),
                    priority="medium",
                )
            )

    return links


# ---------------------------------------------------------------------
# LINK VALIDATION
# ---------------------------------------------------------------------

def remove_duplicate_links(
    links: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Remove duplicate source-target link recommendations.

    Args:
        links:
            List of link recommendations.

    Returns:
        Deduplicated list.
    """

    unique_links = {}

    for link in links:

        key = (
            link["source_page_id"],
            link["target_page_id"],
        )

        if key not in unique_links:
            unique_links[key] = link

    return list(
        unique_links.values()
    )


def validate_links(
    links: List[Dict[str, Any]],
    pages: List[Dict[str, Any]]
) -> None:
    """
    Validate the internal-link graph.

    Ensures:
        - Source pages exist.
        - Target pages exist.
        - A page never links to itself.
        - All target URLs are valid architecture URLs.

    Args:
        links:
            Internal-link recommendations.

        pages:
            Architecture pages.

    Raises:
        ValueError:
            If the linking graph contains invalid references.
    """

    page_ids = {
        page["id"]
        for page in pages
    }

    for link in links:

        source_id = link[
            "source_page_id"
        ]

        target_id = link[
            "target_page_id"
        ]

        if source_id not in page_ids:
            raise ValueError(
                f"Invalid source page: {source_id}"
            )

        if target_id not in page_ids:
            raise ValueError(
                f"Invalid target page: {target_id}"
            )

        if source_id == target_id:
            raise ValueError(
                f"Self-link detected: {source_id}"
            )


# ---------------------------------------------------------------------
# SUMMARY GENERATION
# ---------------------------------------------------------------------

def build_summary(
    pages: List[Dict[str, Any]],
    links: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Build summary statistics for the internal-linking plan.

    Args:
        pages:
            Architecture pages.

        links:
            Generated links.

    Returns:
        Summary dictionary.
    """

    cluster_count = len([
        page
        for page in pages
        if page.get("page_type") == "cluster"
    ])

    content_count = len(pages) - cluster_count

    inbound_counts = {
        page["id"]: 0
        for page in pages
    }

    outbound_counts = {
        page["id"]: 0
        for page in pages
    }

    for link in links:

        outbound_counts[
            link["source_page_id"]
        ] += 1

        inbound_counts[
            link["target_page_id"]
        ] += 1

    return {
        "total_pages": len(pages),
        "cluster_pages": cluster_count,
        "content_pages": content_count,
        "total_links": len(links),
        "average_links_per_page": (
            round(
                len(links) / len(pages),
                2
            )
            if pages
            else 0
        ),
        "pages_without_outbound_links": [
            page_id
            for page_id, count
            in outbound_counts.items()
            if count == 0
        ],
        "pages_without_inbound_links": [
            page_id
            for page_id, count
            in inbound_counts.items()
            if count == 0
        ],
    }


# ---------------------------------------------------------------------
# MAIN PIPELINE
# ---------------------------------------------------------------------

def main() -> None:
    """
    Execute the complete v0.2 internal-linking pipeline.

    Pipeline:

        1. Load URL architecture.
        2. Load final site architecture.
        3. Merge page metadata.
        4. Create cluster links.
        5. Create contextual related-page links.
        6. Remove duplicates.
        7. Validate the link graph.
        8. Build summary.
        9. Save internal_linking.json.
    """

    print("=" * 60)
    print("        V0.2 — INTERNAL LINKING ARCHITECTURE")
    print("=" * 60)

    # -------------------------------------------------------------
    # Step 1
    # -------------------------------------------------------------

    print("\n[Step 1] Loading URL architecture...")

    url_architecture = load_json(
        URL_ARCHITECTURE_FILE
    )

    print("  ✓ URL architecture loaded")

    # -------------------------------------------------------------
    # Step 2
    # -------------------------------------------------------------

    print("\n[Step 2] Loading site architecture...")

    site_architecture = load_json(
        SITE_ARCHITECTURE_FILE
    )

    print("  ✓ Site architecture loaded")

    # -------------------------------------------------------------
    # Step 3
    # -------------------------------------------------------------

    print("\n[Step 3] Preparing page metadata...")

    pages = extract_pages(
        site_architecture,
        url_architecture
    )

    print(
        f"  ✓ Loaded {len(pages)} pages"
    )

    # -------------------------------------------------------------
    # Step 4
    # -------------------------------------------------------------

    print("\n[Step 4] Creating cluster links...")

    cluster_links = create_cluster_links(
        pages
    )

    print(
        f"  ✓ Generated {len(cluster_links)} cluster links"
    )

    # -------------------------------------------------------------
    # Step 5
    # -------------------------------------------------------------

    print("\n[Step 5] Finding related pages...")

    related_links = create_related_links(
        pages
    )

    print(
        f"  ✓ Generated {len(related_links)} related links"
    )

    # -------------------------------------------------------------
    # Step 6
    # -------------------------------------------------------------

    print("\n[Step 6] Removing duplicate links...")

    links = remove_duplicate_links(
        cluster_links + related_links
    )

    print(
        f"  ✓ Final links: {len(links)}"
    )

    # -------------------------------------------------------------
    # Step 7
    # -------------------------------------------------------------

    print("\n[Step 7] Validating link graph...")

    validate_links(
        links,
        pages
    )

    print("  ✓ Link graph is valid")

    # -------------------------------------------------------------
    # Step 8
    # -------------------------------------------------------------

    print("\n[Step 8] Building summary...")

    summary = build_summary(
        pages,
        links
    )

    print(
        f"  ✓ Total pages: "
        f"{summary['total_pages']}"
    )

    print(
        f"  ✓ Total internal links: "
        f"{summary['total_links']}"
    )

    # -------------------------------------------------------------
    # Step 9
    # -------------------------------------------------------------

    output = {
        "version": "0.2",
        "architecture_type": "internal_linking",
        "site_status": "brand_new",
        "linking_strategy": (
            "cluster_hubs_plus_contextual_related_pages"
        ),
        "summary": summary,
        "links": links,
        "source_files": {
            "url_architecture": str(
                URL_ARCHITECTURE_FILE
                .relative_to(BASE_DIR)
            ),
            "site_architecture": str(
                SITE_ARCHITECTURE_FILE
                .relative_to(BASE_DIR)
            ),
        },
    }

    print("\n[Step 9] Saving internal-linking plan...")

    save_json(
        output,
        OUTPUT_FILE
    )

    print(
        f"  ✓ Saved: {OUTPUT_FILE}"
    )

    print("\n" + "=" * 60)
    print("        INTERNAL LINKING COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()