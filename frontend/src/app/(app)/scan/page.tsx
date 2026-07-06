"use client";

import * as React from "react";
import Link from "next/link";
import { FolderSearch, Radar } from "lucide-react";
import { useConnectors, useScanRepository, useSyncConnector } from "@/hooks/api";
import { PageHeader } from "@/components/layout/page-header";
import { SectionCard } from "@/components/ui/section-card";
import { Button } from "@/components/ui/button";
import { ErrorCard } from "@/components/ui/states";
import { ProBadge } from "@/components/ui/pro-badge";
import { UpgradeButton } from "@/components/upsell/upgrade-cta";
import { isLocked, LOCKED_FEATURES } from "@/lib/edition";
import type { ScanSummary } from "@/lib/api/types";

export default function ScanPage() {
  const [repoPath, setRepoPath] = React.useState("");
  const [owner, setOwner] = React.useState("");
  const [lastResult, setLastResult] = React.useState<ScanSummary | null>(null);

  const connectorsLocked = isLocked("runtime_connectors");
  const connectors = useConnectors();
  const scanRepo = useScanRepository();
  const syncConn = useSyncConnector();

  async function handleScan() {
    if (!repoPath.trim()) return;
    const res = await scanRepo.mutateAsync({ path: repoPath.trim(), owner: owner.trim() || "unassigned" });
    setLastResult(res);
  }

  async function handleSync(connectorId: string) {
    const res = await syncConn.mutateAsync({ connectorId, owner: owner.trim() || "unassigned" });
    setLastResult(res);
  }

  const error = (scanRepo.error as Error)?.message ?? (syncConn.error as Error)?.message;

  return (
    <div>
      <PageHeader
        title="Discovery"
        description="Find AI agents by scanning source code or syncing runtime connectors."
      />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <SectionCard
          title="Code scan"
          description="Detect agent frameworks (LangChain, CrewAI, AutoGPT, AutoGen, OpenAI Assistants...) in a repository."
        >
          <div className="flex flex-col gap-3">
            <label className="text-sm">
              <span className="mb-1 block text-muted-foreground">Repository path</span>
              <input
                value={repoPath}
                onChange={(e) => setRepoPath(e.target.value)}
                placeholder="/path/to/repository"
                className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-ring"
              />
            </label>
            <label className="text-sm">
              <span className="mb-1 block text-muted-foreground">Owner (optional)</span>
              <input
                value={owner}
                onChange={(e) => setOwner(e.target.value)}
                placeholder="platform-team"
                className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-ring"
              />
            </label>
            <Button onClick={handleScan} disabled={scanRepo.isPending || !repoPath.trim()}>
              <FolderSearch />
              {scanRepo.isPending ? "Scanning..." : "Scan repository"}
            </Button>
          </div>
        </SectionCard>

        <SectionCard
          title={
            <span className="flex items-center gap-2">
              Runtime connectors
              {connectorsLocked && <ProBadge tier={LOCKED_FEATURES.runtime_connectors.tier} />}
            </span>
          }
          description="Discover live, deployed agents through provider APIs."
        >
          {connectors.isLoading ? (
            <p className="text-sm text-muted-foreground">Loading connectors...</p>
          ) : (
            <div className="flex flex-col gap-3">
              {connectors.data?.connectors.map((c) => (
                <div key={c.id} className="flex items-center justify-between gap-3 rounded-md border border-border p-3">
                  <div className="min-w-0">
                    <div className="font-medium">{c.name}</div>
                    <div className="text-xs text-muted-foreground">{c.description}</div>
                  </div>
                  {connectorsLocked ? (
                    <ProBadge tier={LOCKED_FEATURES.runtime_connectors.tier} />
                  ) : (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleSync(c.id)}
                      disabled={syncConn.isPending}
                    >
                      <Radar />
                      Sync
                    </Button>
                  )}
                </div>
              ))}
              {connectorsLocked && (
                <div className="mt-1 flex flex-col gap-3 rounded-md border border-dashed border-border bg-muted/40 p-4">
                  <p className="text-sm text-muted-foreground">
                    {LOCKED_FEATURES.runtime_connectors.description} Live cloud discovery is a Pro
                    feature.
                  </p>
                  <UpgradeButton size="sm" label="Unlock live connectors" />
                </div>
              )}
            </div>
          )}
        </SectionCard>
      </div>

      {error && (
        <div className="mt-6">
          <ErrorCard message={error} />
        </div>
      )}

      {lastResult && (
        <div className="mt-6">
          <SectionCard
            title="Last discovery result"
            description={lastResult.detail}
            action={
              <Link href="/agents">
                <Button variant="outline" size="sm">
                  View agents
                </Button>
              </Link>
            }
          >
            <div className="flex flex-wrap gap-6 text-sm">
              <Stat label="Discovered" value={lastResult.discovered} />
              <Stat label="New" value={lastResult.new_agents} />
              <Stat label="Updated" value={lastResult.updated_agents} />
              <Stat label="Source" value={lastResult.source} />
            </div>
          </SectionCard>
        </div>
      )}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div>
      <div className="text-xs uppercase tracking-wider text-muted-foreground">{label}</div>
      <div className="text-xl font-semibold tabular-nums">{value}</div>
    </div>
  );
}
