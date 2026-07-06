/**
 * API base URL for the AgentShadow frontend.
 * Set NEXT_PUBLIC_API_URL in .env.local (dev) or the deployment environment.
 */
export const DEFAULT_API_BASE_URL = "http://127.0.0.1:8013";

export function getApiBaseUrl(): string {
  const raw = process.env.NEXT_PUBLIC_API_URL?.trim();
  if (raw) return raw.replace(/\/+$/, "");
  return DEFAULT_API_BASE_URL;
}

/**
 * Optional API key sent as `X-API-Key` when the backend enforces access
 * control. Leave NEXT_PUBLIC_API_KEY unset for an open (demo) backend.
 */
export function getApiKey(): string | undefined {
  const raw = process.env.NEXT_PUBLIC_API_KEY?.trim();
  return raw ? raw : undefined;
}
