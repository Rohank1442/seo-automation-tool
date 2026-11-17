-- Product data is accessed through the FastAPI service-role client.
-- Enable RLS without client policies so browser clients cannot bypass API checks.
-- Existing projects must have been assigned to their owner before owner_id is required.

BEGIN;

DO $$
BEGIN
    IF to_regclass('public.projects') IS NULL THEN
        RAISE EXCEPTION 'public.projects does not exist; apply the project schema first.';
    END IF;

    IF EXISTS (SELECT 1 FROM public.projects WHERE owner_id IS NULL) THEN
        RAISE EXCEPTION 'Some projects have no owner_id; assign them before applying this migration.';
    END IF;
END $$;

ALTER TABLE public.projects ALTER COLUMN owner_id SET NOT NULL;

DO $$
DECLARE
    table_name TEXT;
BEGIN
    FOREACH table_name IN ARRAY ARRAY[
        'projects',
        'project_clarifications',
        'pipeline_runs',
        'clusters',
        'keywords',
        'site_architectures',
        'generated_pages',
        'page_indexing_metrics',
        'monitoring_alerts',
        'access_requests'
    ] LOOP
        IF to_regclass(format('public.%I', table_name)) IS NOT NULL THEN
            EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', table_name);
        END IF;
    END LOOP;
END $$;

COMMIT;
