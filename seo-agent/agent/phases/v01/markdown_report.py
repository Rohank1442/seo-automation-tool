"""Render the human-readable Markdown research report."""

from pathlib import Path


def write_markdown_report(report_path: Path, extraction, saved_clusters, all_cluster_keywords, competitor_data, content_gaps) -> None:
    """Write the detailed report from normalized v0.1 stage results."""
    with open(
        report_path,
        "w",
        encoding="utf-8",
    ) as f:

        # --------------------------------------------------------
        # Project Context
        # --------------------------------------------------------

        f.write("# SEO Niche & Keyword Research Report\n\n")

        f.write("## Project Context\n")

        f.write(
            f"- **Core Topic**: "
            f"{extraction.core_topic}\n"
        )

        f.write(
            f"- **Target Audience**: "
            f"{extraction.target_audience}\n"
        )

        f.write(
            f"- **Site Goal**: "
            f"{extraction.site_goal}\n"
        )

        f.write(
            f"- **Geographic/Language Scope**: "
            f"{extraction.geo_scope}\n"
        )

        f.write(
            f"- **Constraints**: "
            f"{extraction.constraints}\n\n"
        )

        # --------------------------------------------------------
        # Overall summary
        # --------------------------------------------------------

        total_clusters = len(saved_clusters)

        total_keywords = sum(
            len(
                all_cluster_keywords.get(
                    c["name"],
                    [],
                )
            )
            for c in saved_clusters
        )

        total_competitors = sum(
            len(
                competitor_data.get(
                    c["name"],
                    [],
                )
            )
            for c in saved_clusters
        )

        total_gaps = sum(
            len(
                content_gaps.get(
                    c["name"],
                    [],
                )
            )
            for c in saved_clusters
        )

        total_high_priority_gaps = sum(
            sum(
                1
                for gap in content_gaps.get(
                    c["name"],
                    [],
                )
                if str(
                    gap.get("priority", "")
                ).lower()
                == "high"
            )
            for c in saved_clusters
        )

        f.write("## Research Summary\n")

        f.write(
            f"- **Clusters Analyzed**: "
            f"{total_clusters}\n"
        )

        f.write(
            f"- **Total Keywords**: "
            f"{total_keywords}\n"
        )

        f.write(
            f"- **Competitor Pages Crawled**: "
            f"{total_competitors}\n"
        )

        f.write(
            f"- **Content Gaps Identified**: "
            f"{total_gaps}\n"
        )

        f.write(
            f"- **High-Priority Gaps**: "
            f"{total_high_priority_gaps}\n\n"
        )

        # --------------------------------------------------------
        # Cluster details
        # --------------------------------------------------------

        f.write("## Topic Clusters\n\n")

        for c in saved_clusters:

            c_name = c["name"]

            f.write(
                f"### Cluster: {c_name}\n\n"
            )

            f.write(
                f"- **Description**: "
                f"{c['description']}\n"
            )

            kws = all_cluster_keywords.get(
                c_name,
                [],
            )

            f.write(
                f"- **Total Keywords**: "
                f"{len(kws)}\n"
            )

            questions = [
                k["keyword"]
                for k in kws
                if k.get("is_question")
            ]

            f.write(
                f"- **Question Keywords**: "
                f"{len(questions)}\n"
            )

            comps = competitor_data.get(
                c_name,
                [],
            )

            f.write(
                f"- **Competitors Crawled**: "
                f"{len(comps)}\n\n"
            )

            # ====================================================
            # KEYWORDS
            # ====================================================

            f.write("#### Keywords\n\n")

            if kws:

                f.write(
                    "| Keyword | Volume | Competition | "
                    "Level | CPC | Intent | Question |\n"
                )

                f.write(
                    "|---|---:|---:|---|---:|---|---|\n"
                )

                for kw in kws:

                    keyword = kw.get(
                        "keyword",
                        "",
                    )

                    volume = kw.get(
                        "volume"
                    )

                    competition = kw.get(
                        "competition"
                    )

                    competition_level = kw.get(
                        "competition_level"
                    )

                    cpc = kw.get(
                        "cpc"
                    )

                    intent = kw.get(
                        "intent",
                        "",
                    )

                    is_question = kw.get(
                        "is_question",
                        False,
                    )

                    f.write(
                        f"| {keyword} "
                        f"| {volume if volume is not None else '-'} "
                        f"| {competition if competition is not None else '-'} "
                        f"| {competition_level or '-'} "
                        f"| {cpc if cpc is not None else '-'} "
                        f"| {intent or '-'} "
                        f"| {'Yes' if is_question else 'No'} |\n"
                    )

            else:
                f.write(
                    "No keywords available.\n"
                )

            f.write("\n")

            # ====================================================
            # QUESTION KEYWORDS
            # ====================================================

            if questions:

                f.write(
                    "#### Question Keywords\n\n"
                )

                for question in questions:
                    f.write(
                        f"- {question}\n"
                    )

                f.write("\n")

            # ====================================================
            # COMPETITORS
            # ====================================================

            f.write(
                "#### Competitor Research\n\n"
            )

            if comps:

                for index, comp in enumerate(
                    comps,
                    start=1,
                ):

                    title = (
                        comp.get("title")
                        or comp.get("url")
                    )

                    f.write(
                        f"**{index}. "
                        f"[{title}]"
                        f"({comp.get('url')})**\n\n"
                    )

                    f.write(
                        f"- **Word Count**: "
                        f"{comp.get('word_count', 0)}\n"
                    )

                    h1s = comp.get(
                        "h1s",
                        [],
                    )

                    if h1s:

                        f.write(
                            "- **H1s**:\n"
                        )

                        for h1 in h1s:
                            f.write(
                                f"  - {h1}\n"
                            )

                    headings = comp.get(
                        "headings",
                        [],
                    )

                    if headings:

                        f.write(
                            "- **Content Structure**:\n"
                        )

                        # Keep report readable while preserving
                        # the useful competitor structure.
                        for heading in headings[:15]:

                            tag = heading.get(
                                "tag",
                                "",
                            )

                            text = heading.get(
                                "text",
                                "",
                            )

                            f.write(
                                f"  - "
                                f"**{tag.upper()}** "
                                f"{text}\n"
                            )

                    comp_qs = comp.get(
                        "questions",
                        [],
                    )

                    if comp_qs:

                        f.write(
                            "- **Competitor Questions**:\n"
                        )

                        for question in comp_qs:

                            f.write(
                                f"  - {question}\n"
                            )

                    f.write("\n")

            else:

                f.write(
                    "No competitor pages were crawled "
                    "for this cluster.\n\n"
                )

            # ====================================================
            # CONTENT GAPS
            # ====================================================

            f.write(
                "#### Identified Content Gaps\n\n"
            )

            gaps = content_gaps.get(
                c_name,
                [],
            )

            if gaps:

                for gap in gaps:

                    topic = gap.get(
                        "topic",
                        "Untitled",
                    )

                    priority = str(
                        gap.get(
                            "priority",
                            "medium",
                        )
                    ).upper()

                    scope = str(
                        gap.get(
                            "scope",
                            "page",
                        )
                    ).lower()

                    reason = gap.get(
                        "reason",
                        "",
                    )

                    missing_format = gap.get(
                        "missing_format",
                        "",
                    )

                    keyword_ideas = gap.get(
                        "keyword_ideas",
                        [],
                    )

                    f.write(
                        f"**{topic}**\n\n"
                    )

                    f.write(
                        f"- **Priority**: "
                        f"{priority}\n"
                    )

                    f.write(
                        f"- **Scope**: "
                        f"{scope}\n"
                    )

                    f.write(
                        f"- **Reason**: "
                        f"{reason}\n"
                    )

                    f.write(
                        f"- **Recommended Format**: "
                        f"{missing_format}\n"
                    )

                    if keyword_ideas:

                        f.write(
                            "- **Target Keywords**:\n"
                        )

                        for keyword in keyword_ideas:

                            f.write(
                                f"  - {keyword}\n"
                            )

                    f.write("\n")

            else:

                f.write(
                    "No significant content gaps identified.\n\n"
                )

            f.write(
                "\n"
                + "─" * 60
                + "\n\n"
            )
