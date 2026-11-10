"""Orchestrate project-scoped technical SEO specification generation."""

from pathlib import Path
from typing import Any, Optional

from .crawl_files import build_robots_txt, build_sitemap_spec
from .linking import build_internal_linking_checks
from .page_specs import build_page_seo_spec
from .rules import build_global_rules
from .storage import load_json, save_json
from .validation import validate_technical_seo


BASE_URL = "https://example.com"


def main(outputs_root: Optional[Path] = None, base_url: Optional[str] = None) -> dict[str, Any]:
    """Build, validate, and save the technical SEO artifact for one project."""
    root = Path(outputs_root) if outputs_root is not None else Path("outputs")
    output_dir = root / "v02"
    url_path = output_dir / "url_architecture.json"
    site_path = output_dir / "site_architecture.json"
    linking_path = output_dir / "internal_linking.json"
    output_path = output_dir / "technical_seo.json"
    effective_base_url = (base_url or BASE_URL).rstrip("/")

    print("=" * 60 + "\n        V0.2 — TECHNICAL SEO ARCHITECTURE\n" + "=" * 60)
    print("\n[Step 1] Loading URL architecture...")
    url_architecture = load_json(url_path)
    pages = url_architecture.get("urls", [])
    print(f"  ✓ Loaded {len(pages)} pages")

    print("\n[Step 2] Loading site and internal-linking architecture...")
    # Keep the site architecture as a required upstream artifact for this stage.
    load_json(site_path)
    internal_linking = load_json(linking_path)
    print("  ✓ Architecture artifacts loaded")

    print("\n[Step 3] Building page specifications, crawl files, and global rules...")
    page_specs = [build_page_seo_spec(page, effective_base_url) for page in pages]
    robots_content = build_robots_txt(effective_base_url)
    sitemap = build_sitemap_spec(pages, effective_base_url)
    linking_checks = build_internal_linking_checks(internal_linking, pages)
    global_rules = build_global_rules(effective_base_url)
    print(f"  ✓ Generated specifications for {len(page_specs)} pages")
    print(f"  ✓ Sitemap contains {sitemap['indexable_urls']} URLs")

    print("\n[Step 4] Validating technical SEO specification...")
    validation = validate_technical_seo(pages, page_specs, linking_checks)
    print("  ✓ Technical SEO architecture is valid" if validation["valid"] else f"  ⚠ Found {len(validation['errors'])} errors")
    if validation["warnings"]:
        print(f"  ⚠ Found {len(validation['warnings'])} warnings")

    result = {
        "version": "0.2",
        "architecture_type": "technical_seo",
        "site_status": url_architecture.get("site_status", "brand_new"),
        "base_url": effective_base_url,
        "summary": {
            "total_pages": len(pages),
            "indexable_pages": sum(1 for page in pages if page.get("indexable", True)),
            "non_indexable_pages": sum(1 for page in pages if not page.get("indexable", True)),
            "internal_links": linking_checks["total_links"],
            "validation_status": "valid" if validation["valid"] else "review",
        },
        "global_rules": global_rules,
        "robots_txt": {"path": "/robots.txt", "content": robots_content},
        "sitemap": sitemap,
        "internal_linking": linking_checks,
        "pages": page_specs,
        "validation": validation,
        "source_files": {
            "url_architecture": str(url_path),
            "site_architecture": str(site_path),
            "internal_linking": str(linking_path),
        },
    }
    print("\n[Step 5] Saving technical SEO plan...")
    save_json(result, output_path)
    print(f"  ✓ Saved: {output_path}\n" + "=" * 60 + "\n        TECHNICAL SEO COMPLETE\n" + "=" * 60)
    return result
