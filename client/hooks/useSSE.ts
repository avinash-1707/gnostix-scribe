"use client";

import { useEffect, useRef, useState } from "react";
import type { NodeEvent } from "@/lib/api";

export interface SSEState {
  events: NodeEvent[];
  status: "idle" | "open" | "closed" | "error";
  error: string | null;
}

export function useSSE(url: string | null, expectedTopics = 1): SSEState {
  const [events, setEvents] = useState<NodeEvent[]>([]);
  const [status, setStatus] = useState<SSEState["status"]>("idle");
  const [error, setError] = useState<string | null>(null);
  const sourceRef = useRef<EventSource | null>(null);
  const terminalTopicsRef = useRef<Set<string>>(new Set());

  useEffect(() => {
    if (!url) {
      setEvents([]);
      setStatus("idle");
      setError(null);
      return;
    }
    setEvents([]);
    setError(null);
    setStatus("open");
    terminalTopicsRef.current = new Set();

    const es = new EventSource(url);
    sourceRef.current = es;

    es.onmessage = (msg) => {
      try {
        const parsed = JSON.parse(msg.data) as NodeEvent;
        setEvents((prev) => [...prev, parsed]);
        if (parsed.node === "DONE" || parsed.node === "ERROR") {
          // Topics stream concurrently — close only once every topic has
          // reached a terminal event. A topic-less ERROR is stream-fatal.
          terminalTopicsRef.current.add(parsed.topic);
          if (
            !parsed.topic ||
            terminalTopicsRef.current.size >= expectedTopics
          ) {
            es.close();
            setStatus("closed");
          }
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "parse error");
      }
    };

    es.onerror = () => {
      setStatus("error");
      es.close();
    };

    return () => {
      es.close();
      sourceRef.current = null;
    };
  }, [url]);

  return { events, status, error };
}
