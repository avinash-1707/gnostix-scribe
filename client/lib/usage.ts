import { fetchUsage, type Usage } from "./api";
import { getAccessToken, subscribe as subscribeAuth } from "./auth";

let usage: Usage | null = null;
const listeners = new Set<(u: Usage | null) => void>();

function notify() {
  for (const cb of listeners) cb(usage);
}

export function getUsage(): Usage | null {
  return usage;
}

export function subscribe(cb: (u: Usage | null) => void): () => void {
  listeners.add(cb);
  return () => {
    listeners.delete(cb);
  };
}

let inFlight: Promise<Usage | null> | null = null;

export async function refreshUsage(): Promise<Usage | null> {
  if (!getAccessToken()) {
    usage = null;
    notify();
    return null;
  }
  if (inFlight) return inFlight;
  inFlight = (async () => {
    try {
      const u = await fetchUsage();
      usage = u;
      notify();
      return u;
    } catch {
      usage = null;
      notify();
      return null;
    } finally {
      inFlight = null;
    }
  })();
  return inFlight;
}

let started = false;
export function startUsageAuthSync(): () => void {
  if (started) return () => {};
  started = true;
  return subscribeAuth((tok) => {
    if (tok) {
      void refreshUsage();
    } else {
      usage = null;
      notify();
    }
  });
}
