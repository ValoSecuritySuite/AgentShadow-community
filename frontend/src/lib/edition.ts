/**
 * Client-side edition awareness for the AgentShadow Community Edition.
 *
 * The running app doubles as an advert: free features work, premium features
 * render with a "PRO"/"ENTERPRISE" badge and an upgrade CTA. Override with
 * NEXT_PUBLIC_EDITION=pro to unlock the UI locally.
 */

export type Tier = "Pro" | "Enterprise";

export interface LockedFeature {
  key: string;
  title: string;
  description: string;
  tier: Tier;
}

export const EDITION = (process.env.NEXT_PUBLIC_EDITION ?? "community").toLowerCase();

export const isCommunity = EDITION === "community";

export function getUpgradeUrl(): string {
  return process.env.NEXT_PUBLIC_UPGRADE_URL?.trim() || "/pricing";
}

export const LOCKED_FEATURES: Record<string, LockedFeature> = {
  runtime_connectors: {
    key: "runtime_connectors",
    title: "Runtime & SaaS connectors",
    description:
      "Discover live, deployed agents through provider APIs (OpenAI Assistants and more).",
    tier: "Pro",
  },
  pdf_reports: {
    key: "pdf_reports",
    title: "PDF assessment reports",
    description: "Branded, one-click PDF risk assessments for auditors and reviews.",
    tier: "Pro",
  },
  correlation: {
    key: "correlation",
    title: "Correlation engine feed",
    description: "Feed discovered agents into the shared Valo cross-tool asset graph.",
    tier: "Enterprise",
  },
};

/** A feature is locked only when running the Community Edition. */
export function isLocked(featureKey: string): boolean {
  return isCommunity && featureKey in LOCKED_FEATURES;
}
