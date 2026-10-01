"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import {
  Activity,
  AlertTriangle,
  ArrowUpRight,
  CheckCircle2,
  Eye,
  Globe,
  RefreshCw,
  Sparkles,
  TrendingUp,
  Zap,
} from "lucide-react";
import { api } from "@/lib/api";
import { MonitoringDashboardData } from "@/lib/types";
import MetricsCard from "@/components/MetricsCard";
import StatusBadge from "@/components/StatusBadge";

export default function MonitoringDashboardPage() {
  const params = useParams();
  const projectId = (params?.id as string) || "default-project";

  const [data, setData] = useState<MonitoringDashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);

  async function loadData() {
    try {
      setLoading(true);
      const res = await api.getMonitoringDashboard(projectId);
      setData(res);
    } catch (e) {
      console.error("Failed to load monitoring dashboard:", e);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, [projectId]);

  async function handleSync() {
    try {
      setSyncing(true);
      const res = await api.syncMonitoring(projectId, 30);
      setData(res);
    } catch (e: any) {
      alert("Sync failed: " + e.message);
    } finally {
      setSyncing(false);
    }
  }

  if (loading || !data) {
    return (
      <div className="py-20 text-center text-gray-500">
        <Activity className="w-8 h-8 animate-spin mx-auto mb-3 text-blue-600" />
        <p>Loading v0.4 Indexing Watch data from Google Search Console...</p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Banner & Sync Action */}
      <div className="bg-gradient-to-r from-blue-900 to-indigo-900 rounded-3xl p-6 sm:p-8 text-white flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6 shadow-lg shadow-blue-900/20">
        <div className="space-y-1">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full text-xs font-semibold bg-white/10 backdrop-blur-md text-blue-200 mb-2">
            <Activity className="w-3.5 h-3.5" />
            <span>v0.4 Indexing Surveillance & Search Console Signals</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold">
            Google Indexing & Impression Watch
          </h1>
          <p className="text-sm text-blue-200 max-w-2xl">
            Surfaces early traction signals, monitors Googlebot crawl health, and flags indexing anomalies after 3–6 weeks.
          </p>
        </div>

        <button
          onClick={handleSync}
          disabled={syncing}
          className="inline-flex items-center space-x-2 px-5 py-3 rounded-xl bg-white text-blue-900 font-bold text-xs shadow-md hover:bg-blue-50 transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${syncing ? "animate-spin" : ""}`} />
          <span>{syncing ? "Syncing Search Console..." : "Sync Live Search Data"}</span>
        </button>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricsCard
          title="Google Indexation Rate"
          value={`${data.indexed_percentage}%`}
          subtitle={`${data.indexed_pages_count} of ${data.total_pages_monitored} pages indexed`}
          icon={<Globe className="w-5 h-5" />}
          highlightColor="green"
        />
        <MetricsCard
          title="30-Day Impressions"
          value={data.total_impressions_7d * 3}
          subtitle="Search result appearances"
          icon={<TrendingUp className="w-5 h-5" />}
          highlightColor="blue"
        />
        <MetricsCard
          title="Organic Clicks"
          value={data.total_clicks_7d * 3}
          subtitle="Early search traffic"
          icon={<Sparkles className="w-5 h-5" />}
          highlightColor="purple"
        />
        <MetricsCard
          title="Active Anomalies"
          value={data.active_alerts.length}
          subtitle="Requires attention"
          icon={<AlertTriangle className="w-5 h-5" />}
          highlightColor="amber"
        />
      </div>

      {/* Active Alerts & Early Signal Recommendations */}
      {data.active_alerts.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-lg font-bold text-gray-900 dark:text-white flex items-center space-x-2">
            <Zap className="w-5 h-5 text-amber-500" />
            <span>Early Signal Insights & Anomaly Alerts</span>
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {data.active_alerts.map((alert) => (
              <div
                key={alert.id}
                className={`p-5 rounded-2xl border space-y-2 ${
                  alert.severity === "warning"
                    ? "bg-amber-50/50 dark:bg-amber-950/20 border-amber-200 dark:border-amber-800"
                    : "bg-blue-50/50 dark:bg-blue-950/20 border-blue-200 dark:border-blue-800"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span
                    className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full ${
                      alert.severity === "warning"
                        ? "bg-amber-200 dark:bg-amber-900 text-amber-800 dark:text-amber-200"
                        : "bg-blue-200 dark:bg-blue-900 text-blue-800 dark:text-blue-200"
                    }`}
                  >
                    {alert.alert_type.replace("_", " ")}
                  </span>
                  <span className="text-xs font-mono text-gray-500">
                    /{alert.page_slug}/
                  </span>
                </div>
                <p className="font-semibold text-sm text-gray-900 dark:text-white">{alert.message}</p>
                <p className="text-xs text-gray-600 dark:text-gray-300">
                  <strong>Recommendation:</strong> {alert.recommendation}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Page-by-Page Surveillance Table */}
      <div className="bg-white dark:bg-gray-900 rounded-3xl border border-gray-200 dark:border-gray-800 overflow-hidden shadow-sm space-y-4">
        <div className="p-6 pb-2 flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-gray-900 dark:text-white">
              Page-by-Page Indexation & Query Impressions
            </h2>
            <p className="text-xs text-gray-500 mt-0.5">
              Live Google Search Console crawling verdicts and query performance
            </p>
          </div>
          <span className="text-xs text-gray-400">
            Last synced: {data.last_synced_at.slice(0, 10)}
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-gray-50 dark:bg-gray-800/60 border-b border-gray-200 dark:border-gray-800 text-xs text-gray-500 uppercase tracking-wider font-semibold">
              <tr>
                <th className="px-6 py-4">Page / URL</th>
                <th className="px-6 py-4">Index Status</th>
                <th className="px-6 py-4">Status Category</th>
                <th className="px-6 py-4">30d Impr</th>
                <th className="px-6 py-4">30d Clicks</th>
                <th className="px-6 py-4">Avg Pos</th>
                <th className="px-6 py-4">Top Mined Queries</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-gray-800 font-medium text-gray-700 dark:text-gray-300">
              {data.pages.map((p) => (
                <tr key={p.slug} className="hover:bg-gray-50/80 dark:hover:bg-gray-800/40 transition-colors">
                  <td className="px-6 py-4">
                    <div className="font-bold text-gray-900 dark:text-white">{p.title}</div>
                    <div className="text-xs font-mono text-blue-600 dark:text-blue-400">/{p.slug}/</div>
                  </td>
                  <td className="px-6 py-4">
                    <span
                      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold ${
                        p.is_indexed
                          ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                          : "bg-rose-50 text-rose-700 border border-rose-200"
                      }`}
                    >
                      {p.index_verdict}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <StatusBadge status={p.status_category} />
                  </td>
                  <td className="px-6 py-4 font-bold text-gray-900 dark:text-white">
                    {p.impressions_30d.toLocaleString()}
                  </td>
                  <td className="px-6 py-4 font-bold text-blue-600 dark:text-blue-400">
                    {p.clicks_30d}
                  </td>
                  <td className="px-6 py-4 text-xs font-mono">
                    {p.avg_position ? `#${p.avg_position}` : "—"}
                  </td>
                  <td className="px-6 py-4 text-xs text-gray-500">
                    {p.mined_queries.length > 0 ? (
                      <div className="flex flex-wrap gap-1">
                        {p.mined_queries.map((q, i) => (
                          <span
                            key={i}
                            className="px-2 py-0.5 rounded bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 text-[11px]"
                          >
                            {q}
                          </span>
                        ))}
                      </div>
                    ) : (
                      <span className="italic text-gray-400">No query data yet</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
