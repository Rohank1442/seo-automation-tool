"use client";

import Link from "next/link";
import { usePathname, useParams } from "next/navigation";
import { PlayCircle, FileText, Activity, ArrowLeft, Download, Loader2 } from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";

function zipDownloadName(projectName: string): string {
  const cleaned = projectName.trim().replace(/[^A-Za-z0-9._-]+/g, "-").replace(/^[-.]+|[-.]+$/g, "");
  return `seo-pages-${cleaned || "project"}.zip`;
}

export default function ProjectLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const params = useParams();
  const projectId = params?.id as string;
  const [projectName, setProjectName] = useState("Loading project…");
  const [targetDomain, setTargetDomain] = useState("");
  const [modalOpen, setModalOpen] = useState(false);
  const [baseUrl, setBaseUrl] = useState("");
  const [downloading, setDownloading] = useState(false);
  const [downloadError, setDownloadError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    api.getProject(projectId)
      .then((project) => {
        if (!active) return;
        setProjectName(project.name);
        setTargetDomain(project.target_domain || "");
      })
      .catch(() => {
        if (active) setProjectName("Project not found or access denied");
      });

    return () => {
      active = false;
    };
  }, [projectId]);

  useEffect(() => {
    if (!modalOpen) return;
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape" && !downloading) setModalOpen(false);
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [modalOpen, downloading]);

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
    // {
    //   label: "Indexing Watch (v0.4)",
    //   href: `/projects/${projectId}/monitoring`,
    //   icon: Activity,
    // },
  ];

  function openDownloadModal() {
    setBaseUrl(targetDomain);
    setDownloadError(null);
    setModalOpen(true);
  }

  async function handleDownload() {
    const confirmed = baseUrl.trim().replace(/\/+$/, "");
    if (!confirmed) {
      setDownloadError("Enter a base URL.");
      return;
    }

    try {
      setDownloading(true);
      setDownloadError(null);
      await api.downloadPagesZip(projectId, confirmed, zipDownloadName(projectName));
      setTargetDomain(confirmed);
      setModalOpen(false);
    } catch (e: unknown) {
      const message = e instanceof Error ? e.message : "Download failed.";
      setDownloadError(message);
    } finally {
      setDownloading(false);
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
              {projectName}
            </h1>
          </div>
        </div>

        <button
          onClick={openDownloadModal}
          className="inline-flex items-center space-x-2 px-3.5 py-2 rounded-xl bg-gray-900 dark:bg-white text-white dark:text-gray-900 font-semibold text-xs shadow-sm hover:opacity-90 transition-opacity"
        >
          <Download className="w-3.5 h-3.5" />
          <span>Download Pages ZIP</span>
        </button>
      </div>

      {modalOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4"
          onClick={() => {
            if (!downloading) setModalOpen(false);
          }}
        >
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="download-pages-title"
            className="w-full max-w-md rounded-2xl bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 shadow-xl p-5"
            onClick={(event) => event.stopPropagation()}
          >
            <h2 id="download-pages-title" className="text-lg font-semibold text-gray-900 dark:text-white">
              Download Pages ZIP
            </h2>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              This URL is written into each page canonical, sitemap.xml, and robots.txt.
            </p>
            <form
              onSubmit={(event) => {
                event.preventDefault();
                void handleDownload();
              }}
            >
              <label htmlFor="download-base-url" className="mt-4 block text-xs font-semibold uppercase tracking-wide text-gray-500">
                Website base URL
              </label>
              <input
                id="download-base-url"
                value={baseUrl}
                onChange={(event) => setBaseUrl(event.target.value)}
                disabled={downloading}
                autoFocus
                className="mt-1.5 w-full rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-950 px-3 py-2 text-sm text-gray-900 dark:text-white outline-none focus:border-blue-500"
                placeholder="https://yourdomain.com"
              />
              {downloadError && (
                <p className="mt-2 text-sm text-red-600 dark:text-red-400">{downloadError}</p>
              )}
              <div className="mt-5 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setModalOpen(false)}
                  disabled={downloading}
                  className="px-3.5 py-2 rounded-xl text-sm font-medium text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={downloading}
                  className="inline-flex items-center space-x-2 px-3.5 py-2 rounded-xl bg-gray-900 dark:bg-white text-white dark:text-gray-900 font-semibold text-sm disabled:opacity-50"
                >
                  {downloading && <Loader2 className="w-4 h-4 animate-spin" />}
                  <span>{downloading ? "Preparing ZIP…" : "Download ZIP"}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

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
