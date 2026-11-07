"""Extract structured project context and persist supported project fields."""

from core.db import update_project_record
from core.llm import generate_json
from prompts.v01_prompts import ProjectExtraction, EXTRACTION_SYSTEM_PROMPT


def extract_project_context(custom_idea: str, project_id: str) -> ProjectExtraction:
    """Extract the research brief from the submitted project idea and update its record."""
    print(f"\n[Step 1] Researching existing project {project_id}.")
    print("\n[Step 2] Extracting project parameters...")
    try:
        extraction = generate_json(
            prompt=f"Extract parameters from the following project idea:\n\n{custom_idea}",
            response_schema=ProjectExtraction,
            system_instruction=EXTRACTION_SYSTEM_PROMPT,
        )
    except Exception as exc:
        print(f"Error during LLM extraction: {exc}")
        raise RuntimeError("v0.1 could not extract project parameters.") from exc

    print("\nExtracted Parameters:")
    print(f"  • Core Topic:      {extraction.core_topic}")
    print(f"  • Target Audience: {extraction.target_audience}")
    print(f"  • Site Goal:       {extraction.site_goal}")
    print(f"  • Geo/Language:    {extraction.geo_scope}")
    print(f"  • Constraints:     {extraction.constraints}")
    if extraction.is_vague:
        print("Idea is marked vague; continuing with the best available extraction for this web run.")

    # Persist only columns supported by the selected projects schema; the full context goes into the artifact.
    update_project_record(
        project_id,
        {
            "target_audience": extraction.target_audience,
            "primary_goal": extraction.site_goal,
            "status": "researching",
            "current_phase": "v01_research",
        },
    )
    return extraction
