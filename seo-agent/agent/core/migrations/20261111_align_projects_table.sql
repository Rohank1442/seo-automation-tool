-- Add the current project API columns to the legacy projects table.
-- This migration preserves legacy columns and existing project data.

BEGIN;

ALTER TABLE public.projects
    ADD COLUMN IF NOT EXISTS name TEXT,
    ADD COLUMN IF NOT EXISTS target_domain TEXT,
    ADD COLUMN IF NOT EXISTS status TEXT,
    ADD COLUMN IF NOT EXISTS current_phase TEXT,
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ;

-- Retain recognizable project labels where possible, then fall back to the idea text.
UPDATE public.projects
SET name = COALESCE(
    NULLIF(BTRIM(name), ''),
    NULLIF(BTRIM(core_topic), ''),
    NULLIF(LEFT(BTRIM(COALESCE(raw_description, '')), 60), ''),
    'Project ' || id
)
WHERE name IS NULL OR BTRIM(name) = '';

UPDATE public.projects
SET target_domain = 'https://example.com'
WHERE target_domain IS NULL OR BTRIM(target_domain) = '';

UPDATE public.projects
SET status = 'created'
WHERE status IS NULL OR BTRIM(status) = '';

UPDATE public.projects
SET current_phase = 'init'
WHERE current_phase IS NULL OR BTRIM(current_phase) = '';

ALTER TABLE public.projects
    ALTER COLUMN name SET NOT NULL,
    ALTER COLUMN target_domain SET DEFAULT 'https://example.com',
    ALTER COLUMN target_domain SET NOT NULL,
    ALTER COLUMN status SET DEFAULT 'created',
    ALTER COLUMN status SET NOT NULL,
    ALTER COLUMN current_phase SET DEFAULT 'init',
    ALTER COLUMN current_phase SET NOT NULL,
    ALTER COLUMN updated_at SET DEFAULT NOW();

COMMIT;
