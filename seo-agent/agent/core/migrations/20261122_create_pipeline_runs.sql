-- Persist web pipeline state and checkpoints across Render restarts.

BEGIN;

CREATE TABLE IF NOT EXISTS public.pipeline_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    phases_queued TEXT[] NOT NULL DEFAULT ARRAY['v01', 'v02', 'v03']::TEXT[],
    dry_run BOOLEAN NOT NULL DEFAULT FALSE,
    status TEXT NOT NULL DEFAULT 'running'
        CHECK (status IN ('running', 'completed', 'failed', 'interrupted')),
    current_phase TEXT,
    progress_percentage INTEGER NOT NULL DEFAULT 0
        CHECK (progress_percentage BETWEEN 0 AND 100),
    phases_completed TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
    artifact_manifest JSONB NOT NULL DEFAULT '{}'::JSONB,
    error_message TEXT,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS pipeline_runs_project_started_idx
    ON public.pipeline_runs(project_id, started_at DESC);

CREATE INDEX IF NOT EXISTS pipeline_runs_project_status_idx
    ON public.pipeline_runs(project_id, status);

ALTER TABLE public.pipeline_runs ENABLE ROW LEVEL SECURITY;

INSERT INTO storage.buckets (id, name, public)
VALUES ('pipeline-artifacts', 'pipeline-artifacts', FALSE)
ON CONFLICT (id) DO UPDATE SET public = FALSE;

COMMIT;
