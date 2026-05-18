"use client";

import { useState } from "react";
import { motion } from "motion/react";
import { Sparkles, Loader2 } from "lucide-react";

interface TopicFormProps {
  disabled?: boolean;
  onSubmit: (topicsRaw: string) => void;
}

export default function TopicForm({ disabled, onSubmit }: TopicFormProps) {
  const [value, setValue] = useState("");

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = value.trim();
    if (!trimmed) return;
    onSubmit(trimmed);
  }

  return (
    <motion.section
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, ease: [0.25, 0.4, 0.25, 1] as const }}
      className="rounded-2xl border border-white/[0.08] bg-white/[0.02] p-6 md:p-8 backdrop-blur-sm"
    >
      <div className="flex items-center gap-2 mb-1">
        <Sparkles className="h-3.5 w-3.5 text-white/50" />
        <span className="text-xs uppercase tracking-[0.2em] text-white/40">
          New generation
        </span>
      </div>
      <h2 className="text-xl font-semibold tracking-tight text-white/95">
        What should the agent write today?
      </h2>

      <form className="mt-6 flex flex-col gap-4" onSubmit={handleSubmit}>
        <label className="flex flex-col gap-2">
          <span className="sr-only">Topics</span>
          <textarea
            rows={4}
            value={value}
            onChange={(e) => setValue(e.target.value)}
            placeholder="Enter topics, one per line or comma-separated&#10;e.g. Bloom filters, Rust ownership, Postgres MVCC"
            disabled={disabled}
            className="w-full rounded-md bg-white/[0.03] border border-white/[0.1] px-3 py-2.5 text-sm text-white placeholder:text-white/30 focus:outline-none focus:border-white/[0.3] focus:bg-white/[0.05] transition-colors resize-none font-mono leading-relaxed"
          />
        </label>

        <div className="flex items-center justify-between gap-3">
          <p className="text-xs text-white/35">
            Topics run sequentially. Agent fan-outs internally.
          </p>
          <button
            type="submit"
            disabled={disabled || !value.trim()}
            className="group inline-flex items-center gap-2 min-h-10 rounded-md bg-white px-5 py-2 text-sm font-medium text-[#030303] hover:bg-white/90 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            {disabled ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Running
              </>
            ) : (
              <>
                Generate
                <Sparkles className="h-3.5 w-3.5" />
              </>
            )}
          </button>
        </div>
      </form>
    </motion.section>
  );
}
