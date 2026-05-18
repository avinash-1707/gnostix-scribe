"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import TopicForm from "@/components/TopicForm";
import AgentProgressPanel from "@/components/AgentProgressPanel";
import MdxOutputBox from "@/components/MdxOutputBox";
import GenerationHistory from "@/components/GenerationHistory";
import { useSSE } from "@/hooks/useSSE";
import { generateStreamUrl, type NodeEvent } from "@/lib/api";
import { getAccessToken, refresh } from "@/lib/auth";

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
      if (getAccessToken()) {
        if (!cancelled) setBootstrapping(false);
        return;
      }
      const token = await refresh();
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
      <div className="mx-auto max-w-4xl px-4 py-8">
        <p className="text-sm text-gray-500">Loading…</p>
      </div>
    );
  }

  return (
    <div className="mx-auto flex max-w-4xl flex-col gap-6 px-4 py-6 md:py-8">
      <TopicForm disabled={running} onSubmit={handleSubmit} />

      {topics.length > 0 && (
        <section className="flex flex-col gap-4">
          <h2 className="text-lg font-semibold text-gray-900">Agent progress</h2>
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

      {topics.some((t) => perTopic.get(t)?.state.mdx || perTopic.get(t)?.state.errorMsg) && (
        <section className="flex flex-col gap-6">
          <h2 className="text-lg font-semibold text-gray-900">Output</h2>
          {topics.map((topic) => {
            const entry = perTopic.get(topic)!;
            if (entry.state.mdx) {
              return <MdxOutputBox key={topic} topic={topic} mdx={entry.state.mdx} />;
            }
            if (entry.state.errorMsg) {
              return (
                <div key={topic} className="flex flex-col gap-2">
                  <h3 className="text-sm font-semibold text-gray-900 break-words">
                    {topic}
                  </h3>
                  <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-600">
                    {entry.state.errorMsg}
                  </p>
                </div>
              );
            }
            return null;
          })}
        </section>
      )}

      <GenerationHistory refreshKey={historyKey} />
    </div>
  );
}
