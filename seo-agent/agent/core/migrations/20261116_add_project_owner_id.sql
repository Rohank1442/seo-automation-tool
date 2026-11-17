-- Associate existing projects with the Supabase Auth account that owns them.
-- Replace the email placeholder below before running this migration in Supabase SQL Editor.
-- The owner_id column stays nullable until project creation is updated to set it.

BEGIN;

DO $$
BEGIN
    IF to_regclass('public.access_requests') IS NULL THEN
        RAISE EXCEPTION 'public.access_requests does not exist; apply its schema first.';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_class AS relation
        JOIN pg_namespace AS namespace ON namespace.oid = relation.relnamespace
        WHERE namespace.nspname = 'public'
          AND relation.relname = 'access_requests'
          AND relation.relrowsecurity
    ) THEN
        ALTER TABLE public.access_requests ENABLE ROW LEVEL SECURITY;
    END IF;
END $$;

ALTER TABLE public.projects
    ADD COLUMN IF NOT EXISTS owner_id UUID;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'projects_owner_id_fkey'
          AND conrelid = 'public.projects'::regclass
    ) THEN
        ALTER TABLE public.projects
            ADD CONSTRAINT projects_owner_id_fkey
            FOREIGN KEY (owner_id) REFERENCES auth.users(id);
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS projects_owner_id_idx
    ON public.projects(owner_id);

DO $$
DECLARE
    owner_email TEXT := lower('rohanworks14@gmail.com');
    owner_user_id UUID;
BEGIN
    SELECT id
    INTO owner_user_id
    FROM auth.users
    WHERE lower(email) = owner_email;

    IF owner_user_id IS NULL THEN
        RAISE EXCEPTION 'No Supabase Auth user found for email %.', owner_email;
    END IF;

    UPDATE public.projects
    SET owner_id = owner_user_id
    WHERE owner_id IS NULL;

    IF EXISTS (SELECT 1 FROM public.projects WHERE owner_id IS NULL) THEN
        RAISE EXCEPTION 'Some existing projects could not be assigned to the owner.';
    END IF;
END $$;

COMMIT;
