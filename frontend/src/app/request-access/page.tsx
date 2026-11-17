"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { ArrowRight, CheckCircle2, LockKeyhole, Mail, Sparkles } from "lucide-react";
import { api } from "@/lib/api";

export default function HomePage() {
  const [email, setEmail] = useState("");
  const [useCase, setUseCase] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);

    try {
      await api.requestEarlyAccess({ email, use_case: useCase || undefined });
      setSubmitted(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "We couldn't submit your request. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-20 pb-12">
      <section className="grid gap-12 rounded-3xl border border-slate-200 bg-gradient-to-br from-white via-white to-blue-50 p-7 shadow-sm dark:border-slate-800 dark:from-gray-900 dark:to-blue-950/30 sm:p-12 lg:grid-cols-[1.1fr_0.9fr] lg:items-center">
        <div className="max-w-2xl">
          <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-blue-200 bg-blue-50 px-3 py-1.5 text-xs font-semibold text-blue-800 dark:border-blue-900 dark:bg-blue-950/50 dark:text-blue-200">
            <Sparkles className="h-3.5 w-3.5" />
            <span>Early access · Limited places</span>
          </div>
          <h1 className="text-4xl font-black leading-tight tracking-tight text-slate-950 dark:text-white sm:text-5xl">
            Build your SEO growth plan before you publish.
          </h1>
          <p className="mt-5 max-w-xl text-lg leading-relaxed text-slate-600 dark:text-slate-300">
            Find worthwhile topics, organize them into a site structure, and prepare pages to review. You stay in control of what gets published.
          </p>
          <a
            href="#how-it-works"
            className="mt-7 inline-flex items-center gap-2 font-semibold text-blue-700 hover:text-blue-800 dark:text-blue-300 dark:hover:text-blue-200"
          >
            See how early access works <ArrowRight className="h-4 w-4" />
          </a>
        </div>

        <div id="request-access" className="scroll-mt-24 rounded-2xl border border-slate-200 bg-white p-6 shadow-lg shadow-slate-900/5 dark:border-slate-700 dark:bg-gray-900 sm:p-8">
          {submitted ? (
            <div className="py-7 text-center" role="status" aria-live="polite">
              <CheckCircle2 className="mx-auto h-12 w-12 text-emerald-500" />
              <h2 className="mt-4 text-2xl font-bold text-slate-900 dark:text-white">Request received</h2>
              <p className="mt-3 text-sm leading-relaxed text-slate-600 dark:text-slate-300">
                Thanks for your interest. I’ll review your request and email you if I can invite you into the early-access group.
              </p>
            </div>
          ) : (
            <>
              <div className="mb-6">
                <h2 className="text-2xl font-bold text-slate-900 dark:text-white">Request early access</h2>
                <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">
                  Leave your email. I’ll review requests and add people in small batches.
                </p>
              </div>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label htmlFor="email" className="mb-1.5 block text-sm font-semibold text-slate-700 dark:text-slate-200">
                    Email address <span aria-hidden="true">*</span>
                  </label>
                  <div className="relative">
                    <Mail className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                    <input
                      id="email"
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
                <div>
                  <label htmlFor="use-case" className="mb-1.5 block text-sm font-semibold text-slate-700 dark:text-slate-200">
                    What would you use it for? <span className="font-normal text-slate-500">Optional</span>
                  </label>
                  <textarea
                    id="use-case"
                    name="use_case"
                    rows={3}
                    maxLength={1000}
                    value={useCase}
                    onChange={(event) => setUseCase(event.target.value)}
                    placeholder="A sentence about your website or SEO workflow"
                    className="w-full resize-y rounded-xl border border-slate-300 bg-white px-4 py-3 text-slate-900 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 dark:border-slate-700 dark:bg-gray-800 dark:text-white"
                  />
                </div>
                {error && (
                  <p className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700 dark:border-rose-900 dark:bg-rose-950/40 dark:text-rose-300" role="alert">
                    {error}
                  </p>
                )}
                <button
                  type="submit"
                  disabled={submitting}
                  className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-blue-600 px-5 py-3.5 font-semibold text-white shadow-md shadow-blue-600/20 transition hover:bg-blue-700 disabled:cursor-wait disabled:opacity-60"
                >
                  <span>{submitting ? "Sending request…" : "Request access"}</span>
                  {!submitting && <ArrowRight className="h-4 w-4" />}
                </button>
                <p className="text-center text-xs leading-relaxed text-slate-500 dark:text-slate-400">
                  Your email will only be used to follow up about early access.
                </p>
                <p className="text-center text-sm text-slate-600 dark:text-slate-400">
                  Already invited? <Link href="/sign-in" className="font-semibold text-blue-700 hover:underline dark:text-blue-300">Sign in</Link>
                </p>
              </form>
            </>
          )}
        </div>
      </section>

      <section id="how-it-works" className="scroll-mt-24">
        <div className="mx-auto max-w-2xl text-center">
          <p className="text-sm font-bold uppercase tracking-widest text-blue-700 dark:text-blue-300">A deliberate beta</p>
          <h2 className="mt-3 text-3xl font-bold tracking-tight text-slate-900 dark:text-white">You ask. I invite. You stay in control.</h2>
        </div>
        <div className="mx-auto mt-10 grid max-w-5xl gap-5 md:grid-cols-3">
          {[
            { number: "01", title: "Send a request", body: "Share your email and, if you like, a little about your SEO use case." },
            { number: "02", title: "I review it", body: "I’m onboarding a small group while I test the product and manage generation costs." },
            { number: "03", title: "Get an invite", body: "If there’s a fit, I’ll contact you with the next steps for getting access." },
          ].map((step) => (
            <article key={step.number} className="rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-gray-900">
              <span className="text-sm font-bold text-blue-600 dark:text-blue-300">{step.number}</span>
              <h3 className="mt-3 text-lg font-bold text-slate-900 dark:text-white">{step.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-slate-600 dark:text-slate-400">{step.body}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="mx-auto flex max-w-3xl items-start gap-4 rounded-2xl border border-slate-200 bg-slate-100/70 p-5 dark:border-slate-800 dark:bg-gray-900/70">
        <LockKeyhole className="mt-0.5 h-5 w-5 shrink-0 text-slate-500" />
        <p className="text-sm leading-relaxed text-slate-600 dark:text-slate-400">
          Early access is currently invite-only. Requests don’t start an SEO pipeline or generate pages automatically.
        </p>
      </section>
    </div>
  );
}
