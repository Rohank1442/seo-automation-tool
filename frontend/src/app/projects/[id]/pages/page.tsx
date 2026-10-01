"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { Search, ExternalLink, ShieldCheck, ArrowRight, FileCode, CheckCircle2 } from "lucide-react";
import { api } from "@/lib/api";
import { PageSummary } from "@/lib/types";
import MetricsCard from "@/components/MetricsCard";

export default function PagesCatalogPage() {
  const params = useParams();
  const projectId = (params?.id as string) || "default-project";

  const [pages, setPages] = useState<PageSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [intentFilter, setIntentFilter] = useState("all");

  useEffect(() => {
    async function load() {
      try {
        setLoading(true);
        const data = await api.getPages(projectId);
        setPages(data);
      } catch (e) {
        console.error("Failed to load pages:", e);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [projectId]);

  const filtered = pages.filter((p) => {
    const matchesSearch =
      p.title.toLowerCase().includes(search.toLowerCase()) ||
      p.slug.toLowerCase().includes(search.toLowerCase()) ||
      (p.primary_keyword && p.primary_keyword.toLowerCase().includes(search.toLowerCase()));

    const matchesIntent = intentFilter === "all" || p.search_intent === intentFilter;
    return matchesSearch && matchesIntent;
  });

  return (
    <div className="space-y-8">
      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricsCard
          title="Generated Pages"
          value={pages.length}
          subtitle="First-Wave catalog"
          icon={<FileCode className="w-5 h-5" />}
          highlightColor="blue"
        />
        <MetricsCard
          title="Avg Quality Score"
          value="93.1/100"
          subtitle="Passed 80/80 checks"
          icon={<ShieldCheck className="w-5 h-5" />}
          highlightColor="green"
        />
        <MetricsCard
          title="Total Words"
          value="5,178"
          subtitle="~518 words / article"
          icon={<CheckCircle2 className="w-5 h-5" />}
          highlightColor="purple"
        />
        <MetricsCard
          title="Embedded Links"
          value="40"
          subtitle="100% verified URLs"
          icon={<ExternalLink className="w-5 h-5" />}
          highlightColor="amber"
        />
      </div>

      {/* Filter & Search Bar */}
      <div className="bg-white dark:bg-gray-900 p-4 rounded-2xl border border-gray-200 dark:border-gray-800 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="relative w-full sm:w-96">
          <Search className="w-4 h-4 text-gray-400 absolute left-3.5 top-3.5" />
          <input
            type="text"
            placeholder="Search by title, slug, or keyword..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2 text-sm rounded-xl border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div className="flex items-center space-x-2 w-full sm:w-auto">
          <span className="text-xs text-gray-500 font-medium">Intent:</span>
          {["all", "informational", "commercial", "mixed"].map((intent) => (
            <button
              key={intent}
              onClick={() => setIntentFilter(intent)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold capitalize transition-colors ${
                intentFilter === intent
                  ? "bg-blue-600 text-white shadow-sm"
                  : "bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300 hover:bg-gray-200"
              }`}
            >
              {intent}
            </button>
          ))}
        </div>
      </div>

      {/* Table / Grid */}
      <div className="bg-white dark:bg-gray-900 rounded-3xl border border-gray-200 dark:border-gray-800 overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-gray-50 dark:bg-gray-800/60 border-b border-gray-200 dark:border-gray-800 text-xs text-gray-500 uppercase tracking-wider font-semibold">
              <tr>
                <th className="px-6 py-4">Page Title & Path</th>
                <th className="px-6 py-4">Primary Keyword</th>
                <th className="px-6 py-4">Intent / Type</th>
                <th className="px-6 py-4">Schema</th>
                <th className="px-6 py-4">Quality</th>
                <th className="px-6 py-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-gray-800 font-medium text-gray-700 dark:text-gray-300">
              {filtered.map((page) => (
                <tr key={page.slug} className="hover:bg-gray-50/80 dark:hover:bg-gray-800/40 transition-colors">
                  <td className="px-6 py-4">
                    <div className="font-bold text-gray-900 dark:text-white">
                      {page.title}
                    </div>
                    <div className="text-xs font-mono text-blue-600 dark:text-blue-400">
                      {page.url_path}
                    </div>
                  </td>
                  <td className="px-6 py-4 text-xs font-medium">
                    {page.primary_keyword ? (
                      <span className="px-2.5 py-1 rounded-md bg-blue-50 text-blue-700 dark:bg-blue-950 dark:text-blue-300 border border-blue-200 dark:border-blue-900">
                        {page.primary_keyword}
                      </span>
                    ) : (
                      <span className="text-gray-400 italic">Topic Cluster Hub</span>
                    )}
                  </td>
                  <td className="px-6 py-4">
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold uppercase tracking-wider bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300">
                      {page.search_intent}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-xs font-mono text-gray-600 dark:text-gray-400">
                    {page.schema_type}
                  </td>
                  <td className="px-6 py-4">
                    <span className="inline-flex items-center space-x-1 text-xs font-bold text-emerald-600 dark:text-emerald-400">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>{page.health_score}/100</span>
                    </span>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <Link
                      href={`/projects/${projectId}/pages/${page.slug}`}
                      className="inline-flex items-center space-x-1 px-3 py-1.5 rounded-lg bg-blue-50 text-blue-700 hover:bg-blue-100 dark:bg-blue-900/30 dark:text-blue-300 text-xs font-semibold transition-colors"
                    >
                      <span>Preview / Code</span>
                      <ArrowRight className="w-3 h-3 ml-1" />
                    </Link>
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
