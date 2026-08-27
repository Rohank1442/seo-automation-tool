"""
v0.2 — URL Architecture.

This module converts the final site architecture into a validated
URL architecture for a brand-new website.

Input:
    outputs/v02/site_architecture.json

Output:
    outputs/v02/url_architecture.json

The website does not exist yet, so this module does NOT crawl an
existing website or modify existing URLs. It establishes the URL
structure that the future website will use.
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import urlparse


# ============================================================
# PATH CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

ARCHITECTURE_PATH = (
    BASE_DIR
    / "outputs"
    / "v02"
    / "site_architecture.json"
)

URL_ARCHITECTURE_PATH = (
    BASE_DIR
    / "outputs"
    / "v02"
    / "url_architecture.json"
)


# ============================================================
# FILE HELPERS
# ============================================================


def load_json_file(
    path: Path,
) -> Dict[str, Any]:
    """
    Load a JSON file from disk.

    Args:
        path: Path to the JSON file.

    Returns:
        Parsed JSON object.

    Raises:
        FileNotFoundError:
            If the file does not exist.
        ValueError:
            If the JSON does not contain an object.
    """

    if not path.exists():
        raise FileNotFoundError(
            f"Required file not found: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError(
            f"Expected JSON object in: {path}"
        )

    return data


def save_json_file(
    path: Path,
    data: Dict[str, Any],
) -> None:
    """
    Save a dictionary as formatted JSON.

    Args:
        path: Destination file path.
        data: Dictionary to save.
    """

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
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
# URL NORMALIZATION
# ============================================================


def normalize_url(
    url: str,
) -> str:
    """
    Normalize a relative website URL.

    The generated URL architecture uses:
        /page-name/

    This function ensures that:
    - the URL starts with /
    - the URL ends with /
    - duplicate slashes are removed
    - whitespace is removed
    - query parameters are removed
    - fragments are removed

    Args:
        url: Raw relative URL.

    Returns:
        Normalized relative URL.
    """

    if not isinstance(url, str):
        raise ValueError(
            "URL must be a string."
        )

    url = url.strip()

    if not url:
        raise ValueError(
            "URL cannot be empty."
        )

    parsed = urlparse(url)

    # Reject absolute URLs because this stage stores
    # relative URL architecture.
    if parsed.scheme or parsed.netloc:
        raise ValueError(
            f"Expected relative URL, got absolute URL: {url}"
        )

    path = parsed.path

    # Ensure leading slash.
    if not path.startswith("/"):
        path = "/" + path

    # Collapse repeated slashes.
    path = re.sub(
        r"/+",
        "/",
        path,
    )

    # Remove trailing slash temporarily.
    path = path.rstrip("/")

    # Root URL is a special case.
    if not path:
        return "/"

    # All non-root URLs use trailing slash.
    return path + "/"


# ============================================================
# SLUG VALIDATION
# ============================================================


def validate_slug(
    slug: str,
) -> None:
    """
    Validate a page slug.

    A valid slug:
    - contains lowercase letters
    - may contain numbers
    - may contain hyphens
    - does not contain spaces
    - does not begin or end with a hyphen

    Args:
        slug: Page slug to validate.

    Raises:
        ValueError:
            If the slug is invalid.
    """

    if not isinstance(slug, str):
        raise ValueError(
            "Slug must be a string."
        )

    if not slug:
        raise ValueError(
            "Slug cannot be empty."
        )

    pattern = r"^[a-z0-9]+(?:-[a-z0-9]+)*$"

    if not re.fullmatch(
        pattern,
        slug,
    ):
        raise ValueError(
            f"Invalid URL slug: '{slug}'"
        )


# ============================================================
# PAGE URL RECORD
# ============================================================


def build_url_record(
    page: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Convert one architecture page into a URL architecture record.

    Args:
        page: Page from site_architecture.json.

    Returns:
        URL architecture record.
    """

    page_id = page.get(
        "id"
    )

    if not page_id:
        raise ValueError(
            "Architecture page has no ID."
        )

    slug = page.get(
        "slug"
    )

    if not slug:
        raise ValueError(
            f"Page '{page_id}' has no slug."
        )

    validate_slug(
        slug
    )

    raw_url = page.get(
        "url"
    )

    if not raw_url:
        raise ValueError(
            f"Page '{page_id}' has no URL."
        )

    normalized_url = normalize_url(
        raw_url
    )

    expected_url = f"/{slug}/"

    expected_url = normalize_url(
        expected_url
    )

    if normalized_url != expected_url:
        raise ValueError(
            f"URL does not match slug for "
            f"'{page_id}': "
            f"{normalized_url} != {expected_url}"
        )

    return {
        "page_id": page_id,
        "title": page.get(
            "title"
        ),
        "slug": slug,
        "url": normalized_url,
        "page_type": page.get(
            "page_type"
        ),
        "cluster": page.get(
            "cluster"
        ),
        "parent_page_id": page.get(
            "parent_page_id"
        ),
        "primary_keyword": page.get(
            "primary_keyword"
        ),
        "intent": page.get(
            "intent"
        ),
        "priority": page.get(
            "priority"
        ),
        "indexable": page.get(
            "indexable",
            True,
        ),
        "content_status": page.get(
            "content_status",
            "planned",
        ),
    }


