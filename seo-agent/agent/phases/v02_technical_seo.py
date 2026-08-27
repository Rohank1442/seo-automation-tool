"""
V0.2 — Technical SEO Architecture

Generates a machine-readable technical SEO specification from:
    - URL architecture
    - Site architecture
    - Internal linking architecture

This module does NOT build the frontend.
It creates the technical SEO rules that the frontend generator
will consume later.
"""

import json
from pathlib import Path
from urllib.parse import urlparse


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

OUTPUT_DIR = BASE_DIR / "outputs" / "v02"

URL_ARCHITECTURE_FILE = OUTPUT_DIR / "url_architecture.json"
SITE_ARCHITECTURE_FILE = OUTPUT_DIR / "site_architecture.json"
INTERNAL_LINKING_FILE = OUTPUT_DIR / "internal_linking.json"

OUTPUT_FILE = OUTPUT_DIR / "technical_seo.json"

BASE_URL = "https://example.com"


# ============================================================
# FILE HELPERS
# ============================================================

def load_json(file_path: Path) -> dict:
    """
    Load a JSON file and return its contents.

    Args:
        file_path: Path to the JSON file.

    Returns:
        Parsed JSON object.
    """
    if not file_path.exists():
        raise FileNotFoundError(
            f"Required file not found: {file_path}"
        )

    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def save_json(data: dict, file_path: Path) -> None:
    """
    Save a Python dictionary as formatted JSON.

    Args:
        data: Data to save.
        file_path: Destination path.
    """
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            indent=2,
            ensure_ascii=False
        )


# ============================================================
# URL VALIDATION
# ============================================================

def validate_url_structure(url: str) -> dict:
    """
    Validate the basic structure of a site URL.

    The generated architecture uses root-level URLs with
    trailing slashes.
    """

    parsed = urlparse(url)

    return {
        "https": parsed.scheme == "https",
        "has_hostname": bool(parsed.netloc),
        "trailing_slash": url.endswith("/"),
        "root_level": url.count("/") <= 4,
    }


# ============================================================
# PAGE SEO SPECIFICATION
# ============================================================

def build_page_seo_spec(page: dict) -> dict:
    """
    Build technical SEO requirements for a single page.

    Args:
        page: Page metadata from the URL architecture.

    Returns:
        Technical SEO specification for the page.
    """

    url = page["url"]

    full_url = BASE_URL.rstrip("/") + url

    validation = validate_url_structure(full_url)

    indexable = page.get("indexable", True)

    if indexable:
        robots = "index, follow"
    else:
        robots = "noindex, follow"

    return {
        "page_id": page["page_id"],
        "title": page["title"],
        "url": url,
        "canonical_url": full_url,
        "indexable": indexable,
        "robots": robots,

        "seo_requirements": {
            "title_required": True,
            "meta_description_required": True,
            "canonical_required": True,
            "h1_required": True,
            "single_h1_required": True,
            "structured_data_recommended": True,
            "open_graph_required": True,
        },

        "url_validation": validation,

        "status": "valid"
        if all(validation.values())
        else "review",
    }


# ============================================================
# ROBOTS.TXT
# ============================================================

def build_robots_txt() -> str:
    """
    Generate the robots.txt content for the site.

    The site is brand new and all generated pages are
    intended to be crawlable.
    """

    return """User-agent: *
Allow: /

Sitemap: https://example.com/sitemap.xml
"""


# ============================================================
# SITEMAP SPECIFICATION
# ============================================================

def build_sitemap_spec(pages: list) -> dict:
    """
    Build a sitemap specification from indexable pages.

    Args:
        pages: Pages from URL architecture.

    Returns:
        Sitemap configuration.
    """

    urls = []

    for page in pages:
        if not page.get("indexable", True):
            continue

        url = page["url"]

        urls.append({
            "page_id": page["page_id"],
            "url": BASE_URL.rstrip("/") + url,
            "changefreq": "monthly",
            "priority": (
                1.0
                if page.get("priority") == "high"
                else 0.7
            ),
        })

    return {
        "path": "/sitemap.xml",
        "format": "XML",
        "indexable_urls": len(urls),
        "urls": urls,
    }


# ============================================================
# INTERNAL LINKING SEO CHECKS
# ============================================================

