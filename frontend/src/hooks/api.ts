"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  AgentFilters,
  getConnectors,
  getDashboardOverview,
  getDiscoveredAgents,
  getPolicies,
  scanRepository,
  syncConnector,
} from "@/lib/api/requests";

export const queryKeys = {
  agents: (filters: AgentFilters) => ["agents", filters] as const,
  dashboard: () => ["dashboard"] as const,
  connectors: () => ["connectors"] as const,
  policies: () => ["policies"] as const,
};

export function useAgents(filters: AgentFilters = {}) {
  return useQuery({
    queryKey: queryKeys.agents(filters),
    queryFn: () => getDiscoveredAgents(filters),
  });
}

export function useDashboard() {
  return useQuery({ queryKey: queryKeys.dashboard(), queryFn: getDashboardOverview });
}

export function useConnectors() {
  return useQuery({ queryKey: queryKeys.connectors(), queryFn: getConnectors });
}

export function usePolicies() {
  return useQuery({ queryKey: queryKeys.policies(), queryFn: getPolicies });
}

function useInvalidateInventory() {
  const qc = useQueryClient();
  return () => {
    qc.invalidateQueries({ queryKey: ["agents"] });
    qc.invalidateQueries({ queryKey: ["dashboard"] });
  };
}

export function useScanRepository() {
  const invalidate = useInvalidateInventory();
  return useMutation({
    mutationFn: ({ path, owner }: { path: string; owner: string }) => scanRepository(path, owner),
    onSuccess: invalidate,
  });
}

export function useSyncConnector() {
  const invalidate = useInvalidateInventory();
  return useMutation({
    mutationFn: ({ connectorId, owner }: { connectorId: string; owner: string }) =>
      syncConnector(connectorId, owner),
    onSuccess: invalidate,
  });
}
