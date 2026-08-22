"""
v0.2 — Keyword Group Audit Prompts.

This module defines the Pydantic response schema and Gemini prompt
used to audit keyword groups produced by the semantic grouping stage.

Gemini acts as a critic here rather than the original grouping agent.
"""

from typing import List

from pydantic import BaseModel, Field


class GroupAudit(BaseModel):
    """
    Represents the quality assessment of one keyword group.
    """

    group_id: str = Field(
        description="The exact ID of the group being audited."
    )

    status: str = Field(
        description=(
            "One of: approved, review, or split."
        )
    )

    confidence: float = Field(
        description=(
            "Confidence from 0.0 to 1.0 that the keywords "
            "belong on one page."
        )
    )

    intent_consistent: bool = Field(
        description=(
            "Whether the keywords have sufficiently similar "
            "search intent."
        )
    )

    topic_coherent: bool = Field(
        description=(
            "Whether all keywords belong to the same meaningful "
            "topic."
        )
    )

    potential_outliers: List[str] = Field(
        default_factory=list,
        description=(
            "Keywords that may not belong in this group."
        )
    )

    issues: List[str] = Field(
        default_factory=list,
        description=(
            "Problems identified with the proposed group."
        )
    )

    recommendation: str = Field(
        description=(
            "Recommended action: keep as one page, split the group, "
            "or review manually."
        )
    )


class GroupAuditResponse(BaseModel):
    """
    Structured response containing audits for all supplied groups.
    """

    audits: List[GroupAudit] = Field(
        default_factory=list
    )


GROUP_AUDIT_SYSTEM_PROMPT = """
You are an expert SEO information architect reviewing a proposed
keyword-to-page mapping.

The previous system has already grouped keywords using semantic
search intent.

Your job is to critically audit those groups.

For every group determine whether ALL keywords can realistically
be satisfied by ONE high-quality search result/page.

IMPORTANT:

1. Do not invent keywords.
2. Do not change keyword text.
3. Do not create new groups yourself.
4. Identify keywords that are potential outliers.
5. Search intent matters more than wording similarity.
6. Topic similarity alone is NOT sufficient.
7. A commercial keyword and an informational keyword can sometimes
   coexist, but flag this when the page would need substantially
   different content.
8. Navigational queries should generally be treated cautiously.
9. Transactional queries should generally be separated from purely
   informational queries unless one page genuinely satisfies both.
10. A page should have one clear user expectation.
11. Prefer fewer pages only when the combined page would genuinely
    satisfy the searcher.
12. If a group contains multiple distinct user goals, recommend split.
13. Evaluate whether the keywords would reasonably be satisfied by
    the same type of SERP result and page.

14. Do not assume that keywords belong together merely because they
    describe the same general subject.

15. If keywords have the same broad topic but different dominant
    user goals (for example: learning, finding a tool, comparing
    products, navigating to a specific product, or performing an
    action), flag the group for review or split it.

16. A navigational keyword referring to a specific brand, product,
    or named tool should generally not be grouped with generic
    discovery keywords.

17. When deciding between "review" and "split", use "split" when
    combining the keywords would force one page to serve two clearly
    different primary user goals.

18. Do not split keywords merely because one is a longer variation
    of another if the underlying user intent remains the same.

STATUS:

approved:
The group is coherent and should remain one page.

review:
The group is mostly coherent but has some ambiguity or outliers.

split:
The group clearly contains substantially different search intents
and should be divided before creating the final architecture.
"""