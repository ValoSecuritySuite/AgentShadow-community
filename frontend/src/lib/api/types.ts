export type AgentSource = "code" | "runtime";
export type AutonomyLevel = "low" | "medium" | "high" | "unknown";
export type RiskLevel = "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "MINIMAL";
export type PolicyDecisionLiteral = "allow" | "warn" | "deny";

export interface TextFinding {
  rule_id: string;
  family: string | null;
  category: string;
  severity: number;
  weight: number;
  evidence: string;
  match_start?: number | null;
  match_end?: number | null;
}

export interface PolicyDecision {
  policy_id: string;
  name: string;
  matched: boolean;
  decision: PolicyDecisionLiteral;
  severity: number;
  message: string;
  reasons: string[];
  tags: string[];
}

export interface Agent {
  agent_id: string;
  name: string;
  framework: string;
  source: AgentSource;
  owner: string;
  discovery_path: string;
  model: string | null;
  autonomy_level: AutonomyLevel;
  tools: string[];
  tool_count: number;
  risk_score: number;
  risk_level: RiskLevel;
  max_severity: number;
  posture_grade: string;
  final_decision: PolicyDecisionLiteral;
  finding_count: number;
  findings: TextFinding[];
  policy_decisions: PolicyDecision[];
  first_seen: string;
  last_seen: string;
  scan_count: number;
  metadata: Record<string, unknown>;
}

export interface AgentListResponse {
  total: number;
  returned: number;
  agents: Agent[];
}

export interface FrameworkCount {
  framework: string;
  count: number;
  avg_risk: number;
}

export interface RiskDistribution {
  critical: number;
  high: number;
  medium: number;
  low: number;
  minimal: number;
}

export interface DashboardOverview {
  generated_at: string;
  total_agents: number;
  high_risk_agents: number;
  unmanaged_agents: number;
  high_autonomy_agents: number;
  average_risk_score: number;
  by_framework: FrameworkCount[];
  by_source: Record<string, number>;
  risk_distribution: RiskDistribution;
  policy_breaches: number;
}

export interface ScanSummary {
  discovered: number;
  new_agents: number;
  updated_agents: number;
  agents: Agent[];
  source: AgentSource;
  detail: string;
}

export interface ConnectorInfo {
  id: string;
  name: string;
  description: string;
  category: string;
}

export interface Policy {
  id: string;
  name: string;
  description: string | null;
  enabled: boolean;
  enforce: boolean;
  when: { field: string; op: string; value: unknown }[];
  then: { decision: PolicyDecisionLiteral; severity: number; message: string };
  tags: string[];
  version: number;
}
