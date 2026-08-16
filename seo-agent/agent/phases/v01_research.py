import json
import os
import sys
from typing import List, Dict, Any, Tuple
from pydantic import BaseModel

from core.config import validate_config, GEMINI_API_KEY
from core.llm import generate_json, generate_text
from core.db import (
    create_project,
    update_project,
    create_clusters,
    delete_clusters_for_project,
    save_keywords,
)
from core.scraper import (
    get_google_autocomplete,
    get_competitor_urls,
    crawl_competitor_page,
    get_dataforseo_metrics,
    get_people_also_ask,
)
from prompts.v01_prompts import (
    ProjectExtraction,
    FollowUpQuestions,
    TopicClustersResponse,
    BatchKeywordClassification,
    ContentGapAnalysisResponse,
    ClusterSeedsResponse,
    PaaQuestionsResponse,
    EXTRACTION_SYSTEM_PROMPT,
    FOLLOWUP_SYSTEM_PROMPT,
    CLUSTER_GENERATION_SYSTEM_PROMPT,
    CLUSTER_SEEDS_SYSTEM_PROMPT,
    PAA_SIMULATION_SYSTEM_PROMPT,
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

    # --- STEPS 1 & 2 & 3: IDEA DESCRIPTION, EXTRACTION & CLARIFICATION ---
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

    # --- STEPS 4 & 5: CLUSTER GENERATION & APPROVAL ---
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
                # Fallback to simulated PAA using Gemini
                try:
                    paa_prompt = f"Generate simulated PAA questions for the query: '{seed}'"
                    paa_resp = generate_json(
                        prompt=paa_prompt,
                        response_schema=PaaQuestionsResponse,
                        system_instruction=PAA_SIMULATION_SYSTEM_PROMPT
                    )
                    paa_questions = paa_resp.questions
                    print(f"    - Simulated PAA questions for '{seed}': {len(paa_questions)}")
                except Exception as e:
                    print(f"    - Failed to simulate PAA: {e}")
                    paa_questions = []
            else:
                print(f"    - Fetched SerpApi PAA questions for '{seed}': {len(paa_questions)}")
                
            for q in paa_questions:
                clean_q = q.strip()
                if clean_q:
                    unique_kws.add(clean_q.lower())
                    
        # Add the seeds and cluster name themselves
        for seed in seeds:
            unique_kws.add(seed.lower())
        unique_kws.add(c_name.lower())

        kw_list = list(unique_kws)
        print(f"  • Found {len(kw_list)} unique candidate keywords/questions.")

        # debug untill here first

        # 6b. Volume & Difficulty Metrics
        print("  • Fetching metrics (DataForSEO)...")
        # Query DataForSEO
        df_metrics = get_dataforseo_metrics(kw_list)
        print(f"  • Metrics fetched for {len(df_metrics)} keywords.")

        # Process and build initial keyword list
        keywords_data = []
        for kw in kw_list:
            vol = None
            diff = None
            if kw in df_metrics:
                vol = df_metrics[kw].get("volume")
                diff = df_metrics[kw].get("difficulty")

            keywords_data.append(
                {
                    "keyword": kw,
                    "volume": vol,
                    "difficulty": diff,
                    "intent": "informational",  # default
                    "is_question": False,  # default
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

    # --- STEP 7: CRAWL TOP COMPETITORS PER CLUSTER ---
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
                    "headings": p["headings"][
                        :15
                    ],  # limit headings size to prevent prompt bloating
                    "word_count": p["word_count"],
                }
            )

        # Get keyword sample (top 20 for brief analysis context)
        kw_sample = [
            {
                "keyword": kw["keyword"],
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

    # --- STEP 9: SAVE LOCAL REPORT ---
    print("\n[Step 9] Saving local markdown report...")
    os.makedirs("outputs", exist_ok=True)
    report_path = os.path.join("outputs", "research_report.md")

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"# SEO Niche & Keyword Research Report\n\n")
        f.write(f"## Project Context\n")
        f.write(f"- **Core Topic**: {extraction.core_topic}\n")
        f.write(f"- **Target Audience**: {extraction.target_audience}\n")
        f.write(f"- **Site Goal**: {extraction.site_goal}\n")
        f.write(f"- **Geographic/Language Scope**: {extraction.geo_scope}\n")
        f.write(f"- **Constraints**: {extraction.constraints}\n\n")

        f.write(f"## Topic Clusters Summary\n")
        for c in saved_clusters:
            f.write(f"### Cluster: {c['name']}\n")
            f.write(f"- **Description**: {c['description']}\n")
            kws = all_cluster_keywords.get(c["name"], [])
            f.write(f"- **Total Keywords**: {len(kws)}\n")

            # Subtopics
            questions = [k["keyword"] for k in kws if k["is_question"]]
            f.write(f"- **Question Keywords**: {len(questions)}\n")

            # Competitors
            comps = competitor_data.get(c["name"], [])
            f.write(f"- **Competitors Crawled**: {len(comps)}\n")
            for comp in comps:
                f.write(
                    f"  - [{comp['title'] or comp['url']}]({comp['url']}) (Word count: {comp['word_count']})\n"
                )

            # Content Gaps
            f.write(f"#### Identified Content Gaps:\n")
            gaps = content_gaps.get(c["name"], [])
            if gaps:
                for gap in gaps:
                    f.write(
                        f"  - **{gap['topic']}** (Priority: {gap['priority'].upper()})\n"
                    )
                    f.write(f"    - *Reason*: {gap['reason']}\n")
                    f.write(f"    - *Recommended Format*: {gap['missing_format']}\n")
                    f.write(
                        f"    - *Target Keywords*: {', '.join(gap['keyword_ideas'])}\n"
                    )
            else:
                f.write(f"  - No significant content gaps identified.\n")
            f.write("\n" + "─" * 40 + "\n\n")

    print(f"Human-readable report saved to: {report_path}")

    # --- STEP 10: CLI SUMMARY ---
    print_separator("═")
    print("                  RESEARCH COMPLETE                  ")
    print_separator("═")

    total_clusters = len(saved_clusters)
    total_kws = sum(len(all_cluster_keywords[c["name"]]) for c in saved_clusters)

    # Collect top opportunities (e.g. priority content gaps or commercial/informational gaps)
    opportunities = []
    for c_name, gaps in content_gaps.items():
        for gap in gaps:
            if gap["priority"].lower() == "high":
                opportunities.append((c_name, gap["topic"], gap["missing_format"]))

    print(f"Clusters analyzed:   {total_clusters}")
    print(f"Total keywords:      {total_kws}")

    print("\nTop High-Priority Content Gap Opportunities:")
    if opportunities:
        for idx, (c_name, topic, fmt) in enumerate(opportunities[:5]):
            print(f"  {idx+1}. [{c_name}] {topic} ({fmt})")
    else:
        print("  None (all clusters covered or low priority gaps)")

    # Suggest starting cluster (the one with the most high priority gaps)
    cluster_gap_counts = {c["name"]: 0 for c in saved_clusters}
    for c_name, gaps in content_gaps.items():
        cluster_gap_counts[c_name] = sum(
            1 for g in gaps if g["priority"].lower() == "high"
        )

    recommended_cluster = max(cluster_gap_counts, key=cluster_gap_counts.get)

    print(f"\nRecommended starting cluster: {recommended_cluster}")
    print(
        f"Reason: This cluster has the highest density of identified high-priority content gaps ({cluster_gap_counts[recommended_cluster]})."
    )
    print_separator("═")
