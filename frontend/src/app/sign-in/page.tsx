"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { ArrowRight, CheckCircle2, Mail } from "lucide-react";
import { createClient } from "@/lib/supabase/client";

export default function SignInPage() {
  const [email, setEmail] = useState("");
  const [sending, setSending] = useState(false);
  const [sent, setSent] = useState(false);
  const [callbackError, setCallbackError] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setCallbackError(new URLSearchParams(window.location.search).has("error"));
  }, []);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSending(true);
    setError(null);

    try {
      const supabase = createClient();
      const callbackUrl = new URL("/auth/callback", window.location.origin);
      callbackUrl.searchParams.set("next", "/");

      const { error: signInError } = await supabase.auth.signInWithOtp({
        email: email.trim().toLowerCase(),
        options: {
          shouldCreateUser: false,
          emailRedirectTo: callbackUrl.toString(),
        },
      });

      if (signInError) {
        // Keep account-existence details out of the UI; only invited users can sign in.
        setSent(true);
        return;
      }

      setSent(true);
    } catch {
      setError("We couldn't send a sign-in link. Please try again.");
    } finally {
      setSending(false);
    }
  }

  return (
    <section className="mx-auto max-w-lg rounded-2xl border border-slate-200 bg-white p-7 shadow-sm dark:border-slate-800 dark:bg-gray-900 sm:p-9">
      {sent ? (
        <div className="py-5 text-center" role="status" aria-live="polite">
          <CheckCircle2 className="mx-auto h-12 w-12 text-emerald-500" />
          <h1 className="mt-4 text-2xl font-bold text-slate-900 dark:text-white">Check your email</h1>
          <p className="mt-3 text-sm leading-relaxed text-slate-600 dark:text-slate-300">
            If this address belongs to an invited account, a sign-in link is on its way.
          </p>
        </div>
      ) : (
        <>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Sign in</h1>
          <p className="mt-2 text-sm leading-relaxed text-slate-600 dark:text-slate-300">
            Enter the email address that received your invitation. We’ll send you a secure sign-in link.
          </p>
          {callbackError && (
            <p className="mt-5 rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700 dark:border-rose-900 dark:bg-rose-950/40 dark:text-rose-300" role="alert">
              That sign-in link is invalid or has expired. Request a new one below.
            </p>
          )}
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
                  onChange={(event) => setEmail(event.target.value)}
                  placeholder="you@company.com"
                  className="w-full rounded-xl border border-slate-300 bg-white py-3 pl-10 pr-4 text-slate-900 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 dark:border-slate-700 dark:bg-gray-800 dark:text-white"
                />
              </div>
            </div>
            {error && <p className="text-sm text-rose-700 dark:text-rose-300" role="alert">{error}</p>}
            <button
              type="submit"
              disabled={sending}
              className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-blue-600 px-5 py-3.5 font-semibold text-white transition hover:bg-blue-700 disabled:cursor-wait disabled:opacity-60"
            >
              <span>{sending ? "Sending link…" : "Email me a sign-in link"}</span>
              {!sending && <ArrowRight className="h-4 w-4" />}
            </button>
          </form>
          <p className="mt-6 text-center text-sm text-slate-600 dark:text-slate-400">
            Need an invitation? <Link href="/request-access" className="font-semibold text-blue-700 hover:underline dark:text-blue-300">Request access</Link>
          </p>
        </>
      )}
    </section>
  );
}
