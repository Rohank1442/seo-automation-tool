"""
v0.3 — Content Generation Pipeline Skeleton.

This phase consumes the outputs of v0.1 (SEO & Competitor Research) and v0.2
(Site Architecture, Keyword Groups, URL Architecture, Internal Linking, and Technical SEO)
to produce comprehensive, publication-ready SEO content, technical metadata, FAQ blocks,
and internal link placements.

Inputs (Read-only):
    - outputs/research_report.md
    - outputs/v02/site_architecture.json
    - outputs/v02/keyword_groups.json
    - outputs/v02/keyword_group_audit.json (or group_audit.json)
    - outputs/v02/url_architecture.json
    - outputs/v02/internal_linking.json
    - outputs/v02/technical_seo.json

Outputs:
    - outputs/v03/content_manifest.json
    - outputs/v03/content_generation_report.md
    - outputs/v03/pages/{slug}.md
    - outputs/v03/pages/{slug}.json
"""

import argparse
import json
import logging
import os
import re
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel

# Project imports
try:
    from core.llm import generate_json, generate_text
    from prompts.v03_prompts import (
        CONTENT_AUDIT_SYSTEM_PROMPT,
        FAQ_GENERATION_SYSTEM_PROMPT,
        METADATA_GENERATION_SYSTEM_PROMPT,
        PAGE_BRIEF_SYSTEM_PROMPT,
        SECTION_DRAFTING_SYSTEM_PROMPT,
        ContentOutlineResponse,
        ContentQualityAuditResponse,
        FAQSectionResponse,
        PageMetadataResponse,
        build_content_audit_prompt,
        build_drafting_prompt,
        build_faq_prompt,
        build_metadata_prompt,
        build_page_brief_prompt,
    )
except ImportError:
    # Handle direct script execution or module invocation
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from core.llm import generate_json, generate_text
    from prompts.v03_prompts import (
        CONTENT_AUDIT_SYSTEM_PROMPT,
        FAQ_GENERATION_SYSTEM_PROMPT,
        METADATA_GENERATION_SYSTEM_PROMPT,
        PAGE_BRIEF_SYSTEM_PROMPT,
        SECTION_DRAFTING_SYSTEM_PROMPT,
        ContentOutlineResponse,
        ContentQualityAuditResponse,
        FAQSectionResponse,
        PageMetadataResponse,
        build_content_audit_prompt,
        build_drafting_prompt,
        build_faq_prompt,
        build_metadata_prompt,
        build_page_brief_prompt,
    )


# ============================================================
# LOGGING SETUP
# ============================================================

logger = logging.getLogger("v03_content_generation")


def configure_logging(level: int = logging.INFO) -> logging.Logger:
    """Configure structured console logging for the pipeline."""
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [v0.3] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(level)
    return logger


# ============================================================
# PATH CONSTANTS & DIRECTORY DISCOVERY
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUTS_DIR = BASE_DIR / "outputs"
V02_OUTPUTS_DIR = OUTPUTS_DIR / "v02"
V03_OUTPUTS_DIR = OUTPUTS_DIR / "v03"
V03_PAGES_DIR = V03_OUTPUTS_DIR / "pages"


# ============================================================
# DATA STRUCTURES & MODELS
# ============================================================

@dataclass
class LoadedArtifacts:
    """Container for all loaded v0.1 and v0.2 artifacts."""

    research_report_md: str
    site_architecture: Dict[str, Any]
    keyword_groups: Dict[str, Any]
    group_audit: Dict[str, Any]
    url_architecture: Dict[str, Any]
    internal_linking: Dict[str, Any]
    technical_seo: Dict[str, Any]
    loaded_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


