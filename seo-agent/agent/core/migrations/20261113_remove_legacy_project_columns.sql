-- Remove legacy project fields that the current application no longer uses.
-- No CASCADE is used: PostgreSQL will stop if another database object depends on a column.
BEGIN;

ALTER TABLE public.projects
    DROP COLUMN IF EXISTS core_topic,
    DROP COLUMN IF EXISTS site_goal,
    DROP COLUMN IF EXISTS geo_scope,
    DROP COLUMN IF EXISTS constraints,
    DROP COLUMN IF EXISTS confirmed;

COMMIT;
