"""Generate, enrich, and persist topic clusters for a project."""

from core.db import create_clusters
from core.llm import generate_json
from core.scraper import get_google_autocomplete
from prompts.v01_prompts import TopicClustersResponse, CLUSTER_GENERATION_SYSTEM_PROMPT


def generate_project_clusters(project_id: str, extraction):
    """Generate cluster candidates, enrich with autocomplete, and save them under the project."""
    print("\n[Step 4] Finding top-level topic clusters...")
    prompt = (
        f"Generate topic clusters for:\n"
        f"Topic: {extraction.core_topic}\n"
        f"Audience: {extraction.target_audience}\n"
        f"Goal: {extraction.site_goal}\n"
        f"Constraints: {extraction.constraints}"
    )
    try:
        response = generate_json(
            prompt=prompt,
            response_schema=TopicClustersResponse,
            system_instruction=CLUSTER_GENERATION_SYSTEM_PROMPT,
        )
    except Exception as exc:
        print(f"Failed to generate clusters: {exc}")
        raise RuntimeError("v0.1 could not generate topic clusters.") from exc

    print(f"Generated {len(response.clusters)} clusters. Validating via Google Autocomplete...")
    clusters = []
    for candidate in response.clusters:
        suggestions = get_google_autocomplete(candidate.name)
        print(f"Cluster '{candidate.name}' suggestions: {suggestions}")
        description = candidate.description
        if suggestions:
            description += f" (Popular searches: {', '.join(suggestions[:3])})"
        clusters.append({"name": candidate.name, "description": description})

    if not clusters:
        raise ValueError("At least one topic cluster is required to continue v0.1.")

    print("\n[Step 5] Saving generated topic clusters for this web run...")
    saved_clusters = create_clusters(project_id, clusters)
    print(f"Saved {len(saved_clusters)} clusters successfully!")
    return saved_clusters
