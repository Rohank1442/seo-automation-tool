"""
v0.2 LLM prompts and response schemas.

This module contains the Gemini prompt and Pydantic models used
for semantic keyword-to-page grouping.

The LLM is responsible for semantic reasoning.

Python validation is responsible for enforcing that the model
only uses keywords that actually exist in the v0.1 research.
"""

from typing import List

from pydantic import BaseModel, Field


# ============================================================
# RESPONSE SCHEMAS
# ============================================================


class FinalKeywordGroup(BaseModel):
    """
    Represents one final page group produced when a proposed
    semantic group needs to be split.
    """

    group_id: str = Field(
        description="Unique ID for the final page group."
    )

    primary_keyword: str = Field(
        description="Primary keyword targeted by this page."
    )

    secondary_keywords: List[str] = Field(
        default_factory=list,
        description="Closely related keywords targeted by the page."
    )

    page_type: str = Field(
        description="Recommended page type."
    )

    reasoning: str = Field(
        description="Why these keywords belong on one page."
    )

class KeywordPageGroup(BaseModel):
    """
    Represents one group of keywords that can realistically be
    targeted by a single SEO page.
    """

    group_id: str = Field(
        description=(
            "Short stable identifier for the keyword group. "
            "Use lowercase words separated by hyphens."
        )
    )

    primary_keyword: str = Field(
        description=(
            "The single best primary keyword for the page. "
            "It MUST be one of the supplied keywords."
        )
    )

    secondary_keywords: List[str] = Field(
        default_factory=list,
        description=(
            "Other supplied keywords that share the same search "
            "intent and can naturally be addressed by the same page."
        )
    )

    page_type: str = Field(
        description=(
            "Recommended page type, such as category, guide, "
            "comparison, listicle, or FAQ."
        )
    )

    reasoning: str = Field(
        description=(
            "Short explanation of why these keywords can be "
            "satisfied by the same page."
        )
    )


class KeywordGroupingResponse(BaseModel):
    """
    Structured Gemini response containing all keyword groups
    for a single topic cluster.
    """

    groups: List[KeywordPageGroup] = Field(
        description=(
            "Keyword groups. Every supplied keyword should appear "
            "in exactly one group."
        )
    )


# ============================================================
# SYSTEM PROMPT
# ============================================================


KEYWORD_GROUPING_SYSTEM_PROMPT = """
You are an expert SEO information architect.

Your task is to group search keywords into SEO page-level
search-intent groups.

The most important rule is:

MULTIPLE KEYWORDS SHOULD SHARE ONE PAGE WHEN A SINGLE,
COMPREHENSIVE PAGE COULD SATISFY THE SAME SEARCH INTENT.

Do NOT create separate pages merely because keywords use
different wording.

For example:

"festival outfits"
"festival outfit ideas"
"music festival outfits"

may belong to one page if the underlying search intent is the same.

However, keywords should be separated when the user expectation
or required content is substantially different.

For example:

"festival outfits"
"how to clean festival boots"

should NOT be grouped together.

IMPORTANT RULES:

1. You may ONLY use keywords supplied in the input.
2. Never invent a keyword.
3. Every supplied keyword must appear in exactly one group.
4. A keyword cannot appear in multiple groups.
5. Each group must have exactly one primary keyword.
6. The primary keyword must be one of the supplied keywords.
7. Secondary keywords must also come from the supplied list.
8. Prefer fewer high-quality pages over many thin pages.
9. Do not combine keywords with substantially different search intent.
10. Consider the existing intent classification.
11. Consider whether the keyword is a question.
12. Consider the likely content required to satisfy the query.
13. Consider keyword volume and competition when selecting the
    primary keyword, but search intent takes priority over volume.
14. Do not use keyword volume alone as justification for creating
    a separate page.
15. Keep the grouping within the supplied topic cluster.

The objective is to minimize keyword cannibalization while
creating pages that have strong, coherent search intent.
"""