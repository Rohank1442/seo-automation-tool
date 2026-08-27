"""
v0.3 Content Generation Prompts and Response Schemas.

This module defines the Pydantic models, system instructions, and structured
prompt builders used during the v0.3 content generation phase.

Key Responsibilities:
- Page Brief / Content Outline generation
- Section-by-section long-form content drafting
- FAQ & Structured Data generation
- Technical SEO metadata generation (Title, Description, Schema)
- Content Quality & SEO Compliance Audit
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ============================================================
# RESPONSE SCHEMAS
# ============================================================

class SectionBrief(BaseModel):
    """Specification for a single section within a page content outline."""

    heading_level: str = Field(
        default="H2",
        description="Heading level for this section ('H2' or 'H3').",
    )
    heading_text: str = Field(
        description="Text of the section heading.",
    )
    target_keywords: List[str] = Field(
        default_factory=list,
        description="Primary and secondary keywords to weave naturally into this section.",
    )
    key_points: List[str] = Field(
        default_factory=list,
        description="Key takeaways, data points, or topics to cover in this section.",
    )
    recommended_word_count: int = Field(
        default=250,
        description="Target word count for this section.",
    )
    internal_link_opportunities: List[str] = Field(
        default_factory=list,
        description="Target URLs or anchor concepts to link to from this section.",
    )


class ContentOutlineResponse(BaseModel):
    """Structured outline and content brief for an SEO page."""

    page_title: str = Field(
        description="Proposed working title for the page.",
    )
    h1_heading: str = Field(
        description="The single H1 heading for the page.",
    )
    target_audience: str = Field(
        description="Description of the target reader and their search intent.",
    )
    estimated_total_word_count: int = Field(
        default=1200,
        description="Estimated total word count across all sections.",
    )
    content_format: str = Field(
        default="guide",
        description="Content format type (e.g., 'guide', 'listicle', 'comparison', 'faq_hub').",
    )
    sections: List[SectionBrief] = Field(
        default_factory=list,
        description="Ordered list of section briefs covering the entire topic.",
    )
    eeat_focus_areas: List[str] = Field(
        default_factory=list,
        description="Specific trust signals, expert insights, or data points to establish E-E-A-T.",
    )


class FAQItem(BaseModel):
    """A single Question & Answer pair."""

    question: str = Field(
        description="Question text based on search queries and user FAQs.",
    )
    answer: str = Field(
        description="Clear, concise, authoritative answer formatted in Markdown.",
    )
    target_question_keyword: Optional[str] = Field(
        default=None,
        description="The specific question keyword this FAQ answers.",
    )


class FAQSectionResponse(BaseModel):
    """Collection of FAQ items for inclusion in the page and FAQPage schema."""

    section_heading: str = Field(
        default="Frequently Asked Questions",
        description="Section heading for the FAQ block.",
    )
    faq_items: List[FAQItem] = Field(
        default_factory=list,
        description="List of FAQ Q&A items.",
    )


class PageMetadataResponse(BaseModel):
    """Technical SEO and Social metadata for a generated page."""

    seo_title: str = Field(
        description="SEO Title tag (50-60 characters, includes primary keyword).",
    )
    meta_description: str = Field(
        description="Meta description (130-160 characters, compelling CTA, includes primary keyword).",
    )
    primary_keyword: str = Field(
        description="Primary target keyword for the page.",
    )
    secondary_keywords: List[str] = Field(
        default_factory=list,
        description="Secondary target keywords included.",
    )
    canonical_url: str = Field(
        description="Canonical URL for this page.",
    )
    robots: str = Field(
        default="index, follow",
        description="Robots meta directive.",
    )
    schema_type: str = Field(
        default="Article",
        description="Primary schema.org Type (e.g., 'Article', 'HowTo', 'FAQPage').",
    )
    og_title: str = Field(
        description="OpenGraph title for social sharing.",
    )
    og_description: str = Field(
        description="OpenGraph description for social sharing.",
    )


class ContentAuditCheck(BaseModel):
    """Result of an individual quality or SEO audit check."""

    check_name: str = Field(
        description="Name of the audit check.",
    )
    passed: bool = Field(
        description="Whether this check passed.",
    )
    details: str = Field(
        description="Details or score explanation.",
    )


class ContentQualityAuditResponse(BaseModel):
    """Quality and SEO compliance audit of generated content."""

    overall_score: int = Field(
        ge=0,
        le=100,
        description="Overall quality score from 0 to 100.",
    )
    status: str = Field(
        description="Audit status: 'passed', 'needs_revision', or 'failed'.",
    )
    keyword_coverage_score: int = Field(
        ge=0,
        le=100,
        description="Score reflecting how well primary & secondary keywords were integrated.",
    )
    heading_hierarchy_valid: bool = Field(
        description="True if H1/H2/H3 structure follows proper nesting without skipping levels.",
    )
    internal_links_count: int = Field(
        description="Count of internal links placed within the content.",
    )
    word_count: int = Field(
        description="Total word count of the drafted article.",
    )
    readability_rating: str = Field(
        description="Readability rating (e.g., 'clear_and_engaging', 'dense', 'basic').",
    )
    eeat_rating: str = Field(
        description="E-E-A-T rating (e.g., 'strong', 'moderate', 'weak').",
    )
    strengths: List[str] = Field(
        default_factory=list,
        description="Key strengths of the generated content.",
    )
    improvements: List[str] = Field(
        default_factory=list,
        description="Actionable recommendations for improvement.",
    )
    checks: List[ContentAuditCheck] = Field(
        default_factory=list,
        description="Detailed list of compliance checks.",
    )


# ============================================================
# SYSTEM INSTRUCTIONS
# ============================================================

PAGE_BRIEF_SYSTEM_PROMPT = """You are an elite SEO Content Strategist and Information Architect.
Your task is to produce a rigorous, publication-ready Content Brief and Outline for a single SEO page.

