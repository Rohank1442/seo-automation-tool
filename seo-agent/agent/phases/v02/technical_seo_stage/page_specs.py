"""Build per-page canonical, robots, and URL validation specifications."""

from urllib.parse import urlparse
from typing import Any


def validate_url_structure(url: str) -> dict[str, bool]:
    """Check the core URL properties required by this site's architecture."""
    parsed = urlparse(url)
    return {
        "https": parsed.scheme == "https",
        "has_hostname": bool(parsed.netloc),
        "trailing_slash": url.endswith("/"),
        "root_level": url.count("/") <= 4,
    }


def build_page_seo_spec(page: dict[str, Any], base_url: str = "https://example.com") -> dict[str, Any]:
    """Create the technical SEO requirements record for one URL record."""
    url = page["url"]
    canonical_url = base_url.rstrip("/") + url
    validation = validate_url_structure(canonical_url)
    indexable = page.get("indexable", True)
    return {
        "page_id": page["page_id"],
        "title": page["title"],
        "url": url,
        "canonical_url": canonical_url,
        "indexable": indexable,
        "robots": "index, follow" if indexable else "noindex, follow",
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
        "status": "valid" if all(validation.values()) else "review",
    }