def build_internal_linking_checks(
    internal_linking: dict,
    pages: list,
) -> dict:
    """
    Validate that every page participates in the internal
    linking graph.

    Args:
        internal_linking: Internal linking architecture.
        pages: Site pages.

    Returns:
        Internal linking validation results.
    """

    links = internal_linking.get("links", [])

    inbound = {page["page_id"]: 0 for page in pages}
    outbound = {page["page_id"]: 0 for page in pages}

    for link in links:
        source = link.get("source_page_id")
        target = link.get("target_page_id")

        if source in outbound:
            outbound[source] += 1

        if target in inbound:
            inbound[target] += 1

    pages_without_inbound = [
        page_id
        for page_id, count in inbound.items()
        if count == 0
    ]

    pages_without_outbound = [
        page_id
        for page_id, count in outbound.items()
        if count == 0
    ]

    return {
        "total_links": len(links),
        "pages_without_inbound_links": pages_without_inbound,
        "pages_without_outbound_links": pages_without_outbound,
        "graph_valid": (
            not pages_without_inbound
            and not pages_without_outbound
        ),
    }


# ============================================================
# GLOBAL TECHNICAL SEO RULES
# ============================================================

def build_global_rules() -> dict:
    """
    Define technical SEO rules that apply to the entire site.
    """

    return {
        "protocol": "https",
        "canonical_domain": BASE_URL,

        "crawlability": {
            "robots_txt_required": True,
            "sitemap_required": True,
            "allow_search_engine_crawling": True,
        },

        "indexing": {
            "default": "index, follow",
            "non_indexable_pages": "noindex, follow",
        },

        "url_rules": {
            "lowercase": True,
            "hyphens_for_word_separation": True,
            "trailing_slash": True,
            "root_level_urls": True,
            "avoid_query_parameters": True,
        },

        "metadata": {
            "title_required": True,
            "meta_description_required": True,
            "canonical_required": True,
        },

        "headings": {
            "one_h1_per_page": True,
            "logical_h2_h3_hierarchy": True,
        },

        "social_metadata": {
            "open_graph": True,
            "twitter_cards": True,
        },

        "structured_data": {
            "enabled": True,
            "type_should_match_page": True,
        },

        "performance": {
            "responsive_design_required": True,
            "image_optimization_required": True,
            "lazy_loading_recommended": True,
            "minimize_render_blocking_resources": True,
        },

        "mobile": {
            "mobile_friendly_required": True,
        },
    }


# ============================================================
# VALIDATION
# ============================================================