@dataclass
class PageContext:
    """Consolidated context and specifications for generating an individual page."""

    page_id: str
    title: str
    slug: str
    url: str
    page_type: str
    cluster: str
    parent_page_id: Optional[str]
    primary_keyword: Optional[str]
    secondary_keywords: List[str]
    search_intent: str
    priority: str
    indexable: bool
    target_audience: str
    site_purpose: str
    outbound_internal_links: List[Dict[str, Any]] = field(default_factory=list)
    inbound_internal_links: List[Dict[str, Any]] = field(default_factory=list)
    content_gaps: List[Dict[str, Any]] = field(default_factory=list)
    research_questions: List[str] = field(default_factory=list)
    technical_guidelines: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GeneratedPageResult:
    """Full generation outcome for a single page."""

    page_id: str
    slug: str
    url: str
    title: str
    page_type: str
    cluster: str
    primary_keyword: Optional[str]
    secondary_keywords: List[str]
    brief: Optional[Dict[str, Any]] = None
    markdown_content: str = ""
    metadata: Optional[Dict[str, Any]] = None
    faq: Optional[Dict[str, Any]] = None
    audit: Optional[Dict[str, Any]] = None
    word_count: int = 0
    status: str = "pending"
    generated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    error: Optional[str] = None


# ============================================================
# STEP 1: ARTIFACT LOADER & VALIDATOR
# ============================================================

def find_artifact_file(candidate_paths: List[Path], file_desc: str) -> Path:
    """Locate an artifact file among candidate paths or raise FileNotFoundError."""
    for path in candidate_paths:
        if path.exists() and path.is_file():
            return path
    locations = "\n  - ".join(str(p) for p in candidate_paths)
    raise FileNotFoundError(
        f"Required {file_desc} not found. Searched locations:\n  - {locations}"
    )


def load_json_file(path: Path) -> Dict[str, Any]:
    """Safely load and decode a JSON file."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except UnicodeDecodeError:
        with open(path, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to parse JSON file {path}: {e}")
        raise


def load_text_file(path: Path) -> str:
    """Safely load a text/markdown file."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError:
        with open(path, "r", encoding="utf-8-sig") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Failed to read text file {path}: {e}")
        raise


def load_all_pipeline_inputs(base_outputs_dir: Optional[Path] = None) -> LoadedArtifacts:
    """
    Load and validate all v0.1 and v0.2 artifacts.

    Searches in standard and fallback paths to guarantee resiliency.
    """
    out_dir = base_outputs_dir or OUTPUTS_DIR
    v02_dir = out_dir / "v02"

    logger.info("Loading v0.1 and v0.2 artifacts from disk...")

    # 1. Research Report (v0.1)
    research_report_path = find_artifact_file(
        [
            out_dir / "research_report.md",
            BASE_DIR / "research_report.md",
            v02_dir / "research_report.md",
        ],
        "research_report.md",
    )
    research_report_md = load_text_file(research_report_path)
    logger.info(f"  [x] Loaded research_report.md ({len(research_report_md)} bytes)")

    # 2. Site Architecture (v0.2)
    site_arch_path = find_artifact_file(
        [v02_dir / "site_architecture.json", out_dir / "site_architecture.json"],
        "site_architecture.json",
    )
    site_architecture = load_json_file(site_arch_path)
    logger.info(f"  [x] Loaded site_architecture.json (clusters: {len(site_architecture.get('clusters', []))})")

    # 3. Keyword Groups (v0.2)
    keyword_groups_path = find_artifact_file(
        [v02_dir / "keyword_groups.json", out_dir / "keyword_groups.json"],
        "keyword_groups.json",
    )
    keyword_groups = load_json_file(keyword_groups_path)
    logger.info("  [x] Loaded keyword_groups.json")

    # 4. Keyword Group Audit (v0.2 - support both naming variants)
    group_audit_path = find_artifact_file(
        [
            v02_dir / "keyword_group_audit.json",
            v02_dir / "group_audit.json",
            out_dir / "keyword_group_audit.json",
            out_dir / "group_audit.json",
        ],
        "group_audit.json / keyword_group_audit.json",
    )
    group_audit = load_json_file(group_audit_path)
    logger.info("  [x] Loaded group audit artifact")

    # 5. URL Architecture (v0.2)
    url_arch_path = find_artifact_file(
        [v02_dir / "url_architecture.json", out_dir / "url_architecture.json"],
        "url_architecture.json",
    )
    url_architecture = load_json_file(url_arch_path)
    logger.info(f"  [x] Loaded url_architecture.json (urls: {len(url_architecture.get('urls', []))})")

    # 6. Internal Linking (v0.2)
    internal_linking_path = find_artifact_file(
        [v02_dir / "internal_linking.json", out_dir / "internal_linking.json"],
        "internal_linking.json",
    )
    internal_linking = load_json_file(internal_linking_path)
    logger.info(f"  [x] Loaded internal_linking.json (links: {len(internal_linking.get('links', []))})")

    # 7. Technical SEO (v0.2)
    technical_seo_path = find_artifact_file(
        [v02_dir / "technical_seo.json", out_dir / "technical_seo.json"],
        "technical_seo.json",
    )
    technical_seo = load_json_file(technical_seo_path)
    logger.info("  [x] Loaded technical_seo.json")

    logger.info("All 7 v0.1/v0.2 pipeline inputs loaded and validated successfully.")

    return LoadedArtifacts(
        research_report_md=research_report_md,
        site_architecture=site_architecture,
        keyword_groups=keyword_groups,
        group_audit=group_audit,
        url_architecture=url_architecture,
        internal_linking=internal_linking,
        technical_seo=technical_seo,
    )


