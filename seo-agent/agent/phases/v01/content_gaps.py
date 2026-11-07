"""Analyze competitor and keyword data to identify content gaps."""

import json
from typing import Any, Dict, List

from core.llm import generate_json
from prompts.v01_prompts import ContentGapAnalysisResponse, GAP_ANALYSIS_SYSTEM_PROMPT
from .logging_utils import print_separator


def analyze_content_gaps(saved_clusters, extraction, all_cluster_keywords, competitor_data):
    """Generate page and section opportunities for each topic cluster."""
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
    return content_gaps
