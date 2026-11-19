"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowRight, Lock, Mail, ShieldAlert } from "lucide-react";
import { api } from "@/lib/api";

export default function SignInPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isPendingApproval, setIsPendingApproval] = useState(false);
  const [needsSignUp, setNeedsSignUp] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    setIsPendingApproval(false);
    setNeedsSignUp(false);

    try {
      await api.signIn({
        email: email.trim().toLowerCase(),
        password,
      });

      // Redirect directly to dashboard upon successful authentication
      router.push("/");
      router.refresh();
    } catch (err: any) {
      const message = err?.message || "";
      const status = err?.status;

      if (status === 403 || message.toLowerCase().includes("waiting for admin approval")) {
        setIsPendingApproval(true);
        setError("Your account is currently waiting for admin approval.");
      } else if (message.toLowerCase().includes("sign up first")) {
        setNeedsSignUp(true);
        setError("Your email is approved! Please create your password on the sign-up page.");
      } else if (status === 401 || message.toLowerCase().includes("invalid email or password")) {
        setError("Invalid email or password. Please try again.");
      } else {
        setError(message || "Invalid email or password.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="mx-auto max-w-lg rounded-2xl border border-slate-200 bg-white p-7 shadow-sm dark:border-slate-800 dark:bg-gray-900 sm:p-9">
      <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Sign In</h1>
      <p className="mt-2 text-sm leading-relaxed text-slate-600 dark:text-slate-300">
        Sign in to access your SEO Engine dashboard and projects.
      </p>

      {isPendingApproval ? (
        <div className="mt-5 rounded-xl border border-amber-300 bg-amber-50 p-4 dark:border-amber-800/60 dark:bg-amber-950/40">
          <div className="flex items-start gap-3">
            <ShieldAlert className="mt-0.5 h-5 w-5 shrink-0 text-amber-600 dark:text-amber-400" />
            <div className="text-sm">
              <p className="font-semibold text-amber-900 dark:text-amber-200">
                Access Pending Approval
              </p>
              <p className="mt-1 text-amber-800 dark:text-amber-300">
                Your email request has been received and is waiting for administrator approval.
              </p>
            </div>
          </div>
        </div>
      ) : needsSignUp ? (
        <div className="mt-5 rounded-xl border border-blue-200 bg-blue-50 p-4 dark:border-blue-900/60 dark:bg-blue-950/40">
          <p className="text-sm text-blue-900 dark:text-blue-200">
            Your email has been approved!
          </p>
          <div className="mt-2">
            <Link
              href="/sign-up"
              className="inline-flex items-center gap-1.5 text-sm font-semibold text-blue-700 hover:underline dark:text-blue-300"
            >
              <span>Click here to set your password and complete signup</span>
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </div>
      ) : error ? (
        <p className="mt-5 rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700 dark:border-rose-900 dark:bg-rose-950/40 dark:text-rose-300" role="alert">
          {error}
        </p>
      ) : null}

      <form onSubmit={handleSubmit} className="mt-6 space-y-4">
        <div>
          <label htmlFor="sign-in-email" className="mb-1.5 block text-sm font-semibold text-slate-700 dark:text-slate-200">
            Email address
          </label>
          <div className="relative">
            <Mail className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <input
              id="sign-in-email"
              name="email"
              type="email"
              autoComplete="email"
              maxLength={320}
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@company.com"
              className="w-full rounded-xl border border-slate-300 bg-white py-3 pl-10 pr-4 text-slate-900 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 dark:border-slate-700 dark:bg-gray-800 dark:text-white"
            />
          </div>
        </div>

        <div>
          <label htmlFor="sign-in-password" className="mb-1.5 block text-sm font-semibold text-slate-700 dark:text-slate-200">
            Password
          </label>
          <div className="relative">
            <Lock className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <input
              id="sign-in-password"
              name="password"
              type="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full rounded-xl border border-slate-300 bg-white py-3 pl-10 pr-4 text-slate-900 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 dark:border-slate-700 dark:bg-gray-800 dark:text-white"
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={submitting}
          className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-blue-600 px-5 py-3.5 font-semibold text-white transition hover:bg-blue-700 disabled:cursor-wait disabled:opacity-60"
        >
          <span>{submitting ? "Signing in…" : "Sign in"}</span>
          {!submitting && <ArrowRight className="h-4 w-4" />}
        </button>
      </form>

      <div className="mt-6 flex flex-col items-center gap-2 text-center text-sm text-slate-600 dark:text-slate-400 sm:flex-row sm:justify-between">
        <span>
          Don’t have an account?{" "}
          <Link href="/sign-up" className="font-semibold text-blue-700 hover:underline dark:text-blue-300">
            Sign up
          </Link>
        </span>
        <Link href="/request-access" className="font-semibold text-slate-500 hover:underline dark:text-slate-400">
          Need an invitation?
        </Link>
      </div>
    </section>
  );
}
