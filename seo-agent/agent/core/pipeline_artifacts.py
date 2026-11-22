"""Persist and restore pipeline checkpoint files using private Supabase Storage."""

import mimetypes
from pathlib import Path, PurePosixPath
from typing import Any, Dict, List

from core.config import PIPELINE_ARTIFACTS_BUCKET
from core.db import ProjectStoreError, _require_project_db_client


def _phase_files(project_outputs: Path, phase: str) -> List[Path]:
    if phase == "v01":
        candidates = [
            project_outputs / "research_report.md",
            project_outputs / "page_opportunities.json",
        ]
        return [path for path in candidates if path.is_file()]
    if phase == "v02":
        v02_dir = project_outputs / "v02"
        return sorted(path for path in v02_dir.rglob("*") if path.is_file()) if v02_dir.is_dir() else []
    raise ValueError(f"Unsupported pipeline artifact phase: {phase}")


def upload_phase_artifacts(
    project_id: str,
    run_id: str,
    phase: str,
    project_outputs: Path,
) -> List[Dict[str, str]]:
    """Upload a completed phase's files and return their local/object paths."""
    files = _phase_files(project_outputs, phase)
    if not files:
        raise FileNotFoundError(f"No files found to checkpoint for {phase}.")

    client = _require_project_db_client()
    storage = client.storage.from_(PIPELINE_ARTIFACTS_BUCKET)
    manifest: List[Dict[str, str]] = []
    root = project_outputs.resolve()

    try:
        for file_path in files:
            local_relative = file_path.resolve().relative_to(root).as_posix()
            object_key = f"projects/{project_id}/runs/{run_id}/{phase}/{local_relative}"
            content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
            storage.upload(
                object_key,
                file_path.read_bytes(),
                file_options={"content-type": content_type, "upsert": "true"},
            )
            manifest.append({"local_path": local_relative, "object_key": object_key})
    except Exception as exc:
        raise ProjectStoreError(f"Could not upload {phase} pipeline artifacts to Supabase Storage.") from exc

    return manifest


def download_phase_artifacts(
    phase_manifest: List[Dict[str, str]],
    project_outputs: Path,
) -> int:
    """Restore checkpoint files to the project's temporary working directory."""
    if not phase_manifest:
        return 0

    client = _require_project_db_client()
    storage = client.storage.from_(PIPELINE_ARTIFACTS_BUCKET)
    root = project_outputs.resolve()
    restored = 0

    try:
        for item in phase_manifest:
            relative = PurePosixPath(item["local_path"])
            if relative.is_absolute() or ".." in relative.parts:
                raise ValueError("Artifact manifest contains an unsafe local path.")
            destination = (root / Path(*relative.parts)).resolve()
            destination.relative_to(root)
            destination.parent.mkdir(parents=True, exist_ok=True)
            data = storage.download(item["object_key"])
            destination.write_bytes(data)
            restored += 1
    except Exception as exc:
        raise ProjectStoreError("Could not restore pipeline artifacts from Supabase Storage.") from exc

    return restored
