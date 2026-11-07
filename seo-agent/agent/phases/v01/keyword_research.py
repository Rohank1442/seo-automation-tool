"""Keyword discovery, metric collection, intent classification, and persistence for v0.1."""

import json
from typing import Any, Dict, List

from core.db import save_keywords
from core.llm import generate_json
from core.scraper import (
    get_dataforseo_metrics,
    get_ddg_related_searches,
    get_google_autocomplete,
    get_people_also_ask,
)
from prompts.v01_prompts import (
    BatchKeywordClassification,
    CLUSTER_SEEDS_SYSTEM_PROMPT,
    INTENT_CLASSIFICATION_SYSTEM_PROMPT,
    ClusterSeedsResponse,
)
from .logging_utils import print_separator


def research_cluster_keywords(saved_clusters, extraction):
    """Collect and persist the classified keyword set for each saved cluster."""
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
    return all_cluster_keywords
