"use client";

import * as React from "react";
import { Download, X } from "lucide-react";
import type { Agent } from "@/lib/api/types";
import { Button } from "@/components/ui/button";
import { DecisionBadge, Pill, RiskLevelBadge, ScoreBadge } from "@/components/ui/badges";
import { ProBadge } from "@/components/ui/pro-badge";
import { UpgradeButton } from "@/components/upsell/upgrade-cta";
import { downloadAgentReport } from "@/lib/api/requests";
import { isLocked, LOCKED_FEATURES } from "@/lib/edition";
import { titleCase } from "@/lib/format";

export function AgentDrawer({ agent, onClose }: { agent: Agent; onClose: () => void }) {
  const [downloading, setDownloading] = React.useState(false);
  const [downloadError, setDownloadError] = React.useState<string | null>(null);
  const pdfLocked = isLocked("pdf_reports");

  async function handleDownload() {
    setDownloading(true);
    setDownloadError(null);
    try {
      await downloadAgentReport(agent);
    } catch (e) {
      setDownloadError(e instanceof Error ? e.message : "Failed to generate report");
    } finally {
      setDownloading(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} aria-hidden />
      <div className="relative flex h-full w-full max-w-xl flex-col overflow-y-auto border-l border-border bg-card shadow-xl">
        <div className="sticky top-0 flex items-start justify-between gap-3 border-b border-border bg-card p-5">
          <div className="min-w-0">
            <div className="truncate text-lg font-semibold">{agent.name}</div>
            <div className="truncate text-xs text-muted-foreground">{agent.agent_id}</div>
          </div>
          <Button variant="ghost" size="icon" onClick={onClose} aria-label="Close">
            <X />
          </Button>
        </div>

        <div className="flex flex-col gap-5 p-5">
          <div className="flex flex-wrap items-center gap-2">
            <RiskLevelBadge level={agent.risk_level} />
            <ScoreBadge value={agent.risk_score} />
            <DecisionBadge decision={agent.final_decision} />
            <Pill>{titleCase(agent.framework)}</Pill>
            <Pill tone="neutral">{agent.source}</Pill>
          </div>

          <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
            <Meta label="Owner" value={agent.owner} />
            <Meta label="Autonomy" value={titleCase(agent.autonomy_level)} />
            <Meta label="Model" value={agent.model ?? "unknown"} />
            <Meta label="Tools" value={String(agent.tool_count)} />
            <Meta label="Scans" value={String(agent.scan_count)} />
            <Meta label="Max severity" value={String(agent.max_severity)} />
          </dl>

          {agent.tools.length > 0 && (
            <div>
              <div className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Capabilities
              </div>
              <div className="flex flex-wrap gap-1.5">
                {agent.tools.map((t) => (
                  <Pill key={t} tone="medium">
                    {titleCase(t)}
                  </Pill>
                ))}
              </div>
            </div>
          )}

          <div>
            <div className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Findings ({agent.finding_count})
            </div>
            {agent.findings.length === 0 ? (
              <p className="text-sm text-muted-foreground">No risk findings.</p>
            ) : (
              <div className="flex flex-col gap-2">
                {agent.findings.map((f, i) => (
                  <div key={`${f.rule_id}-${i}`} className="rounded-md border border-border p-3">
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-mono text-xs font-medium">{f.rule_id}</span>
                      <Pill tone={f.severity >= 4 ? "critical" : f.severity >= 3 ? "medium" : "low"}>
                        sev {f.severity}
                      </Pill>
                    </div>
                    {f.family && <div className="mt-1 text-xs text-muted-foreground">{titleCase(f.family)}</div>}
                    <pre className="mt-2 overflow-x-auto whitespace-pre-wrap break-words text-[11px] text-muted-foreground">
                      {f.evidence}
                    </pre>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div>
            <div className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Governance policies
            </div>
            <div className="flex flex-col gap-2">
              {agent.policy_decisions.map((d) => (
                <div
                  key={d.policy_id}
                  className={`rounded-md border p-3 ${d.matched ? "border-border" : "border-border/50 opacity-60"}`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-sm font-medium">{d.name}</span>
                    <DecisionBadge decision={d.matched ? d.decision : "allow"} />
                  </div>
                  <div className="mt-1 text-xs text-muted-foreground">
                    {d.matched ? d.message : "Did not match"}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="sticky bottom-0 border-t border-border bg-card p-5">
          {pdfLocked ? (
            <div className="flex flex-col gap-3 rounded-md border border-dashed border-border bg-muted/40 p-4">
              <div className="flex items-center gap-2">
                <ProBadge tier={LOCKED_FEATURES.pdf_reports.tier} />
                <span className="text-sm font-semibold">PDF assessment report</span>
              </div>
              <p className="text-sm text-muted-foreground">
                {LOCKED_FEATURES.pdf_reports.description}
              </p>
              <UpgradeButton size="sm" label="Unlock PDF reports" />
            </div>
          ) : (
            <>
              {downloadError && (
                <p className="mb-3 text-sm text-destructive" role="alert">
                  {downloadError}
                </p>
              )}
              <Button onClick={handleDownload} disabled={downloading} className="w-full">
                <Download />
                {downloading ? "Generating PDF..." : "Download assessment report"}
              </Button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function Meta({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-xs text-muted-foreground">{label}</dt>
      <dd className="font-medium">{value}</dd>
    </div>
  );
}
