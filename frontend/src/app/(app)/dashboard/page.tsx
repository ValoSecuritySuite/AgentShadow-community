"use client";

import Link from "next/link";
import { AlertTriangle, Bot, ShieldAlert, UserX, Zap } from "lucide-react";
import { useDashboard } from "@/hooks/api";
import { PageHeader } from "@/components/layout/page-header";
import { StatCard } from "@/components/ui/stat-card";
import { SectionCard } from "@/components/ui/section-card";
import { Pill, ScoreBadge } from "@/components/ui/badges";
import { Button } from "@/components/ui/button";
import { EmptyState, ErrorCard, Skeleton } from "@/components/ui/states";
import { titleCase, type ScoreBand } from "@/lib/format";
import type { RiskDistribution } from "@/lib/api/types";

const RISK_BARS: { key: keyof RiskDistribution; label: string; tone: ScoreBand }[] = [
  { key: "critical", label: "Critical", tone: "critical" },
  { key: "high", label: "High", tone: "high" },
  { key: "medium", label: "Medium", tone: "medium" },
  { key: "low", label: "Low", tone: "low" },
  { key: "minimal", label: "Minimal", tone: "neutral" },
];

const barColor: Record<ScoreBand, string> = {
  critical: "bg-red-500",
  high: "bg-orange-500",
  medium: "bg-amber-500",
  low: "bg-emerald-500",
  neutral: "bg-slate-400",
};

export default function DashboardPage() {
  const { data, isLoading, isError, error } = useDashboard();

  return (
    <div>
      <PageHeader
        title="Executive Dashboard"
        description="Organization-wide AI agent posture at a glance."
        action={
          <Link href="/scan">
            <Button>Run discovery</Button>
          </Link>
        }
      />

      {isError && <ErrorCard message={(error as Error)?.message ?? "Failed to load dashboard"} />}

      {isLoading ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-28" />
          ))}
        </div>
      ) : data && data.total_agents === 0 ? (
        <EmptyState
          icon={<Bot />}
          title="No agents discovered yet"
          description="Run a code scan or sync a runtime connector to populate your agent inventory."
          action={
            <Link href="/scan">
              <Button>Go to Discovery</Button>
            </Link>
          }
        />
      ) : data ? (
        <div className="flex flex-col gap-6">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5">
            <StatCard label="Total agents" value={data.total_agents} icon={<Bot />} />
            <StatCard
              label="High risk"
              value={data.high_risk_agents}
              accent="danger"
              icon={<ShieldAlert />}
              subtitle="score >= 60"
            />
            <StatCard
              label="High autonomy"
              value={data.high_autonomy_agents}
              accent="warning"
              icon={<Zap />}
            />
            <StatCard label="Unmanaged" value={data.unmanaged_agents} icon={<UserX />} subtitle="no owner" />
            <StatCard
              label="Avg risk score"
              value={data.average_risk_score.toFixed(1)}
              icon={<AlertTriangle />}
            />
          </div>

          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <SectionCard title="Risk distribution" description="Agents grouped by risk band">
              <div className="flex flex-col gap-3">
                {RISK_BARS.map((bar) => {
                  const count = data.risk_distribution[bar.key];
                  const pct = data.total_agents ? Math.round((count / data.total_agents) * 100) : 0;
                  return (
                    <div key={bar.key}>
                      <div className="mb-1 flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">{bar.label}</span>
                        <span className="font-medium tabular-nums">{count}</span>
                      </div>
                      <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
                        <div className={`h-full ${barColor[bar.tone]}`} style={{ width: `${pct}%` }} />
                      </div>
                    </div>
                  );
                })}
              </div>
            </SectionCard>

            <SectionCard title="By framework" description="Agent count and average risk per framework">
              {data.by_framework.length === 0 ? (
                <p className="text-sm text-muted-foreground">No frameworks detected.</p>
              ) : (
                <div className="flex flex-col divide-y divide-border">
                  {data.by_framework.map((fw) => (
                    <div key={fw.framework} className="flex items-center justify-between py-2.5">
                      <div className="flex items-center gap-2">
                        <Pill>{titleCase(fw.framework)}</Pill>
                        <span className="text-sm text-muted-foreground">{fw.count} agent(s)</span>
                      </div>
                      <ScoreBadge value={fw.avg_risk} />
                    </div>
                  ))}
                </div>
              )}
            </SectionCard>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <StatCard
              label="Policy breaches"
              value={data.policy_breaches}
              accent="danger"
              subtitle="warn or deny verdicts"
            />
            <StatCard label="Discovered via code" value={data.by_source.code ?? 0} />
            <StatCard label="Discovered via runtime" value={data.by_source.runtime ?? 0} />
          </div>
        </div>
      ) : null}
    </div>
  );
}
