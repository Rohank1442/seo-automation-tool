"""Compatibility imports for the v0.2 technical SEO package."""

from pathlib import Path

from .technical_seo_stage.crawl_files import build_robots_txt, build_sitemap_spec
from .technical_seo_stage.linking import build_internal_linking_checks
from .technical_seo_stage.page_specs import build_page_seo_spec, validate_url_structure
from .technical_seo_stage.rules import build_global_rules
from .technical_seo_stage.service import BASE_URL, main
from .technical_seo_stage.storage import load_json, save_json
from .technical_seo_stage.validation import validate_technical_seo

# Preserve the old path constants for integrations that imported them.
BASE_DIR = Path(__file__).resolve().parent.parent.parent
OUTPUT_DIR = BASE_DIR / "outputs" / "v02"
URL_ARCHITECTURE_FILE = OUTPUT_DIR / "url_architecture.json"
SITE_ARCHITECTURE_FILE = OUTPUT_DIR / "site_architecture.json"
INTERNAL_LINKING_FILE = OUTPUT_DIR / "internal_linking.json"
OUTPUT_FILE = OUTPUT_DIR / "technical_seo.json"

__all__ = [
    "BASE_DIR",
    "BASE_URL",
    "INTERNAL_LINKING_FILE",
    "OUTPUT_DIR",
    "OUTPUT_FILE",
    "SITE_ARCHITECTURE_FILE",
    "URL_ARCHITECTURE_FILE",
    "build_global_rules",
    "build_internal_linking_checks",
    "build_page_seo_spec",
    "build_robots_txt",
    "build_sitemap_spec",
    "load_json",
    "main",
    "save_json",
    "validate_technical_seo",
    "validate_url_structure",
]


if __name__ == "__main__":
    main()
