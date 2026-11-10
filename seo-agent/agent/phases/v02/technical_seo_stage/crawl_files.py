"""Build site-wide robots.txt and sitemap specifications."""

from typing import Any


def build_robots_txt(base_url: str = "https://example.com") -> str:
    """Create a robots.txt policy that permits crawling and advertises sitemap."""
    return f"User-agent: *\nAllow: /\n\nSitemap: {base_url.rstrip('/')}/sitemap.xml\n"


def build_sitemap_spec(pages: list[dict[str, Any]], base_url: str = "https://example.com") -> dict[str, Any]:
    """List indexable pages in the sitemap with their crawl priorities."""
    urls = []
    for page in pages:
        if not page.get("indexable", True):
            continue
        urls.append({
            "page_id": page["page_id"],
            "url": base_url.rstrip("/") + page["url"],
            "changefreq": "monthly",
            "priority": 1.0 if page.get("priority") == "high" else 0.7,
        })
    return {"path": "/sitemap.xml", "format": "XML", "indexable_urls": len(urls), "urls": urls}
