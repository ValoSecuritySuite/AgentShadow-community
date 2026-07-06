import * as React from "react";
import { cn } from "@/lib/utils";
import { bandFromLevel, bandFromScore, formatScore, type ScoreBand } from "@/lib/format";
import type { PolicyDecisionLiteral } from "@/lib/api/types";

const bandClasses: Record<ScoreBand, string> = {
  critical: "border-red-200 bg-red-50 text-red-700 dark:border-red-900/50 dark:bg-red-950/50 dark:text-red-300",
  high: "border-orange-200 bg-orange-50 text-orange-700 dark:border-orange-900/50 dark:bg-orange-950/50 dark:text-orange-300",
  medium: "border-amber-200 bg-amber-50 text-amber-700 dark:border-amber-900/50 dark:bg-amber-950/50 dark:text-amber-300",
  low: "border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-900/50 dark:bg-emerald-950/50 dark:text-emerald-300",
  neutral: "border-border bg-muted text-muted-foreground",
};

const baseBadge =
  "inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-semibold tabular-nums";

export function ScoreBadge({ value }: { value: number | null | undefined }) {
  return <span className={cn(baseBadge, bandClasses[bandFromScore(value)])}>{formatScore(value, 1)}</span>;
}

export function RiskLevelBadge({ level }: { level: string }) {
  return <span className={cn(baseBadge, bandClasses[bandFromLevel(level)])}>{level}</span>;
}

const decisionClasses: Record<PolicyDecisionLiteral, string> = {
  deny: bandClasses.critical,
  warn: bandClasses.medium,
  allow: bandClasses.low,
};

export function DecisionBadge({ decision }: { decision: PolicyDecisionLiteral }) {
  return <span className={cn(baseBadge, decisionClasses[decision])}>{decision.toUpperCase()}</span>;
}

export function Pill({ children, tone = "neutral" }: { children: React.ReactNode; tone?: ScoreBand }) {
  return <span className={cn(baseBadge, "font-medium", bandClasses[tone])}>{children}</span>;
}
