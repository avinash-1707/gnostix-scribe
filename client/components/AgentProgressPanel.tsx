"use client";

import { motion } from "motion/react";
import { Check, Loader2, Minus, X } from "lucide-react";
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
      <Loader2
        aria-label="running"
        className="h-3.5 w-3.5 animate-spin text-sky-400"
      />
    );
  }
  if (status === "done") {
    return <Check aria-label="done" className="h-3.5 w-3.5 text-emerald-400" />;
  }
  if (status === "error") {
    return <X aria-label="error" className="h-3.5 w-3.5 text-rose-400" />;
  }
  return <Minus aria-label="pending" className="h-3.5 w-3.5 text-white/30" />;
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
        : "Processing";
  const headerToneCls =
    terminal === "DONE"
      ? "text-emerald-300 bg-emerald-500/[0.08] border-emerald-500/[0.18]"
      : terminal === "ERROR"
        ? "text-rose-300 bg-rose-500/[0.08] border-rose-500/[0.18]"
        : "text-sky-300 bg-sky-500/[0.08] border-sky-500/[0.18]";

  return (
    <motion.section
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: [0.25, 0.4, 0.25, 1] as const }}
      className="overflow-hidden rounded-2xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-sm"
    >
      <header className="flex items-center justify-between gap-3 border-b border-white/[0.06] px-5 py-3.5">
        <h3 className="min-w-0 text-sm font-medium text-white/90 break-words">
          {topic}
        </h3>
        <span
          className={`shrink-0 inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-[11px] font-medium uppercase tracking-wider ${headerToneCls}`}
        >
          {terminal === null && (
            <Loader2 className="h-3 w-3 animate-spin" />
          )}
          {headerLabel}
        </span>
      </header>

      <ul className="divide-y divide-white/[0.05]">
        {NODE_ORDER.map(({ name, label }, i) => {
          const row = rows.get(name)!;
          const isActive = row.status === "running";
          return (
            <li
              key={name}
              className={`flex flex-col gap-1 px-5 py-2.5 sm:flex-row sm:items-center sm:gap-4 transition-colors ${
                isActive ? "bg-white/[0.02]" : ""
              }`}
            >
              <span className="flex w-5 items-center justify-center">
                <StatusIcon status={row.status} />
              </span>
              <span className="flex w-6 shrink-0 items-center font-mono text-[11px] text-white/30 tabular-nums">
                {String(i + 1).padStart(2, "0")}
              </span>
              <span className="min-w-0 flex-1 text-sm font-medium text-white/85">
                {label}
                {row.retryCount > 0 && (
                  <span className="ml-2 rounded-full border border-amber-500/[0.2] bg-amber-500/[0.08] px-1.5 py-0.5 text-[10px] uppercase tracking-wider text-amber-300">
                    retry × {row.retryCount}
                  </span>
                )}
              </span>
              <span className="shrink-0 font-mono text-[11px] text-white/40 tabular-nums">
                {row.status === "pending" ? "—" : `${row.elapsed_ms}ms`}
              </span>
              <span className="flex-1 truncate text-xs text-white/40 sm:max-w-xs">
                {row.message}
              </span>
            </li>
          );
        })}
      </ul>
    </motion.section>
  );
}