# ============================================================
# URL COLLECTION
# ============================================================


def build_url_records(
    architecture: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Build URL records for every page in the architecture.

    Args:
        architecture:
            Final site architecture.

    Returns:
        List of validated URL records.
    """

    pages = architecture.get(
        "pages",
        [],
    )

    if not isinstance(
        pages,
        list,
    ):
        raise ValueError(
            "Architecture 'pages' must be a list."
        )

    records = []

    for page in pages:
        if not isinstance(
            page,
            dict,
        ):
            continue

        records.append(
            build_url_record(
                page
            )
        )

    return records


# ============================================================
# DUPLICATE VALIDATION
# ============================================================


def validate_unique_urls(
    records: List[Dict[str, Any]],
) -> None:
    """
    Ensure that every page has a unique URL.

    Args:
        records: URL architecture records.

    Raises:
        ValueError:
            If two pages share the same URL.
    """

    seen_urls = {}

    for record in records:
        url = record["url"]
        page_id = record["page_id"]

        if url in seen_urls:
            raise ValueError(
                f"Duplicate URL detected: "
                f"{url} "
                f"used by '{seen_urls[url]}' "
                f"and '{page_id}'."
            )

        seen_urls[url] = page_id


def validate_unique_slugs(
    records: List[Dict[str, Any]],
) -> None:
    """
    Ensure that every page has a unique slug.

    Args:
        records: URL architecture records.

    Raises:
        ValueError:
            If two pages share the same slug.
    """

    seen_slugs = {}

    for record in records:
        slug = record["slug"]
        page_id = record["page_id"]

        if slug in seen_slugs:
            raise ValueError(
                f"Duplicate slug detected: "
                f"'{slug}' "
                f"used by '{seen_slugs[slug]}' "
                f"and '{page_id}'."
            )

        seen_slugs[slug] = page_id


# ============================================================
# HIERARCHY VALIDATION
# ============================================================


def validate_parent_relationships(
    records: List[Dict[str, Any]],
) -> None:
    """
    Ensure that every referenced parent page exists.

    Args:
        records: URL architecture records.

    Raises:
        ValueError:
            If a page references a missing parent.
    """

    page_ids = {
        record["page_id"]
        for record in records
    }

    for record in records:
        parent_id = record.get(
            "parent_page_id"
        )

        if parent_id is None:
            continue

        if parent_id not in page_ids:
            raise ValueError(
                f"Page '{record['page_id']}' "
                f"references missing parent "
                f"'{parent_id}'."
            )


def validate_cluster_roots(
    records: List[Dict[str, Any]],
) -> None:
    """
    Validate cluster root pages.

    Each cluster root should:
    - have page_type='cluster'
    - have no parent
    - be indexable

    Args:
        records: URL architecture records.

    Raises:
        ValueError:
            If cluster root rules are violated.
    """

    for record in records:
        if record.get(
            "page_type"
        ) != "cluster":
            continue

        if record.get(
            "parent_page_id"
        ) is not None:
            raise ValueError(
                f"Cluster page '{record['page_id']}' "
                f"must not have a parent."
            )

        if not record.get(
            "indexable",
            True,
        ):
            raise ValueError(
                f"Cluster page '{record['page_id']}' "
                f"must be indexable."
            )


# ============================================================
# URL STRATEGY
# ============================================================


def determine_url_strategy(
    architecture: Dict[str, Any],
) -> str:
    """
    Determine the URL strategy used by the site.

    The current architecture uses root-level URLs for pages while
    preserving cluster relationships through metadata and future
    internal links.

    This is appropriate for the current brand-new content site.

    Args:
        architecture:
            Final site architecture.

    Returns:
        Name of the URL strategy.
    """

    site_status = architecture.get(
        "site_status"
    )

    if site_status == "brand_new":
        return "flat_root_level"

    return "existing_site_preservation"


# ============================================================
# URL SUMMARY
# ============================================================


def build_url_summary(
    records: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Build summary statistics for the URL architecture.

    Args:
        records: URL architecture records.

    Returns:
        URL architecture summary.
    """

    cluster_count = sum(
        1
        for record in records
        if record.get(
            "page_type"
        ) == "cluster"
    )

    indexable_count = sum(
        1
        for record in records
        if record.get(
            "indexable",
            True,
        )
    )

    return {
        "total_urls": len(records),
        "cluster_urls": cluster_count,
        "content_urls": len(records)
        - cluster_count,
        "indexable_urls": indexable_count,
        "non_indexable_urls": (
            len(records)
            - indexable_count
        ),
    }


# ============================================================
# FINAL VALIDATION
# ============================================================


def validate_url_architecture(
    url_architecture: Dict[str, Any],
) -> None:
    """
    Perform final validation of the complete URL architecture.

    Args:
        url_architecture:
            Generated URL architecture.

    Raises:
        ValueError:
            If any URL architecture rule fails.
    """

    records = url_architecture.get(
        "urls",
        [],
    )

    if not records:
        raise ValueError(
            "URL architecture contains no URLs."
        )

    validate_unique_urls(
        records
    )

    validate_unique_slugs(
        records
    )

    validate_parent_relationships(
        records
    )

    validate_cluster_roots(
        records
    )


# ============================================================
# BUILD URL ARCHITECTURE
# ============================================================


def build_url_architecture(
    architecture: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Build the complete URL architecture from the final site
    architecture.

    Args:
        architecture:
            Final site architecture from v0.2.

    Returns:
        Complete URL architecture object.
    """

    records = build_url_records(
        architecture
    )

    strategy = determine_url_strategy(
        architecture
    )

    summary = build_url_summary(
        records
    )

    return {
        "version": "0.2",
        "architecture_type": "url_architecture",
        "site_status": architecture.get(
            "site_status",
            "brand_new",
        ),
        "url_strategy": strategy,
        "base_url": "https://example.com",
        "summary": summary,
        "urls": records,
        "source_file": str(
            ARCHITECTURE_PATH.relative_to(
                BASE_DIR
            )
        ),
    }


# ============================================================
# MAIN PIPELINE
# ============================================================


def run_v02_url_architecture() -> Dict[str, Any]:
    """
    Execute the complete URL architecture stage.

    Pipeline:

        load final architecture
                ↓
        build URL records
                ↓
        validate slugs
                ↓
        validate URLs
                ↓
        validate duplicates
                ↓
        validate hierarchy
                ↓
        save URL architecture

    Returns:
        Generated URL architecture dictionary.
    """

    print(
        "\n" + "=" * 60
    )

    print(
        "        V0.2 — URL ARCHITECTURE"
    )

    print(
        "=" * 60
    )

    # --------------------------------------------------------
    # Step 1
    # --------------------------------------------------------

    print(
        "\n[Step 1] Loading final site architecture..."
    )

    architecture = load_json_file(
        ARCHITECTURE_PATH
    )

    print(
        "  ✓ Architecture loaded"
    )

    # --------------------------------------------------------
    # Step 2
    # --------------------------------------------------------

    print(
        "\n[Step 2] Building URL architecture..."
    )

    url_architecture = build_url_architecture(
        architecture
    )

    print(
        f"  ✓ Generated "
        f"{url_architecture['summary']['total_urls']} URLs"
    )

    # --------------------------------------------------------
    # Step 3
    # --------------------------------------------------------

    print(
        "\n[Step 3] Validating URL architecture..."
    )

    validate_url_architecture(
        url_architecture
    )

    print(
        "  ✓ URLs are valid"
    )

    print(
        "  ✓ URLs are unique"
    )

    print(
        "  ✓ Slugs are unique"
    )

    print(
        "  ✓ Parent relationships are valid"
    )

    # --------------------------------------------------------
    # Step 4
    # --------------------------------------------------------

    print(
        "\n[Step 4] Saving URL architecture..."
    )

    save_json_file(
        URL_ARCHITECTURE_PATH,
        url_architecture,
    )

    print(
        f"  ✓ Saved: "
        f"{URL_ARCHITECTURE_PATH}"
    )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print(
        "\n" + "=" * 60
    )

    print(
        "        URL ARCHITECTURE COMPLETE"
    )

    print(
        "=" * 60
    )

    return url_architecture


# ============================================================
# SCRIPT ENTRY POINT
# ============================================================


if __name__ == "__main__":
    run_v02_url_architecture()