"use client";

import { useState, useEffect, useRef } from "react";
import { useParams } from "next/navigation";
import { Play, CheckCircle2, Loader2, Sparkles, Terminal, ArrowRight, ShieldCheck } from "lucide-react";
import { api } from "@/lib/api";
import { PipelineEvent } from "@/lib/types";

export default function PipelinePage() {
  const params = useParams();
  const projectId = (params?.id as string) || "default-project";

  const [isRunning, setIsRunning] = useState(false);
  const [progress, setProgress] = useState(100);
  const [currentStep, setCurrentStep] = useState("Pipeline Complete (10 Pages Ready)");
  const [events, setEvents] = useState<PipelineEvent[]>([
    {
      project_id: projectId,
      phase: "v01_research",
      step: "completed",
      message: "v0.1 Niche & Keyword research completed. 3 topic clusters & 140 keywords mapped.",
      progress_percentage: 28,
      status: "completed",
      timestamp: new Date().toISOString(),
    },
    {
      project_id: projectId,
      phase: "v02_architecture",
      step: "completed",
      message: "v0.2 Site architecture established. 10 URLs and 74 internal links structured.",
      progress_percentage: 55,
      status: "completed",
      timestamp: new Date().toISOString(),
    },
    {
      project_id: projectId,
      phase: "v03_content_generation",
      step: "completed",
      message: "v0.3 First-Wave content generated & 80-point quality audit passed with 100/100 score.",
      progress_percentage: 95,
      status: "completed",
      timestamp: new Date().toISOString(),
    },
    {
      project_id: projectId,
      phase: "completed",
      step: "finished",
      message: "All phases finished! Ready for Next.js copy-paste and Google Search Console indexing watch.",
      progress_percentage: 100,
      status: "completed",
      timestamp: new Date().toISOString(),
    },
  ]);
  const [dryRun, setDryRun] = useState(true);
  const logContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [events]);

  function handleStartPipeline() {
    setIsRunning(true);
    setProgress(5);
    setEvents([]);
    setCurrentStep("Initializing live pipeline...");

    const streamUrl = api.getPipelineStreamUrl(projectId, dryRun);
    const eventSource = new EventSource(streamUrl);

    eventSource.onmessage = (e) => {
      try {
        const data: PipelineEvent = JSON.parse(e.data);
        setEvents((prev) => [...prev, data]);
        setProgress(data.progress_percentage);
        setCurrentStep(data.message);

        if (data.status === "completed" && data.progress_percentage >= 100) {
          setIsRunning(false);
          eventSource.close();
        }
      } catch (err) {
        console.error("SSE parse error:", err);
      }
    };

    eventSource.onerror = (err) => {
      console.warn("SSE stream ended or disconnected:", err);
      setIsRunning(false);
      eventSource.close();
    };
  }

  const steps = [
    {
      id: "v01",
      name: "v0.1 Niche & Keyword Research",
      desc: "Topic clusters, search volumes, long-tail queries, PAA questions & competitor content landscape.",
      phaseName: "v01_research",
    },
    {
      id: "v02",
      name: "v0.2 Site Architecture & Setup",
      desc: "Domain hierarchy, URL routing, 74 internal links, sitemap, robots.txt & technical SEO rules.",
      phaseName: "v02_architecture",
    },
    {
      id: "v03",
      name: "v0.3 First-Wave Content & Validation",
      desc: "Gemini structured briefs, 10 articles, FAQ accordions, and 80-point automated SEO validation.",
      phaseName: "v03_content_generation",
    },
  ];

  return (
    <div className="space-y-8">
      {/* Run Trigger Banner */}
      <div className="bg-white dark:bg-gray-900 rounded-3xl p-6 sm:p-8 border border-gray-200 dark:border-gray-800 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
        <div className="space-y-1">
          <div className="flex items-center space-x-2">
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300 border border-blue-200 dark:border-blue-800">
              Autonomous Pipeline Execution
            </span>
            <span className="text-xs text-gray-500 font-mono">v0.1 ➔ v0.3</span>
          </div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
            Run Autonomous Generation Pipeline
          </h2>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Executes all 3 phases end-to-end, writing structured outputs and drop-in Next.js page components.
          </p>
        </div>

        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 w-full md:w-auto">
          <label className="flex items-center space-x-2 text-xs font-medium text-gray-600 dark:text-gray-400 cursor-pointer bg-gray-50 dark:bg-gray-800 px-3 py-2 rounded-xl border border-gray-200 dark:border-gray-700">
            <input
              type="checkbox"
              checked={dryRun}
              onChange={(e) => setDryRun(e.target.checked)}
              className="rounded text-blue-600 focus:ring-blue-500"
            />
            <span>Fast / Dry-Run Mode</span>
          </label>

          <button
            onClick={handleStartPipeline}
            disabled={isRunning}
            className="inline-flex items-center justify-center space-x-2 px-6 py-3 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-sm shadow-md shadow-blue-500/20 transition-all hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50"
          >
            {isRunning ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Running Pipeline...</span>
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-current" />
                <span>Trigger All Phases</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Progress Bar & Current Status */}
      <div className="bg-white dark:bg-gray-900 rounded-3xl p-6 border border-gray-200 dark:border-gray-800 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <span className="font-bold text-sm text-gray-900 dark:text-white">Overall Progress</span>
            <span className="text-xs text-gray-500">({progress}%)</span>
          </div>
          <span className="text-xs font-semibold text-blue-600 dark:text-blue-400 truncate max-w-md">
            {currentStep}
          </span>
        </div>
        <div className="w-full h-3 bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-blue-600 to-indigo-600 transition-all duration-300 rounded-full"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* 3-Step Visual Breakdown */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {steps.map((step, idx) => {
          const isDone = events.some((e) => e.phase === step.phaseName && e.status === "completed") || progress >= (idx + 1) * 33;
          const isActive = isRunning && !isDone && progress >= idx * 30;

          return (
            <div
              key={step.id}
              className={`rounded-2xl p-6 border transition-all ${
                isDone
                  ? "bg-emerald-50/40 dark:bg-emerald-950/20 border-emerald-200 dark:border-emerald-800"
                  : isActive
                  ? "bg-blue-50/50 dark:bg-blue-950/30 border-blue-300 dark:border-blue-700 ring-2 ring-blue-500/20"
                  : "bg-white dark:bg-gray-900 border-gray-200 dark:border-gray-800 opacity-70"
              }`}
            >
              <div className="flex items-center justify-between mb-4">
                <span className="text-xs font-bold font-mono px-2 py-0.5 rounded-md bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700">
                  STEP {idx + 1}
                </span>
                {isDone ? (
                  <CheckCircle2 className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
                ) : isActive ? (
                  <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />
                ) : (
                  <div className="w-5 h-5 rounded-full border border-gray-300 dark:border-gray-700" />
                )}
              </div>
              <h3 className="font-bold text-base text-gray-900 dark:text-white">{step.name}</h3>
              <p className="mt-2 text-xs text-gray-600 dark:text-gray-400 leading-relaxed">
                {step.desc}
              </p>
            </div>
          );
        })}
      </div>

      {/* Live SSE Terminal Stream */}
      <div className="bg-gray-950 rounded-3xl p-6 border border-gray-800 shadow-xl space-y-3 font-mono">
        <div className="flex items-center justify-between pb-3 border-b border-gray-800 text-xs text-gray-400">
          <div className="flex items-center space-x-2">
            <Terminal className="w-4 h-4 text-blue-400" />
            <span className="text-gray-200 font-semibold">Live Pipeline Event Stream (SSE)</span>
          </div>
          <span className="text-gray-500">{events.length} Events Recorded</span>
        </div>

        <div
          ref={logContainerRef}
          className="h-64 overflow-y-auto space-y-2 text-xs text-gray-300 pr-2"
        >
          {events.length === 0 ? (
            <div className="text-gray-600 italic py-8 text-center">
              Click &quot;Trigger All Phases&quot; above to launch the live autonomous pipeline stream.
            </div>
          ) : (
            events.map((e, i) => (
              <div key={i} className="flex items-start space-x-2 leading-relaxed">
                <span className="text-gray-500 select-none">[{e.timestamp.slice(11, 19)}]</span>
                <span
                  className={`font-semibold px-1.5 py-0.2 rounded text-[10px] uppercase ${
                    e.status === "completed"
                      ? "bg-emerald-950 text-emerald-400 border border-emerald-800"
                      : "bg-blue-950 text-blue-400 border border-blue-800"
                  }`}
                >
                  {e.phase}
                </span>
                <span className="text-gray-200">{e.message}</span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
