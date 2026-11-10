"""Orchestrate project-scoped URL architecture generation."""

from pathlib import Path
from typing import Any, Optional

from .storage import load_json_file, save_json_file
from .summary import build_url_summary, determine_url_strategy
from .url_records import build_url_records
from .validation import validate_url_architecture


BASE_DIR = Path(__file__).resolve().parents[3]
ARCHITECTURE_PATH = BASE_DIR / "outputs" / "v02" / "site_architecture.json"
URL_ARCHITECTURE_PATH = BASE_DIR / "outputs" / "v02" / "url_architecture.json"


def _source_label(path: Path) -> str:
    """Prefer a repository-relative source path, with absolute fallback."""
    try:
        return str(path.relative_to(BASE_DIR))
    except ValueError:
        return str(path)


def build_url_architecture(architecture: dict[str, Any], base_url: str = "https://example.com",
                           architecture_path: Optional[Path] = None) -> dict[str, Any]:
    """Assemble the complete URL architecture artifact from site pages."""
    records = build_url_records(architecture)
    source_path = architecture_path or ARCHITECTURE_PATH
    return {
        "version": "0.2",
        "architecture_type": "url_architecture",
        "site_status": architecture.get("site_status", "brand_new"),
        "url_strategy": determine_url_strategy(architecture),
        "base_url": base_url.rstrip("/"),
        "summary": build_url_summary(records),
        "urls": records,
        "source_file": _source_label(source_path),
    }


def run_v02_url_architecture(outputs_root: Optional[Path] = None,
                             base_url: str = "https://example.com") -> dict[str, Any]:
    """Load site architecture, build and validate URLs, and save the result."""
    root = Path(outputs_root) if outputs_root is not None else Path("outputs")
    v02_dir = root / "v02"
    architecture_path = v02_dir / "site_architecture.json"
    output_path = v02_dir / "url_architecture.json"

    print("\n" + "=" * 60 + "\n        V0.2 — URL ARCHITECTURE\n" + "=" * 60)
    print("\n[Step 1] Loading final site architecture...")
    architecture = load_json_file(architecture_path)
    print("  ✓ Architecture loaded\n\n[Step 2] Building URL architecture...")
    result = build_url_architecture(architecture, base_url, architecture_path)
    print(f"  ✓ Generated {result['summary']['total_urls']} URLs\n\n[Step 3] Validating URL architecture...")
    validate_url_architecture(result)
    print("  ✓ URLs, slugs, and parent relationships are valid")
    print("\n[Step 4] Saving URL architecture...")
    save_json_file(output_path, result)
    print(f"  ✓ Saved: {output_path}\n" + "=" * 60 + "\n        URL ARCHITECTURE COMPLETE\n" + "=" * 60)
    return result
