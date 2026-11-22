"""Unit tests for durable pipeline artifact checkpoint files."""

import tempfile
import unittest
import asyncio
from pathlib import Path
from unittest.mock import patch

from core.db import ProjectStoreError
from core.pipeline_artifacts import download_phase_artifacts, upload_phase_artifacts
from services.pipeline_service import ACTIVE_RUNS, PipelineService


class MemoryBucket:
    def __init__(self):
        self.objects: dict[str, bytes] = {}

    def upload(self, path: str, data: bytes, file_options: dict[str, str]) -> None:
        self.objects[path] = data

    def download(self, path: str) -> bytes:
        return self.objects[path]


class MemoryStorage:
    def __init__(self, bucket: MemoryBucket):
        self.bucket = bucket
        self.requested_bucket = None

    def from_(self, bucket_name: str) -> MemoryBucket:
        self.requested_bucket = bucket_name
        return self.bucket


class MemoryClient:
    def __init__(self):
        self.bucket = MemoryBucket()
        self.storage = MemoryStorage(self.bucket)


class PipelineArtifactTests(unittest.TestCase):
    def test_v01_and_v02_checkpoints_round_trip_to_run_scoped_keys(self) -> None:
        client = MemoryClient()
        with tempfile.TemporaryDirectory() as source, tempfile.TemporaryDirectory() as restored:
            source_root = Path(source)
            (source_root / "research_report.md").write_text("research", encoding="utf-8")
            (source_root / "page_opportunities.json").write_text("{}", encoding="utf-8")
            (source_root / "v02").mkdir()
            (source_root / "v02" / "site_architecture.json").write_text("{}", encoding="utf-8")
            (source_root / "v03").mkdir()
            (source_root / "v03" / "generated-page.json").write_text("{}", encoding="utf-8")

            with patch("core.pipeline_artifacts._require_project_db_client", return_value=client):
                v01_manifest = upload_phase_artifacts("project-1", "run-1", "v01", source_root)
                v02_manifest = upload_phase_artifacts("project-1", "run-1", "v02", source_root)
                restored_count = download_phase_artifacts(v01_manifest + v02_manifest, Path(restored))

            self.assertEqual(client.storage.requested_bucket, "pipeline-artifacts")
            self.assertEqual(restored_count, 3)
            self.assertEqual((Path(restored) / "research_report.md").read_text(encoding="utf-8"), "research")
            self.assertEqual((Path(restored) / "page_opportunities.json").read_text(encoding="utf-8"), "{}")
            self.assertEqual((Path(restored) / "v02" / "site_architecture.json").read_text(encoding="utf-8"), "{}")
            self.assertNotIn("v03/generated-page.json", [item["local_path"] for item in v02_manifest])
            self.assertTrue(all("/runs/run-1/" in key for key in client.bucket.objects))

    def test_restore_rejects_path_traversal(self) -> None:
        client = MemoryClient()
        with tempfile.TemporaryDirectory() as destination:
            manifest = [{"local_path": "../outside.txt", "object_key": "safe/object"}]
            with patch("core.pipeline_artifacts._require_project_db_client", return_value=client):
                with self.assertRaises(ProjectStoreError):
                    download_phase_artifacts(manifest, Path(destination))


class PipelineResumeTests(unittest.TestCase):
    def test_resumes_after_v02_without_rerunning_v01_or_v02(self) -> None:
        run = {
            "id": "run-1",
            "project_id": "project-1",
            "phases_queued": ["v01", "v02", "v03"],
            "dry_run": False,
            "status": "failed",
            "current_phase": "v03_content_generation",
            "phases_completed": ["v01", "v02"],
            "artifact_manifest": {"v01": [{"local_path": "page_opportunities.json", "object_key": "v01.json"}],
                                  "v02": [{"local_path": "v02/site_architecture.json", "object_key": "v02.json"}]},
        }

        async def collect_events():
            return [
                event async for event in PipelineService.run_pipeline_stream(
                    project_id="project-1",
                    user_idea="An example project",
                    dry_run=False,
                    min_pages=1,
                    max_pages=1,
                    export_frontend=False,
                )
            ]

        ACTIVE_RUNS.pop("project-1", None)
        try:
            with (
                patch("services.pipeline_service.get_resumable_pipeline_run", return_value=run),
                patch("services.pipeline_service.update_pipeline_run_record", return_value=run),
                patch("services.pipeline_service.create_pipeline_run_record") as create_run,
                patch("services.pipeline_service.download_phase_artifacts", return_value=1) as restore,
                patch("services.pipeline_service.run_research_phase") as research,
                patch("services.pipeline_service.run_v02_pipeline") as architecture,
                patch("services.pipeline_service.run_content_generation_phase") as generation,
            ):
                events = asyncio.run(collect_events())

            self.assertEqual(restore.call_count, 2)
            create_run.assert_not_called()
            research.assert_not_called()
            architecture.assert_not_called()
            generation.assert_called_once()
            self.assertTrue(any(event["step"] == "restored" and event["phase"] == "v01_research" for event in events))
            self.assertTrue(any(event["step"] == "restored" and event["phase"] == "v02_architecture" for event in events))
            self.assertEqual(events[-1]["status"], "completed")
        finally:
            ACTIVE_RUNS.pop("project-1", None)


if __name__ == "__main__":
    unittest.main()
