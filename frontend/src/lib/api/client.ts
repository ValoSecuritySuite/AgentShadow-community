/**
 * Centralized API client for the AgentShadow frontend.
 * Forked from SaaSShadow's client: timeout-aware fetch, normalized errors,
 * JSON + blob helpers. Native fetch (no axios).
 */
import { getApiBaseUrl, getApiKey } from "./config";

const DEFAULT_TIMEOUT_MS = 30_000;
const DEFAULT_HEADERS: Record<string, string> = {
  "Content-Type": "application/json",
  Accept: "application/json",
};

function authHeaders(): Record<string, string> {
  const key = getApiKey();
  return key ? { "X-API-Key": key } : {};
}

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly code?: string,
    public readonly detail?: unknown,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

function buildUrl(path: string, query?: Record<string, string>): string {
  const base = getApiBaseUrl().replace(/\/$/, "");
  const pathNorm = path.startsWith("/") ? path : `/${path}`;
  const url = `${base}${pathNorm}`;
  if (!query || Object.keys(query).length === 0) return url;
  const params = new URLSearchParams(query);
  return `${url}?${params.toString()}`;
}

function withTimeout(timeoutMs: number): AbortSignal {
  const controller = new AbortController();
  setTimeout(() => controller.abort(), timeoutMs);
  return controller.signal;
}

function parseErrorBody(text: string): { message?: string; detail?: unknown } {
  try {
    const data = JSON.parse(text) as Record<string, unknown>;
    if (typeof data.detail === "string") return { message: data.detail };
    // Structured upgrade_required payload from the Community Edition gate.
    if (data.detail && typeof data.detail === "object") {
      const d = data.detail as Record<string, unknown>;
      if (typeof d.message === "string") return { message: d.message, detail: d };
    }
    return { message: typeof data.message === "string" ? data.message : undefined, detail: data.detail };
  } catch {
    return { message: text || undefined };
  }
}

export async function requestJson<T>(
  path: string,
  init: RequestInit & { query?: Record<string, string>; timeoutMs?: number } = {},
): Promise<T> {
  const { query, timeoutMs = DEFAULT_TIMEOUT_MS, ...fetchInit } = init;
  const url = buildUrl(path, query);
  let res: Response;
  try {
    res = await fetch(url, {
      ...fetchInit,
      headers: {
        ...DEFAULT_HEADERS,
        ...authHeaders(),
        ...(fetchInit.headers as Record<string, string>),
      },
      signal: withTimeout(timeoutMs),
    });
  } catch (e) {
    if (e instanceof Error && e.name === "AbortError") {
      throw new ApiError("Request timeout", 408, "TIMEOUT");
    }
    throw new ApiError(e instanceof Error ? e.message : String(e), 0, "NETWORK_ERROR", e);
  }

  const text = await res.text();
  if (!res.ok) {
    const parsed = parseErrorBody(text);
    const code = res.status === 402 ? "UPGRADE_REQUIRED" : undefined;
    throw new ApiError(parsed.message ?? `API error ${res.status}`, res.status, code, parsed.detail);
  }
  if (text.trim() === "") return {} as T;
  return JSON.parse(text) as T;
}

export async function requestBlob(
  path: string,
  init: RequestInit & { query?: Record<string, string>; timeoutMs?: number } = {},
): Promise<{ blob: Blob; filename: string | null }> {
  const { query, timeoutMs = 60_000, ...fetchInit } = init;
  const url = buildUrl(path, query);
  const extraHeaders = (fetchInit.headers as Record<string, string> | undefined) ?? {};
  const headers: Record<string, string> = {
    Accept: "application/pdf",
    ...authHeaders(),
    ...extraHeaders,
  };
  if (fetchInit.body != null && !headers["Content-Type"] && !headers["content-type"]) {
    headers["Content-Type"] = "application/json";
  }
  const res = await fetch(url, {
    ...fetchInit,
    headers,
    signal: withTimeout(timeoutMs),
  });
  if (!res.ok) {
    const parsed = parseErrorBody(await res.text());
    const code = res.status === 402 ? "UPGRADE_REQUIRED" : undefined;
    throw new ApiError(parsed.message ?? `API error ${res.status}`, res.status, code);
  }
  const blob = await res.blob();
  const disposition = res.headers.get("Content-Disposition");
  let filename: string | null = null;
  if (disposition) {
    const match = /filename="?([^";\n]+)"?/.exec(disposition);
    if (match) filename = match[1].trim();
  }
  return { blob, filename };
}
