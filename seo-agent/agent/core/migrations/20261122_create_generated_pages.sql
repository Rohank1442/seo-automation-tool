-- Store completed v0.3 pages durably in Supabase.
-- Page content stays in Markdown; variable FAQs and links are JSONB.

BEGIN;

CREATE TABLE IF NOT EXISTS public.generated_pages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_page_id TEXT,
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    cluster_id UUID NULL REFERENCES public.clusters(id) ON DELETE SET NULL,
    slug TEXT NOT NULL,
    url_path TEXT NOT NULL,
    title TEXT NOT NULL,
    h1 TEXT NOT NULL,
    meta_title TEXT,
    meta_description TEXT,
    canonical_url TEXT,
    robots TEXT NOT NULL DEFAULT 'index, follow',
    schema_type TEXT NOT NULL DEFAULT 'Article',
    primary_keyword TEXT,
    secondary_keywords TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
    page_type TEXT NOT NULL DEFAULT 'guide',
    search_intent TEXT NOT NULL DEFAULT 'informational',
    word_count INTEGER NOT NULL DEFAULT 0,
    health_score NUMERIC NOT NULL DEFAULT 100.0,
    markdown_content TEXT NOT NULL DEFAULT '',
    faqs JSONB NOT NULL DEFAULT '[]'::JSONB,
    internal_links JSONB NOT NULL DEFAULT '[]'::JSONB,
    validation_issues JSONB NOT NULL DEFAULT '[]'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT generated_pages_project_slug_key UNIQUE (project_id, slug)
);

CREATE INDEX IF NOT EXISTS generated_pages_project_id_idx
    ON public.generated_pages(project_id);

CREATE INDEX IF NOT EXISTS generated_pages_cluster_id_idx
    ON public.generated_pages(cluster_id);

ALTER TABLE public.generated_pages ENABLE ROW LEVEL SECURITY;

COMMIT;
