"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft, Copy, Check, Code, Eye, Layers, HelpCircle, ExternalLink, ShieldCheck } from "lucide-react";
import { api } from "@/lib/api";
import { PageDetail } from "@/lib/types";

export default function PageDetailPage() {
  const params = useParams();
  const projectId = (params?.id as string) || "default-project";
  const slug = params?.slug as string;

  const [page, setPage] = useState<PageDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<"preview" | "code" | "schema" | "faqs">("preview");
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        setLoading(true);
        const data = await api.getPageDetail(projectId, slug);
        setPage(data);
      } catch (e) {
        console.error("Failed to load page detail:", e);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [projectId, slug]);

  function handleCopy() {
    if (!page) return;
    navigator.clipboard.writeText(page.nextjs_jsx_code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  if (loading) {
    return <div className="py-20 text-center text-gray-500">Loading page details...</div>;
  }

  if (!page) {
    return <div className="py-20 text-center text-rose-500">Page not found.</div>;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-gray-200 dark:border-gray-800">
        <div className="space-y-1">
          <Link
            href={`/projects/${projectId}/pages`}
            className="inline-flex items-center space-x-1 text-xs font-semibold text-blue-600 hover:underline mb-1"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to Pages Catalog</span>
          </Link>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">{page.title}</h1>
          <div className="flex items-center space-x-2 text-xs text-gray-500">
            <span className="font-mono text-blue-600 dark:text-blue-400">{page.url_path}</span>
            <span>•</span>
            <span>{page.word_count} words</span>
            <span>•</span>
            <span className="font-semibold text-emerald-600">Audit {page.health_score}/100</span>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={handleCopy}
            className="inline-flex items-center space-x-2 px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold shadow-sm transition-all"
          >
            {copied ? <Check className="w-4 h-4 text-emerald-300" /> : <Copy className="w-4 h-4" />}
            <span>{copied ? "Copied Next.js Code!" : "Copy Next.js Component"}</span>
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex space-x-2 border-b border-gray-200 dark:border-gray-800">
        {[
          { key: "preview", label: "Rendered Preview", icon: Eye },
          { key: "code", label: "Next.js (.tsx) Component", icon: Code },
          { key: "faqs", label: `FAQs (${page.faqs.length})`, icon: HelpCircle },
          { key: "schema", label: "Schema.org JSON-LD", icon: Layers },
        ].map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            onClick={() => setTab(key as any)}
            className={`flex items-center space-x-2 px-4 py-2 border-b-2 text-xs font-semibold transition-all ${
              tab === key
                ? "border-blue-600 text-blue-600 font-bold"
                : "border-transparent text-gray-500 hover:text-gray-700"
            }`}
          >
            <Icon className="w-3.5 h-3.5" />
            <span>{label}</span>
          </button>
        ))}
      </div>

      {/* Tab Panels */}
      {tab === "preview" && (
        <div className="bg-white dark:bg-gray-900 rounded-3xl p-8 border border-gray-200 dark:border-gray-800 shadow-sm max-w-4xl mx-auto space-y-6">
          <div className="p-4 rounded-xl bg-gray-50 dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700 text-xs space-y-1 font-mono">
            <div><strong className="text-gray-700 dark:text-gray-300">SEO Title:</strong> {page.title}</div>
            <div><strong className="text-gray-700 dark:text-gray-300">Meta Description:</strong> {page.meta_description}</div>
            <div><strong className="text-gray-700 dark:text-gray-300">Canonical:</strong> {page.canonical_url}</div>
          </div>

          <div className="prose prose-blue dark:prose-invert max-w-none">
            <h1 className="text-3xl font-extrabold">{page.h1}</h1>
            <div className="whitespace-pre-wrap leading-relaxed text-gray-700 dark:text-gray-300">
              {page.markdown_content.replace(/^---[\s\S]*?---\n*/, "")}
            </div>
          </div>
        </div>
      )}

      {tab === "code" && (
        <div className="bg-gray-950 rounded-3xl p-6 border border-gray-800 shadow-xl space-y-4">
          <div className="flex items-center justify-between text-xs text-gray-400 pb-3 border-b border-gray-800">
            <span className="font-mono text-blue-400">app/{slug}/page.tsx</span>
            <button
              onClick={handleCopy}
              className="text-xs font-semibold text-gray-300 hover:text-white flex items-center space-x-1"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copied ? "Copied" : "Copy Code"}</span>
            </button>
          </div>
          <pre className="overflow-x-auto text-xs font-mono text-gray-300 p-2 leading-relaxed">
            {page.nextjs_jsx_code}
          </pre>
        </div>
      )}

      {tab === "faqs" && (
        <div className="space-y-4 max-w-3xl">
          {page.faqs.map((faq, idx) => (
            <div
              key={idx}
              className="bg-white dark:bg-gray-900 rounded-2xl p-5 border border-gray-200 dark:border-gray-800 space-y-2"
            >
              <h3 className="font-bold text-sm text-gray-900 dark:text-white">{faq.question}</h3>
              <p className="text-xs text-gray-600 dark:text-gray-300 leading-relaxed">{faq.answer}</p>
            </div>
          ))}
        </div>
      )}

      {tab === "schema" && (
        <div className="bg-gray-950 rounded-3xl p-6 border border-gray-800 shadow-xl space-y-3 font-mono text-xs text-gray-300">
          <pre className="overflow-x-auto p-2">
            {JSON.stringify(page.schema_json_ld, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}