Key Guidelines:
1. Search Intent Alignment: Fully satisfy the search intent (informational, commercial, navigational, transactional).
2. Keyword Integration: Strategically assign the primary keyword and secondary keywords across logical H2/H3 sections.
3. Content Gap Superiority: Address competitor weaknesses and missing subtopics identified in the research report.
4. E-E-A-T Standards: Design sections that demonstrate First-Hand Experience, Expertise, Authoritativeness, and Trustworthiness.
5. Internal Linking Readiness: Identify natural anchor opportunities for required internal links.
6. Logical Hierarchy: Ensure exactly one main topic theme, structured with clean H2 sections and nested H3 sub-points.

Always return the response adhering strictly to the JSON schema.
"""

SECTION_DRAFTING_SYSTEM_PROMPT = """You are a world-class SEO content writer and subject matter expert.
Your goal is to write authoritative, comprehensive, engaging, and well-structured Markdown content for an SEO page.

Writing Standards:
1. High Information Density: Avoid fluff, generic filler, repetitive preamble, or AI clichés ("In today's fast-paced world", "delve into", "testament").
2. Natural Keyword Placement: Include assigned keywords naturally without keyword stuffing or awkward phrasing.
3. Formatting Excellence: Use bullet points, bold key terms, tables, and callout blocks where they enhance readability.
4. Actionable Value: Provide clear step-by-step guidance, comparisons, or practical takeaways.
5. Internal Link Integration: Seamlessly embed markdown links with descriptive anchor text to specified target URLs.
6. Clean Markdown: Return clean GitHub-flavored Markdown. Do NOT wrap markdown in unnecessary outer meta blocks.
"""

FAQ_GENERATION_SYSTEM_PROMPT = """You are a technical SEO specialist specializing in rich snippets, People Also Ask (PAA) optimization, and FAQ schema.
Your task is to generate concise, highly accurate, and helpful FAQ Q&A items that directly answer high-intent user questions.

