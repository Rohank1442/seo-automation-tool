import {
  MonitoringDashboardData,
  PageDetail,
  PageSummary,
  Project,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1";

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers || {}),
    },
  });
  if (!res.ok) {
    const errorText = await res.text();
    throw new Error(`API Error ${res.status}: ${errorText}`);
  }
  return res.json();
}

export const api = {
  // Projects
  async getProjects(): Promise<Project[]> {
    return fetchJson<Project[]>(`${API_BASE}/projects`);
  },

  async getProject(id: string): Promise<Project> {
    return fetchJson<Project>(`${API_BASE}/projects/${id}`);
  },

  async createProject(data: {
    raw_description: string;
    name?: string;
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
