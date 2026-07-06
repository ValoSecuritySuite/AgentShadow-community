export type RiskLevel = "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "MINIMAL";

export type ScoreBand = "critical" | "high" | "medium" | "low" | "neutral";

export function bandFromScore(score: number | null | undefined): ScoreBand {
  if (score == null || Number.isNaN(score)) return "neutral";
  if (score >= 80) return "critical";
  if (score >= 60) return "high";
  if (score >= 40) return "medium";
  if (score >= 20) return "low";
  return "low";
}

export function bandFromLevel(level: string): ScoreBand {
  const l = level.toUpperCase();
  if (l === "CRITICAL") return "critical";
  if (l === "HIGH") return "high";
  if (l === "MEDIUM") return "medium";
  if (l === "LOW") return "low";
  return "neutral";
}

export function formatScore(value: number | null | undefined, decimals = 0): string {
  if (value == null || Number.isNaN(value)) return "—";
  return value.toFixed(decimals);
}

export function formatRelativeTime(iso: string | null | undefined): string {
  if (!iso) return "—";
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return "—";
  const diff = Date.now() - then;
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

export function titleCase(s: string): string {
  return s
    .replace(/[_-]/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}
