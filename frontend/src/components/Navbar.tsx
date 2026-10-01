"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Sparkles, Globe, Activity, FileText, Layers } from "lucide-react";

export default function Navbar() {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-50 bg-white/80 dark:bg-gray-900/80 backdrop-blur-md border-b border-gray-200 dark:border-gray-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <Link href="/" className="flex items-center space-x-3 group">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center text-white shadow-md shadow-blue-500/20 group-hover:scale-105 transition-transform">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <span className="font-bold text-lg tracking-tight bg-gradient-to-r from-gray-900 to-gray-600 dark:from-white dark:to-gray-300 bg-clip-text text-transparent">
              SEO Engine
            </span>
            <span className="ml-2 text-xs px-2 py-0.5 rounded-full font-semibold bg-blue-50 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300 border border-blue-200 dark:border-blue-800">
              v0.4.0
            </span>
          </div>
        </Link>

        <nav className="flex items-center space-x-1 sm:space-x-4">
          <Link
            href="/"
            className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
              pathname === "/"
                ? "bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300 font-semibold"
                : "text-gray-600 hover:text-gray-900 dark:text-gray-300 dark:hover:text-white"
            }`}
          >
            Projects
          </Link>
          <Link
            href="/projects/default-project/pipeline"
            className="px-3 py-2 rounded-lg text-sm font-medium text-gray-600 hover:text-gray-900 dark:text-gray-300 dark:hover:text-white transition-colors"
          >
            Live Pipeline
          </Link>
          <Link
            href="/projects/default-project/pages"
            className="px-3 py-2 rounded-lg text-sm font-medium text-gray-600 hover:text-gray-900 dark:text-gray-300 dark:hover:text-white transition-colors"
          >
            Generated Pages
          </Link>
          <Link
            href="/projects/default-project/monitoring"
            className="px-3 py-2 rounded-lg text-sm font-medium text-gray-600 hover:text-gray-900 dark:text-gray-300 dark:hover:text-white transition-colors"
          >
            v0.4 Indexing Watch
          </Link>
        </nav>
      </div>
    </header>
  );
}
