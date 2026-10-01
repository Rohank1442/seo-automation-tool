import React from "react";

interface StatusBadgeProps {
  status: string;
}

export default function StatusBadge({ status }: StatusBadgeProps) {
  const configs: Record<string, { label: string; class: string }> = {
    // Project & Pipeline Statuses
    completed: {
      label: "Completed",
      class: "bg-emerald-50 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800",
    },
    running: {
      label: "Running...",
      class: "bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300 border-blue-200 dark:border-blue-800 animate-pulse",
    },
    created: {
      label: "Ready",
      class: "bg-gray-50 text-gray-700 dark:bg-gray-800 dark:text-gray-300 border-gray-200 dark:border-gray-700",
    },
    // v0.4 Monitoring Categories
    indexed_and_alive: {
      label: "Indexed & Active",
      class: "bg-emerald-50 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800",
    },
    breakout_candidate: {
      label: "Breakout Growth 🚀",
      class: "bg-purple-50 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300 border-purple-200 dark:border-purple-800",
    },
    indexed_silent: {
      label: "Indexed (0 Impr)",
      class: "bg-amber-50 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300 border-amber-200 dark:border-amber-800",
    },
    invisible_anomaly: {
      label: "Invisible / Delay ⚠️",
      class: "bg-rose-50 text-rose-700 dark:bg-rose-900/30 dark:text-rose-300 border-rose-200 dark:border-rose-800",
    },
  };

  const config = configs[status] || {
    label: status.replace("_", " ").toUpperCase(),
    class: "bg-gray-100 text-gray-700 border-gray-200",
  };

  return (
    <span
      className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold border ${config.class}`}
    >
      {config.label}
    </span>
  );
}
