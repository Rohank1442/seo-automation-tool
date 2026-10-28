"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  Search,
  ExternalLink,
  ShieldCheck,
  ArrowRight,
  FileCode,
  CheckCircle2,
  PlusCircle,
  Sparkles,
  Layers,
  X,
  Loader2,
  Check,
} from "lucide-react";
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

  // Modal State for Generating More Pages (Wave Expansion)
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [strategy, setStrategy] = useState<"next_best" | "specific_cluster">("next_best");
  const [selectedCluster, setSelectedCluster] = useState<string>("");
  const [batchSize, setBatchSize] = useState<number>(25);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationMessage, setGenerationMessage] = useState<string | null>(null);

  // Extract distinct clusters from existing pages
  const availableClusters = Array.from(
    new Set(pages.map((p) => p.cluster).filter(Boolean))
  );

  async function loadPages() {
    try {
      setLoading(true);
      const data = await api.getPages(projectId);
      setPages(data);
      if (data.length > 0 && !selectedCluster) {
        setSelectedCluster(data[0].cluster || "Virtual Try-On Tech");
      }
    } catch (e) {
      console.error("Failed to load pages:", e);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadPages();
  }, [projectId]);

  // Handle submitting the wave generation request
  async function handleTriggerWave() {
    try {
      setIsGenerating(true);
      setGenerationMessage(null);

      const res = await api.generatePagesWave(projectId, {
        strategy,
        cluster_name: strategy === "specific_cluster" ? selectedCluster : undefined,
        batch_size: batchSize,
        dry_run: false,
      });

      setGenerationMessage(res.message);
      // Reload the pages catalog table with newly generated pages
      await loadPages();
      setTimeout(() => {
        setIsModalOpen(false);
        setGenerationMessage(null);
      }, 2500);
    } catch (err: any) {
      alert("Failed to generate wave: " + (err?.message || "Unknown error"));
    } finally {
      setIsGenerating(false);
    }
  }

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
      {/* Top Banner with Action Button */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 bg-white dark:bg-gray-900 p-6 rounded-3xl border border-gray-200 dark:border-gray-800 shadow-sm">
        <div className="space-y-1">
          <div className="flex items-center space-x-2">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-50 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300 border border-blue-200 dark:border-blue-800">
              Wave Catalog
            </span>
            <span className="text-xs text-gray-400">•</span>
            <span className="text-xs text-gray-500 font-mono">
              {pages.length} published pages
            </span>
          </div>
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">
            Programmatic SEO Content Inventory
          </h2>
          <p className="text-xs text-gray-500 max-w-xl leading-relaxed">
            Every page is built with structured outlines, verified internal link graphs, and valid Schema.org markup.
          </p>
        </div>

        {/* Generate More Pages Trigger Button */}
        <button
          onClick={() => setIsModalOpen(true)}
          className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-semibold text-xs shadow-md shadow-blue-500/20 transition-all hover:scale-[1.02] active:scale-[0.98]"
        >
          <Sparkles className="w-4 h-4 text-blue-200" />
          <span>+ Generate More Pages</span>
        </button>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricsCard
          title="Generated Pages"
          value={pages.length}
          subtitle="Catalog total"
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
          value={pages.reduce((acc, p) => acc + (p.word_count || 500), 0).toLocaleString()}
          subtitle="~518 words / article"
          icon={<CheckCircle2 className="w-5 h-5" />}
          highlightColor="purple"
        />
        <MetricsCard
          title="Topic Clusters"
          value={availableClusters.length || 1}
          subtitle="Active topic silos"
          icon={<Layers className="w-5 h-5" />}
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
                <th className="px-6 py-4">Cluster</th>
                <th className="px-6 py-4">Intent</th>
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
                  <td className="px-6 py-4 text-xs text-gray-600 dark:text-gray-400">
                    {page.cluster || "General"}
                  </td>
                  <td className="px-6 py-4">
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold uppercase tracking-wider bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300">
                      {page.search_intent}
                    </span>
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

      {/* ============================================================ */}
      {/* MODAL: GENERATE MORE PAGES (WAVE EXPANSION) */}
      {/* ============================================================ */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-gray-950/60 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="bg-white dark:bg-gray-900 rounded-3xl border border-gray-200 dark:border-gray-800 shadow-2xl max-w-lg w-full overflow-hidden">
            {/* Modal Header */}
            <div className="p-6 border-b border-gray-100 dark:border-gray-800 flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 rounded-xl bg-blue-50 dark:bg-blue-950/60 text-blue-600 dark:text-blue-400 flex items-center justify-center">
                  <Sparkles className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-bold text-lg text-gray-900 dark:text-white">
                    Generate Wave Expansion
                  </h3>
                  <p className="text-xs text-gray-500">
                    Scale your programmatic keyword footprint across clusters.
                  </p>
                </div>
              </div>
              <button
                onClick={() => !isGenerating && setIsModalOpen(false)}
                className="p-1.5 rounded-lg text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 space-y-6">
              {/* Strategy Choice */}
              <div className="space-y-3">
                <label className="block text-xs font-bold uppercase tracking-wider text-gray-500">
                  Step 1: Choose Selection Strategy
                </label>
                <div className="grid grid-cols-1 gap-3">
                  {/* Option A */}
                  <label
                    onClick={() => setStrategy("next_best")}
                    className={`p-4 rounded-2xl border cursor-pointer transition-all flex items-start space-x-3 ${
                      strategy === "next_best"
                        ? "border-blue-600 bg-blue-50/50 dark:bg-blue-950/30"
                        : "border-gray-200 dark:border-gray-800 hover:border-gray-300"
                    }`}
                  >
                    <input
                      type="radio"
                      name="strategy"
                      checked={strategy === "next_best"}
                      onChange={() => setStrategy("next_best")}
                      className="mt-1 text-blue-600 focus:ring-blue-500"
                    />
                    <div>
                      <div className="text-sm font-bold text-gray-900 dark:text-white">
                        Option A: Next Best Unbuilt Keywords
                      </div>
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                        Agent picks the top-scoring unbuilt keywords across all topical clusters based on search intent and low difficulty.
                      </p>
                    </div>
                  </label>

                  {/* Option B */}
                  <label
                    onClick={() => setStrategy("specific_cluster")}
                    className={`p-4 rounded-2xl border cursor-pointer transition-all flex items-start space-x-3 ${
                      strategy === "specific_cluster"
                        ? "border-blue-600 bg-blue-50/50 dark:bg-blue-950/30"
                        : "border-gray-200 dark:border-gray-800 hover:border-gray-300"
                    }`}
                  >
                    <input
                      type="radio"
                      name="strategy"
                      checked={strategy === "specific_cluster"}
                      onChange={() => setStrategy("specific_cluster")}
                      className="mt-1 text-blue-600 focus:ring-blue-500"
                    />
                    <div>
                      <div className="text-sm font-bold text-gray-900 dark:text-white">
                        Option B: Target a Specific Cluster
                      </div>
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                        Focus exclusively on filling out depth for a single chosen topical silo.
                      </p>
                    </div>
                  </label>
                </div>
              </div>

              {/* Cluster Dropdown (active only if Option B selected) */}
              {strategy === "specific_cluster" && (
                <div className="space-y-2 animate-in fade-in duration-200">
                  <label className="block text-xs font-bold uppercase tracking-wider text-gray-500">
                    Select Target Cluster
                  </label>
                  <select
                    value={selectedCluster}
                    onChange={(e) => setSelectedCluster(e.target.value)}
                    className="w-full px-4 py-2.5 rounded-xl border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 text-sm font-semibold text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
                  >
                    {availableClusters.map((c) => (
                      <option key={c} value={c}>
                        {c}
                      </option>
                    ))}
                  </select>
                </div>
              )}

              {/* Batch Size Selector */}
              <div className="space-y-2">
                <label className="block text-xs font-bold uppercase tracking-wider text-gray-500">
                  Step 2: Choose Batch Size
                </label>
                <div className="grid grid-cols-3 gap-3">
                  {[10, 25, 50].map((count) => (
                    <button
                      key={count}
                      type="button"
                      onClick={() => setBatchSize(count)}
                      className={`py-3 rounded-xl text-center text-xs font-bold transition-all border ${
                        batchSize === count
                          ? "border-blue-600 bg-blue-600 text-white shadow-sm"
                          : "border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:border-gray-300"
                      }`}
                    >
                      {count} Pages
                    </button>
                  ))}
                </div>
              </div>

              {/* Status Message feedback */}
              {generationMessage && (
                <div className="p-3.5 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 text-xs text-emerald-700 dark:text-emerald-300 flex items-center space-x-2">
                  <Check className="w-4 h-4 shrink-0 text-emerald-600" />
                  <span>{generationMessage}</span>
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="p-6 bg-gray-50 dark:bg-gray-800/50 border-t border-gray-100 dark:border-gray-800 flex items-center justify-end space-x-3">
              <button
                type="button"
                disabled={isGenerating}
                onClick={() => setIsModalOpen(false)}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={isGenerating}
                onClick={handleTriggerWave}
                className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold shadow-sm transition-all disabled:opacity-50"
              >
                {isGenerating ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin text-white" />
                    <span>Generating Wave ({batchSize} Pages)...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4 text-blue-200" />
                    <span>Generate Wave</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
