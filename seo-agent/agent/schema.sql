-- SEO Automation Agent Database Schema

-- Enable UUID extension if not enabled
create extension if not exists "uuid-ossp";

-- 1. Projects Table
create table if not exists projects (
    id uuid default gen_random_uuid() primary key,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null,
    raw_description text not null,
    core_topic text,
    target_audience text,
    site_goal text,
    geo_scope text,
    constraints text,
    confirmed boolean default false not null
);

-- 2. Clusters Table
create table if not exists clusters (
    id uuid default gen_random_uuid() primary key,
    project_id uuid references projects(id) on delete cascade not null,
    name text not null,
    description text,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- 3. Keywords Table
create table if not exists keywords (
    id uuid default gen_random_uuid() primary key,
    cluster_id uuid references clusters(id) on delete cascade not null,
    keyword text not null,
    volume integer,
    difficulty integer,
    intent text check (intent in ('informational', 'commercial', 'transactional', 'navigational')),
    is_question boolean default false not null,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null,
    unique(cluster_id, keyword)
);