Guidelines:
1. Direct Answers: Start each answer with a direct, definitive answer in the first sentence.
2. Value-Add: Follow with 2-3 sentences of context, actionable tips, or clarifying details.
3. Tone: Professional, authoritative, and helpful.
4. Target Queries: Prioritize questions from user search queries and competitor FAQ gaps.
"""

METADATA_GENERATION_SYSTEM_PROMPT = """You are an expert on-page technical SEO engineer.
Your task is to generate perfectly optimized metadata for search engines and social sharing.

Rules:
1. SEO Title: 50-60 characters. Must contain the primary keyword near the beginning. Compelling click-through appeal.
2. Meta Description: 130-155 characters. Includes primary keyword. Active voice, clear value proposition, and call to action.
3. Canonical URL: Exact URL path provided.
4. Schema Type: Select most accurate Schema.org type (Article, HowTo, FAQPage, CollectionPage).
"""

CONTENT_AUDIT_SYSTEM_PROMPT = """You are a strict SEO Quality Assurance Auditor.
Your task is to evaluate drafted content against search quality standards, keyword integration, and technical SEO hygiene.

Audit Criteria:
1. Intent fulfillment: Does this completely satisfy user search queries?
2. Keyword presence: Are primary & secondary keywords used naturally and adequately?
3. Heading depth & structure: Is there logical progression without skipped heading levels?
4. Internal linking: Are outbound internal links placed with appropriate anchor text?
5. Originality & E-E-A-T: Does this provide unique value beyond generic competitor summaries?

Provide an honest numerical score (0-100) and actionable feedback.
"""


# ============================================================
# PROMPT BUILDERS
# ============================================================

def build_page_brief_prompt(
    page_title: str,
    page_url: str,
    page_type: str,
    cluster_name: str,
    primary_keyword: Optional[str],
    secondary_keywords: List[str],
    search_intent: str,
    content_gaps: List[Dict[str, Any]],
    internal_links_outbound: List[Dict[str, Any]],
    target_audience: str,
    site_purpose: str,
) -> str:
    """Build user prompt for generating a page brief/outline."""
    gaps_formatted = "\n".join(
        f"- {g.get('topic', 'Gap')}: {g.get('reason', '')} (Missing format: {g.get('missing_format', 'N/A')})"
        for g in content_gaps[:4]
    ) if content_gaps else "None specified."

    links_formatted = "\n".join(
        f"- Link to '{link.get('target_url', '')}' (Recommended anchor: '{link.get('anchor_text', '')}', Relationship: '{link.get('relationship', '')}')"
        for link in internal_links_outbound[:8]
    ) if internal_links_outbound else "No specific outbound internal links required."

    secondary_kws_str = ", ".join(secondary_keywords) if secondary_keywords else "None"

    return f"""Create a comprehensive SEO Content Brief and Outline for the following page:

PAGE SPECIFICATIONS:
- Page Title: {page_title}
- URL: {page_url}
- Page Type: {page_type}
- Topical Cluster: {cluster_name}
- Search Intent: {search_intent}
- Target Audience: {target_audience}
- Site Purpose: {site_purpose}

TARGET KEYWORDS:
- Primary Keyword: {primary_keyword or 'Topical Overview'}
- Secondary Keywords: {secondary_kws_str}

RELEVANT CONTENT GAPS TO SOLVE:
{gaps_formatted}

PLANNED INTERNAL LINKS (MUST BE INCORPORATED):
{links_formatted}

