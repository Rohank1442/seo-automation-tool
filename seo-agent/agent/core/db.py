from typing import List, Dict, Any, Optional
from supabase import create_client, Client
from core.config import SUPABASE_URL, SUPABASE_KEY

_client: Optional[Client] = None

def get_db_client() -> Client:
    global _client
    if _client is None:
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be configured in your .env file.")
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _client

def create_project(raw_description: str) -> Dict[str, Any]:
    """Insert a new project and return its data."""
    client = get_db_client()
    response = client.table("projects").insert({
        "raw_description": raw_description,
        "confirmed": False
    }).execute()
    
    if not response.data:
        raise RuntimeError("Failed to create project in Supabase.")
    return response.data[0]

def update_project(project_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    """Update project columns (e.g. core_topic, target_audience, confirmed, etc.)."""
    client = get_db_client()
    response = client.table("projects").update(updates).eq("id", project_id).execute()
    
    if not response.data:
        raise RuntimeError(f"Failed to update project {project_id} in Supabase.")
    return response.data[0]

def create_clusters(project_id: str, clusters: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    """
    Insert a list of clusters for a project.
    clusters: List of dicts with keys: name, description
    """
    client = get_db_client()
    data_to_insert = [
        {"project_id": project_id, "name": c["name"], "description": c.get("description", "")}
        for c in clusters
    ]
    response = client.table("clusters").insert(data_to_insert).execute()
    return response.data

def delete_clusters_for_project(project_id: str):
    """Delete existing clusters for a project to allow resetting/re-running."""
    client = get_db_client()
    client.table("clusters").delete().eq("project_id", project_id).execute()

def save_keywords(cluster_id: str, keywords: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Upsert keywords for a specific cluster.
    keywords: List of dicts with keys: keyword, volume, difficulty, intent, is_question
    """
    client = get_db_client()
    data_to_upsert = []
    for kw in keywords:
        data_to_upsert.append({
            "cluster_id": cluster_id,
            "keyword": kw["keyword"],
            "volume": kw.get("volume"),
            "difficulty": kw.get("difficulty"),
            "intent": kw.get("intent", "informational"),
            "is_question": kw.get("is_question", False)
        })
        
    if not data_to_upsert:
        return []
        
    # Perform upsert on conflict of cluster_id + keyword
    response = client.table("keywords").upsert(
        data_to_upsert,
        on_conflict="cluster_id,keyword"
    ).execute()
    return response.data
