-- ============================================================
-- Supabase / PostgreSQL Schema for SEO Automation Platform
-- ============================================================

-- 0. Custom Users Table (Custom Auth with Email & Password)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT NOT NULL UNIQUE,
    hashed_password TEXT NOT NULL,
    full_name TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(lower(email));
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- 1. Projects Table
CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    raw_description TEXT NOT NULL,
    target_domain TEXT NOT NULL DEFAULT 'https://example.com',
    target_audience TEXT,
    status TEXT NOT NULL DEFAULT 'created',
    current_phase TEXT NOT NULL DEFAULT 'init',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;

-- 1a. Public early-access requests (manually reviewed by the product owner)
CREATE TABLE IF NOT EXISTS access_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT NOT NULL UNIQUE,
    use_case TEXT,
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'approved', 'declined', 'registered')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    reviewed_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_access_requests_email ON access_requests(lower(email));
ALTER TABLE access_requests ENABLE ROW LEVEL SECURITY;

-- 2. Durable Pipeline Runs & Artifact Checkpoints
CREATE TABLE IF NOT EXISTS pipeline_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    phases_queued TEXT[] NOT NULL DEFAULT ARRAY['v01', 'v02', 'v03']::TEXT[],
    dry_run BOOLEAN NOT NULL DEFAULT FALSE,
    status TEXT NOT NULL DEFAULT 'running'
        CHECK (status IN ('running', 'completed', 'failed', 'interrupted')),
    current_phase TEXT,
    progress_percentage INT NOT NULL DEFAULT 0 CHECK (progress_percentage BETWEEN 0 AND 100),
    phases_completed TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
    artifact_manifest JSONB NOT NULL DEFAULT '{}'::jsonb,
    error_message TEXT,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS pipeline_runs_project_started_idx ON pipeline_runs(project_id, started_at DESC);
CREATE INDEX IF NOT EXISTS pipeline_runs_project_status_idx ON pipeline_runs(project_id, status);
ALTER TABLE pipeline_runs ENABLE ROW LEVEL SECURITY;


-- 4. Topic Clusters Table (v0.1 Research)
CREATE TABLE IF NOT EXISTS clusters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    tier TEXT DEFAULT 'tier_1',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
ALTER TABLE clusters ENABLE ROW LEVEL SECURITY;

-- 5. Keywords Table (v0.1 Research)
CREATE TABLE IF NOT EXISTS keywords (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cluster_id UUID REFERENCES clusters(id) ON DELETE CASCADE,
    keyword TEXT NOT NULL,
    volume INT,
    difficulty INT,
    intent TEXT DEFAULT 'informational',
    is_question BOOLEAN DEFAULT FALSE,
    cpc NUMERIC DEFAULT 0.0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(cluster_id, keyword)
);
ALTER TABLE keywords ENABLE ROW LEVEL SECURITY;


-- 7. Generated Pages Table (v0.3 Content Generation)
CREATE TABLE IF NOT EXISTS generated_pages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_page_id TEXT,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    cluster_id UUID REFERENCES clusters(id) ON DELETE SET NULL,
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
    word_count INT NOT NULL DEFAULT 0,
    health_score NUMERIC NOT NULL DEFAULT 100.0,
    markdown_content TEXT NOT NULL DEFAULT '',
    faqs JSONB NOT NULL DEFAULT '[]'::jsonb,
    internal_links JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    validation_issues JSONB NOT NULL DEFAULT '[]'::jsonb,
    UNIQUE(project_id, slug)
);
CREATE INDEX IF NOT EXISTS generated_pages_project_id_idx ON generated_pages(project_id);
CREATE INDEX IF NOT EXISTS generated_pages_cluster_id_idx ON generated_pages(cluster_id);
ALTER TABLE generated_pages ENABLE ROW LEVEL SECURITY;
