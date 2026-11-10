"""Define technical SEO rules that apply across the generated site."""


def build_global_rules(base_url: str = "https://example.com") -> dict:
    """Return the shared crawl, indexing, metadata, structure, and performance rules."""
    return {
        "protocol": "https",
        "canonical_domain": base_url.rstrip("/"),
        "crawlability": {"robots_txt_required": True, "sitemap_required": True, "allow_search_engine_crawling": True},
        "indexing": {"default": "index, follow", "non_indexable_pages": "noindex, follow"},
        "url_rules": {"lowercase": True, "hyphens_for_word_separation": True, "trailing_slash": True, "root_level_urls": True, "avoid_query_parameters": True},
        "metadata": {"title_required": True, "meta_description_required": True, "canonical_required": True},
        "headings": {"one_h1_per_page": True, "logical_h2_h3_hierarchy": True},
        "social_metadata": {"open_graph": True, "twitter_cards": True},
        "structured_data": {"enabled": True, "type_should_match_page": True},
        "performance": {"responsive_design_required": True, "image_optimization_required": True, "lazy_loading_recommended": True, "minimize_render_blocking_resources": True},
        "mobile": {"mobile_friendly_required": True},
    }
