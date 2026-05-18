"use client";

import { useEffect, useState } from "react";
import { fetchHistory, type GenerationRecord } from "@/lib/api";
import { CopyableMdx } from "./MdxOutputBox";

interface GenerationHistoryProps {
  refreshKey: number;
}

function statusBadge(status: string) {
  const map: Record<string, string> = {
    complete: "bg-green-50 text-green-600",
    error: "bg-red-50 text-red-600",
    partial: "bg-yellow-50 text-yellow-700",
  };
  const cls = map[status] ?? "bg-gray-50 text-gray-600";
  return (
    <span className={`rounded px-2 py-0.5 text-xs font-medium ${cls}`}>
      {status}
    </span>
  );
}

export default function GenerationHistory({ refreshKey }: GenerationHistoryProps) {
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
    <section className="flex flex-col gap-3">
      <h2 className="text-lg font-semibold text-gray-900">History</h2>
      {loading && <p className="text-sm text-gray-500">Loading…</p>}
      {error && <p className="text-sm text-red-600">{error}</p>}
      {!loading && !error && records.length === 0 && (
        <p className="text-sm text-gray-500">No generations yet.</p>
      )}
      <ul className="flex flex-col gap-2">
        {records.map((rec) => {
          const open = expanded.has(rec.id);
          return (
            <li
              key={rec.id}
              className="rounded-lg border border-gray-200 bg-white"
            >
              <button
                type="button"
                onClick={() => toggle(rec.id)}
                className="flex w-full items-center justify-between gap-3 px-4 py-3 text-left"
              >
                <div className="min-w-0 flex-1">
                  <p className="text-xs text-gray-500">
                    {new Date(rec.created_at).toLocaleString()}
                  </p>
                  <p className="truncate text-sm font-medium text-gray-900">
                    {rec.topics.join(", ")}
                  </p>
                </div>
                {statusBadge(rec.overall_status)}
              </button>
              {open && (
                <div className="flex flex-col gap-4 border-t border-gray-100 px-4 py-3">
                  {rec.mdx_outputs.map((out, idx) => (
                    <div key={`${rec.id}-${idx}`} className="flex flex-col gap-2">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium text-gray-700 break-words">
                          {out.topic}
                        </span>
                        {statusBadge(out.status)}
                      </div>
                      {out.mdx ? (
                        <CopyableMdx mdx={out.mdx} />
                      ) : (
                        <p className="text-xs text-gray-500">No MDX produced.</p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </li>
          );
        })}
      </ul>
    </section>
  );
}
