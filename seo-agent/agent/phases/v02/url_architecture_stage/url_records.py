"""Normalize URL paths and build one URL record per architecture page."""

import re
from typing import Any
from urllib.parse import urlparse


def normalize_url(url: str) -> str:
    """Return a clean relative path with a leading and trailing slash."""
    if not isinstance(url, str):
        raise ValueError("URL must be a string.")
    url = url.strip()
    if not url:
        raise ValueError("URL cannot be empty.")
    parsed = urlparse(url)
    if parsed.scheme or parsed.netloc:
        raise ValueError(f"Expected relative URL, got absolute URL: {url}")
    path = re.sub(r"/+", "/", parsed.path)
    if not path.startswith("/"):
        path = "/" + path
    path = path.rstrip("/")
    return path + "/" if path else "/"


def validate_slug(slug: str) -> None:
    """Require lowercase alphanumeric words separated by single hyphens."""
    if not isinstance(slug, str):
        raise ValueError("Slug must be a string.")
    if not slug:
        raise ValueError("Slug cannot be empty.")
    if not re.fullmatch(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", slug):
        raise ValueError(f"Invalid URL slug: '{slug}'")


def build_url_record(page: dict[str, Any]) -> dict[str, Any]:
    """Convert one final site-architecture page into its URL record."""
    page_id = page.get("id")
    if not page_id:
        raise ValueError("Architecture page has no ID.")
    slug = page.get("slug")
    if not slug:
        raise ValueError(f"Page '{page_id}' has no slug.")
    validate_slug(slug)
    raw_url = page.get("url")
    if not raw_url:
        raise ValueError(f"Page '{page_id}' has no URL.")
    normalized_url = normalize_url(raw_url)
    expected_url = normalize_url(f"/{slug}/")
    if normalized_url != expected_url:
        raise ValueError(f"URL does not match slug for '{page_id}': {normalized_url} != {expected_url}")
    return {
        "page_id": page_id,
        "title": page.get("title"),
        "slug": slug,
        "url": normalized_url,
        "page_type": page.get("page_type"),
        "cluster": page.get("cluster"),
        "parent_page_id": page.get("parent_page_id"),
        "primary_keyword": page.get("primary_keyword"),
        "intent": page.get("intent"),
        "priority": page.get("priority"),
        "indexable": page.get("indexable", True),
        "content_status": page.get("content_status", "planned"),
    }


def build_url_records(architecture: dict[str, Any]) -> list[dict[str, Any]]:
    """Build URL records for all valid page objects in the architecture."""
    pages = architecture.get("pages", [])
    if not isinstance(pages, list):
        raise ValueError("Architecture 'pages' must be a list.")
    return [build_url_record(page) for page in pages if isinstance(page, dict)]
