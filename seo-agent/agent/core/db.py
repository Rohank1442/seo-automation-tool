"""
Database & Persistence Layer with Dual Support (Supabase Cloud + Local In-Memory Fallback).
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.config import SUPABASE_KEY, SUPABASE_URL

logger = logging.getLogger("db")

try:
    from supabase import Client, create_client
    HAS_SUPABASE = True
except ImportError:
    HAS_SUPABASE = False
    Client = Any

_client: Optional[Client] = None

# Local persistence cache
_LOCAL_PROJECTS: Dict[str, Dict[str, Any]] = {}
_LOCAL_CLUSTERS: Dict[str, List[Dict[str, Any]]] = {}
_LOCAL_KEYWORDS: Dict[str, List[Dict[str, Any]]] = {}


def get_db_client() -> Optional[Client]:
    """Get Supabase client if configured, otherwise None."""
    global _client
    if not HAS_SUPABASE or not SUPABASE_URL or not SUPABASE_KEY:
        return None
    if _client is None:
        try:
            _client = create_client(SUPABASE_URL, SUPABASE_KEY)
        except Exception as e:
            logger.warning(f"Failed to initialize Supabase client ({e}). Falling back to local storage.")
            _client = None
    return _client


def create_project(raw_description: str) -> Dict[str, Any]:
    """Insert a new project and return its data."""
    client = get_db_client()
    if client:
        try:
            response = client.table("projects").insert({
                "raw_description": raw_description,
                "confirmed": False,
            }).execute()
            if response.data:
                return response.data[0]
        except Exception as e:
            logger.warning(f"Supabase create_project error: {e}. Using local storage.")

    # Local Fallback
    project_id = str(uuid.uuid4())[:8]
    data = {
        "id": project_id,
        "raw_description": raw_description,
        "confirmed": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    _LOCAL_PROJECTS[project_id] = data
    return data


def update_project(project_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    """Update project columns (e.g. core_topic, target_audience, confirmed, etc.)."""
    client = get_db_client()
    if client:
        try:
            response = client.table("projects").update(updates).eq("id", project_id).execute()
            if response.data:
                return response.data[0]
        except Exception as e:
            logger.warning(f"Supabase update_project error: {e}. Using local storage.")

    if project_id in _LOCAL_PROJECTS:
        _LOCAL_PROJECTS[project_id].update(updates)
        return _LOCAL_PROJECTS[project_id]
    return {"id": project_id, **updates}


def create_clusters(project_id: str, clusters: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    """Insert a list of clusters for a project."""
    client = get_db_client()
    data_to_insert = [
        {"project_id": project_id, "name": c["name"], "description": c.get("description", "")}
        for c in clusters
    ]

    if client:
        try:
            response = client.table("clusters").insert(data_to_insert).execute()
            if response.data:
                return response.data
        except Exception as e:
            logger.warning(f"Supabase create_clusters error: {e}. Using local storage.")

    # Local fallback
    res = []
    for idx, item in enumerate(data_to_insert):
        c_data = {"id": f"cluster-{project_id}-{idx}", **item}
        res.append(c_data)
    _LOCAL_CLUSTERS[project_id] = res
    return res


def delete_clusters_for_project(project_id: str):
    """Delete existing clusters for a project to allow resetting/re-running."""
    client = get_db_client()
    if client:
        try:
            client.table("clusters").delete().eq("project_id", project_id).execute()
        except Exception:
            pass
    _LOCAL_CLUSTERS.pop(project_id, None)


def save_keywords(cluster_id: str, keywords: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Upsert keywords for a specific cluster."""
    data_to_upsert = []
    for kw in keywords:
        data_to_upsert.append({
            "cluster_id": cluster_id,
            "keyword": kw["keyword"],
            "volume": kw.get("volume"),
            "difficulty": kw.get("difficulty"),
            "intent": kw.get("intent", "informational"),
            "is_question": kw.get("is_question", False),
        })

    if not data_to_upsert:
        return []

    client = get_db_client()
    if client:
        try:
            response = client.table("keywords").upsert(
                data_to_upsert,
                on_conflict="cluster_id,keyword"
            ).execute()
            if response.data:
                return response.data
        except Exception as e:
            logger.warning(f"Supabase save_keywords error: {e}. Using local storage.")

    _LOCAL_KEYWORDS[cluster_id] = data_to_upsert
    return data_to_upsert
