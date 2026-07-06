"use client";

import * as React from "react";
import { Bot } from "lucide-react";
import { useAgents } from "@/hooks/api";
import { PageHeader } from "@/components/layout/page-header";
import { SectionCard } from "@/components/ui/section-card";
import { DecisionBadge, Pill, RiskLevelBadge, ScoreBadge } from "@/components/ui/badges";
import { EmptyState, ErrorCard, Skeleton } from "@/components/ui/states";
import { AgentDrawer } from "@/components/agents/agent-drawer";
import { formatRelativeTime, titleCase } from "@/lib/format";
import type { Agent } from "@/lib/api/types";

const SOURCES = ["", "code", "runtime"];
const RISK_LEVELS = ["", "CRITICAL", "HIGH", "MEDIUM", "LOW", "MINIMAL"];

export default function AgentsPage() {
  const [source, setSource] = React.useState("");
  const [riskLevel, setRiskLevel] = React.useState("");
  const [selected, setSelected] = React.useState<Agent | null>(null);

  const { data, isLoading, isError, error } = useAgents({
    source: source || undefined,
    risk_level: riskLevel || undefined,
  });

  return (
    <div>
      <PageHeader
        title="Discovered Agents"
        description="Every AI agent found across code and runtime, scored and governed."
      />

      <div className="mb-4 flex flex-wrap items-center gap-3">
        <Filter label="Source" value={source} options={SOURCES} onChange={setSource} format={(v) => v || "All"} />
        <Filter
          label="Risk"
          value={riskLevel}
          options={RISK_LEVELS}
          onChange={setRiskLevel}
          format={(v) => v || "All"}
        />
        {data && <span className="text-sm text-muted-foreground">{data.total} agent(s)</span>}
      </div>

      {isError && <ErrorCard message={(error as Error)?.message ?? "Failed to load agents"} />}

      <SectionCard padding="none">
        {isLoading ? (
          <div className="flex flex-col gap-2 p-5">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className="h-10" />
            ))}
          </div>
        ) : data && data.agents.length === 0 ? (
          <div className="p-5">
            <EmptyState
              icon={<Bot />}
              title="No agents match these filters"
              description="Adjust filters or run a new discovery scan."
            />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-left text-xs uppercase tracking-wider text-muted-foreground">
                  <th className="px-4 py-3 font-medium">Agent</th>
                  <th className="px-4 py-3 font-medium">Framework</th>
                  <th className="px-4 py-3 font-medium">Source</th>
                  <th className="px-4 py-3 font-medium">Owner</th>
                  <th className="px-4 py-3 font-medium">Autonomy</th>
                  <th className="px-4 py-3 font-medium">Risk</th>
                  <th className="px-4 py-3 font-medium">Verdict</th>
                  <th className="px-4 py-3 font-medium">Last seen</th>
                </tr>
              </thead>
              <tbody>
                {data?.agents.map((agent) => (
                  <tr
                    key={agent.agent_id}
                    className="cursor-pointer border-b border-border transition-colors last:border-0 hover:bg-accent/50"
                    onClick={() => setSelected(agent)}
                  >
                    <td className="max-w-xs px-4 py-3">
                      <div className="truncate font-medium">{agent.name}</div>
                      <div className="truncate text-xs text-muted-foreground">{agent.tool_count} tool(s)</div>
                    </td>
                    <td className="px-4 py-3">
                      <Pill>{titleCase(agent.framework)}</Pill>
                    </td>
                    <td className="px-4 py-3 text-muted-foreground">{agent.source}</td>
                    <td className="px-4 py-3">
                      {agent.owner === "unassigned" ? (
                        <span className="text-amber-600 dark:text-amber-400">unassigned</span>
                      ) : (
                        agent.owner
                      )}
                    </td>
                    <td className="px-4 py-3 text-muted-foreground">{titleCase(agent.autonomy_level)}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <ScoreBadge value={agent.risk_score} />
                        <RiskLevelBadge level={agent.risk_level} />
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <DecisionBadge decision={agent.final_decision} />
                    </td>
                    <td className="px-4 py-3 text-muted-foreground">{formatRelativeTime(agent.last_seen)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </SectionCard>

      {selected && <AgentDrawer agent={selected} onClose={() => setSelected(null)} />}
    </div>
  );
}

function Filter({
  label,
  value,
  options,
  onChange,
  format,
}: {
  label: string;
  value: string;
  options: string[];
  onChange: (v: string) => void;
  format: (v: string) => string;
}) {
  return (
    <label className="flex items-center gap-2 text-sm">
      <span className="text-muted-foreground">{label}</span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="rounded-md border border-border bg-background px-2 py-1.5 text-sm outline-none focus:ring-2 focus:ring-ring"
      >
        {options.map((opt) => (
          <option key={opt} value={opt}>
            {format(opt)}
          </option>
        ))}
      </select>
    </label>
  );
}
