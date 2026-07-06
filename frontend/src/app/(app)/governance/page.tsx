"use client";

import { usePolicies } from "@/hooks/api";
import { PageHeader } from "@/components/layout/page-header";
import { SectionCard } from "@/components/ui/section-card";
import { DecisionBadge, Pill } from "@/components/ui/badges";
import { ErrorCard, Skeleton } from "@/components/ui/states";

export default function GovernancePage() {
  const { data, isLoading, isError, error } = usePolicies();

  return (
    <div>
      <PageHeader
        title="Governance"
        description="Policies evaluated against every discovered agent (reuses the Valo policy engine)."
      />

      {isError && <ErrorCard message={(error as Error)?.message ?? "Failed to load policies"} />}

      {isLoading ? (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-32" />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          {data?.policies.map((p) => (
            <SectionCard key={p.id} title={p.name} description={p.description ?? undefined}>
              <div className="flex flex-col gap-3">
                <div className="flex flex-wrap items-center gap-2">
                  <DecisionBadge decision={p.then.decision} />
                  <Pill tone={p.enforce ? "high" : "neutral"}>{p.enforce ? "enforced" : "monitor"}</Pill>
                  <Pill tone={p.enabled ? "low" : "neutral"}>{p.enabled ? "enabled" : "disabled"}</Pill>
                </div>
                <div className="rounded-md bg-muted/60 p-3 font-mono text-xs">
                  {p.when.length === 0 ? (
                    <span className="text-muted-foreground">matches every agent</span>
                  ) : (
                    p.when.map((c, i) => (
                      <div key={i}>
                        {c.field} {c.op} {JSON.stringify(c.value)}
                      </div>
                    ))
                  )}
                </div>
                <div className="text-sm text-muted-foreground">{p.then.message}</div>
                {p.tags.length > 0 && (
                  <div className="flex flex-wrap gap-1.5">
                    {p.tags.map((t) => (
                      <Pill key={t} tone="neutral">
                        {t}
                      </Pill>
                    ))}
                  </div>
                )}
              </div>
            </SectionCard>
          ))}
        </div>
      )}
    </div>
  );
}
