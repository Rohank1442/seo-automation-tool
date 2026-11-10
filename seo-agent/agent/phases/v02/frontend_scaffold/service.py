"""Coordinate the v0.2 frontend scaffold generation stage."""

import json
from pathlib import Path

from .inputs import load_inputs
from .page_context import build_page_context
from .renderer import build_link_map, render_page
from .technical_files import robots_txt, sitemap_xml
from .validation import validate_frontend


def _output_path(frontend_dir: Path, url: str) -> Path:
    """Map a canonical site path to its static HTML file."""
    relative = (url or "/").strip("/")
    return frontend_dir / (Path(relative) / "index.html" if relative else "index.html")


def run_frontend_scaffold(project_outputs: Path, base_url: str | None = None) -> dict:
    """Generate and validate the static v0.2 frontend for one project."""
    project_outputs = Path(project_outputs)
    artifacts = load_inputs(project_outputs)
    url_architecture = artifacts["url_architecture"]
    technical_seo = artifacts["technical_seo"]
    pages = build_page_context(url_architecture.get("urls", []), technical_seo)
    link_map = build_link_map(artifacts["internal_linking"])
    frontend_dir = project_outputs / "v02" / "frontend"
    frontend_dir.mkdir(parents=True, exist_ok=True)

    outputs = []
    for page in pages:
        output = _output_path(frontend_dir, page.get("url", "/"))
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(render_page(page, pages, link_map), encoding="utf-8")
        outputs.append({"page_id": page["page_id"], "title": page.get("title"), "url": page.get("url"), "output": str(output)})

    (frontend_dir / "robots.txt").write_text(robots_txt(technical_seo, base_url), encoding="utf-8")
    (frontend_dir / "sitemap.xml").write_text(sitemap_xml(technical_seo), encoding="utf-8")
    errors = validate_frontend(pages, frontend_dir)
    if errors:
        raise RuntimeError("Frontend scaffold validation failed: " + "; ".join(errors))

    manifest = {
        "version": "0.2",
        "architecture_type": "frontend_generation",
        "site_status": url_architecture.get("site_status", "brand_new"),
        "output_directory": str(frontend_dir),
        "summary": {"total_pages": len(pages), "generated_pages": len(outputs), "internal_links": sum(map(len, link_map.values())), "robots_txt": True, "sitemap": True, "validation_status": "valid"},
        "pages": outputs,
        "source_files": {name: str(project_outputs / "v02" / f"{name}.json") for name in ("site_architecture", "url_architecture", "internal_linking", "technical_seo")},
    }
    manifest_path = project_outputs / "v02" / "frontend_generation.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest
