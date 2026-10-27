"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  ArrowLeft,
  Copy,
  Check,
  Code,
  Eye,
  Layers,
  HelpCircle,
  ExternalLink,
  ShieldCheck,
  Globe,
  FileText,
  ChevronDown,
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
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
  const [openFaqIndices, setOpenFaqIndices] = useState<Record<number, boolean>>({ 0: true });

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

  function toggleFaq(idx: number) {
    setOpenFaqIndices((prev) => ({ ...prev, [idx]: !prev[idx] }));
  }

  if (loading) {
    return <div className="py-20 text-center text-gray-500">Loading page details...</div>;
  }

  if (!page) {
    return <div className="py-20 text-center text-rose-500">Page not found.</div>;
  }

  // Strip YAML frontmatter from raw markdown content if present
  const cleanedMarkdown = page.markdown_content.replace(/^---[\s\S]*?---\n*/, "");

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
        <div className="space-y-6 max-w-4xl mx-auto">
          {/* SEO Metadata Card */}
          <div className="p-4 rounded-2xl bg-white border border-gray-200 shadow-sm text-xs space-y-1.5 font-mono text-gray-700">
            <div className="flex items-center space-x-2 pb-1 border-b border-gray-100 text-[11px] font-sans font-semibold text-gray-500 uppercase tracking-wider">
              <Globe className="w-3.5 h-3.5 text-blue-600" />
              <span>SEO Meta Tag Inspection</span>
            </div>
            <div className="pt-1"><strong className="text-gray-900 font-medium">Title:</strong> {page.title}</div>
            <div><strong className="text-gray-900 font-medium">Meta Description:</strong> {page.meta_description}</div>
            <div><strong className="text-gray-900 font-medium">Canonical URL:</strong> {page.canonical_url}</div>
            <div><strong className="text-gray-900 font-medium">Robots:</strong> {page.robots}</div>
          </div>

          {/* Browser Window Mockup with Pure White Background */}
          <div className="bg-white rounded-2xl border border-gray-200 shadow-lg overflow-hidden text-gray-900">
            {/* Browser chrome header bar */}
            <div className="px-4 py-3 bg-gray-50 border-b border-gray-200 flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <span className="w-3 h-3 rounded-full bg-red-400 inline-block" />
                <span className="w-3 h-3 rounded-full bg-yellow-400 inline-block" />
                <span className="w-3 h-3 rounded-full bg-green-400 inline-block" />
              </div>
              <div className="px-4 py-1 rounded-md bg-white border border-gray-200 text-xs font-mono text-gray-500 max-w-md w-full text-center truncate shadow-inner">
                {page.canonical_url}
              </div>
              <div className="w-12 text-right">
                <span className="inline-flex items-center text-[10px] uppercase font-bold px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-800">
                  Live
                </span>
              </div>
            </div>

            {/* Article Content on Pure White (#ffffff) Canvas */}
            <article className="p-8 sm:p-12 bg-white text-gray-900">
              <div className="prose prose-neutral max-w-none prose-headings:text-gray-900 prose-headings:font-bold prose-p:text-gray-700 prose-p:leading-relaxed prose-li:text-gray-700 prose-a:text-blue-600 prose-a:underline hover:prose-a:text-blue-800 prose-strong:text-gray-900">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={{
                    a: ({ href, children, ...props }) => {
                      if (href && href.startsWith("/")) {
                        return (
                          <Link
                            href={`/projects/${projectId}/pages${href.replace(/\/$/, "")}`}
                            className="text-blue-600 font-medium underline underline-offset-2 hover:text-blue-800 inline-flex items-center gap-0.5"
                            {...props}
                          >
                            <span>{children}</span>
                            <ExternalLink className="w-3 h-3 inline opacity-60" />
                          </Link>
                        );
                      }
                      return (
                        <a
                          href={href}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-600 font-medium underline underline-offset-2 hover:text-blue-800 inline-flex items-center gap-0.5"
                          {...props}
                        >
                          <span>{children}</span>
                          <ExternalLink className="w-3 h-3 inline opacity-60" />
                        </a>
                      );
                    },
                  }}
                >
                  {cleanedMarkdown}
                </ReactMarkdown>
              </div>

              {/* Verified Internal Links Section */}
              {page.internal_links && page.internal_links.length > 0 && (
                <div className="mt-12 pt-8 border-t border-gray-200">
                  <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
                    <FileText className="w-5 h-5 text-blue-600" />
                    <span>Related Articles & Recommended Guides</span>
                  </h3>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {page.internal_links.map((link, idx) => (
                      <Link
                        key={idx}
                        href={`/projects/${projectId}/pages/${link.target_slug}`}
                        className="p-3.5 rounded-xl border border-gray-200 hover:border-blue-400 hover:bg-blue-50/40 transition-all flex items-center justify-between group"
                      >
                        <div className="space-y-0.5 min-w-0 pr-2">
                          <span className="text-xs font-semibold text-gray-900 group-hover:text-blue-600 block truncate">
                            {link.anchor_text || link.target_slug}
                          </span>
                          <span className="text-[11px] font-mono text-gray-400 block truncate">
                            {link.target_url}
                          </span>
                        </div>
                        <ExternalLink className="w-4 h-4 text-gray-400 group-hover:text-blue-600 shrink-0" />
                      </Link>
                    ))}
                  </div>
                </div>
              )}

              {/* FAQs Accordion embedded directly in the page preview */}
              {page.faqs && page.faqs.length > 0 && (
                <div className="mt-12 pt-8 border-t border-gray-200">
                  <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
                    <HelpCircle className="w-5 h-5 text-indigo-600" />
                    <span>Frequently Asked Questions</span>
                  </h3>
                  <div className="space-y-3">
                    {page.faqs.map((faq, idx) => {
                      const isOpen = !!openFaqIndices[idx];
                      return (
                        <div
                          key={idx}
                          className="rounded-xl border border-gray-200 bg-gray-50/50 overflow-hidden transition-all"
                        >
                          <button
                            type="button"
                            onClick={() => toggleFaq(idx)}
                            className="w-full p-4 text-left flex items-center justify-between gap-4 font-semibold text-sm text-gray-900 hover:bg-gray-100/50 transition-colors"
                          >
                            <span>{faq.question}</span>
                            <ChevronDown
                              className={`w-4 h-4 text-gray-500 transition-transform duration-200 shrink-0 ${
                                isOpen ? "rotate-180" : ""
                              }`}
                            />
                          </button>
                          {isOpen && (
                            <div className="px-4 pb-4 pt-1 text-xs text-gray-600 leading-relaxed border-t border-gray-200/50 bg-white">
                              {faq.answer}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </article>
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
              className="bg-white rounded-2xl p-5 border border-gray-200 shadow-sm space-y-2"
            >
              <h3 className="font-bold text-sm text-gray-900">{faq.question}</h3>
              <p className="text-xs text-gray-600 leading-relaxed">{faq.answer}</p>
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
