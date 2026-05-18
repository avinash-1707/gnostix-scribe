"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "motion/react";
import { AlertCircle, Loader2 } from "lucide-react";
import TopicForm from "@/components/TopicForm";
import AgentProgressPanel from "@/components/AgentProgressPanel";
import MdxOutputBox from "@/components/MdxOutputBox";
import GenerationHistory from "@/components/GenerationHistory";
import { useSSE } from "@/hooks/useSSE";
import { generateStreamUrl, type NodeEvent } from "@/lib/api";
import { bootstrapAuth, getAccessToken } from "@/lib/auth";

interface TopicState {
  terminal: "DONE" | "ERROR" | null;
  mdx: string | null;
  errorMsg: string | null;
}

function parseTopics(raw: string): string[] {
  const seen = new Set<string>();
  const out: string[] = [];
  for (const part of raw.split(/[\n,]/)) {
    const t = part.trim();
    if (!t || seen.has(t)) continue;
    seen.add(t);
    out.push(t);
  }
  return out;
}

export default function DashboardPage() {
  const router = useRouter();
  const [bootstrapping, setBootstrapping] = useState(true);
  const [streamUrl, setStreamUrl] = useState<string | null>(null);
  const [topics, setTopics] = useState<string[]>([]);
  const [historyKey, setHistoryKey] = useState(0);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const token = await bootstrapAuth();
      if (cancelled) return;
      if (!token) router.replace("/login");
      else setBootstrapping(false);
    })();
    return () => {
      cancelled = true;
    };
  }, [router]);

  const { events, status } = useSSE(streamUrl);

  const perTopic = useMemo(() => {
    const map = new Map<string, { events: NodeEvent[]; state: TopicState }>();
    for (const t of topics) {
      map.set(t, {
        events: [],
        state: { terminal: null, mdx: null, errorMsg: null },
      });
    }
    for (const ev of events) {
      const entry = map.get(ev.topic);
      if (!entry) continue;
      if (ev.node === "DONE") {
        entry.state.terminal = "DONE";
        entry.state.mdx = ev.message;
      } else if (ev.node === "ERROR") {
        entry.state.terminal = "ERROR";
        entry.state.errorMsg = ev.message;
      } else {
        entry.events.push(ev);
      }
    }
    return map;
  }, [events, topics]);

  useEffect(() => {
    if (streamUrl && (status === "closed" || status === "error")) {
      setHistoryKey((k) => k + 1);
    }
  }, [status, streamUrl]);

  function handleSubmit(topicsRaw: string) {
    const parsed = parseTopics(topicsRaw);
    if (!parsed.length) return;
    const token = getAccessToken();
    if (!token) {
      router.replace("/login");
      return;
    }
    setTopics(parsed);
    setStreamUrl(generateStreamUrl(topicsRaw, token));
  }

  const running = streamUrl !== null && status === "open";

  if (bootstrapping) {
    return (
      <div className="mx-auto flex max-w-4xl items-center gap-2 px-4 py-12 text-sm text-white/50">
        <Loader2 className="h-4 w-4 animate-spin text-white/40" />
        Loading session…
      </div>
    );
  }

  const hasOutput = topics.some(
    (t) => perTopic.get(t)?.state.mdx || perTopic.get(t)?.state.errorMsg,
  );

  return (
    <div className="mx-auto flex max-w-4xl flex-col gap-8 px-4 py-10 md:py-14">
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: [0.25, 0.4, 0.25, 1] as const }}
      >
        <span className="text-xs uppercase tracking-[0.2em] text-white/40">
          Dashboard
        </span>
        <h1 className="mt-2 text-3xl md:text-4xl font-semibold tracking-tight text-white/95">
          Generate{" "}
          <span className="bg-clip-text text-transparent bg-gradient-to-r from-indigo-300 via-white/90 to-rose-300 italic font-light">
            publication-ready
          </span>{" "}
          MDX.
        </h1>
        <p className="mt-2 text-sm text-white/50 max-w-xl">
          Topic in. Live agent timeline out. Copy the MDX when the validator
          smiles.
        </p>
      </motion.div>

      <TopicForm disabled={running} onSubmit={handleSubmit} />

      {topics.length > 0 && (
        <section className="flex flex-col gap-4">
          <div className="flex items-center gap-2">
            <Loader2
              className={`h-3.5 w-3.5 text-white/50 ${running ? "animate-spin" : ""}`}
            />
            <span className="text-xs uppercase tracking-[0.2em] text-white/40">
              Agent progress
            </span>
          </div>
          {topics.map((topic) => {
            const entry = perTopic.get(topic)!;
            return (
              <AgentProgressPanel
                key={topic}
                topic={topic}
                events={entry.events}
                terminal={entry.state.terminal}
              />
            );
          })}
        </section>
      )}

      {hasOutput && (
        <section className="flex flex-col gap-5">
          <span className="text-xs uppercase tracking-[0.2em] text-white/40">
            Output
          </span>
          {topics.map((topic) => {
            const entry = perTopic.get(topic)!;
            if (entry.state.mdx) {
              return (
                <MdxOutputBox
                  key={topic}
                  topic={topic}
                  mdx={entry.state.mdx}
                />
              );
            }
            if (entry.state.errorMsg) {
              return (
                <div key={topic} className="flex flex-col gap-2">
                  <h3 className="text-base font-medium text-white/90 break-words tracking-tight">
                    {topic}
                  </h3>
                  <p className="flex items-center gap-2 rounded-md border border-rose-500/[0.2] bg-rose-500/[0.06] px-3 py-2 text-sm text-rose-300">
                    <AlertCircle className="h-3.5 w-3.5 shrink-0" />
                    {entry.state.errorMsg}
                  </p>
                </div>
              );
            }
            return null;
          })}
        </section>
      )}

      <div className="mt-2 h-px w-full bg-gradient-to-r from-transparent via-white/[0.08] to-transparent" />

      <GenerationHistory refreshKey={historyKey} />
    </div>
  );
}
