"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { LogOut, Sparkles } from "lucide-react";
import { api, getStoredToken } from "@/lib/api";

export default function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
  const [sessionChecked, setSessionChecked] = useState(false);
  const [signedIn, setSignedIn] = useState(false);
  const [signOutError, setSignOutError] = useState<string | null>(null);
  const [signingOut, setSigningOut] = useState(false);

  useEffect(() => {
    let active = true;

    // Fast check for local token or cookie
    const token = getStoredToken();
    if (!token && typeof document !== "undefined") {
      const hasCookie = document.cookie.includes("access_token") || document.cookie.includes("seo_access_token");
      if (!hasCookie) {
        setSignedIn(false);
        setSessionChecked(true);
        return;
      }
    }

    api
      .getMe()
      .then((user) => {
        if (active) {
          setSignedIn(Boolean(user?.id));
          setSessionChecked(true);
        }
      })
      .catch(() => {
        if (active) {
          setSignedIn(false);
          setSessionChecked(true);
        }
      });

    return () => {
      active = false;
    };
  }, [pathname]);

  async function handleSignOut() {
    setSigningOut(true);
    setSignOutError(null);
    try {
      await api.signOut();
      setSignedIn(false);
      router.replace("/sign-in");
      router.refresh();
    } catch {
      setSignOutError("We couldn't sign you out. Please try again.");
    } finally {
      setSigningOut(false);
    }
  }

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
          {sessionChecked && signedIn ? (
            <>
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
              <button
                type="button"
                onClick={handleSignOut}
                disabled={signingOut}
                className="inline-flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-semibold text-gray-600 transition-colors hover:bg-gray-100 hover:text-gray-900 disabled:cursor-wait disabled:opacity-60 dark:text-gray-300 dark:hover:bg-gray-800 dark:hover:text-white"
              >
                <LogOut className="h-4 w-4" />
                {signingOut ? "Signing out…" : "Sign out"}
              </button>
            </>
          ) : sessionChecked ? (
            <>
              <Link
                href="/sign-in"
                className={`rounded-lg px-3 py-2 text-sm font-semibold transition-colors ${
                  pathname === "/sign-in"
                    ? "bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300"
                    : "text-gray-600 hover:text-gray-900 dark:text-gray-300 dark:hover:text-white"
                }`}
              >
                Sign in
              </Link>
              <Link
                href="/sign-up"
                className={`rounded-lg px-3.5 py-2 text-sm font-semibold text-white bg-blue-600 hover:bg-blue-700 transition-colors ${
                  pathname === "/sign-up" ? "ring-2 ring-blue-500/30" : ""
                }`}
              >
                Sign up
              </Link>
            </>
          ) : null}
        </nav>
      </div>
      {signOutError && (
        <p className="border-t border-rose-200 bg-rose-50 px-4 py-2 text-center text-sm text-rose-700 dark:border-rose-900 dark:bg-rose-950/40 dark:text-rose-300" role="alert">
          {signOutError}
        </p>
      )}
    </header>
  );
}
