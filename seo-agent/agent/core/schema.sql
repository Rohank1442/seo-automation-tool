-- ============================================================
-- Supabase / PostgreSQL Schema for SEO Automation Platform
-- ============================================================

-- 1. Projects Table
CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    raw_description TEXT NOT NULL,
    target_domain TEXT DEFAULT 'https://example.com',
    target_audience TEXT,
    primary_goal TEXT,
    status TEXT DEFAULT 'created',
    current_phase TEXT DEFAULT 'init',
    health_score NUMERIC DEFAULT 100.0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Project Clarifications / Interactive Interview Table (v0.1 Pre-run confirmation)
CREATE TABLE IF NOT EXISTS project_clarifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id TEXT REFERENCES projects(id) ON DELETE CASCADE,
    agent_understanding TEXT NOT NULL,
    suggested_focus_areas TEXT[] DEFAULT ARRAY[]::TEXT[],
    clarification_questions JSONB DEFAULT '[]'::jsonb,
    user_answers JSONB DEFAULT '{}'::jsonb,
    is_confirmed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Pipeline Runs Table (Async execution & SSE logs persistence)
CREATE TABLE IF NOT EXISTS pipeline_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id TEXT REFERENCES projects(id) ON DELETE CASCADE,
    phases_queued TEXT[] DEFAULT ARRAY['v0.1', 'v0.2', 'v0.3']::TEXT[],
    dry_run BOOLEAN DEFAULT FALSE,
    status TEXT DEFAULT 'running', -- 'running', 'completed', 'failed', 'cancelled'
    current_phase TEXT DEFAULT 'v01_research',
    progress_percentage INT DEFAULT 0,
    phases_completed TEXT[] DEFAULT ARRAY[]::TEXT[],
    logs JSONB DEFAULT '[]'::jsonb, -- Array of { timestamp, phase, level, message, details }
    error_message TEXT,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- 4. Topic Clusters Table (v0.1 Research)
CREATE TABLE IF NOT EXISTS clusters (
    id TEXT PRIMARY KEY,
    project_id TEXT REFERENCES projects(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    tier TEXT DEFAULT 'tier_1',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5. Keywords Table (v0.1 Research)
CREATE TABLE IF NOT EXISTS keywords (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cluster_id TEXT REFERENCES clusters(id) ON DELETE CASCADE,
    keyword TEXT NOT NULL,
    volume INT,
    difficulty INT,
    intent TEXT DEFAULT 'informational',
    is_question BOOLEAN DEFAULT FALSE,
    cpc NUMERIC DEFAULT 0.0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(cluster_id, keyword)
);

-- 6. Site Architecture & Technical Foundation Table (v0.2 Site Setup)
CREATE TABLE IF NOT EXISTS site_architectures (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id TEXT REFERENCES projects(id) ON DELETE CASCADE,
    domain_structure TEXT DEFAULT 'subfolder', -- 'subfolder', 'subdomain', 'root'
    sitemap_xml TEXT,
    robots_txt TEXT,
    gsc_site_url TEXT,
    total_urls_in_sitemap INT DEFAULT 0,
    hierarchy_rules JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(project_id)
);

-- 7. Generated Pages Table (v0.3 Content Generation)
CREATE TABLE IF NOT EXISTS generated_pages (
    id TEXT PRIMARY KEY,
    project_id TEXT REFERENCES projects(id) ON DELETE CASCADE,
    slug TEXT NOT NULL,
    url_path TEXT NOT NULL,
    title TEXT NOT NULL,
    h1 TEXT NOT NULL,
    meta_description TEXT,
    canonical_url TEXT,
    robots TEXT DEFAULT 'index, follow',
    schema_type TEXT DEFAULT 'Article',
    primary_keyword TEXT,
    secondary_keywords TEXT[],
    cluster_name TEXT,
    page_type TEXT DEFAULT 'guide',
    search_intent TEXT DEFAULT 'informational',
    word_count INT DEFAULT 500,
    health_score NUMERIC DEFAULT 100.0,
    markdown_content TEXT,
    nextjs_jsx_code TEXT,
    faqs JSONB DEFAULT '[]'::jsonb,
    internal_links JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(project_id, slug)
);

-- 8. v0.4 Page Indexing & Search Console Metrics (Weekly Surveillance)
CREATE TABLE IF NOT EXISTS page_indexing_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    page_id TEXT REFERENCES generated_pages(id) ON DELETE CASCADE,
    project_id TEXT REFERENCES projects(id) ON DELETE CASCADE,
    check_date DATE NOT NULL DEFAULT CURRENT_DATE,
    is_indexed BOOLEAN DEFAULT FALSE,
    index_verdict TEXT DEFAULT 'DISCOVERED_NOT_INDEXED',
    impressions_7d INT DEFAULT 0,
    impressions_30d INT DEFAULT 0,
    clicks_7d INT DEFAULT 0,
    clicks_30d INT DEFAULT 0,
    avg_position NUMERIC DEFAULT 0.0,
    ctr_percentage NUMERIC DEFAULT 0.0,
    status_category TEXT DEFAULT 'invisible_anomaly', -- 'indexed_and_alive', 'indexed_silent', 'invisible_anomaly', 'breakout_candidate'
    mined_queries TEXT[] DEFAULT ARRAY[]::TEXT[],
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 9. Monitoring Alerts Table (v0.4 Signal & Anomaly Flags)
CREATE TABLE IF NOT EXISTS monitoring_alerts (
    id TEXT PRIMARY KEY,
    project_id TEXT REFERENCES projects(id) ON DELETE CASCADE,
    page_slug TEXT,
    severity TEXT DEFAULT 'info', -- 'info', 'warning', 'critical'
    alert_type TEXT NOT NULL,
    message TEXT NOT NULL,
    recommendation TEXT NOT NULL,
    is_resolved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
