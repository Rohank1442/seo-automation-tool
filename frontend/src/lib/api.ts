import {
  MonitoringDashboardData,
  PageDetail,
  PageSummary,
  Project,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1";

export function getStoredToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("seo_access_token");
}

export function setStoredToken(token: string): void {
  if (typeof window === "undefined") return;
  localStorage.setItem("seo_access_token", token);
  // Also store in document.cookie for immediate Next.js middleware recognition
  document.cookie = `access_token=${encodeURIComponent(token)}; path=/; max-age=604800; SameSite=Lax`;
  document.cookie = `seo_access_token=${encodeURIComponent(token)}; path=/; max-age=604800; SameSite=Lax`;
}

export function clearStoredToken(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem("seo_access_token");
  document.cookie = "access_token=; path=/; max-age=0; SameSite=Lax";
  document.cookie = "seo_access_token=; path=/; max-age=0; SameSite=Lax";
}

async function fetchJson<T>(
  url: string,
  options?: RequestInit,
  authenticated: boolean = true,
): Promise<T> {
  const headers = new Headers(options?.headers);
  if (!headers.has("Content-Type")) headers.set("Content-Type", "application/json");

  if (authenticated) {
    const token = getStoredToken();
    if (token) {
      headers.set("Authorization", `Bearer ${token}`);
    }
  }

  const res = await fetch(url, {
    ...options,
    headers,
    credentials: "include", // Ensure session cookies are sent/received
  });

  if (!res.ok) {
    let errorDetail = `API Error ${res.status}`;
    try {
      const data = await res.json();
      if (data?.detail) {
        errorDetail = typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail);
      }
    } catch {
      const text = await res.text().catch(() => "");
      if (text) errorDetail = text;
    }
    const error = new Error(errorDetail);
    (error as any).status = res.status;
    throw error;
  }
  return res.json();
}

export const api = {
  // Authentication
  async signUp(data: { email: string; password: string; full_name?: string }): Promise<{
    access_token: string;
    token_type: string;
    user: { id: string; email: string; full_name?: string };
  }> {
    const res = await fetchJson<{
      access_token: string;
      token_type: string;
      user: { id: string; email: string; full_name?: string };
    }>(`${API_BASE}/auth/sign-up`, {
      method: "POST",
      body: JSON.stringify(data),
    }, false);

    if (res?.access_token) {
      setStoredToken(res.access_token);
    }
    return res;
  },

  async signIn(data: { email: string; password: string }): Promise<{
    access_token: string;
    token_type: string;
    user: { id: string; email: string; full_name?: string };
  }> {
    const res = await fetchJson<{
      access_token: string;
      token_type: string;
      user: { id: string; email: string; full_name?: string };
    }>(`${API_BASE}/auth/sign-in`, {
      method: "POST",
      body: JSON.stringify(data),
    }, false);

    if (res?.access_token) {
      setStoredToken(res.access_token);
    }
    return res;
  },

  async signOut(): Promise<void> {
    try {
      await fetchJson(`${API_BASE}/auth/sign-out`, { method: "POST" }, false);
    } catch {
      // Ignore network errors on signout
    } finally {
      clearStoredToken();
    }
  },

  async getMe(): Promise<{ id: string; email: string; full_name?: string }> {
    return fetchJson(`${API_BASE}/auth/me`);
  },

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
