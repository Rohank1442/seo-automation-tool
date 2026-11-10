"""Validate the expected scaffold outputs for a project."""

from pathlib import Path


def validate_frontend(pages: list, frontend_dir: Path) -> list[str]:
    """Return missing page or crawl-file errors; an empty list means valid."""
    errors = []
    for page in pages:
        url = page.get("url") or "/"
        relative = url.strip("/")
        output = frontend_dir / (Path(relative) / "index.html" if relative else "index.html")
        if not output.is_file():
            errors.append(f"Missing generated page: {output}")
    for name in ("robots.txt", "sitemap.xml"):
        if not (frontend_dir / name).is_file():
            errors.append(f"Missing generated file: {frontend_dir / name}")
    return errors
