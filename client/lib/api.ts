import { apiUrl, getAccessToken, refresh } from "./auth";

export interface MdxOutput {
  topic: string;
  mdx: string;
  status: string;
  cloudinary_image_urls: string[];
}

export interface GenerationRecord {
  id: number;
  topics: string[];
  mdx_outputs: MdxOutput[];
  overall_status: string;
  created_at: string;
  completed_at: string | null;
}

export type NodeStatus = "pending" | "running" | "done" | "error";

export interface NodeEvent {
  node: string;
  status: NodeStatus;
  message: string;
  elapsed_ms: number;
  topic: string;
}

async function authedFetch(path: string, init: RequestInit = {}): Promise<Response> {
  const token = getAccessToken();
  const headers = new Headers(init.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);
  let res = await fetch(apiUrl(path), { ...init, headers, credentials: "include" });
  if (res.status === 401) {
    const newToken = await refresh();
    if (!newToken) return res;
    headers.set("Authorization", `Bearer ${newToken}`);
    res = await fetch(apiUrl(path), { ...init, headers, credentials: "include" });
  }
  return res;
}

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

async function detail(res: Response): Promise<string> {
  try {
    const j = (await res.json()) as { detail?: unknown };
    return typeof j.detail === "string" ? j.detail : JSON.stringify(j.detail ?? j);
  } catch {
    return res.statusText || "request failed";
  }
}

export interface Usage {
  used: number;
  limit: number;
  remaining: number;
}

export async function fetchUsage(): Promise<Usage> {
  const res = await authedFetch("/usage");
  if (!res.ok) throw new ApiError(await detail(res), res.status);
  return (await res.json()) as Usage;
}

export async function fetchHistory(): Promise<GenerationRecord[]> {
  const res = await authedFetch("/history");
  if (!res.ok) throw new ApiError(await detail(res), res.status);
  return (await res.json()) as GenerationRecord[];
}

export async function fetchRecord(id: number): Promise<GenerationRecord> {
  const res = await authedFetch(`/history/${id}`);
  if (!res.ok) throw new ApiError(await detail(res), res.status);
  return (await res.json()) as GenerationRecord;
}

export function generateStreamUrl(topicsRaw: string, token: string): string {
  const u = new URL(apiUrl("/generate"));
  u.searchParams.set("topics", topicsRaw);
  u.searchParams.set("token", token);
  return u.toString();
}
