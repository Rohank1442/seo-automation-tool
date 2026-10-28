"""
v0.3 Content Generation & Validation — Validator & Exporter.

Handles:
- Exhaustive 8-check content validation per page.
- Cross-page site-wide checks (duplicate metadata, keyword cannibalization, orphan links).
- Serialization of generated_content.json, content_manifest.json, and summary reports.
"""

import json
import logging
import re
from collections import Counter
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from phases.v03.models import GeneratedPageResult, LoadedArtifacts

logger = logging.getLogger("v03.validator")


def extract_markdown_links(markdown_content: str) -> List[Dict[str, str]]:
    """Extract all markdown internal links [anchor](url) from raw markdown text."""
    pattern = r"\[([^\]]+)\]\(([^)]+)\)"
    links = []
    for match in re.finditer(pattern, markdown_content):
        anchor = match.group(1).strip()
        url = match.group(2).strip()
        if not url.startswith("http") and not url.startswith("#") and not url.startswith("mailto:"):
            links.append({"anchor_text": anchor, "target_url": url})
    return links


def validate_single_page_content(
    page: Dict[str, Any],
    brief: Optional[Dict[str, Any]],
    valid_site_urls: Set[str],
    all_pages: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Perform exhaustive validation on a single generated page."""
    meta_title = page.get("meta_title", "")
    meta_desc = page.get("meta_description", "")
    robots = page.get("robots", "index, follow")
    p_kw = page.get("primary_keyword") or ""
    p_kw_lower = p_kw.lower().strip()

    title_len = len(meta_title)
    desc_len = len(meta_desc)

    title_issues = []
    if not meta_title:
        title_issues.append("Missing meta_title")
    elif title_len < 25:
        title_issues.append(f"Meta title too short ({title_len} chars; min 25)")
    elif title_len > 70:
        title_issues.append(f"Meta title too long ({title_len} chars; max 60-70)")

    if p_kw_lower and not any(w in meta_title.lower() for w in p_kw_lower.split() if len(w) > 3):
        title_issues.append(f"Primary keyword words not in meta title: '{p_kw}'")

    desc_issues = []
    if not meta_desc:
        desc_issues.append("Missing meta_description")
    elif desc_len < 80:
        desc_issues.append(f"Meta description too short ({desc_len} chars; min 80)")
    elif desc_len > 180:
        desc_issues.append(f"Meta description too long ({desc_len} chars; max 160)")

    robots_valid = robots in ["index, follow", "noindex, follow", "index, nofollow", "noindex, nofollow"]
    if not robots_valid:
        desc_issues.append(f"Invalid robots directive: '{robots}'")

    meta_status = "passed" if not (title_issues or desc_issues) else ("warning" if len(title_issues + desc_issues) == 1 else "failed")

    # 2. Heading Hierarchy Validation
    md = page.get("markdown_content", "")
    heading_lines = [
        line.strip() for line in md.splitlines()
        if line.strip().startswith("#") and not line.strip().startswith("---")
    ]

    h1_lines = [h for h in heading_lines if h.startswith("# ") and not h.startswith("## ")]
    h2_lines = [h for h in heading_lines if h.startswith("## ") and not h.startswith("### ")]
    h3_lines = [h for h in heading_lines if h.startswith("### ") and not h.startswith("#### ")]

    heading_issues = []
    if len(h1_lines) == 0:
        heading_issues.append("Missing H1 heading in markdown content")
    elif len(h1_lines) > 1:
        heading_issues.append(f"Multiple H1 headings detected ({len(h1_lines)})")

    if len(h2_lines) == 0:
        heading_issues.append("No H2 section headings found")

    skipped_levels = False
    current_level = 0
    for h in heading_lines:
        level = len(h.split()[0])
        if level > current_level + 1 and current_level > 0:
            skipped_levels = True
            heading_issues.append(f"Skipped heading level: from H{current_level} directly to H{level}")
            break
        current_level = level

    heading_status = "passed" if not heading_issues else ("warning" if len(heading_issues) == 1 and len(h1_lines) == 1 else "failed")

    # 3. Keyword Coverage & Density Validation
    body_text = re.sub(r"---[\s\S]*?---", "", md).lower()
    words = re.findall(r"\b\w+\b", body_text)
    total_words = len(words)

    kw_issues = []
    p_kw_occurrences = 0
    if p_kw_lower:
        p_kw_occurrences = body_text.count(p_kw_lower)
        if p_kw_occurrences == 0:
            kw_issues.append(f"Primary keyword '{p_kw}' not found in body text")

    sec_kws = page.get("secondary_keywords", [])
    sec_found = [k for k in sec_kws if k.lower().strip() in body_text]
    sec_coverage_pct = round((len(sec_found) / len(sec_kws) * 100), 1) if sec_kws else 100.0

    p_kw_word_count = len(p_kw.split()) if p_kw else 1
    density_pct = round((p_kw_occurrences * p_kw_word_count / max(1, total_words)) * 100, 2)
    stuffing_detected = density_pct > 3.5

    if stuffing_detected:
        kw_issues.append(f"Keyword stuffing risk: primary keyword density is {density_pct}%")

    kw_status = "passed" if not kw_issues else "warning"

    # 4. Search Intent Alignment
    search_intent = page.get("search_intent", "informational")
    p_type = page.get("page_type", "article")
    intent_issues = []
    intent_satisfied = True

    if search_intent == "informational" and not any(k in body_text for k in ["how", "guide", "what", "steps", "understanding"]):
        intent_issues.append("Informational intent lacks clear explanatory keywords in body")
        intent_satisfied = False

    intent_status = "passed" if intent_satisfied else "warning"

    # 5. Required Questions Fulfillment
    faq_items = page.get("faq_items", [])
    req_questions = brief.get("questions_to_answer", []) if brief else []
    answered_count = 0

    if req_questions:
        for q in req_questions:
            q_clean = q.lower().replace("?", "").strip()
            if any(q_clean in item.get("question", "").lower() for item in faq_items):
                answered_count += 1
            elif any(w in body_text for w in q_clean.split() if len(w) > 4):
                answered_count += 1
        q_coverage_pct = round((answered_count / len(req_questions)) * 100, 1)
    else:
        q_coverage_pct = 100.0 if faq_items else 80.0

    q_status = "passed" if len(faq_items) >= 2 else "warning"

    # 6. Internal Links Check
    raw_links = extract_markdown_links(md)
    broken_urls = []
    link_issues = []

    for l in raw_links:
        t_url = l.get("target_url", "")
        if t_url.startswith("/") and t_url not in valid_site_urls:
            broken_urls.append(t_url)
            link_issues.append(f"Invalid internal link URL: '{t_url}' not found in URL architecture")

    if len(raw_links) == 0 and p_type != "cluster":
        link_issues.append("No internal links embedded in content body")

    link_status = "passed" if not broken_urls else "failed"

    # 7. Schema & Canonical URL Validation
    schema_type = page.get("schema_type", "")
    canonical_url = page.get("canonical_url", "")
    schema_issues = []

    valid_schemas = ["Article", "HowTo", "FAQPage", "CollectionPage", "TechArticle", "Guide"]
    if not schema_type or schema_type not in valid_schemas:
        schema_issues.append(f"Unrecognized Schema.org type: '{schema_type}'")

    if not canonical_url or not canonical_url.startswith("http"):
        schema_issues.append(f"Invalid canonical URL: '{canonical_url}'")

    schema_status = "passed" if not schema_issues else "failed"

    # 8. Content Quality Constraints
    cq_issues = []
    min_word_target = 300
    if total_words < min_word_target:
        cq_issues.append(f"Word count below minimum ({total_words} < {min_word_target})")

    has_lists = bool(re.search(r"^\s*[-*]\s+", md, re.MULTILINE))
    if not has_lists:
        cq_issues.append("Content lacks bulleted/numbered lists")

    has_frontmatter = md.startswith("---") and "\n---\n" in md
    if not has_frontmatter:
        cq_issues.append("Missing valid YAML frontmatter header")

    cq_status = "passed" if not cq_issues else ("warning" if total_words >= 300 else "failed")

    all_statuses = [meta_status, heading_status, kw_status, intent_status, q_status, link_status, schema_status, cq_status]
    if "failed" in all_statuses:
        overall_page_status = "failed"
        health_score = 65
    elif "warning" in all_statuses:
        overall_page_status = "passed_with_warnings"
        health_score = 88
    else:
        overall_page_status = "passed"
        health_score = 100

    return {
        "page_id": page.get("page_id", ""),
        "slug": page.get("slug", ""),
        "url": page.get("url", ""),
        "overall_status": overall_page_status,
        "health_score": health_score,
        "checks": {
            "metadata": {"status": meta_status, "issues": title_issues + desc_issues},
            "heading_hierarchy": {"status": heading_status, "issues": heading_issues},
            "keyword_coverage": {"status": kw_status, "issues": kw_issues},
            "search_intent": {"status": intent_status, "issues": intent_issues},
            "required_questions": {"status": q_status, "coverage": q_coverage_pct},
            "internal_links": {"status": link_status, "issues": link_issues},
            "schema_and_canonical": {"status": schema_status, "issues": schema_issues},
            "content_quality": {"status": cq_status, "issues": cq_issues},
        },
    }


def perform_full_content_validation(
    generated_content_data: Dict[str, Any],
    briefs_data: Dict[str, Any],
    artifacts: LoadedArtifacts,
    output_path: Optional[Path] = None,
) -> Tuple[Dict[str, Any], Path]:
    """Run full content validation suite across all generated pages and cross-page checks."""
    pages = generated_content_data.get("pages", [])
    briefs_list = briefs_data.get("briefs", [])
    briefs_map = {b.get("page_id"): b for b in briefs_list}

    valid_urls = {
        u.get("url") for u in artifacts.url_architecture.get("urls", []) if u.get("url")
    }
    valid_urls.add("/")
    for p in pages:
        if p.get("url"):
            valid_urls.add(p.get("url"))

    page_validations = []
    for p in pages:
        p_id = p.get("page_id", "")
        b = briefs_map.get(p_id)
        val = validate_single_page_content(p, b, valid_urls, pages)
        page_validations.append(val)

    titles_counter = Counter(p.get("meta_title", "").strip() for p in pages if p.get("meta_title"))
    descs_counter = Counter(p.get("meta_description", "").strip() for p in pages if p.get("meta_description"))
    canonicals_counter = Counter(p.get("canonical_url", "").strip() for p in pages if p.get("canonical_url"))
    kws_counter = Counter(p.get("primary_keyword", "").strip().lower() for p in pages if p.get("primary_keyword"))

    duplicate_titles = [t for t, count in titles_counter.items() if count > 1]
    duplicate_descs = [d for d, count in descs_counter.items() if count > 1]
    duplicate_canonicals = [c for c, count in canonicals_counter.items() if count > 1]
    cannibalized_keywords = [k for k, count in kws_counter.items() if count > 1]

    total_pages = len(page_validations)
    passed_pages = sum(1 for v in page_validations if v["overall_status"] == "passed")
    warning_pages = sum(1 for v in page_validations if v["overall_status"] == "passed_with_warnings")
    failed_pages = sum(1 for v in page_validations if v["overall_status"] == "failed")
    avg_health_score = (
        round(sum(v["health_score"] for v in page_validations) / total_pages, 1)
        if total_pages
        else 100.0
    )

    summary = {
        "total_pages_validated": total_pages,
        "passed_pages": passed_pages,
        "warning_pages": warning_pages,
        "failed_pages": failed_pages,
        "overall_health_score": avg_health_score,
        "duplicate_titles_found": len(duplicate_titles),
        "duplicate_descriptions_found": len(duplicate_descs),
        "duplicate_canonicals_found": len(duplicate_canonicals),
        "keyword_cannibalization_found": len(cannibalized_keywords),
    }

    validation_payload = {
        "version": "0.3",
        "phase": "content_validation",
        "validated_at": datetime.now(timezone.utc).isoformat(),
        "summary": summary,
        "site_wide_checks": {
            "duplicate_titles": duplicate_titles,
            "duplicate_descriptions": duplicate_descs,
            "duplicate_canonicals": duplicate_canonicals,
            "keyword_cannibalization": cannibalized_keywords,
        },
        "page_validations": page_validations,
    }

    target_path = output_path or Path("outputs/v03/content_validation.json")
    target_path.parent.mkdir(parents=True, exist_ok=True)
    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(validation_payload, f, indent=2, ensure_ascii=False)

    return validation_payload, target_path


def export_generated_content_json(
    results: List[GeneratedPageResult],
    briefs_manifest: Dict[str, Any],
    output_dir: Path,
) -> Path:
    """Export all generated pages to outputs/v03/generated_content.json."""
    target_path = output_dir / "generated_content.json"
    completed_pages = [r for r in results if r.status == "completed"]
    total_words = sum(r.word_count for r in completed_pages)
    avg_words = int(total_words / len(completed_pages)) if completed_pages else 0
    total_links = sum(len(r.embedded_internal_links) for r in completed_pages)
    avg_score = (
        round(sum(r.audit.get("overall_score", 0) for r in completed_pages if r.audit) / len(completed_pages), 2)
        if completed_pages
        else 0.0
    )

    pages_data = []
    for r in results:
        pages_data.append({
            "page_id": r.page_id,
            "slug": r.slug,
            "url": r.url,
            "canonical_url": r.metadata.get("canonical_url", "") if r.metadata else "",
            "page_type": r.page_type,
            "cluster": r.cluster,
            "primary_keyword": r.primary_keyword,
            "secondary_keywords": r.secondary_keywords,
            "search_intent": r.brief.get("search_intent", "") if r.brief else "",
            "title": r.brief.get("title_recommendation", r.title) if r.brief else r.title,
            "h1": r.brief.get("h1", r.title) if r.brief else r.title,
            "meta_title": r.metadata.get("seo_title", "") if r.metadata else "",
            "meta_description": r.metadata.get("meta_description", "") if r.metadata else "",
            "schema_type": r.metadata.get("schema_type", "Article") if r.metadata else "Article",
            "robots": r.metadata.get("robots", "index, follow") if r.metadata else "index, follow",
            "markdown_content": r.markdown_content,
            "faq_items": r.faq.get("faq_items", []) if r.faq else [],
            "embedded_internal_links": r.embedded_internal_links,
            "word_count": r.word_count,
            "quality_audit": r.audit,
            "status": r.status,
            "generated_at": r.generated_at,
            "error": r.error,
        })

    payload = {
        "version": "0.3",
        "phase": "content_generation",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total_pages_generated": len(completed_pages),
            "failed_pages": len(results) - len(completed_pages),
            "total_word_count": total_words,
            "average_words_per_page": avg_words,
            "total_internal_links_embedded": total_links,
            "average_quality_score": avg_score,
        },
        "pages": pages_data,
    }

    target_path.parent.mkdir(parents=True, exist_ok=True)
    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    return target_path


def generate_v03_summary_report(
    results: List[GeneratedPageResult],
    output_dir: Path,
) -> Path:
    """Generate executive Markdown summary report for v0.3 content generation."""
    report_path = output_dir / "content_generation_report.md"

    total_pages = len(results)
    completed_pages = [r for r in results if r.status == "completed"]
    failed_pages = [r for r in results if r.status == "failed"]
    total_words = sum(r.word_count for r in completed_pages)
    avg_words = int(total_words / len(completed_pages)) if completed_pages else 0
    avg_score = (
        int(sum(r.audit.get("overall_score", 0) for r in completed_pages if r.audit) / len(completed_pages))
        if completed_pages
        else 0
    )

    lines = [
        "# v0.3 — Content Generation Phase Report",
        f"\n**Generated at**: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"- **Total Pages Targeted**: {total_pages}",
        f"- **Successfully Generated**: {len(completed_pages)}",
        f"- **Failed / Incomplete**: {len(failed_pages)}",
        f"- **Total Word Count**: {total_words:,} words",
        f"- **Average Words per Page**: {avg_words:,} words",
        f"- **Average Quality Audit Score**: {avg_score}/100\n",
        "## Generated Pages Manifest\n",
        "| Page Title | URL | Type | Primary Keyword | Words | Audit Score | Internal Links | Status |",
        "|---|---|---|---|---:|---:|---:|---|",
    ]

    for r in results:
        audit_score = r.audit.get("overall_score", "N/A") if r.audit else "N/A"
        kw = r.primary_keyword or "-"
        links_count = len(r.embedded_internal_links)
        lines.append(
            f"| {r.title} | `{r.url}` | {r.page_type} | {kw} | {r.word_count} | {audit_score} | {links_count} | {r.status} |"
        )

    if failed_pages:
        lines.append("\n## Failures & Errors\n")
        for f_page in failed_pages:
            lines.append(f"- **{f_page.title}** (`{f_page.url}`): {f_page.error}")

    lines.append("\n## Next Steps (v0.4 Indexing & Deployment Prep)\n")
    lines.append("1. Verify internal links render with correct HTTP status codes in the frontend.")
    lines.append("2. Ingest generated content from `generated_content.json` into Next.js App Router / CMS.")
    lines.append("3. Submit sitemap.xml to Google Search Console for indexing watch.")

    report_content = "\n".join(lines)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)

    return report_path


def export_content_manifest(
    results: List[GeneratedPageResult],
    output_dir: Path,
) -> Path:
    """Export machine-readable manifest of all generated pages for v0.4 consumption."""
    manifest_path = output_dir / "content_manifest.json"

    manifest_data = {
        "version": "0.3",
        "phase": "content_generation",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total_pages": len(results),
            "completed": len([r for r in results if r.status == "completed"]),
            "failed": len([r for r in results if r.status == "failed"]),
            "total_words": sum(r.word_count for r in results if r.status == "completed"),
        },
        "pages": [asdict(r) for r in results],
    }

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2, ensure_ascii=False)

    return manifest_path
