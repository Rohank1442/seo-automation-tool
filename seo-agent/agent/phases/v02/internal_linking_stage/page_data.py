"""Merge semantic page records with their canonical URL records."""

from typing import Any


def extract_pages(site_architecture: dict[str, Any], url_architecture: dict[str, Any]) -> list[dict[str, Any]]:
    """Join site pages and URL records by page ID, keeping URL data authoritative."""
    site_pages = {
        page.get("id"): page
        for page in site_architecture.get("pages", [])
        if page.get("id")
    }
    pages = []
    for url_page in url_architecture.get("urls", []):
        page_id = url_page.get("page_id")
        if not page_id:
            raise ValueError("URL architecture contains a page without page_id.")
        semantic_page = site_pages.get(page_id, {})
        merged = {**semantic_page, **url_page}
        # Both keys are retained for existing callers and artifact conventions.
        merged.setdefault("id", page_id)
        pages.append(merged)
    return pages


def get_anchor_text(target_page: dict[str, Any]) -> str:
    """Prefer the target page's primary keyword, then title, then slug."""
    return target_page.get("primary_keyword") or target_page.get("title") or target_page.get("slug", "Read more")
