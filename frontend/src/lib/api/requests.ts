import { requestBlob, requestJson } from "./client";
import type {
  Agent,
  AgentListResponse,
  ConnectorInfo,
  DashboardOverview,
  Policy,
  ScanSummary,
} from "./types";

export interface AgentFilters {
  framework?: string;
  source?: string;
  risk_level?: string;
  owner?: string;
}

function toQuery(filters: AgentFilters): Record<string, string> {
  const q: Record<string, string> = {};
  if (filters.framework) q.framework = filters.framework;
  if (filters.source) q.source = filters.source;
  if (filters.risk_level) q.risk_level = filters.risk_level;
  if (filters.owner) q.owner = filters.owner;
  return q;
}

export function getDiscoveredAgents(filters: AgentFilters = {}): Promise<AgentListResponse> {
  return requestJson<AgentListResponse>("/agents/discovered", { query: toQuery(filters) });
}

export function getDashboardOverview(): Promise<DashboardOverview> {
  return requestJson<DashboardOverview>("/dashboard/overview");
}

export function getConnectors(): Promise<{ connectors: ConnectorInfo[] }> {
  return requestJson<{ connectors: ConnectorInfo[] }>("/connectors");
}

export function getPolicies(): Promise<{ total: number; policies: Policy[] }> {
  return requestJson<{ total: number; policies: Policy[] }>("/policies");
}

export function scanRepository(path: string, owner: string): Promise<ScanSummary> {
  return requestJson<ScanSummary>("/scan/repository", {
    method: "POST",
    body: JSON.stringify({ path, owner }),
    timeoutMs: 120_000,
  });
}

export function syncConnector(connectorId: string, owner: string): Promise<ScanSummary> {
  return requestJson<ScanSummary>(`/connectors/${connectorId}/sync`, {
    method: "POST",
    body: JSON.stringify({ owner, options: {} }),
    timeoutMs: 60_000,
  });
}

export async function downloadAgentReport(agent: Agent): Promise<void> {
  const { blob, filename } = await requestBlob("/report/pdf", {
    method: "POST",
    query: { agent_id: agent.agent_id },
  });
  const safeName = agent.name.replace(/[/:\\]/g, "_");
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename ?? `AgentShadow_${safeName}.pdf`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}
