"use client";

import type { NodeEvent, NodeStatus } from "@/lib/api";

const NODE_ORDER: { name: string; label: string }[] = [
  { name: "topic_router", label: "Routing Topic" },
  { name: "gfg_scraper", label: "Scraping GeeksForGeeks" },
  { name: "tpointtech_scraper", label: "Scraping TpointTech" },
  { name: "llm_knowledge", label: "Generating LLM Knowledge" },
  { name: "content_merger", label: "Merging Content" },
  { name: "content_analyser", label: "Analysing Content" },
  { name: "image_generator", label: "Generating Images" },
  { name: "mdx_generator", label: "Generating MDX" },
  { name: "mdx_validator", label: "Validating MDX" },
  { name: "file_writer", label: "Writing Output File" },
];

interface NodeRowState {
  status: NodeStatus | "pending";
  elapsed_ms: number;
  message: string;
  retryCount: number;
}

function deriveRows(events: NodeEvent[]): Map<string, NodeRowState> {
  const map = new Map<string, NodeRowState>();
  for (const { name } of NODE_ORDER) {
    map.set(name, { status: "pending", elapsed_ms: 0, message: "", retryCount: 0 });
  }
  for (const ev of events) {
    if (ev.node === "DONE" || ev.node === "ERROR") continue;
    const prev = map.get(ev.node);
    if (!prev) continue;
    const next: NodeRowState = {
      status: ev.status,
      elapsed_ms: ev.elapsed_ms,
      message: ev.message,
      retryCount: prev.retryCount,
    };
    if (ev.status === "running" && prev.status === "done") {
      next.retryCount = prev.retryCount + 1;
    }
    map.set(ev.node, next);
  }
  return map;
}

function StatusIcon({ status }: { status: NodeRowState["status"] }) {
  if (status === "running") {
    return (
      <span
        aria-label="running"
        className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-blue-600 border-t-transparent"
      />
    );
  }
  if (status === "done") {
    return <span aria-label="done" className="text-green-600">✓</span>;
  }
  if (status === "error") {
    return <span aria-label="error" className="text-red-600">✕</span>;
  }
  return <span aria-label="pending" className="text-gray-400">–</span>;
}

interface AgentProgressPanelProps {
  topic: string;
  events: NodeEvent[];
  terminal: "DONE" | "ERROR" | null;
}

export default function AgentProgressPanel({
  topic,
  events,
  terminal,
}: AgentProgressPanelProps) {
  const rows = deriveRows(events);
  const headerLabel =
    terminal === "DONE"
      ? "Complete"
      : terminal === "ERROR"
        ? "Failed"
        : "Processing…";

  return (
    <section className="rounded-lg border border-gray-200 bg-white">
      <header className="flex items-center justify-between border-b border-gray-200 px-4 py-3">
        <h3 className="text-sm font-semibold text-gray-900 break-words">
          {topic}
        </h3>
        <span
          className={`text-xs font-medium ${
            terminal === "DONE"
              ? "text-green-600"
              : terminal === "ERROR"
                ? "text-red-600"
                : "text-blue-600"
          }`}
        >
          {headerLabel}
        </span>
      </header>
      <ul className="divide-y divide-gray-100">
        {NODE_ORDER.map(({ name, label }) => {
          const row = rows.get(name)!;
          return (
            <li
              key={name}
              className="flex flex-col gap-1 px-4 py-2 sm:flex-row sm:items-center sm:gap-3"
            >
              <span className="flex w-6 items-center justify-center">
                <StatusIcon status={row.status} />
              </span>
              <span className="flex-1 text-sm font-medium text-gray-900">
                {label}
                {row.retryCount > 0 && (
                  <span className="ml-2 rounded bg-yellow-50 px-1.5 py-0.5 text-xs text-yellow-700">
                    retry × {row.retryCount}
                  </span>
                )}
              </span>
              <span className="text-xs text-gray-500 tabular-nums">
                {row.status === "pending" ? "—" : `${row.elapsed_ms} ms`}
              </span>
              <span className="flex-1 truncate text-xs text-gray-500 sm:max-w-xs">
                {row.message}
              </span>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