# ============================================================
# STEP 2: CONTEXT AGGREGATION & PAGE SPEC COMPILER
# ============================================================

def extract_research_questions(research_report_md: str) -> List[str]:
    """Extract FAQ questions and question keywords from the v0.1 research report."""
    questions: List[str] = []
    for line in research_report_md.splitlines():
        line = line.strip()
        # Look for table rows with is_question == Yes or lines ending with '?'
        if line.startswith("|") and "Yes" in line:
            parts = [p.strip() for p in line.split("|")]
            if len(parts) > 1 and parts[1]:
                kw = parts[1]
                if kw not in ["Keyword", "---"]:
                    questions.append(kw)
        elif line.startswith("-") and line.endswith("?"):
            questions.append(line.lstrip("- ").strip())
    return list(dict.fromkeys(questions))


def extract_content_gaps(site_architecture: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract content gaps if present in site architecture or profile."""
    gaps: List[Dict[str, Any]] = []
    # Check if page_opportunities structure is embedded
    for cluster in site_architecture.get("clusters", []):
        for gap in cluster.get("content_gaps", []):
            gaps.append(gap)
    return gaps


def compile_page_contexts(artifacts: LoadedArtifacts) -> List[PageContext]:
    """
    Compile unified PageContext objects for every planned page by merging:
    - Site & URL architecture specifications
    - Semantic keyword groups & secondary keywords
    - Outbound and inbound internal links
    - Technical SEO guidelines
    - Extracted research gaps and user questions
    """
    contexts: List[PageContext] = []

    site_profile = artifacts.site_architecture.get("site_profile", {})
    target_audience = site_profile.get("target_audience", "General fashion audience")
    site_purpose = site_profile.get("primary_purpose", "High quality SEO resource")

    # Build lookup map of internal links by source and target URL
    links = artifacts.internal_linking.get("links", [])
    outbound_by_url: Dict[str, List[Dict[str, Any]]] = {}
    inbound_by_url: Dict[str, List[Dict[str, Any]]] = {}

    for link in links:
        s_url = link.get("source_url")
        t_url = link.get("target_url")
        if s_url:
            outbound_by_url.setdefault(s_url, []).append(link)
        if t_url:
            inbound_by_url.setdefault(t_url, []).append(link)

    # Build lookup map of keyword groups by group_id or primary_keyword
    kw_group_map: Dict[str, Dict[str, Any]] = {}
    for cluster_item in artifacts.keyword_groups.get("clusters", []):
        for grp in cluster_item.get("groups", []):
            if grp.get("group_id"):
                kw_group_map[grp["group_id"]] = grp
            if grp.get("primary_keyword"):
                kw_group_map[grp["primary_keyword"].lower()] = grp

    # Extract global research questions & content gaps
    research_questions = extract_research_questions(artifacts.research_report_md)
    content_gaps = extract_content_gaps(artifacts.site_architecture)
    technical_rules = artifacts.technical_seo.get("global_rules", {})

    # Iterate through each planned page in site_architecture
    for cluster_wrapper in artifacts.site_architecture.get("clusters", []):
        cluster_name = cluster_wrapper.get("cluster", {}).get("title", "Main Cluster")
        pages = cluster_wrapper.get("pages", [])

        for page in pages:
            page_id = page.get("id", "")
            title = page.get("title", "Untitled Page")
            slug = page.get("slug", "")
            url = page.get("url", f"/{slug}/")
            page_type = page.get("page_type", "article")
            parent_id = page.get("parent_page_id")
            primary_kw = page.get("primary_keyword")
            secondary_kws = page.get("secondary_keywords", [])
            intent = page.get("intent", "informational")
            priority = page.get("priority", "medium")
            indexable = page.get("indexable", True)

            # Enrich secondary keywords if missing from keyword_groups.json
            if not secondary_kws and primary_kw:
                matched_grp = kw_group_map.get(primary_kw.lower())
                if matched_grp:
                    secondary_kws = matched_grp.get("secondary_keywords", [])

            # Filter relevant questions for this page
            page_questions = [
                q for q in research_questions
                if any(w in q.lower() for w in (primary_kw or slug).replace("-", " ").lower().split() if len(w) > 3)
            ]
            if not page_questions:
                page_questions = research_questions[:4]

            ctx = PageContext(
                page_id=page_id,
                title=title,
                slug=slug,
                url=url,
                page_type=page_type,
                cluster=cluster_name,
                parent_page_id=parent_id,
                primary_keyword=primary_kw,
                secondary_keywords=secondary_kws,
                search_intent=intent,
                priority=priority,
                indexable=indexable,
                target_audience=target_audience,
                site_purpose=site_purpose,
                outbound_internal_links=outbound_by_url.get(url, []),
                inbound_internal_links=inbound_by_url.get(url, []),
                content_gaps=content_gaps,
                research_questions=page_questions,
                technical_guidelines=technical_rules,
            )
            contexts.append(ctx)

    logger.info(f"Compiled {len(contexts)} page generation context specifications.")
    return contexts


# ============================================================
# STEP 3: CONTENT GENERATION GENERATOR FUNCTIONS
# ============================================================

def generate_page_brief(context: PageContext, dry_run: bool = False) -> ContentOutlineResponse:
    """Generate a structured content brief and section outline for the page."""
    if dry_run:
        logger.info(f"  [DRY-RUN] Generating content brief for: {context.title}")
        return ContentOutlineResponse(
            page_title=context.title,
            h1_heading=f"{context.title}: The Complete Guide",
            target_audience=context.target_audience,
            estimated_total_word_count=1200,
            content_format=context.page_type,
            sections=[
                {
                    "heading_level": "H2",
                    "heading_text": f"Understanding {context.title}",
                    "target_keywords": [context.primary_keyword] if context.primary_keyword else [],
                    "key_points": ["Core definitions", "Current industry state", "Why it matters"],
                    "recommended_word_count": 300,
                    "internal_link_opportunities": [
                        l.get("target_url", "") for l in context.outbound_internal_links[:2]
                    ],
                },
                {
                    "heading_level": "H2",
                    "heading_text": "Key Benefits and Real-World Applications",
                    "target_keywords": context.secondary_keywords[:2],
                    "key_points": ["Practical advantages", "User experience enhancement", "E-commerce impact"],
                    "recommended_word_count": 400,
                    "internal_link_opportunities": [
                        l.get("target_url", "") for l in context.outbound_internal_links[2:4]
                    ],
                },
                {
                    "heading_level": "H2",
                    "heading_text": "Step-by-Step Implementation Guide",
                    "target_keywords": context.secondary_keywords[2:4],
                    "key_points": ["Tools to use", "Step 1 to 4 workflow", "Best practices"],
                    "recommended_word_count": 350,
                    "internal_link_opportunities": [],
                },
                {
                    "heading_level": "H2",
                    "heading_text": "Future Trends and Next Steps",
                    "target_keywords": [],
                    "key_points": ["Emerging technologies", "Creator opportunities", "Final thoughts"],
                    "recommended_word_count": 150,
                    "internal_link_opportunities": [],
                },
            ],
            eeat_focus_areas=["First-hand testing methodology", "Real product examples", "Authoritative sources"],
        )

    prompt = build_page_brief_prompt(
        page_title=context.title,
        page_url=context.url,
        page_type=context.page_type,
        cluster_name=context.cluster,
        primary_keyword=context.primary_keyword,
        secondary_keywords=context.secondary_keywords,
        search_intent=context.search_intent,
        content_gaps=context.content_gaps,
        internal_links_outbound=context.outbound_internal_links,
        target_audience=context.target_audience,
        site_purpose=context.site_purpose,
    )

    logger.info(f"Requesting LLM brief generation for '{context.title}'...")
    brief_data: ContentOutlineResponse = generate_json(
        prompt=prompt,
        response_schema=ContentOutlineResponse,
        system_instruction=PAGE_BRIEF_SYSTEM_PROMPT,
    )
    return brief_data


def draft_page_content(
    context: PageContext,
    brief: ContentOutlineResponse,
    dry_run: bool = False,
) -> str:
    """Draft full-length Markdown article based on the outline brief and link specifications."""
    if dry_run:
        logger.info(f"  [DRY-RUN] Drafting markdown content for: {context.title}")
        md_lines = [
            f"# {brief.h1_heading}\n",
            f"*{context.title} is an essential component of modern {context.cluster.lower()}. "
            f"Whether you are exploring {context.primary_keyword or 'new solutions'} or optimizing your workflow, "
            f"this guide provides comprehensive, actionable insights.* \n",
        ]
        for sec in brief.sections:
            md_lines.append(f"\n## {sec.heading_text}\n")
            md_lines.append(
                f"When addressing **{sec.heading_text}**, it is important to consider the primary factors that drive quality. "
                f"Incorporating key elements such as {', '.join(sec.target_keywords) if sec.target_keywords else 'best practices'} "
                f"ensures consistent, high-performing outcomes across all use cases.\n"
            )
            for kp in sec.key_points:
                md_lines.append(f"- **{kp}**: Detailed analysis and actionable recommendation.")
            md_lines.append("")

            # Embed mock internal links
            if sec.internal_link_opportunities:
                link_target = sec.internal_link_opportunities[0]
                matching_link = next(
                    (l for l in context.outbound_internal_links if l.get("target_url") == link_target),
                    None,
                )
                anchor = matching_link.get("anchor_text", "learn more here") if matching_link else "related guide"
                md_lines.append(f"\nFor more in-depth background, explore our dedicated [{anchor}]({link_target}).\n")

        return "\n".join(md_lines)

    prompt = build_drafting_prompt(
        page_title=context.title,
        h1_heading=brief.h1_heading,
        page_url=context.url,
        page_type=context.page_type,
        cluster_name=context.cluster,
        primary_keyword=context.primary_keyword,
        secondary_keywords=context.secondary_keywords,
        outline_data=brief.model_dump(),
        internal_links=context.outbound_internal_links,
    )

    logger.info(f"Drafting full Markdown article content for '{context.title}'...")
    content_md = generate_text(
        prompt=prompt,
        system_instruction=SECTION_DRAFTING_SYSTEM_PROMPT,
    )
    return content_md


def generate_page_faq(context: PageContext, dry_run: bool = False) -> FAQSectionResponse:
    """Generate FAQ Q&A block tailored to question keywords and user search queries."""
    if dry_run:
        return FAQSectionResponse(
            section_heading="Frequently Asked Questions",
            faq_items=[
                {
                    "question": f"What is the best way to get started with {context.title.lower()}?",
                    "answer": f"Getting started with {context.title.lower()} begins with understanding your core requirements, selecting reputable tools, and following step-by-step best practices.",
                    "target_question_keyword": context.primary_keyword,
                },
                {
                    "question": f"Is {context.title.lower()} completely free to use?",
                    "answer": "Many platforms provide free tiers or trials, while advanced features and enterprise integrations may require a premium subscription.",
                    "target_question_keyword": None,
                },
                {
                    "question": "How does this compare to traditional alternatives?",
                    "answer": "Modern AI-driven approaches offer faster turnaround times, lower cost, and greater flexibility compared to legacy manual workflows.",
                    "target_question_keyword": None,
                },
            ],
        )

    prompt = build_faq_prompt(
        page_title=context.title,
        primary_keyword=context.primary_keyword,
        secondary_keywords=context.secondary_keywords,
        research_questions=context.research_questions,
        cluster_name=context.cluster,
    )

    logger.info(f"Generating FAQ block for '{context.title}'...")
    faq_data: FAQSectionResponse = generate_json(
        prompt=prompt,
        response_schema=FAQSectionResponse,
        system_instruction=FAQ_GENERATION_SYSTEM_PROMPT,
    )
    return faq_data


def generate_page_metadata(context: PageContext, dry_run: bool = False) -> PageMetadataResponse:
    """Generate technical SEO Title, Description, and Schema.org metadata."""
    if dry_run:
        kw = context.primary_keyword or context.title
        seo_title = f"{context.title} (2026 Complete Guide)"[:60]
        meta_desc = f"Discover everything you need to know about {kw}. Step-by-step tips, tool reviews, and actionable styling advice."[:155]
        return PageMetadataResponse(
            seo_title=seo_title,
            meta_description=meta_desc,
            primary_keyword=context.primary_keyword or context.title,
            secondary_keywords=context.secondary_keywords[:4],
            canonical_url=context.url,
            robots="index, follow" if context.indexable else "noindex, follow",
            schema_type="Article",
            og_title=seo_title,
            og_description=meta_desc,
        )

    prompt = build_metadata_prompt(
        page_title=context.title,
        page_url=context.url,
        primary_keyword=context.primary_keyword,
        secondary_keywords=context.secondary_keywords,
        cluster_name=context.cluster,
        target_audience=context.target_audience,
    )

    logger.info(f"Generating technical metadata for '{context.title}'...")
    metadata: PageMetadataResponse = generate_json(
        prompt=prompt,
        response_schema=PageMetadataResponse,
        system_instruction=METADATA_GENERATION_SYSTEM_PROMPT,
    )
    return metadata


def audit_page_content(
    context: PageContext,
    markdown_content: str,
    dry_run: bool = False,
) -> ContentQualityAuditResponse:
    """Perform quality and technical compliance audit on drafted article."""
    words = len(re.findall(r"\b\w+\b", markdown_content))
    links_found = len(re.findall(r"\[([^\]]+)\]\(([^)]+)\)", markdown_content))

    if dry_run:
        return ContentQualityAuditResponse(
            overall_score=92,
            status="passed",
            keyword_coverage_score=90,
            heading_hierarchy_valid=True,
            internal_links_count=links_found,
            word_count=words,
            readability_rating="clear_and_engaging",
            eeat_rating="strong",
            strengths=[
                "Directly satisfies search intent in opening paragraph",
                "Logical H2 and H3 heading hierarchy",
                "Natural keyword integration",
            ],
            improvements=[
                "Consider adding a quick summary comparison table",
            ],
            checks=[
                {"check_name": "Word Count Compliance", "passed": words >= 300, "details": f"{words} words drafted"},
                {"check_name": "Heading Structure", "passed": True, "details": "Clean H1/H2/H3 nesting"},
                {"check_name": "Internal Links Present", "passed": links_found > 0, "details": f"{links_found} internal links embedded"},
            ],
        )

    prompt = build_content_audit_prompt(
        page_title=context.title,
        primary_keyword=context.primary_keyword,
        secondary_keywords=context.secondary_keywords,
        draft_content=markdown_content,
        planned_links=context.outbound_internal_links,
    )

    logger.info(f"Auditing drafted content for '{context.title}'...")
    audit_data: ContentQualityAuditResponse = generate_json(
        prompt=prompt,
        response_schema=ContentQualityAuditResponse,
        system_instruction=CONTENT_AUDIT_SYSTEM_PROMPT,
    )
    return audit_data


# ============================================================
# STEP 4: SINGLE PAGE ORCHESTRATION & COMPOSITION
# ============================================================

def compose_complete_markdown_page(
    context: PageContext,
    metadata: PageMetadataResponse,
    article_md: str,
    faq: FAQSectionResponse,
) -> str:
    """Compose the final unified markdown document with YAML frontmatter, body, and FAQ."""
    # Build YAML frontmatter
    sec_kws_formatted = json.dumps(metadata.secondary_keywords)
    safe_title = metadata.seo_title.replace('"', '\\"')
    safe_desc = metadata.meta_description.replace('"', '\\"')
    frontmatter = f"""---
title: "{safe_title}"
description: "{safe_desc}"
url: "{context.url}"
canonical: "{metadata.canonical_url}"
robots: "{metadata.robots}"
primary_keyword: "{metadata.primary_keyword}"
secondary_keywords: {sec_kws_formatted}
cluster: "{context.cluster}"
page_type: "{context.page_type}"
schema_type: "{metadata.schema_type}"
generated_at: "{datetime.now(timezone.utc).isoformat()}"
---

"""
    # Append FAQ section if available and not already in article
    faq_block = ""
    if faq and faq.faq_items and "Frequently Asked Questions" not in article_md:
        faq_block = f"\n\n## {faq.section_heading}\n\n"
        for item in faq.faq_items:
            faq_block += f"### {item.question}\n\n{item.answer}\n\n"

    return frontmatter + article_md.strip() + faq_block


def process_single_page(
    context: PageContext,
    dry_run: bool = False,
) -> GeneratedPageResult:
    """Execute the end-to-end content generation pipeline for a single page."""
    logger.info(f"\n==================================================")
    logger.info(f"Processing Page: {context.title} ({context.url})")
    logger.info(f"Primary Keyword: '{context.primary_keyword}' | Type: {context.page_type}")
    logger.info(f"==================================================")

    result = GeneratedPageResult(
        page_id=context.page_id,
        slug=context.slug,
        url=context.url,
        title=context.title,
        page_type=context.page_type,
        cluster=context.cluster,
        primary_keyword=context.primary_keyword,
        secondary_keywords=context.secondary_keywords,
    )

    try:
        # 1. Generate Content Brief & Outline
        brief = generate_page_brief(context, dry_run=dry_run)
        result.brief = brief.model_dump()

        # 2. Draft Article Body Markdown
        article_md = draft_page_content(context, brief, dry_run=dry_run)

        # 3. Generate FAQ Block
        faq = generate_page_faq(context, dry_run=dry_run)
        result.faq = faq.model_dump()

        # 4. Generate Technical Metadata
        meta = generate_page_metadata(context, dry_run=dry_run)
        result.metadata = meta.model_dump()

        # 5. Compose Full Page (Frontmatter + Markdown + FAQ)
        full_markdown = compose_complete_markdown_page(context, meta, article_md, faq)
        result.markdown_content = full_markdown
        result.word_count = len(re.findall(r"\b\w+\b", full_markdown))

        # 6. Quality & SEO Compliance Audit
        audit = audit_page_content(context, full_markdown, dry_run=dry_run)
        result.audit = audit.model_dump()

        result.status = "completed"
        logger.info(f" Successfully generated '{context.title}' ({result.word_count} words | Audit score: {audit.overall_score}/100)")

    except Exception as e:
        logger.error(f" Failed generating '{context.title}': {e}", exc_info=True)
        result.status = "failed"
        result.error = str(e)

    return result


# ============================================================
# STEP 5: ARTIFACT SERIALIZATION & REPOSITORIES
# ============================================================

def save_generated_page(result: GeneratedPageResult, pages_dir: Path) -> Tuple[Path, Path]:
    """Save individual page Markdown and structured JSON files."""
    pages_dir.mkdir(parents=True, exist_ok=True)
    safe_slug = result.slug.strip("/").replace("/", "_") or "home"

    md_path = pages_dir / f"{safe_slug}.md"
    json_path = pages_dir / f"{safe_slug}.json"

    # Save Markdown file
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(result.markdown_content)

    # Save JSON file
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(asdict(result), f, indent=2, ensure_ascii=False)

    return md_path, json_path


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
        "| Page Title | URL | Type | Primary Keyword | Words | Audit Score | Status |",
        "|---|---|---|---|---:|---:|---|",
    ]

    for r in results:
        audit_score = r.audit.get("overall_score", "N/A") if r.audit else "N/A"
        kw = r.primary_keyword or "-"
        lines.append(
            f"| {r.title} | `{r.url}` | {r.page_type} | {kw} | {r.word_count} | {audit_score} | {r.status} |"
        )

    if failed_pages:
        lines.append("\n## Failures & Errors\n")
        for f_page in failed_pages:
            lines.append(f"- **{f_page.title}** (`{f_page.url}`): {f_page.error}")

    lines.append("\n## Next Steps (v0.4 Indexing & Deployment Prep)\n")
    lines.append("1. Feed generated articles into CMS or static Next.js frontend pages.")
    lines.append("2. Verify internal links render with correct HTTP status codes.")
    lines.append("3. Submit updated sitemap.xml to Google Search Console for indexing watch.")

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


# ============================================================
# STEP 6: MAIN PIPELINE RUNNER
# ============================================================

def run_content_generation_phase(
    dry_run: bool = False,
    target_slug: Optional[str] = None,
    max_pages: Optional[int] = None,
    output_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Main entry point for v0.3 Content Generation Phase.

    Args:
        dry_run: When True, uses deterministic mock generation instead of live LLM API calls.
        target_slug: Optional slug filter to generate a single specific page.
        max_pages: Optional limit on the number of pages to generate in this run.
        output_dir: Custom destination directory for v0.3 outputs (defaults to outputs/v03).

    Returns:
        Summary dict containing counts, artifacts paths, and execution status.
    """
    configure_logging()
    logger.info("==========================================================")
    logger.info("STARTING V0.3 CONTENT GENERATION PIPELINE")
    logger.info(f"Dry-run mode: {dry_run} | Target slug: {target_slug or 'ALL'}")
    logger.info("==========================================================")

    out_dir = output_dir or V03_OUTPUTS_DIR
    pages_dir = out_dir / "pages"
    out_dir.mkdir(parents=True, exist_ok=True)
    pages_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load inputs
    artifacts = load_all_pipeline_inputs()

    # 2. Compile page contexts
    page_contexts = compile_page_contexts(artifacts)

    # Apply filters if requested
    if target_slug:
        page_contexts = [c for c in page_contexts if c.slug == target_slug or c.slug.strip("/") == target_slug.strip("/")]
        if not page_contexts:
            logger.warning(f"No pages matched the target slug '{target_slug}'.")

    if max_pages and max_pages > 0:
        page_contexts = page_contexts[:max_pages]
        logger.info(f"Constrained generation run to top {max_pages} pages.")

    # 3. Process pages
    results: List[GeneratedPageResult] = []
    for idx, ctx in enumerate(page_contexts, start=1):
        logger.info(f"\n[Page {idx}/{len(page_contexts)}]")
        res = process_single_page(ctx, dry_run=dry_run)
        save_generated_page(res, pages_dir)
        results.append(res)

    # 4. Export Manifest & Summary Report
    manifest_path = export_content_manifest(results, out_dir)
    report_path = generate_v03_summary_report(results, out_dir)

    logger.info("\n==========================================================")
    logger.info("V0.3 CONTENT GENERATION COMPLETED")
    logger.info(f"  Manifest: {manifest_path}")
    logger.info(f"  Report:   {report_path}")
    logger.info(f"  Pages Saved In: {pages_dir}")
    logger.info("==========================================================")

    return {
        "status": "success",
        "total_processed": len(results),
        "completed": len([r for r in results if r.status == "completed"]),
        "manifest_path": str(manifest_path),
        "report_path": str(report_path),
        "output_directory": str(out_dir),
    }


# ============================================================
# CLI ENTRY POINT
# ============================================================

def main():
    """Command-line interface for running the v0.3 content generation pipeline."""
    parser = argparse.ArgumentParser(
        description="v0.3 Content Generation Pipeline for SEO Automation",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without calling external LLM APIs (generates structured template content)",
    )
    parser.add_argument(
        "--slug",
        type=str,
        default=None,
        help="Generate content only for a specific page slug",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Limit number of pages to generate in this run",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug-level logging",
    )

    args = parser.parse_args()

    if args.verbose:
        configure_logging(logging.DEBUG)

    try:
        run_content_generation_phase(
            dry_run=args.dry_run,
            target_slug=args.slug,
            max_pages=args.max_pages,
        )
    except Exception as e:
        logger.error(f"Pipeline execution aborted due to unhandled exception: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
