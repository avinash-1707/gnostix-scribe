"use client";

import { useEffect, useRef, useState } from "react";
import { motion } from "motion/react";
import { Sparkles, Loader2, X } from "lucide-react";
import type { Usage } from "@/lib/api";
import { getUsage, subscribe as subscribeUsage } from "@/lib/usage";

interface TopicFormProps {
  disabled?: boolean;
  onSubmit: (topicsRaw: string) => void;
}

export default function TopicForm({ disabled, onSubmit }: TopicFormProps) {
  const [chips, setChips] = useState<string[]>([]);
  const [draft, setDraft] = useState("");
  const [usage, setUsage] = useState<Usage | null>(getUsage());
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    setUsage(getUsage());
    return subscribeUsage(setUsage);
  }, []);

  const remaining = usage?.remaining ?? 0;
  const atCap = chips.length >= remaining;
  const quotaExhausted = usage !== null && remaining === 0;

  function commitDraft(): boolean {
    const t = draft.trim();
    if (!t) return false;
    setDraft("");
    if (chips.includes(t)) return false;
    if (atCap) return false;
    setChips([...chips, t]);
    return true;
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter") {
      e.preventDefault();
      commitDraft();
    } else if (e.key === ",") {
      e.preventDefault();
      commitDraft();
    } else if (e.key === "Backspace" && !draft && chips.length > 0) {
      setChips(chips.slice(0, -1));
    }
  }

  function removeChip(idx: number) {
    setChips(chips.filter((_, i) => i !== idx));
    inputRef.current?.focus();
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const list = [...chips];
    const last = draft.trim();
    if (last && !list.includes(last) && list.length < remaining) {
      list.push(last);
    }
    if (!list.length) return;
    onSubmit(list.join(","));
    setChips([]);
    setDraft("");
  }

  const canSubmit =
    !disabled && !quotaExhausted && (chips.length > 0 || draft.trim().length > 0);

  return (
    <motion.section
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, ease: [0.25, 0.4, 0.25, 1] as const }}
      className="rounded-2xl border border-white/[0.08] bg-white/[0.02] p-6 md:p-8 backdrop-blur-sm"
    >
      <div className="flex items-center justify-between gap-2 mb-1">
        <div className="flex items-center gap-2">
          <Sparkles className="h-3.5 w-3.5 text-white/50" />
          <span className="text-xs uppercase tracking-[0.2em] text-white/40">
            New generation
          </span>
        </div>
        {usage && (
          <span className="text-xs text-white/40">
            <span className="text-white/80 font-medium">{remaining}</span> of{" "}
            {usage.limit} topics left
          </span>
        )}
      </div>
      <h2 className="text-xl font-semibold tracking-tight text-white/95">
        What should the agent write today?
      </h2>

      <form className="mt-6 flex flex-col gap-4" onSubmit={handleSubmit}>
        <div
          onClick={() => inputRef.current?.focus()}
          className="flex min-h-[3.25rem] w-full flex-wrap items-center gap-2 rounded-md border border-white/[0.1] bg-white/[0.03] px-3 py-2.5 transition-colors focus-within:border-white/[0.3] focus-within:bg-white/[0.05]"
        >
          {chips.map((chip, i) => (
            <motion.span
              key={`${chip}-${i}`}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.15 }}
              className="inline-flex items-center gap-1.5 rounded-md border border-white/[0.12] bg-white/[0.06] pl-2.5 pr-1 py-1 text-sm text-white/90"
            >
              <span className="break-all">{chip}</span>
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  removeChip(i);
                }}
                disabled={disabled}
                className="inline-flex h-5 w-5 items-center justify-center rounded-sm text-white/50 hover:text-white hover:bg-white/[0.1] transition-colors disabled:opacity-40"
                aria-label={`Remove ${chip}`}
              >
                <X className="h-3 w-3" />
              </button>
            </motion.span>
          ))}
          <input
            ref={inputRef}
            type="text"
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={handleKeyDown}
            onBlur={() => commitDraft()}
            disabled={disabled || quotaExhausted || atCap}
            placeholder={
              quotaExhausted
                ? "Quota exhausted"
                : atCap
                  ? `Cap reached (${remaining})`
                  : chips.length === 0
                    ? "Type a topic and press Enter…"
                    : "Add another…"
            }
            className="flex-1 min-w-[10rem] bg-transparent text-sm text-white placeholder:text-white/30 focus:outline-none disabled:cursor-not-allowed"
          />
        </div>

        <div className="flex items-center justify-between gap-3">
          <p className="text-xs text-white/35">
            Press Enter or comma to add. Backspace removes last.
          </p>
          <button
            type="submit"
            disabled={!canSubmit}
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
