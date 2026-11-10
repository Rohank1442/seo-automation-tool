"""Combine URL and technical SEO records into renderer-ready page data."""


def build_page_context(url_pages: list, technical_seo: dict) -> list:
    """Merge each URL record with its matching technical SEO specification."""
    specs = {
        item.get("page_id"): item
        for item in technical_seo.get("pages", [])
        if item.get("page_id")
    }
    contexts = []
    for page in url_pages:
        page_id = page.get("page_id")
        if not page_id:
            raise ValueError("URL architecture page is missing page_id")
        spec = specs.get(page_id, {})
        contexts.append({
            **page,
            "canonical_url": spec.get("canonical_url"),
            "meta_description": spec.get("meta_description") or (
                f"Explore practical information and resources about {page.get('title', 'this topic')}."
            ),
            "robots": spec.get("robots", "index, follow" if page.get("indexable", True) else "noindex, follow"),
        })
    return contexts
