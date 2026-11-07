"""Competitor discovery and page crawling for each v0.1 topic cluster."""

from typing import Any, Dict, List

from core.scraper import crawl_competitor_page, get_competitor_urls
from .logging_utils import print_separator


def research_competitors(saved_clusters):
    """Find and crawl the top ranking competitor pages for every cluster."""
    # --- STEP 7: CRAWL TOP COMPETITORS PER CLUSTER ---
    # ============================================================
    print_separator()
    print("\n[Step 7] Crawling Competitors Per Cluster")
    print("Identifying top 5 ranking pages and crawling outline structures...")
    print_separator()

    competitor_data: Dict[str, List[Dict[str, Any]]] = {}

    for cluster in saved_clusters:
        c_name = cluster["name"]
        print(f"\nFinding competitors for cluster: '{c_name}'...")
        urls = get_competitor_urls(c_name, max_results=5)
        print(f"  • Top competitor URLs found: {len(urls)}")

        crawled_pages = []
        for url in urls:
            print(f"  • Crawling {url} ...")
            page_data = crawl_competitor_page(url)
            crawled_pages.append(page_data)

        competitor_data[c_name] = crawled_pages
    return competitor_data
