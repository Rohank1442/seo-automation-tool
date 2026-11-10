"""Coordinate project-scoped internal-link planning from inputs to artifact."""

from pathlib import Path
from typing import Any, Optional

from .graph import build_summary, remove_duplicate_links, validate_links
from .link_builder import create_cluster_links, create_related_links
from .page_data import extract_pages
from .storage import load_json, save_json


def main(outputs_root: Optional[Path] = None) -> dict[str, Any]:
    """Generate and save internal-link recommendations for one project."""
    v02_dir = (Path(outputs_root) if outputs_root is not None else Path("outputs")) / "v02"
    url_path = v02_dir / "url_architecture.json"
    site_path = v02_dir / "site_architecture.json"
    output_path = v02_dir / "internal_linking.json"

    print("=" * 60 + "\n        V0.2 — INTERNAL LINKING ARCHITECTURE\n" + "=" * 60)
    print("\n[Step 1] Loading URL and site architecture...")
    url_architecture, site_architecture = load_json(url_path), load_json(site_path)
    pages = extract_pages(site_architecture, url_architecture)
    print(f"  ✓ Loaded {len(pages)} pages")

    print("\n[Step 2] Creating cluster and related-page links...")
    cluster_links = create_cluster_links(pages)
    related_links = create_related_links(pages)
    links = remove_duplicate_links(cluster_links + related_links)
    print(f"  ✓ Generated {len(cluster_links)} cluster links and {len(related_links)} related links")

    print("\n[Step 3] Validating link graph...")
    validate_links(links, pages)
    summary = build_summary(pages, links)
    print(f"  ✓ Valid graph with {summary['total_links']} links")

    # Keep source paths portable so project output roots need not be under the agent folder.
    result = {
        "version": "0.2",
        "architecture_type": "internal_linking",
        "site_status": url_architecture.get("site_status", "brand_new"),
        "linking_strategy": "cluster_hubs_plus_contextual_related_pages",
        "summary": summary,
        "links": links,
        "source_files": {"url_architecture": str(url_path), "site_architecture": str(site_path)},
    }
    print("\n[Step 4] Saving internal-linking plan...")
    save_json(result, output_path)
    print(f"  ✓ Saved: {output_path}\n" + "=" * 60 + "\n        INTERNAL LINKING COMPLETE\n" + "=" * 60)
    return result
