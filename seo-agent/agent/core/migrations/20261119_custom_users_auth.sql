-- ============================================================
-- Migration: 20261119_custom_users_auth.sql
-- Description: Transition from Supabase GoTrue Auth to custom email/password authentication.
-- 1. Create public.users table.
-- 2. Update access_requests status constraint to allow 'registered'.
-- 3. Update projects.owner_id foreign key to point to public.users(id).
-- 4. Enable RLS on public.users.
-- ============================================================

BEGIN;

-- 1. Create custom users table
CREATE TABLE IF NOT EXISTS public.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT NOT NULL UNIQUE,
    hashed_password TEXT NOT NULL,
    full_name TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_email ON public.users (lower(email));

-- Enable RLS (access is mediated via service role API in FastAPI)
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;

-- 2. Update access_requests check constraint to support 'registered'
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'access_requests_status_check'
          AND conrelid = 'public.access_requests'::regclass
    ) THEN
        ALTER TABLE public.access_requests DROP CONSTRAINT access_requests_status_check;
    END IF;

    ALTER TABLE public.access_requests
        ADD CONSTRAINT access_requests_status_check
        CHECK (status IN ('pending', 'approved', 'declined', 'registered'));
END $$;

CREATE INDEX IF NOT EXISTS idx_access_requests_email ON public.access_requests (lower(email));

-- 3. Handle projects.owner_id foreign key transition to public.users(id)
DO $$
BEGIN
    -- Drop old foreign key constraint pointing to auth.users if it exists
    IF EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'projects_owner_id_fkey'
          AND conrelid = 'public.projects'::regclass
    ) THEN
        ALTER TABLE public.projects DROP CONSTRAINT projects_owner_id_fkey;
    END IF;

    -- If there are existing auth.users linked to projects, import them into public.users with placeholder hash
    IF to_regclass('auth.users') IS NOT NULL THEN
        INSERT INTO public.users (id, email, hashed_password, created_at)
        SELECT DISTINCT
            au.id, 
            au.email, 
            '$2b$12$e80MvQ0iR1Uq8M0Yn0v60.WbqvE2Q161NqK24W2rGzB5.55qQ.5eq', -- Placeholder hash
            au.created_at
        FROM auth.users au
        JOIN public.projects p ON p.owner_id = au.id
        WHERE au.email NOT IN (SELECT email FROM public.users)
        ON CONFLICT (id) DO NOTHING;
    END IF;

    -- Add foreign key constraint to public.users(id)
    ALTER TABLE public.projects
        ADD CONSTRAINT projects_owner_id_fkey
        FOREIGN KEY (owner_id) REFERENCES public.users(id) ON DELETE CASCADE;
END $$;

COMMIT;
