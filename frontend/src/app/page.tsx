"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Sparkles, ArrowRight, Layers, FileText, Activity, ShieldCheck } from "lucide-react";
import { api } from "@/lib/api";
import { Project } from "@/lib/types";
import StatusBadge from "@/components/StatusBadge";

export default function HomePage() {
  const router = useRouter();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({
    name: "",
    raw_description: "",
    target_audience: "",
    target_domain: "https://example.com",
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        setLoading(true);
        const data = await api.getProjects();
        setProjects(data);
      } catch (err: any) {
        console.error("Failed to load projects:", err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  async function handleCreateProject(e: React.FormEvent) {
    e.preventDefault();
    if (!form.raw_description.trim()) {
      setError("Please describe your website idea or problem statement.");
      return;
    }

    try {
      setSubmitting(true);
      setError(null);
      const newProj = await api.createProject(form);
      // Navigate to the live pipeline page to trigger generation
      router.push(`/projects/${newProj.id}/pipeline`);
    } catch (err: any) {
      setError(err.message || "Failed to create project");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-12">
      {/* Hero & Submission Form */}
      <section className="bg-gradient-to-br from-white to-blue-50/50 dark:from-gray-900 dark:to-gray-800/40 rounded-3xl p-8 sm:p-12 border border-gray-200 dark:border-gray-800 shadow-sm">
        <div className="max-w-3xl">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full text-xs font-semibold bg-blue-100 text-blue-800 dark:bg-blue-900/50 dark:text-blue-300 mb-4">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Autonomous SEO Pipeline (v0.1 — v0.4)</span>
          </div>
          <h1 className="text-3xl sm:text-5xl font-black tracking-tight text-gray-900 dark:text-white leading-tight">
            Turn your website idea into ranked, publication-ready pages.
          </h1>
          <p className="mt-4 text-base sm:text-lg text-gray-600 dark:text-gray-300 leading-relaxed">
            Enter your niche or problem statement. The agent handles keyword discovery, cluster architecture, first-wave content generation, and Google Search Console indexing surveillance.
          </p>

          <form onSubmit={handleCreateProject} className="mt-8 space-y-4">
            <div>
              <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                What is your website idea or problem statement? *
              </label>
              <textarea
                required
                rows={3}
                placeholder="e.g. A fashion tech platform providing AI virtual try-on tools, clothing design apps, and shopping comparison guides for online fashion shoppers..."
                value={form.raw_description}
                onChange={(e) => setForm({ ...form, raw_description: e.target.value })}
                className="w-full px-4 py-3 rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all shadow-sm"
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
                  Target Domain (Canonical)
                </label>
                <input
                  type="text"
                  placeholder="https://mysite.com"
                  value={form.target_domain}
                  onChange={(e) => setForm({ ...form, target_domain: e.target.value })}
                  className="w-full px-3.5 py-2.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
                  Target Audience / Customer Persona
                </label>
                <input
                  type="text"
                  placeholder="e.g. Online shoppers & fashion creators"
                  value={form.target_audience}
                  onChange={(e) => setForm({ ...form, target_audience: e.target.value })}
                  className="w-full px-3.5 py-2.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm"
                />
              </div>
            </div>

            {error && (
              <div className="p-3 rounded-lg bg-rose-50 text-rose-700 text-sm border border-rose-200">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={submitting}
              className="inline-flex items-center space-x-2 px-6 py-3.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-base shadow-md shadow-blue-500/20 transition-all hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50"
            >
              <Sparkles className="w-4 h-4" />
              <span>{submitting ? "Initializing Project..." : "Launch Autonomous Pipeline"}</span>
              <ArrowRight className="w-4 h-4 ml-1" />
            </button>
          </form>
        </div>
      </section>

      {/* Existing Projects Section */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">Active Projects</h2>
          <span className="text-sm text-gray-500">{projects.length} Total</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {projects.map((proj) => (
            <div
              key={proj.id}
              className="bg-white dark:bg-gray-900 rounded-2xl p-6 border border-gray-200 dark:border-gray-800 shadow-sm hover:shadow-md transition-all flex flex-col justify-between space-y-4"
            >
              <div>
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-mono text-gray-400">#{proj.id}</span>
                  <StatusBadge status={proj.status} />
                </div>
                <h3 className="font-bold text-lg text-gray-900 dark:text-white group-hover:text-blue-600 line-clamp-1">
                  {proj.name}
                </h3>
                <p className="mt-2 text-sm text-gray-600 dark:text-gray-400 line-clamp-2">
                  {proj.raw_description}
                </p>
              </div>

              <div className="pt-4 border-t border-gray-100 dark:border-gray-800 flex items-center justify-between text-xs text-gray-500">
                <span>{proj.pages_count} Pages</span>
                <span>{proj.health_score}/100 Health</span>
                <Link
                  href={`/projects/${proj.id}/pages`}
                  className="font-semibold text-blue-600 hover:text-blue-700 flex items-center space-x-1"
                >
                  <span>Explore</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
