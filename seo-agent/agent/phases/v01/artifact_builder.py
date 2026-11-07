"""Transform research stage results into the v0.1 page-opportunity contract."""

from typing import Any, Dict


def build_page_opportunities(project_id, extraction, target_domain, saved_clusters, all_cluster_keywords, competitor_data, content_gaps) -> Dict[str, Any]:
    """Normalize raw research into the JSON contract consumed by v0.2 and v0.3."""
    # ------------------------------------------------------------
    # Build machine-readable page opportunities
    # ------------------------------------------------------------

    page_opportunities = {
        "project_id": project_id,
        "project": {
            "core_topic": extraction.core_topic,
            "target_audience": extraction.target_audience,
            "site_goal": extraction.site_goal,
            "geo_scope": extraction.geo_scope,
            "constraints": extraction.constraints,
            "target_domain": target_domain or "https://example.com",
        },
        "clusters": [],
    }


    for cluster in saved_clusters:
        c_name = cluster["name"]

        kws = all_cluster_keywords.get(c_name, [])
        comps = competitor_data.get(c_name, [])
        gaps = content_gaps.get(c_name, [])

        # --------------------------------------------------------
        # Keyword data
        # --------------------------------------------------------

        keyword_data = []

        for kw in kws:
            keyword_data.append(
                {
                    "keyword": kw.get("keyword"),
                    "volume": kw.get("volume"),
                    "competition": kw.get("competition"),
                    "competition_level": kw.get("competition_level"),
                    "cpc": kw.get("cpc"),
                    "intent": kw.get("intent"),
                    "is_question": kw.get("is_question"),
                }
            )

        # --------------------------------------------------------
        # Competitor data
        # --------------------------------------------------------

        competitor_data_for_cluster = []

        for comp in comps:
            competitor_data_for_cluster.append(
                {
                    "url": comp.get("url"),
                    "title": comp.get("title"),
                    "h1s": comp.get("h1s", []),
                    "headings": comp.get("headings", []),
                    "questions": comp.get("questions", []),
                    "word_count": comp.get("word_count", 0),
                    "error": comp.get("error"),
                }
            )

        # --------------------------------------------------------
        # Content gaps / page opportunities
        # --------------------------------------------------------

        page_gap_data = []

        for gap in gaps:
            keyword_ideas = gap.get("keyword_ideas", [])

            # Normalize priority
            priority = str(
                gap.get("priority", "medium")
            ).lower()

            # If your ContentGapAnalysis schema later contains
            # "scope", this will use it.
            # Otherwise default to page.
            scope = str(
                gap.get("scope", "page")
            ).lower()

            page_gap_data.append(
                {
                    "topic": gap.get("topic"),
                    "priority": priority,
                    "scope": scope,
                    "reason": gap.get("reason"),
                    "missing_format": gap.get("missing_format"),
                    "keyword_ideas": keyword_ideas,
                }
            )

        # --------------------------------------------------------
        # Cluster-level page planning object
        # --------------------------------------------------------

        cluster_output = {
            "name": c_name,
            "description": cluster.get("description"),
            "keywords": keyword_data,
            "competitors": competitor_data_for_cluster,
            "content_gaps": page_gap_data,
            "summary": {
                "total_keywords": len(kws),
                "question_keywords": sum(
                    1
                    for kw in kws
                    if kw.get("is_question")
                ),
                "competitors_crawled": len(comps),
                "content_gaps": len(gaps),
                "high_priority_gaps": sum(
                    1
                    for gap in gaps
                    if str(
                        gap.get("priority", "")
                    ).lower()
                    == "high"
                ),
                "page_level_opportunities": sum(
                    1
                    for gap in gaps
                    if str(
                        gap.get("scope", "page")
                    ).lower()
                    == "page"
                ),
                "section_level_opportunities": sum(
                    1
                    for gap in gaps
                    if str(
                        gap.get("scope", "page")
                    ).lower()
                    == "section"
                ),
            },
        }

        page_opportunities["clusters"].append(
            cluster_output
        )
    return page_opportunities
