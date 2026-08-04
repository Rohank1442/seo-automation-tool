from typing import List, Optional
from pydantic import BaseModel, Field

# --- PYDANTIC SCHEMAS FOR STRUCTURED OUTPUT ---

class ProjectExtraction(BaseModel):
    core_topic: str = Field(description="The primary niche or core topic of the site.")
    target_audience: str = Field(description="The intended audience or customer profile.")
    site_goal: str = Field(description="What the site hopes to achieve (e.g. lead gen, affiliate sales, brand authority).")
    geo_scope: str = Field(description="Geographic location or language focus (e.g. US/Global English).")
    constraints: str = Field(description="Any limitations, rules, or budget details mentioned by the user.")
    is_vague: bool = Field(description="True if the description is too broad or lacks critical details to build a specific content plan.")
    vagueness_reason: str = Field(description="Why the description is vague, or empty if not vague.")

class FollowUpQuestions(BaseModel):
    questions: List[str] = Field(description="1 to 3 highly targeted questions to clarify the project scope and details.")

class SeedCluster(BaseModel):
    name: str = Field(description="Short, descriptive name of the topic cluster (2-4 words).")
    description: str = Field(description="One-sentence description of what this cluster covers.")

class TopicClustersResponse(BaseModel):
    clusters: List[SeedCluster] = Field(description="List of suggested seed topic clusters.")

class KeywordClassification(BaseModel):
    keyword: str
    intent: str = Field(description="Must be one of: 'informational', 'commercial', 'transactional', 'navigational'")
    is_question: bool = Field(description="True if the keyword is a question (how, why, what, where, etc.), False otherwise.")

class BatchKeywordClassification(BaseModel):
    keywords: List[KeywordClassification]

class ContentGap(BaseModel):
    topic: str = Field(description="The specific subtopic or angle that represents a content gap.")
    keyword_ideas: List[str] = Field(description="Related keywords from the keyword list that map to this gap.")
    missing_format: str = Field(description="The type of content missing (e.g. definitive guide, comparison list, visual checklist).")
    priority: str = Field(description="Priority of addressing this gap (high, medium, low).")
    reason: str = Field(description="Why this is a gap based on competitor analysis.")

class ContentGapAnalysisResponse(BaseModel):
    gaps: List[ContentGap] = Field(description="List of identified content gaps per cluster.")


# --- SYSTEM PROMPTS ---

EXTRACTION_SYSTEM_PROMPT = """You are an expert SEO architect. Your task is to analyze the user's site idea and extract structural details to build an SEO automation project.
Evaluate if the idea is too broad (e.g., 'fitness site' or 'finance') or lacks critical parameters.
If it is vague, set is_vague to true and explain why in vagueness_reason."""

FOLLOWUP_SYSTEM_PROMPT = """You are an expert SEO planner. The user has described a site idea, but it lacks details.
Generate 1 to 3 targeted clarification questions to extract details like target audience, monetisation model, geography, or specific sub-niche constraints."""

CLUSTER_GENERATION_SYSTEM_PROMPT = """You are an SEO Strategist. Based on the confirmed project description, break down the niche into 5 to 10 logical topic clusters.
Each cluster should represent a major category of content that would exist on the website.
Avoid overlapping topics. Keep cluster names concise but descriptive."""

INTENT_CLASSIFICATION_SYSTEM_PROMPT = """You are an SEO analyzer. Classify the search intent of the provided list of keywords.
Intent types:
- 'informational': user wants to learn, get answers, or research a topic (e.g. 'how to grow tomatoes')
- 'commercial': user is comparing options, looking for reviews/tips before buying (e.g. 'best tomato seeds')
- 'transactional': user is ready to buy/sign up (e.g. 'buy organic tomato seeds online')
- 'navigational': user wants to go to a specific website or brand (e.g. 'burpee seeds tomato section')
Also identify if the keyword is phrased as a question."""

GAP_ANALYSIS_SYSTEM_PROMPT = """You are an SEO auditor. Analyze the provided competitor page outlines (their titles, H1s, H2/H3 headings, word count) alongside our list of target keywords for a topic cluster.
Identify content gaps:
1. Subtopics or search queries in our list that competitor pages completely ignore or cover very briefly.
2. Angles or page formats that competitors are missing (e.g., they all did listicles but no one created a step-by-step calculator or in-depth guide).
3. Question-based queries that don't have dedicated answer blocks.
Provide actionable, prioritized recommendations."""
