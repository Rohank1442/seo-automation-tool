"""Run final consistency checks on page specs and link graph results."""

from typing import Any


def validate_technical_seo(pages: list[dict[str, Any]], page_specs: list[dict[str, Any]], internal_linking_checks: dict[str, Any]) -> dict[str, Any]:
    """Return errors and warnings found in the technical SEO specification."""
    errors, warnings = [], []
    if not pages:
        errors.append("No pages found in URL architecture.")
    urls = [page["url"] for page in pages]
    if len(urls) != len(set(urls)):
        errors.append("Duplicate URLs detected.")
    canonicals = [spec["canonical_url"] for spec in page_specs]
    if len(canonicals) != len(set(canonicals)):
        errors.append("Duplicate canonical URLs detected.")
    for spec in page_specs:
        checks = spec["url_validation"]
        if not checks["https"]:
            errors.append(f"Non-HTTPS URL: {spec['url']}")
        if not checks["trailing_slash"]:
            warnings.append(f"URL does not use trailing slash: {spec['url']}")
        if not checks["root_level"]:
            warnings.append(f"URL is not root-level: {spec['url']}")
    if not internal_linking_checks["graph_valid"]:
        errors.append("Internal linking graph contains isolated pages.")
    return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}
