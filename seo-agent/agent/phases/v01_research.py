import json
import os
import sys
import re
from typing import List, Dict, Any
from pydantic import BaseModel

from core.config import validate_config, GEMINI_API_KEY
from core.llm import generate_json
from core.db import (
    create_project,
    update_project,
    create_clusters,
    save_keywords,
)
from core.scraper import (
    get_google_autocomplete,
    get_competitor_urls,
    crawl_competitor_page,
    get_dataforseo_metrics,
    get_people_also_ask,
    get_ddg_related_searches,
)
from prompts.v01_prompts import (
    ProjectExtraction,
    FollowUpQuestions,
    TopicClustersResponse,
    BatchKeywordClassification,
    ContentGapAnalysisResponse,
    ClusterSeedsResponse,
    EXTRACTION_SYSTEM_PROMPT,
    FOLLOWUP_SYSTEM_PROMPT,
    CLUSTER_GENERATION_SYSTEM_PROMPT,
    CLUSTER_SEEDS_SYSTEM_PROMPT,
    INTENT_CLASSIFICATION_SYSTEM_PROMPT,
    GAP_ANALYSIS_SYSTEM_PROMPT,
)


def print_separator(char="─", length=50):
    print(char * length)


def run_research_phase():
    print_separator("═")
    print("      SEO AUTOMATION AGENT - PHASE v0.1 RESEACH      ")
    print_separator("═")

    # 0. Validate Configuration
    validate_config()

    # ============================================================
    # --- STEPS 1 & 2 & 3: IDEA DESCRIPTION, EXTRACTION & CLARIFICATION ---
    # ============================================================
    print("\n[Step 1] Describe your website idea.")
    print(
        "Example: 'A blog about indoor tomato gardening for apartment dwellers in New York, monetized with affiliate links.'"
    )
    raw_desc = input("\nEnter your idea: ").strip()
    while not raw_desc:
        raw_desc = input("Idea cannot be empty. Enter your idea: ").strip()

    print("\nSaving project drafts to Supabase...")
    project = create_project(raw_desc)
    project_id = project["id"]
    print(f"Project created with ID: {project_id}")

    # Extraction loop
    confirmed = False
    context_desc = raw_desc
    extraction = None

    for round_num in range(1, 4):
        print(f"\n[Step 2] Extracting project parameters (Round {round_num})...")
        prompt = (
            f"Extract parameters from the following project idea:\n\n{context_desc}"
        )

        try:
            extraction = generate_json(
                prompt=prompt,
                response_schema=ProjectExtraction,
                system_instruction=EXTRACTION_SYSTEM_PROMPT,
            )
        except Exception as e:
            print(f"Error during LLM extraction: {e}")
            break

        print("\nExtracted Parameters:")
        print(f"  • Core Topic:      {extraction.core_topic}")
        print(f"  • Target Audience: {extraction.target_audience}")
        print(f"  • Site Goal:       {extraction.site_goal}")
        print(f"  • Geo/Language:    {extraction.geo_scope}")
        print(f"  • Constraints:     {extraction.constraints}")

        if not extraction.is_vague:
            print("\nParameters are clear and well-defined!")
            break

        print(f"\n[Vague Idea Flagged] Reason: {extraction.vagueness_reason}")
        print("Let's clarify a few details.")

        # Ask follow-up questions
        followup_prompt = (
            f"Generate 2-3 short, precise clarification questions based on this extraction:\n"
            f"{extraction.model_dump_json()}"
        )
        try:
            questions_obj = generate_json(
                prompt=followup_prompt,
                response_schema=FollowUpQuestions,
                system_instruction=FOLLOWUP_SYSTEM_PROMPT,
            )
        except Exception as e:
            print(f"Error generating follow-ups: {e}")
            break

        answers = []
        for q in questions_obj.questions:
            print(f"\nQuestion: {q}")
            ans = input("Your answer: ").strip()
            answers.append(f"Q: {q}\nA: {ans}")

        # Append answers to context for next extraction pass
        context_desc += "\n\n" + "\n".join(answers)

    # Final confirmation
    print_separator()
    print("\n[Step 3] Final Project Confirmation")
    print(f"Core Topic:      {extraction.core_topic if extraction else 'N/A'}")
    print(f"Target Audience: {extraction.target_audience if extraction else 'N/A'}")
    print(f"Site Goal:       {extraction.site_goal if extraction else 'N/A'}")
    print(f"Geo Scope:       {extraction.geo_scope if extraction else 'N/A'}")
    print(f"Constraints:     {extraction.constraints if extraction else 'N/A'}")

    confirm = input("\nDoes this look correct? (y/n/edit): ").strip().lower()
    if confirm == "edit":
        extraction.core_topic = (
            input(f"Core Topic [{extraction.core_topic}]: ").strip()
            or extraction.core_topic
        )
        extraction.target_audience = (
            input(f"Target Audience [{extraction.target_audience}]: ").strip()
            or extraction.target_audience
        )
        extraction.site_goal = (
            input(f"Site Goal [{extraction.site_goal}]: ").strip()
            or extraction.site_goal
        )
        extraction.geo_scope = (
            input(f"Geo Scope [{extraction.geo_scope}]: ").strip()
            or extraction.geo_scope
        )
        extraction.constraints = (
            input(f"Constraints [{extraction.constraints}]: ").strip()
            or extraction.constraints
        )

    # Save confirmed project details
    update_project(
        project_id,
        {
            "core_topic": extraction.core_topic,
            "target_audience": extraction.target_audience,
            "site_goal": extraction.site_goal,
            "geo_scope": extraction.geo_scope,
            "constraints": extraction.constraints,
            "confirmed": True,
        },
    )
    print("\nProject details updated and saved in Supabase!")

    # ============================================================
    # --- STEPS 4 & 5: CLUSTER GENERATION & APPROVAL ---
    # ============================================================
    print("\n[Step 4] Finding top-level topic clusters...")
    cluster_prompt = (
        f"Generate topic clusters for:\n"
        f"Topic: {extraction.core_topic}\n"
        f"Audience: {extraction.target_audience}\n"
        f"Goal: {extraction.site_goal}\n"
        f"Constraints: {extraction.constraints}"
    )

    try:
        clusters_resp = generate_json(
            prompt=cluster_prompt,
            response_schema=TopicClustersResponse,
            system_instruction=CLUSTER_GENERATION_SYSTEM_PROMPT,
        )
    except Exception as e:
        print(f"Failed to generate clusters: {e}")
        sys.exit(1)

    print(
        f"Generated {len(clusters_resp.clusters)} clusters. Validating via Google Autocomplete..."
    )

    validated_clusters = []

    # autocomplete working and returning suggestions correctly
    for c in clusters_resp.clusters:
        suggestions = get_google_autocomplete(c.name)
        print(f"Cluster '{c.name}' suggestions: {suggestions}")
        # Append some popular autocomplete keywords to description to show real user search interest
        desc = c.description
        if suggestions:
            sample_terms = ", ".join(suggestions[:3])
            desc += f" (Popular searches: {sample_terms})"
        validated_clusters.append({"name": c.name, "description": desc})

    print_separator()
    print("\n[Step 5] Approve and Refine Topic Clusters")
    print("Review the clusters below. You can keep, remove, or rename each one.")
    print_separator()

    approved_clusters = []
    for i, c in enumerate(validated_clusters):
        print(f"\nCluster #{i+1}: {c['name']}")
        print(f"Description: {c['description']}")

        action = input("Keep (y) / Remove (n) / Rename (type new name) [y]: ").strip()
        if action.lower() == "n":
            print("Removed.")
            continue
        elif action and action.lower() != "y":
            print(f"Renamed to: {action}")
            approved_clusters.append({"name": action, "description": c["description"]})
        else:
            approved_clusters.append(c)

    while True:
        add_more = (
            input("\nWould you like to add a custom topic cluster? (y/n) [n]: ")
            .strip()
            .lower()
        )
        if add_more != "y":
            break
        custom_name = input("Enter cluster name: ").strip()
        custom_desc = input("Enter cluster description: ").strip()
        if custom_name:
            approved_clusters.append({"name": custom_name, "description": custom_desc})

    if not approved_clusters:
        print("Error: You must have at least one approved cluster to proceed.")
        sys.exit(1)

    print("\nSaving clusters to Supabase...")
    saved_clusters = create_clusters(project_id, approved_clusters)
    print(f"Saved {len(saved_clusters)} clusters successfully!")

    # --- STEP 6: DEEP KEYWORD RESEARCH PER CLUSTER ---
    print_separator()
    print("\n[Step 6] Running Deep Keyword Research Per Cluster")
    print(
        "This will fetch keyword ideas, volume & difficulty metrics, and classify search intent."
    )
    print_separator()

    all_cluster_keywords: Dict[str, List[Dict[str, Any]]] = {}

    for cluster in saved_clusters:
        c_id = cluster["id"]
        c_name = cluster["name"]
        c_desc = cluster.get("description", "")
        print(f"\nProcessing Cluster: '{c_name}'...")

        # 6a. Generating search-friendly seeds for the cluster
        print("  • Generating search-friendly seeds using Gemini...")

        seed_prompt = (
            f"Topic Cluster: {c_name}\n"
            f"Description: {c_desc}\n"
            f"Niche/Project context: {extraction.core_topic}"
        )
        try:
            seeds_resp = generate_json(
                prompt=seed_prompt,
                response_schema=ClusterSeedsResponse,
                system_instruction=CLUSTER_SEEDS_SYSTEM_PROMPT
            )
            seeds = seeds_resp.seeds
            print(f"    - Generated seeds: {seeds}")
        except Exception as e:
            print(f"    - Failed to generate seeds: {e}. Using cluster name as seed.")
            seeds = [c_name]

        # 6b. Harvesting keyword ideas (Autocomplete + PAA)
        unique_kws = set()
        print("  • Harvesting keyword ideas (Autocomplete + People Also Ask)...")
        
        for seed in seeds:
            # 1. Autocomplete (First-level)
            suggestions = get_google_autocomplete(seed)
            print(f"    - Autocomplete suggestions for '{seed}': {len(suggestions)}")
            for s in suggestions:
                clean_s = s.strip().lower()
                if clean_s:
                    unique_kws.add(clean_s)
            
            # 2. People Also Ask (PAA)
            paa_questions = get_people_also_ask(seed)

            if not paa_questions:
                print(f"    - SerpApi not configured. Running Autocomplete Q&A Harvester for '{seed}'...")
                
                # 1. Clean the seed by stripping common leading question words
                clean_seed = seed.strip().lower()
                clean_seed = re.sub(r'^(how to|why|what is|can you|where to|what|how|where)\s+', '', clean_seed)
                
                # Optional: Clean up leading prepositions left behind (e.g., "for my body shape")
                base_target = re.sub(r'^(for|to|on|in|with)\s+', '', clean_seed)

                # 2. Build natural query templates using wildcards (_) and clean variations
                q_queries = [
                    f"how to {base_target}",
                    f"why {base_target}",
                    f"what is {base_target}",
                    f"can you {base_target}",
                    f"where to {base_target}",
                    f"best {base_target} for",      # Great for buyer-intent keywords
                    f"{base_target} vs",             # Great for comparison keywords
                    f"{base_target} _"               # Wildcard triggers mid-tail suggestions
                ]

                for q_query in q_queries:
                    q_suggestions = get_google_autocomplete(q_query)
                    # print(f"    - Autocomplete suggestions for query '{q_query}': {q_suggestions}")
                    for qs in q_suggestions:
                        clean_qs = qs.strip().lower()
                        if clean_qs:
                            unique_kws.add(clean_qs)
            else:
                print(f"    - Fetched SerpApi PAA questions for '{seed}': {len(paa_questions)}")
                for q in paa_questions:
                    clean_q = q.strip().lower()
                    if clean_q:
                        unique_kws.add(clean_q)
                        
            # 3. DuckDuckGo Related Searches (Option 2)
            ddg_suggestions = get_ddg_related_searches(seed)
            print(f"    - DuckDuckGo suggestions for '{seed}': {ddg_suggestions}")
            for ds in ddg_suggestions:
                clean_ds = ds.strip().lower()
                if clean_ds:
                    unique_kws.add(clean_ds)

            # 4. Competitor Crawl Question Extraction (Step 7)
            #     We crawl the top 5 competitor URLs. While parsing their HTML, we extract any H2 or H3 headings that end with a ? (question mark).
            #     Result: The exact FAQ topics and questions your top ranking competitors are answering in their articles.

        # Add the seeds and cluster name themselves
        for seed in seeds:
            unique_kws.add(seed.lower())
        unique_kws.add(c_name.lower())

        kw_list = list(unique_kws)
        # for kw in kw_list:
            # print("----------------- all keywords:", kw)

        print(f"  • Found {len(kw_list)} unique candidate keywords/questions.")

        # 6b. Keyword Metrics
        print("  • Fetching metrics (DataForSEO)...")

        df_metrics = get_dataforseo_metrics(kw_list)

        print(f"  • Metrics fetched for {len(df_metrics)} keywords.")

        keywords_data = []

        for kw in kw_list:
            metrics = df_metrics.get(kw, {})

            keywords_data.append(
                {
                    "keyword": kw,
                    "volume": metrics.get("volume"),
                    "competition": metrics.get("competition"),
                    "competition_level": metrics.get("competition_level"),
                    "cpc": metrics.get("cpc"),
                    "intent": "informational",
                    "is_question": False,
                }
            )

        # 6c. Intent & Question Classification
        print("  • Classifying intent and question keywords using Gemini...")
        classified_keywords = []
        batch_size = 50

        for i in range(0, len(keywords_data), batch_size):
            batch = keywords_data[i : i + batch_size]
            batch_kws = [k["keyword"] for k in batch]

            intent_prompt = (
                f"Classify the following list of keywords:\n{json.dumps(batch_kws)}"
            )
            try:
                classified_res = generate_json(
                    prompt=intent_prompt,
                    response_schema=BatchKeywordClassification,
                    system_instruction=INTENT_CLASSIFICATION_SYSTEM_PROMPT,
                )

                # Create a map for fast lookup
                class_map = {item.keyword: item for item in classified_res.keywords}

                for item in batch:
                    kw_text = item["keyword"]
                    if kw_text in class_map:
                        item["intent"] = class_map[kw_text].intent
                        item["is_question"] = class_map[kw_text].is_question

                    classified_keywords.append(item)
            except Exception as e:
                print(
                    f"    - Error classifying batch starting at {i}: {e}. Keeping defaults."
                )
                classified_keywords.extend(batch)

        # Save keywords to database
        print(f"  • Saving {len(classified_keywords)} keywords to Supabase...")
        save_keywords(c_id, classified_keywords)
        all_cluster_keywords[c_name] = classified_keywords

    # ============================================================
    # --- STEP 7: CRAWL TOP COMPETITORS PER CLUSTER ---
    # ============================================================
    print_separator()
    print("\n[Step 7] Crawling Competitors Per Cluster")
    print("Identifying top 5 ranking pages and crawling outline structures...")
    print_separator()

    competitor_data: Dict[str, List[Dict[str, Any]]] = {}

    for cluster in saved_clusters:
        c_name = cluster["name"]
        print(f"\nFinding competitors for cluster: '{c_name}'...")
        urls = get_competitor_urls(c_name, max_results=5)
        print(f"  • Top competitor URLs found: {len(urls)}")

        crawled_pages = []
        for url in urls:
            print(f"  • Crawling {url} ...")
            page_data = crawl_competitor_page(url)
            crawled_pages.append(page_data)

        competitor_data[c_name] = crawled_pages

    # --- STEP 8: CONTENT GAP ANALYSIS ---
    print_separator()
    print("\n[Step 8] Identifying Content Gaps")
    print("LLM reasoning identifies topic and format opportunities...")
    print_separator()

    content_gaps: Dict[str, List[Dict[str, Any]]] = {}

    for cluster in saved_clusters:
        c_name = cluster["name"]
        print(f"\nAnalyzing gaps for cluster: '{c_name}'...")

        # Prepare competitor context payload
        comp_context = []
        for p in competitor_data.get(c_name, []):
            if p.get("error"):
                continue
            comp_context.append(
                {
                    "url": p["url"],
                    "title": p["title"],
                    "h1s": p["h1s"],
                    "headings": p["headings"][:15],  # limit headings size to prevent prompt bloating
                    "questions": p.get("questions", []), # Option 3: competitor FAQ questions ending in ?
                    "word_count": p["word_count"],
                }
            )

        # Get keyword sample (top 20 for brief analysis context)
        kw_sample = [
            {
                "keyword": kw["keyword"],
                "volume": kw.get("volume"),
                "competition": kw.get("competition"),
                "competition_level": kw.get("competition_level"),
                "intent": kw["intent"],
                "is_question": kw["is_question"],
            }
            for kw in all_cluster_keywords.get(c_name, [])[:40]
        ]

        gap_prompt = (
            f"Perform content gap analysis for Cluster '{c_name}' under the project context:\n"
            f"Topic: {extraction.core_topic}\n"
            f"Audience: {extraction.target_audience}\n\n"
            f"Target Keywords:\n{json.dumps(kw_sample, indent=2)}\n\n"
            f"Competitor Content Structure:\n{json.dumps(comp_context, indent=2)}"
        )

        try:
            gap_res = generate_json(
                prompt=gap_prompt,
                response_schema=ContentGapAnalysisResponse,
                system_instruction=GAP_ANALYSIS_SYSTEM_PROMPT,
            )
            content_gaps[c_name] = [gap.model_dump() for gap in gap_res.gaps]
            print(f"  • Found {len(content_gaps[c_name])} high-value gaps!")
        except Exception as e:
            print(f"  • Error during gap analysis: {e}")
            content_gaps[c_name] = []

    # ============================================================
    # STEP 9: SAVE LOCAL REPORT + PAGE OPPORTUNITIES
    # ============================================================

    print_separator()
    print("\n[Step 9] Saving SEO research and page-planning reports...")
    print_separator()

    os.makedirs("outputs", exist_ok=True)

    report_path = os.path.join("outputs", "research_report.md")
    page_opportunities_path = os.path.join(
        "outputs",
        "page_opportunities.json",
    )

    # ------------------------------------------------------------
    # Build machine-readable page opportunities
    # ------------------------------------------------------------

    page_opportunities = {
        "project": {
            "core_topic": extraction.core_topic,
            "target_audience": extraction.target_audience,
            "site_goal": extraction.site_goal,
            "geo_scope": extraction.geo_scope,
            "constraints": extraction.constraints,
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


    # ------------------------------------------------------------
    # Save machine-readable JSON
    # ------------------------------------------------------------

    with open(
        page_opportunities_path,
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            page_opportunities,
            f,
            indent=2,
            ensure_ascii=False,
        )

    print(
        f"Page-planning data saved to: "
        f"{page_opportunities_path}"
    )


    # ============================================================
    # HUMAN-READABLE MARKDOWN REPORT
    # ============================================================

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


    print(
        f"Human-readable report saved to: "
        f"{report_path}"
    )

    print(
        f"Machine-readable page opportunities saved to: "
        f"{page_opportunities_path}"
    )


    # ============================================================
    # STEP 10: CLI SUMMARY
    # ============================================================

    print_separator("═")
    print("                  RESEARCH COMPLETE                  ")
    print_separator("═")


    # ------------------------------------------------------------
    # Overall metrics
    # ------------------------------------------------------------

    total_clusters = len(
        saved_clusters
    )

    total_kws = sum(
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


    print(
        f"Clusters analyzed:        {total_clusters}"
    )

    print(
        f"Total keywords:           {total_kws}"
    )

    print(
        f"Competitors crawled:      {total_competitors}"
    )

    print(
        f"Content gaps identified:  {total_gaps}"
    )

    print(
        f"High-priority gaps:       {total_high_priority_gaps}"
    )


    # ------------------------------------------------------------
    # Top page opportunities
    # ------------------------------------------------------------

    page_opportunity_list = []

    for c_name, gaps in content_gaps.items():

        for gap in gaps:

            priority = str(
                gap.get(
                    "priority",
                    "medium",
                )
            ).lower()

            scope = str(
                gap.get(
                    "scope",
                    "page",
                )
            ).lower()

            # Only treat explicit page-level gaps as page
            # opportunities.
            if scope != "page":
                continue

            if priority == "high":

                page_opportunity_list.append(
                    {
                        "cluster": c_name,
                        "topic": gap.get(
                            "topic",
                            "Untitled",
                        ),
                        "format": gap.get(
                            "missing_format",
                            "Unknown",
                        ),
                        "keywords": gap.get(
                            "keyword_ideas",
                            [],
                        ),
                        "reason": gap.get(
                            "reason",
                            "",
                        ),
                    }
                )


    print(
        "\nTop High-Priority Page Opportunities:"
    )

    if page_opportunity_list:

        for idx, opportunity in enumerate(
            page_opportunity_list[:10],
            start=1,
        ):

            print(
                f"  {idx}. "
                f"[{opportunity['cluster']}] "
                f"{opportunity['topic']} "
                f"({opportunity['format']})"
            )

    else:

        print(
            "  None identified."
        )


    # ------------------------------------------------------------
    # Recommended starting cluster
    # ------------------------------------------------------------

    cluster_page_counts = {
        c["name"]: 0
        for c in saved_clusters
    }

    cluster_high_priority_counts = {
        c["name"]: 0
        for c in saved_clusters
    }


    for c_name, gaps in content_gaps.items():

        for gap in gaps:

            priority = str(
                gap.get(
                    "priority",
                    "medium",
                )
            ).lower()

            scope = str(
                gap.get(
                    "scope",
                    "page",
                )
            ).lower()

            if scope == "page":

                cluster_page_counts[c_name] = (
                    cluster_page_counts.get(
                        c_name,
                        0,
                    )
                    + 1
                )

                if priority == "high":

                    cluster_high_priority_counts[c_name] = (
                        cluster_high_priority_counts.get(
                            c_name,
                            0,
                        )
                        + 1
                    )


    # Only recommend a cluster that actually has page
    # opportunities.
    eligible_clusters = {
        name: count
        for name, count in cluster_page_counts.items()
        if count > 0
    }


    if eligible_clusters:

        # Prefer high-priority opportunities first.
        recommended_cluster = max(
            eligible_clusters,
            key=lambda name: (
                cluster_high_priority_counts.get(
                    name,
                    0,
                ),
                cluster_page_counts.get(
                    name,
                    0,
                ),
            ),
        )

        high_priority_count = (
            cluster_high_priority_counts.get(
                recommended_cluster,
                0,
            )
        )

        page_count = (
            cluster_page_counts.get(
                recommended_cluster,
                0,
            )
        )

        print(
            f"\nRecommended starting cluster: "
            f"{recommended_cluster}"
        )

        print(
            "Reason: "
            f"{high_priority_count} high-priority "
            f"page opportunity/opportunities and "
            f"{page_count} total page opportunity/"
            f"opportunities were identified."
        )

    else:

        print(
            "\nRecommended starting cluster: "
            "None"
        )

        print(
            "Reason: No page-level content opportunities "
            "were identified."
        )


    # ------------------------------------------------------------
    # Output files
    # ------------------------------------------------------------

    print(
        "\nOutput files:"
    )

    print(
        f"  • Human report: "
        f"{report_path}"
    )

    print(
        f"  • Page planning data: "
        f"{page_opportunities_path}"
    )

    print_separator("═")