const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

let accessToken: string | null = null;
const listeners = new Set<(token: string | null) => void>();

function notify() {
  for (const cb of listeners) cb(accessToken);
}

export function getAccessToken(): string | null {
  return accessToken;
}

export function setAccessToken(token: string | null) {
  accessToken = token;
  notify();
}

export function subscribe(cb: (token: string | null) => void): () => void {
  listeners.add(cb);
  return () => listeners.delete(cb);
}

export interface AuthError extends Error {
  status?: number;
}

function authError(message: string, status?: number): AuthError {
  const err = new Error(message) as AuthError;
  err.status = status;
  return err;
}

async function parseDetail(res: Response): Promise<string> {
  try {
    const data = (await res.json()) as { detail?: unknown };
    if (typeof data.detail === "string") return data.detail;
    return JSON.stringify(data.detail ?? data);
  } catch {
    return res.statusText || "request failed";
  }
}

export async function register(email: string, password: string): Promise<void> {
  const res = await fetch(`${API_URL}/auth/register`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) throw authError(await parseDetail(res), res.status);
}

export async function login(email: string, password: string): Promise<string> {
  const res = await fetch(`${API_URL}/auth/login`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) throw authError(await parseDetail(res), res.status);
  const data = (await res.json()) as { access_token: string };
  setAccessToken(data.access_token);
  return data.access_token;
}

let refreshInFlight: Promise<string | null> | null = null;

export async function refresh(): Promise<string | null> {
  if (refreshInFlight) return refreshInFlight;
  refreshInFlight = (async () => {
    try {
      const res = await fetch(`${API_URL}/auth/refresh`, {
        method: "POST",
        credentials: "include",
      });
      if (!res.ok) {
        setAccessToken(null);
        return null;
      }
      const data = (await res.json()) as { access_token: string };
      setAccessToken(data.access_token);
      return data.access_token;
    } catch {
      setAccessToken(null);
      return null;
    } finally {
      refreshInFlight = null;
    }
  })();
  return refreshInFlight;
}

export async function bootstrapAuth(): Promise<string | null> {
  if (accessToken) return accessToken;
  return refresh();
}

export async function logout(): Promise<void> {
  try {
    await fetch(`${API_URL}/auth/logout`, {
      method: "POST",
      credentials: "include",
    });
  } finally {
    setAccessToken(null);
  }
}

export function apiUrl(path: string): string {
  return `${API_URL}${path}`;
}