Please provide a detailed ContentOutlineResponse JSON covering all sections, target keywords per section, and internal link placements.
"""


def build_drafting_prompt(
    page_title: str,
    h1_heading: str,
    page_url: str,
    page_type: str,
    cluster_name: str,
    primary_keyword: Optional[str],
    secondary_keywords: List[str],
    outline_data: Dict[str, Any],
    internal_links: List[Dict[str, Any]],
    site_name: str = "Our Platform",
) -> str:
    """Build user prompt for drafting complete article content in Markdown."""
    sections = outline_data.get("sections", [])
    sections_str = "\n".join(
        f"### {s.get('heading_level', 'H2')}: {s.get('heading_text', '')}\n"
        f"Target Keywords: {', '.join(s.get('target_keywords', []))}\n"
        f"Key Points: {', '.join(s.get('key_points', []))}\n"
        f"Target Words: {s.get('recommended_word_count', 250)}"
        for s in sections
    )

    links_guide = "\n".join(
        f"- Target URL: `{l.get('target_url')}`, Context Anchor: `{l.get('anchor_text')}` ({l.get('reason', '')})"
        for l in internal_links[:8]
    )

    return f"""Draft a comprehensive, high-ranking SEO article in Markdown based on the outline below.

PAGE CONTEXT:
- Title: {page_title}
- H1: {h1_heading}
- URL Path: {page_url}
- Primary Keyword: {primary_keyword or 'Topical Overview'}
- Secondary Keywords: {', '.join(secondary_keywords)}
- Cluster: {cluster_name}
- Site / Brand: {site_name}

PLANNED SECTIONS OUTLINE:
{sections_str}

INTERNAL LINKS TO EMBED NATURALLY:
{links_guide}

INSTRUCTIONS:
1. Begin directly with the H1 heading `# {h1_heading}`.
2. Follow with an engaging introduction paragraph answering search intent immediately.
3. Write thorough, detailed content for every section in the outline using appropriate H2 and H3 markdown headings.
4. Seamlessly embed the specified internal links using Markdown syntax `[Anchor Text](target_url)`.
5. Maintain an informative, authoritative tone with high signal-to-noise ratio.
6. Provide actionable insights, structured lists, and comparison points.
"""


def build_faq_prompt(
    page_title: str,
    primary_keyword: Optional[str],
    secondary_keywords: List[str],
    research_questions: List[str],
    cluster_name: str,
) -> str:
    """Build user prompt for FAQ Q&A generation."""
    questions_list = "\n".join(f"- {q}" for q in research_questions[:6]) if research_questions else "None provided."

    return f"""Generate 4 to 6 relevant FAQ Question & Answer pairs for this page:

Page Title: {page_title}
Primary Keyword: {primary_keyword or 'Topical Overview'}
Secondary Keywords: {', '.join(secondary_keywords[:6])}
Topical Cluster: {cluster_name}

Identified User Search Questions / Competitor FAQs:
{questions_list}

Return the results as a FAQSectionResponse JSON with clear, authoritative answers.
"""


def build_metadata_prompt(
    page_title: str,
    page_url: str,
    primary_keyword: Optional[str],
    secondary_keywords: List[str],
    cluster_name: str,
    target_audience: str,
) -> str:
    """Build user prompt for technical SEO metadata."""
    return f"""Generate optimal SEO and OpenGraph metadata for the following page:

Page Title: {page_title}
URL: {page_url}
Primary Keyword: {primary_keyword or 'Topical Overview'}
Secondary Keywords: {', '.join(secondary_keywords[:5])}
Cluster: {cluster_name}
Target Audience: {target_audience}

Return a PageMetadataResponse JSON with strict character constraints (Title: 50-60 chars, Description: 130-155 chars).
"""


def build_content_audit_prompt(
    page_title: str,
    primary_keyword: Optional[str],
    secondary_keywords: List[str],
    draft_content: str,
    planned_links: List[Dict[str, Any]],
) -> str:
    """Build user prompt for auditing drafted content against SEO quality criteria."""
    sample_content = draft_content[:4000] if len(draft_content) > 4000 else draft_content

    return f"""Perform an SEO Quality & Compliance Audit on the drafted article:

Page Title: {page_title}
Primary Keyword: {primary_keyword}
Secondary Keywords: {', '.join(secondary_keywords)}
Expected Internal Links: {len(planned_links)} planned

ARTICLE CONTENT (Excerpt/Full):
```markdown
{sample_content}
```

Audit the content thoroughly and return a ContentQualityAuditResponse JSON with overall score, checks, strengths, and recommendations.
"""
