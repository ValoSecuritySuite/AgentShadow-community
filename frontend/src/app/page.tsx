import type { Metadata } from "next";
import { LandingPage } from "@/components/landing/landing-page";

export const metadata: Metadata = {
  title: "AgentShadow Community Edition — Scan. Score. Free.",
  description:
    "The free AgentShadow Community Edition finds AI agents in your source code and scores their risk deterministically. Upgrade to Pro for live cloud discovery, PDF reports and correlation.",
};

export default function Home() {
  return <LandingPage />;
}
