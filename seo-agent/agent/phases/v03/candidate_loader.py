"""
v0.3 Content Generation & Validation — Input Loader & Candidate Normalizer.

Handles:
- Finding and loading all v0.1 research and v0.2 technical/architecture artifacts.
- Parsing keyword groups, URL architecture, and group audits.
- Normalizing raw inputs into strongly-typed `PageCandidatesManifest` and `NormalizedPageCandidate` models.
"""

import json
import logging
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from phases.v03.models import (
    ContentStrategySpec,
    GroupAuditSummary,
    InternalLinkingContainer,
    KeywordsContainer,
    LoadedArtifacts,
    NormalizedPageCandidate,
    PageCandidatesManifest,
    TechnicalSeoRules,
)

logger = logging.getLogger("v03.candidate_loader")

# Path constants
BASE_DIR = Path(__file__).resolve().parent.parent.parent
OUTPUTS_DIR = BASE_DIR / "outputs"
V02_OUTPUTS_DIR = OUTPUTS_DIR / "v02"
V03_OUTPUTS_DIR = OUTPUTS_DIR / "v03"
PAGE_CANDIDATES_PATH = V03_OUTPUTS_DIR / "page_candidates.json"


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
    Load and validate all v0.1 and v0.2 artifacts required for content generation.
    """
    out_dir = base_outputs_dir or OUTPUTS_DIR
    v02_dir = out_dir / "v02"

    logger.info("Loading v0.1 and v0.2 artifacts from disk...")

    research_report_path = find_artifact_file(
        [
            out_dir / "research_report.md",
            BASE_DIR / "research_report.md",
            v02_dir / "research_report.md",
        ],
        "research_report.md",
    )
    research_report_md = load_text_file(research_report_path)

    site_arch_path = find_artifact_file(
        [v02_dir / "site_architecture.json", out_dir / "site_architecture.json"],
        "site_architecture.json",
    )
    site_architecture = load_json_file(site_arch_path)

    keyword_groups_path = find_artifact_file(
        [v02_dir / "keyword_groups.json", out_dir / "keyword_groups.json"],
        "keyword_groups.json",
    )
    keyword_groups = load_json_file(keyword_groups_path)

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

    url_arch_path = find_artifact_file(
        [v02_dir / "url_architecture.json", out_dir / "url_architecture.json"],
        "url_architecture.json",
    )
    url_architecture = load_json_file(url_arch_path)

    internal_linking_path = find_artifact_file(
        [v02_dir / "internal_linking.json", out_dir / "internal_linking.json"],
        "internal_linking.json",
    )
    internal_linking = load_json_file(internal_linking_path)

    technical_seo_path = find_artifact_file(
        [v02_dir / "technical_seo.json", out_dir / "technical_seo.json"],
        "technical_seo.json",
    )
    technical_seo = load_json_file(technical_seo_path)

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


def extract_research_questions(research_report_md: str) -> List[str]:
    """Extract FAQ questions and question keywords from the v0.1 research report."""
    questions: List[str] = []
    for line in research_report_md.splitlines():
        line = line.strip()
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
    for cluster in site_architecture.get("clusters", []):
        for gap in cluster.get("content_gaps", []):
            gaps.append(gap)
    return gaps


def determine_recommended_schema_type(page_type: str) -> str:
    """Select standard Schema.org type based on page format."""
    mapping = {
        "cluster": "CollectionPage",
        "guide": "HowTo",
        "informational": "Article",
        "listicle": "Article",
        "comparison": "Article",
        "faq_hub": "FAQPage",
    }
    return mapping.get(page_type.lower(), "Article")


def build_unified_page_candidates(artifacts: LoadedArtifacts) -> PageCandidatesManifest:
    """
    Build a normalized, unified page candidate model by combining all loaded artifacts.
    """
    logger.info("Building unified page candidates from all loaded artifacts...")

    site_profile = artifacts.site_architecture.get("site_profile", {})
    target_audience = site_profile.get("target_audience", "General audience")
    site_purpose = site_profile.get("primary_purpose", "High quality SEO resource")

    tech_rules = artifacts.technical_seo.get("global_rules", {})
    canonical_domain = tech_rules.get("canonical_domain", "https://example.com").rstrip("/")
    default_indexing = tech_rules.get("indexing", {}).get("default", "index, follow")

    # 1. Build lookup map of internal links
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

    # 2. Build lookup maps for keyword groups
    kw_group_by_id: Dict[str, Dict[str, Any]] = {}
    kw_group_by_primary_kw: Dict[str, Dict[str, Any]] = {}

    for cluster_item in artifacts.keyword_groups.get("clusters", []):
        for grp in cluster_item.get("groups", []):
            gid = grp.get("group_id")
            p_kw = grp.get("primary_keyword")
            if gid:
                kw_group_by_id[gid] = grp
            if p_kw:
                kw_group_by_primary_kw[p_kw.lower().strip()] = grp

    # 3. Build lookup map for keyword group audits
    audit_by_group_id: Dict[str, Dict[str, Any]] = {}
    for cluster_item in artifacts.group_audit.get("clusters", []):
        for aud in cluster_item.get("audits", []):
            gid = aud.get("group_id")
            if gid:
                audit_by_group_id[gid] = aud

    # 4. Extract global questions and content gaps
    research_questions = extract_research_questions(artifacts.research_report_md)
    content_gaps = extract_content_gaps(artifacts.site_architecture)

    # 5. Iterate and normalize all pages
    candidates: List[NormalizedPageCandidate] = []

    for cluster_item in artifacts.site_architecture.get("clusters", []):
        cluster_info = cluster_item.get("cluster", {})
        cluster_name = cluster_info.get("title", cluster_info.get("name", "Topical Cluster"))
        pages = cluster_item.get("pages", [])

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
            content_status = page.get("content_status", "candidate")

            canonical_url = f"{canonical_domain}{url}"

            matched_group = None
            raw_group_id = page_id.replace("page:", "").replace("cluster:", "")
            if raw_group_id in kw_group_by_id:
                matched_group = kw_group_by_id[raw_group_id]
            elif primary_kw and primary_kw.lower().strip() in kw_group_by_primary_kw:
                matched_group = kw_group_by_primary_kw[primary_kw.lower().strip()]

            all_kw_details: List[Dict[str, Any]] = []
            question_kws: List[str] = []

            if matched_group:
                if not secondary_kws:
                    secondary_kws = matched_group.get("secondary_keywords", [])
                for kw_item in matched_group.get("keywords", []):
                    all_kw_details.append(kw_item)
                    if kw_item.get("is_question"):
                        question_kws.append(kw_item.get("keyword"))

            if not question_kws and primary_kw and any(w in primary_kw.lower() for w in ["what", "how", "why", "which", "where", "can"]):
                question_kws.append(primary_kw)

            audit_obj = None
            if raw_group_id in audit_by_group_id:
                audit_obj = audit_by_group_id[raw_group_id]
            elif matched_group and matched_group.get("group_id") in audit_by_group_id:
                audit_obj = audit_by_group_id[matched_group["group_id"]]

            if audit_obj:
                audit_summary = GroupAuditSummary(
                    group_id=audit_obj.get("group_id"),
                    status=audit_obj.get("status", "approved"),
                    confidence=audit_obj.get("confidence", 1.0),
                    intent_consistent=audit_obj.get("intent_consistent", True),
                    topic_coherent=audit_obj.get("topic_coherent", True),
                    potential_outliers=audit_obj.get("potential_outliers", []),
                    issues=audit_obj.get("issues", []),
                    recommendation=audit_obj.get("recommendation", "Proceed with generation."),
                )
            elif page_type == "cluster":
                audit_summary = GroupAuditSummary(
                    group_id=raw_group_id,
                    status="approved",
                    confidence=1.0,
                    intent_consistent=True,
                    topic_coherent=True,
                    potential_outliers=[],
                    issues=[],
                    recommendation="Top-level cluster hub page.",
                )
            else:
                audit_summary = GroupAuditSummary(
                    group_id=raw_group_id,
                    status="approved",
                    confidence=0.9,
                    intent_consistent=True,
                    topic_coherent=True,
                    issues=[],
                    recommendation="Approved candidate.",
                )

            outbound_links = outbound_by_url.get(url, [])
            inbound_links = inbound_by_url.get(url, [])

            linking_container = InternalLinkingContainer(
                outbound_links=outbound_links,
                inbound_links=inbound_links,
                outbound_count=len(outbound_links),
                inbound_count=len(inbound_links),
            )

            schema_type = determine_recommended_schema_type(page_type)
            tech_seo = TechnicalSeoRules(
                robots=default_indexing if indexable else "noindex, follow",
                canonical_url=canonical_url,
                schema_type=schema_type,
                max_title_length=60,
                max_meta_description_length=160,
                protocol=tech_rules.get("protocol", "https"),
                canonical_domain=canonical_domain,
            )

            page_faqs = [
                q for q in research_questions
                if any(w in q.lower() for w in (primary_kw or slug).replace("-", " ").lower().split() if len(w) > 3)
            ]
            if not page_faqs:
                page_faqs = research_questions[:4]

            suggested_sections = [
                f"Introduction to {title}",
                f"Core Concepts and User Guide",
                f"Best Practices & Comparison",
                f"Frequently Asked Questions",
            ]

            content_strat = ContentStrategySpec(
                target_audience=target_audience,
                site_purpose=site_purpose,
                content_gaps=content_gaps,
                relevant_faqs=page_faqs,
                recommended_word_count=1500 if page_type in ["guide", "cluster"] else 1200,
                suggested_sections=suggested_sections,
            )

            readiness = "ready_for_generation"
            if audit_summary.status in ["review", "split"] and audit_summary.confidence < 0.7:
                readiness = "needs_review"

            candidate = NormalizedPageCandidate(
                candidate_id=page_id,
                title=title,
                slug=slug,
                url=url,
                canonical_url=canonical_url,
                page_type=page_type,
                cluster=cluster_name,
                parent_page_id=parent_id,
                search_intent=intent,
                priority=priority,
                indexable=indexable,
                content_status=content_status,
                readiness_status=readiness,
                keywords=KeywordsContainer(
                    primary_keyword=primary_kw,
                    secondary_keywords=secondary_kws,
                    all_keyword_details=all_kw_details,
                    question_keywords=question_kws,
                ),
                keyword_audit=audit_summary,
                internal_linking=linking_container,
                technical_seo=tech_seo,
                content_strategy=content_strat,
            )
            candidates.append(candidate)

    summary = {
        "total_candidates": len(candidates),
        "cluster_pages": sum(1 for c in candidates if c.page_type == "cluster"),
        "content_pages": sum(1 for c in candidates if c.page_type != "cluster"),
        "high_priority_pages": sum(1 for c in candidates if c.priority == "high"),
        "medium_priority_pages": sum(1 for c in candidates if c.priority == "medium"),
        "ready_for_generation": sum(1 for c in candidates if c.readiness_status == "ready_for_generation"),
        "needs_review": sum(1 for c in candidates if c.readiness_status == "needs_review"),
        "total_internal_links": len(links),
    }

    manifest = PageCandidatesManifest(
        version="0.3",
        phase="page_candidates_preparation",
        site_profile=site_profile,
        summary=summary,
        global_technical_seo=tech_rules,
        candidates=candidates,
    )

    logger.info(
        f"Unified Page Candidates built successfully: {len(candidates)} candidates ready."
    )
    return manifest


def save_page_candidates(
    manifest: PageCandidatesManifest,
    output_path: Optional[Path] = None,
) -> Path:
    """Save normalized page candidates manifest to JSON."""
    target_path = output_path or PAGE_CANDIDATES_PATH
    target_path.parent.mkdir(parents=True, exist_ok=True)

    manifest_dict = asdict(manifest)

    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(manifest_dict, f, indent=2, ensure_ascii=False)

    logger.info(f"Saved normalized page candidates to: {target_path}")
    return target_path
