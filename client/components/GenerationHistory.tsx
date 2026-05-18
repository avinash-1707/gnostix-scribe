"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import { ChevronDown, History as HistoryIcon } from "lucide-react";
import { fetchHistory, type GenerationRecord } from "@/lib/api";
import { CopyableMdx } from "./MdxOutputBox";

interface GenerationHistoryProps {
  refreshKey: number;
}

function statusBadge(status: string) {
  const map: Record<string, string> = {
    complete:
      "bg-emerald-500/[0.08] text-emerald-300 border-emerald-500/[0.18]",
    error: "bg-rose-500/[0.08] text-rose-300 border-rose-500/[0.18]",
    partial: "bg-amber-500/[0.08] text-amber-300 border-amber-500/[0.18]",
  };
  const cls = map[status] ?? "bg-white/[0.04] text-white/60 border-white/[0.1]";
  return (
    <span
      className={`shrink-0 rounded-full border px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider ${cls}`}
    >
      {status}
    </span>
  );
}

export default function GenerationHistory({
  refreshKey,
}: GenerationHistoryProps) {
  const [records, setRecords] = useState<GenerationRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<Set<number>>(new Set());

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    fetchHistory()
      .then((rows) => {
        if (!cancelled) setRecords(rows);
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "failed to load history");
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [refreshKey]);

  function toggle(id: number) {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  return (
    <section className="flex flex-col gap-4">
      <div className="flex items-center gap-2">
        <HistoryIcon className="h-3.5 w-3.5 text-white/50" />
        <span className="text-xs uppercase tracking-[0.2em] text-white/40">
          History
        </span>
      </div>

      {loading && <p className="text-sm text-white/50">Loading…</p>}
      {error && (
        <p className="rounded-md border border-rose-500/[0.2] bg-rose-500/[0.06] px-3 py-2 text-sm text-rose-300">
          {error}
        </p>
      )}
      {!loading && !error && records.length === 0 && (
        <p className="rounded-xl border border-dashed border-white/[0.08] bg-white/[0.01] px-5 py-8 text-center text-sm text-white/40">
          No generations yet. Submit a topic above to get started.
        </p>
      )}

      <ul className="flex flex-col gap-2">
        {records.map((rec, i) => {
          const open = expanded.has(rec.id);
          return (
            <motion.li
              key={rec.id}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{
                duration: 0.4,
                delay: Math.min(i * 0.04, 0.3),
                ease: [0.25, 0.4, 0.25, 1] as const,
              }}
              className="overflow-hidden rounded-xl border border-white/[0.08] bg-white/[0.02] backdrop-blur-sm"
            >
              <button
                type="button"
                onClick={() => toggle(rec.id)}
                className="flex w-full items-center justify-between gap-3 px-5 py-3.5 text-left hover:bg-white/[0.02] transition-colors"
                aria-expanded={open}
              >
                <div className="min-w-0 flex-1">
                  <p className="font-mono text-[11px] uppercase tracking-wider text-white/35">
                    {new Date(rec.created_at).toLocaleString()}
                  </p>
                  <p className="mt-1 truncate text-sm font-medium text-white/85">
                    {rec.topics.join(", ")}
                  </p>
                </div>
                {statusBadge(rec.overall_status)}
                <ChevronDown
                  className={`h-4 w-4 text-white/40 transition-transform ${open ? "rotate-180" : ""}`}
                />
              </button>

              <AnimatePresence initial={false}>
                {open && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{
                      duration: 0.35,
                      ease: [0.25, 0.4, 0.25, 1] as const,
                    }}
                    className="overflow-hidden"
                  >
                    <div className="flex flex-col gap-5 border-t border-white/[0.06] px-5 py-4">
                      {rec.mdx_outputs.map((out, idx) => (
                        <div
                          key={`${rec.id}-${idx}`}
                          className="flex flex-col gap-2"
                        >
                          <div className="flex items-center justify-between gap-3">
                            <span className="text-sm font-medium text-white/85 break-words">
                              {out.topic}
                            </span>
                            {statusBadge(out.status)}
                          </div>
                          {out.mdx ? (
                            <CopyableMdx mdx={out.mdx} />
                          ) : (
                            <p className="text-xs text-white/40">
                              No MDX produced.
                            </p>
                          )}
                        </div>
                      ))}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.li>
          );
        })}
      </ul>
    </section>
  );
}
