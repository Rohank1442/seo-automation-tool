"use client";

import Link from "next/link";
import { usePathname, useParams } from "next/navigation";
import { PlayCircle, FileText, Activity, ShieldCheck, ArrowLeft, Download } from "lucide-react";
import { useState } from "react";
import { api } from "@/lib/api";

export default function ProjectLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const params = useParams();
  const projectId = (params?.id as string) || "default-project";
  const [exporting, setExporting] = useState(false);
  const [exportMsg, setExportMsg] = useState<string | null>(null);

  const navItems = [
    {
      label: "Pipeline Runner",
      href: `/projects/${projectId}/pipeline`,
      icon: PlayCircle,
    },
    {
      label: "Generated Pages (v0.3)",
      href: `/projects/${projectId}/pages`,
      icon: FileText,
    },
    {
      label: "Indexing Watch (v0.4)",
      href: `/projects/${projectId}/monitoring`,
      icon: Activity,
    },
  ];

  async function handleExport() {
    try {
      setExporting(true);
      const res = await api.exportFrontend(projectId, {
        framework: "next-app",
        language: "ts",
        styling: "tailwind",
      });
      setExportMsg(`Exported ${res.exported_count} pages to ./generated-pages/`);
      setTimeout(() => setExportMsg(null), 4000);
    } catch (e: any) {
      alert("Export failed: " + e.message);
    } finally {
      setExporting(false);
    }
  }

  return (
    <div className="space-y-6">
      {/* Project Sub-Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-gray-200 dark:border-gray-800">
        <div className="flex items-center space-x-3">
          <Link
            href="/"
            className="p-2 rounded-lg text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <span className="text-xs font-mono uppercase tracking-wider text-blue-600 font-semibold">
              Project #{projectId}
            </span>
            <h1 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white">
              Virtual Try-On Fashion SEO
            </h1>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          {exportMsg && (
            <span className="text-xs font-semibold px-2.5 py-1 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">
              {exportMsg}
            </span>
          )}
          <button
            onClick={handleExport}
            disabled={exporting}
            className="inline-flex items-center space-x-2 px-3.5 py-2 rounded-xl bg-gray-900 dark:bg-white text-white dark:text-gray-900 font-semibold text-xs shadow-sm hover:opacity-90 transition-opacity disabled:opacity-50"
          >
            <Download className="w-3.5 h-3.5" />
            <span>{exporting ? "Compiling..." : "Export Next.js Pages"}</span>
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex space-x-2 border-b border-gray-200 dark:border-gray-800">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center space-x-2 px-4 py-2.5 border-b-2 text-sm font-medium transition-all ${
                isActive
                  ? "border-blue-600 text-blue-600 dark:text-blue-400 font-semibold"
                  : "border-transparent text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
              }`}
            >
              <Icon className="w-4 h-4" />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </div>

      {/* Tab Content */}
      <div>{children}</div>
    </div>
  );
}
