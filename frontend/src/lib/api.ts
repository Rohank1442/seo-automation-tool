import {
  MonitoringDashboardData,
  PageDetail,
  PageSummary,
  Project,
} from "./types";
import { createClient } from "@/lib/supabase/client";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1";

async function fetchJson<T>(
  url: string,
  options?: RequestInit,
  authenticated: boolean = true,
): Promise<T> {
  const headers = new Headers(options?.headers);
  if (!headers.has("Content-Type")) headers.set("Content-Type", "application/json");

  if (authenticated) {
    const { data: { session } } = await createClient().auth.getSession();
    if (session?.access_token) {
      headers.set("Authorization", `Bearer ${session.access_token}`);
    }
  }

  const res = await fetch(url, { ...options, headers });
  if (!res.ok) {
    const errorText = await res.text();
    throw new Error(`API Error ${res.status}: ${errorText}`);
  }
  return res.json();
}

export const api = {
  // Public early-access requests
  async requestEarlyAccess(data: { email: string; use_case?: string }): Promise<{ status: string }> {
    return fetchJson(`${API_BASE}/access-requests`, {
      method: "POST",
      body: JSON.stringify(data),
    }, false);
  },

  // Projects
  async getProjects(): Promise<Project[]> {
    return fetchJson<Project[]>(`${API_BASE}/projects`);
  },

  async getProject(id: string): Promise<Project> {
    return fetchJson<Project>(`${API_BASE}/projects/${id}`);
  },

  async createProject(data: {
    raw_description: string;
    name: string;
    target_audience?: string;
    target_domain?: string;
  }): Promise<Project> {
    return fetchJson<Project>(`${API_BASE}/projects`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  // Pipeline Execution
  getPipelineStreamUrl(projectId: string, dryRun: boolean = true): string {
    return `${API_BASE}/pipeline/${projectId}/stream?dry_run=${dryRun}`;
  },

  // Pages
  async getPages(projectId: string): Promise<PageSummary[]> {
    return fetchJson<PageSummary[]>(`${API_BASE}/projects/${projectId}/pages`);
  },

  async getPageDetail(projectId: string, slug: string): Promise<PageDetail> {
    return fetchJson<PageDetail>(`${API_BASE}/projects/${projectId}/pages/${slug}`);
  },

  async exportFrontend(projectId: string, data?: { framework?: string; language?: string; styling?: string }): Promise<any> {
    return fetchJson(`${API_BASE}/projects/${projectId}/pages/export`, {
      method: "POST",
      body: JSON.stringify(data || {}),
    });
  },

  async generatePagesWave(
    projectId: string,
    data: {
      strategy: "next_best" | "specific_cluster";
      cluster_name?: string;
      batch_size: number;
      dry_run?: boolean;
    }
  ): Promise<{
    status: string;
    strategy_applied: string;
    cluster_name?: string;
    pages_generated_count: number;
    generated_slugs: string[];
    total_project_pages: number;
    message: string;
  }> {
    return fetchJson(`${API_BASE}/projects/${projectId}/pages/generate-wave`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  // v0.4 Monitoring
  async getMonitoringDashboard(projectId: string): Promise<MonitoringDashboardData> {
    return fetchJson<MonitoringDashboardData>(`${API_BASE}/monitoring/${projectId}/dashboard`);
  },

  async syncMonitoring(projectId: string, daysBack: number = 30): Promise<MonitoringDashboardData> {
    return fetchJson<MonitoringDashboardData>(`${API_BASE}/monitoring/${projectId}/sync`, {
      method: "POST",
      body: JSON.stringify({ days_back: daysBack }),
    });
  },
};