def validate_technical_seo(
    pages: list,
    page_specs: list,
    internal_linking_checks: dict,
) -> dict:
    """
    Run final technical SEO validation.
    """

    errors = []
    warnings = []

    # Check page count.
    if not pages:
        errors.append("No pages found in URL architecture.")

    # Check duplicate URLs.
    urls = [page["url"] for page in pages]

    if len(urls) != len(set(urls)):
        errors.append("Duplicate URLs detected.")

    # Check duplicate canonical URLs.
    canonicals = [
        spec["canonical_url"]
        for spec in page_specs
    ]

    if len(canonicals) != len(set(canonicals)):
        errors.append("Duplicate canonical URLs detected.")

    # Check URL structure.
    for spec in page_specs:
        validation = spec["url_validation"]

        if not validation["https"]:
            errors.append(
                f"Non-HTTPS URL: {spec['url']}"
            )

        if not validation["trailing_slash"]:
            warnings.append(
                f"URL does not use trailing slash: {spec['url']}"
            )

        if not validation["root_level"]:
            warnings.append(
                f"URL is not root-level: {spec['url']}"
            )

    # Check internal linking.
    if not internal_linking_checks["graph_valid"]:
        errors.append(
            "Internal linking graph contains isolated pages."
        )

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
    }


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    """
    Execute the complete technical SEO architecture pipeline.
    """

    print("=" * 60)
    print("        V0.2 — TECHNICAL SEO ARCHITECTURE")
    print("=" * 60)

    # --------------------------------------------------------
    # STEP 1
    # --------------------------------------------------------

    print("\n[Step 1] Loading URL architecture...")

    url_architecture = load_json(
        URL_ARCHITECTURE_FILE
    )

    pages = url_architecture.get("urls", [])

    print(
        f"  ✓ Loaded {len(pages)} pages"
    )

    # --------------------------------------------------------
    # STEP 2
    # --------------------------------------------------------

    print("\n[Step 2] Loading site architecture...")

    site_architecture = load_json(
        SITE_ARCHITECTURE_FILE
    )

    print("  ✓ Site architecture loaded")

    # --------------------------------------------------------
    # STEP 3
    # --------------------------------------------------------

    print("\n[Step 3] Loading internal linking architecture...")

    internal_linking = load_json(
        INTERNAL_LINKING_FILE
    )

    print("  ✓ Internal linking architecture loaded")

    # --------------------------------------------------------
    # STEP 4
    # --------------------------------------------------------

    print("\n[Step 4] Building page SEO specifications...")

    page_specs = [
        build_page_seo_spec(page)
        for page in pages
    ]

    print(
        f"  ✓ Generated specifications for "
        f"{len(page_specs)} pages"
    )

    # --------------------------------------------------------
    # STEP 5
    # --------------------------------------------------------

    print("\n[Step 5] Building robots.txt specification...")

    robots_txt = build_robots_txt()

    print("  ✓ robots.txt generated")

    # --------------------------------------------------------
    # STEP 6
    # --------------------------------------------------------

    print("\n[Step 6] Building sitemap specification...")

    sitemap = build_sitemap_spec(pages)

    print(
        f"  ✓ Sitemap contains "
        f"{sitemap['indexable_urls']} URLs"
    )

    # --------------------------------------------------------
    # STEP 7
    # --------------------------------------------------------

    print("\n[Step 7] Validating internal linking...")

    internal_linking_checks = build_internal_linking_checks(
        internal_linking,
        pages,
    )

    print(
        f"  ✓ Checked {internal_linking_checks['total_links']} links"
    )

    if internal_linking_checks["graph_valid"]:
        print("  ✓ Link graph is valid")
    else:
        print("  ⚠ Link graph requires review")

    # --------------------------------------------------------
    # STEP 8
    # --------------------------------------------------------

    print("\n[Step 8] Building global technical SEO rules...")

    global_rules = build_global_rules()

    print("  ✓ Global SEO rules generated")

    # --------------------------------------------------------
    # STEP 9
    # --------------------------------------------------------

    print("\n[Step 9] Running final validation...")

    validation = validate_technical_seo(
        pages,
        page_specs,
        internal_linking_checks,
    )

    if validation["valid"]:
        print("  ✓ Technical SEO architecture is valid")
    else:
        print(
            f"  ⚠ Found {len(validation['errors'])} errors"
        )

    if validation["warnings"]:
        print(
            f"  ⚠ Found {len(validation['warnings'])} warnings"
        )

    # --------------------------------------------------------
    # STEP 10
    # --------------------------------------------------------

    print("\n[Step 10] Building final technical SEO output...")

    result = {
        "version": "0.2",
        "architecture_type": "technical_seo",
        "site_status": url_architecture.get(
            "site_status",
            "brand_new",
        ),

        "base_url": BASE_URL,

        "summary": {
            "total_pages": len(pages),
            "indexable_pages": sum(
                1
                for page in pages
                if page.get("indexable", True)
            ),
            "non_indexable_pages": sum(
                1
                for page in pages
                if not page.get("indexable", True)
            ),
            "internal_links": internal_linking_checks[
                "total_links"
            ],
            "validation_status": (
                "valid"
                if validation["valid"]
                else "review"
            ),
        },

        "global_rules": global_rules,

        "robots_txt": {
            "path": "/robots.txt",
            "content": robots_txt,
        },

        "sitemap": sitemap,

        "internal_linking": internal_linking_checks,

        "pages": page_specs,

        "validation": validation,

        "source_files": {
            "url_architecture": str(
                URL_ARCHITECTURE_FILE
            ),
            "site_architecture": str(
                SITE_ARCHITECTURE_FILE
            ),
            "internal_linking": str(
                INTERNAL_LINKING_FILE
            ),
        },
    }

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    save_json(
        result,
        OUTPUT_FILE,
    )

    print("\n[Step 11] Saving technical SEO plan...")

    print(
        f"  ✓ Saved: {OUTPUT_FILE}"
    )

    print("\n" + "=" * 60)
    print("        TECHNICAL SEO COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()