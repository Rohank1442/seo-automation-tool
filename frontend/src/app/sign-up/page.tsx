"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowRight, Lock, Mail, ShieldAlert, User } from "lucide-react";
import { api } from "@/lib/api";

export default function SignUpPage() {
  const router = useRouter();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isNotApproved, setIsNotApproved] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsNotApproved(false);

    if (password.length < 8) {
      setError("Password must be at least 8 characters long.");
      return;
    }

    if (password !== confirmPassword) {
      setError("Passwords do not match. Please verify both fields.");
      return;
    }

    setSubmitting(true);

    try {
      await api.signUp({
        email: email.trim().toLowerCase(),
        password,
        full_name: fullName.trim() || undefined,
      });

      // Successful registration - redirect to dashboard
      router.push("/");
      router.refresh();
    } catch (err: any) {
      const message = err?.message || "";
      const status = err?.status;

      if (
        status === 403 ||
        message.toLowerCase().includes("not approved") ||
        message.toLowerCase().includes("request access") ||
        message.toLowerCase().includes("waiting for admin approval")
      ) {
        setIsNotApproved(true);
        setError("This email has not been approved for access yet. Please request access first.");
      } else if (message.toLowerCase().includes("already exists")) {
        setError("An account with this email already exists. Please sign in below.");
      } else {
        setError(message || "Registration failed. Please check your details and try again.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="mx-auto max-w-lg rounded-2xl border border-slate-200 bg-white p-7 shadow-sm dark:border-slate-800 dark:bg-gray-900 sm:p-9">
      <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Create an Account</h1>
      <p className="mt-2 text-sm leading-relaxed text-slate-600 dark:text-slate-300">
        Enter your approved email and choose a secure password to set up your account.
      </p>

      {isNotApproved ? (
        <div className="mt-5 rounded-xl border border-amber-300 bg-amber-50 p-4 dark:border-amber-800/60 dark:bg-amber-950/40">
          <div className="flex items-start gap-3">
            <ShieldAlert className="mt-0.5 h-5 w-5 shrink-0 text-amber-600 dark:text-amber-400" />
            <div className="text-sm">
              <p className="font-semibold text-amber-900 dark:text-amber-200">
                Access Approval Required
              </p>
              <p className="mt-1 text-amber-800 dark:text-amber-300">
                This email has not been approved for early access yet.
              </p>
              <div className="mt-3">
                <Link
                  href="/request-access"
                  className="inline-flex items-center gap-1.5 font-semibold text-blue-700 hover:underline dark:text-blue-300"
                >
                  <span>Request access now</span>
                  <ArrowRight className="h-4 w-4" />
                </Link>
              </div>
            </div>
          </div>
        </div>
      ) : error ? (
        <p className="mt-5 rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700 dark:border-rose-900 dark:bg-rose-950/40 dark:text-rose-300" role="alert">
          {error}
        </p>
      ) : null}

      <form onSubmit={handleSubmit} className="mt-6 space-y-4">
        <div>
          <label htmlFor="sign-up-name" className="mb-1.5 block text-sm font-semibold text-slate-700 dark:text-slate-200">
            Full name <span className="font-normal text-slate-400">(optional)</span>
          </label>
          <div className="relative">
            <User className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <input
              id="sign-up-name"
              name="fullName"
              type="text"
              autoComplete="name"
              maxLength={200}
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              placeholder="Jane Doe"
              className="w-full rounded-xl border border-slate-300 bg-white py-3 pl-10 pr-4 text-slate-900 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 dark:border-slate-700 dark:bg-gray-800 dark:text-white"
            />
          </div>
        </div>

        <div>
          <label htmlFor="sign-up-email" className="mb-1.5 block text-sm font-semibold text-slate-700 dark:text-slate-200">
            Approved email address
          </label>
          <div className="relative">
            <Mail className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <input
              id="sign-up-email"
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
          <label htmlFor="sign-up-password" className="mb-1.5 block text-sm font-semibold text-slate-700 dark:text-slate-200">
            Password <span className="font-normal text-slate-400">(minimum 8 characters)</span>
          </label>
          <div className="relative">
            <Lock className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <input
              id="sign-up-password"
              name="password"
              type="password"
              autoComplete="new-password"
              minLength={8}
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full rounded-xl border border-slate-300 bg-white py-3 pl-10 pr-4 text-slate-900 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 dark:border-slate-700 dark:bg-gray-800 dark:text-white"
            />
          </div>
        </div>

        <div>
          <label htmlFor="sign-up-confirm-password" className="mb-1.5 block text-sm font-semibold text-slate-700 dark:text-slate-200">
            Confirm password
          </label>
          <div className="relative">
            <Lock className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <input
              id="sign-up-confirm-password"
              name="confirmPassword"
              type="password"
              autoComplete="new-password"
              minLength={8}
              required
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
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
          <span>{submitting ? "Creating account…" : "Create account"}</span>
          {!submitting && <ArrowRight className="h-4 w-4" />}
        </button>
      </form>

      <div className="mt-6 flex flex-col items-center gap-2 text-center text-sm text-slate-600 dark:text-slate-400 sm:flex-row sm:justify-between">
        <span>
          Already have an account?{" "}
          <Link href="/sign-in" className="font-semibold text-blue-700 hover:underline dark:text-blue-300">
            Sign in
          </Link>
        </span>
        <Link href="/request-access" className="font-semibold text-slate-500 hover:underline dark:text-slate-400">
          Request access
        </Link>
      </div>
    </section>
  );
}
