"""Generate crawl discovery files from the project's technical SEO artifact."""

from html import escape


def robots_txt(technical_seo: dict, base_url: str | None) -> str:
    """Use configured robots content, with a project-specific sitemap fallback."""
    configured = technical_seo.get("robots_txt", {}).get("content")
    if configured:
        return configured
    sitemap_url = f"{base_url.rstrip('/')}/sitemap.xml" if base_url else "/sitemap.xml"
    return f"User-agent: *\nAllow: /\n\nSitemap: {sitemap_url}\n"


def sitemap_xml(technical_seo: dict) -> str:
    """Serialize the sitemap URLs already selected by the technical SEO stage."""
    entries = []
    for item in technical_seo.get("sitemap", {}).get("urls", []):
        url = item.get("url")
        if not url:
            continue
        priority = item.get("priority", 0.7)
        entries.append(
            f"<url><loc>{escape(url)}</loc><changefreq>{escape(str(item.get('changefreq', 'monthly')))}</changefreq><priority>{priority}</priority></url>"
        )
    return '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + "".join(entries) + "</urlset>\n"
