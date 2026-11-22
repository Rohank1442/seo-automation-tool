"""Map completed v0.3 page results into durable project page records."""

from typing import Any, Dict

from core.db import get_cluster_id_for_page, save_generated_page_record
from .models import GeneratedPageResult


def persist_generated_page(project_id: str, result: GeneratedPageResult) -> Dict[str, Any]:
    """Persist one completed page, resolving its optional project cluster."""
    brief = result.brief or {}
    metadata = result.metadata or {}
    audit = result.audit or {}
    faq_data = result.faq or {}
    faq_items = faq_data.get("faq_items", []) if isinstance(faq_data, dict) else faq_data
    slug = result.slug.strip("/")

    page_data = {
        "source_page_id": result.page_id,
        "project_id": project_id,
        "cluster_id": get_cluster_id_for_page(project_id, result.cluster),
        "slug": slug,
        "url_path": f"/{slug}/",
        "title": result.title,
        "h1": brief.get("h1") or result.title,
        "meta_title": brief.get("meta_title") or result.title,
        "meta_description": metadata.get("meta_description") or brief.get("meta_description"),
        "canonical_url": brief.get("canonical_url") or metadata.get("canonical_url") or result.url,
        "robots": metadata.get("robots", "index, follow"),
        "schema_type": metadata.get("schema_type") or brief.get("schema_type", "Article"),
        "primary_keyword": result.primary_keyword,
        "secondary_keywords": result.secondary_keywords or [],
        "page_type": result.page_type or "guide",
        "search_intent": brief.get("search_intent", "informational"),
        "word_count": result.word_count,
        "health_score": float(audit.get("overall_score", audit.get("total_score", 100))),
        "markdown_content": result.markdown_content,
        "faqs": faq_items or [],
        "internal_links": result.embedded_internal_links or [],
        "validation_issues": audit.get("issues", []),
        "updated_at": result.generated_at,
    }
    return save_generated_page_record(page_data)
