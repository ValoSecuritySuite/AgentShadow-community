import type { Metadata } from "next";
import Link from "next/link";
import { ArrowLeft, Bot } from "lucide-react";
import { PricingSection } from "@/components/landing/pricing-section";
import "@/styles/landing.css";

export const metadata: Metadata = {
  title: "AgentShadow — Plans & Pricing",
  description:
    "Compare the free AgentShadow Community Edition with Pro and Enterprise: runtime connectors, PDF reporting, and the shared correlation graph.",
};

export default function PricingPage() {
  return (
    <div className="lp" id="top">
      <div className="lp-glow" />

      <header className="lp-header">
        <Link className="lp-logo" href="/">
          <span className="lp-logo-mark">
            <Bot size={18} strokeWidth={2.4} />
          </span>
          <span className="lp-logo-word">
            Agent<span className="lp-accent">Shadow</span>
          </span>
          <span className="lp-badge">Community Edition</span>
        </Link>
        <Link className="lp-btn" href="/">
          <ArrowLeft size={15} /> Back home
        </Link>
      </header>

      <main className="lp-main">
        <PricingSection id="plans" />
      </main>

      <footer className="lp-footer">
        <span>© AgentShadow Community Edition · AI Agent Security Posture Management</span>
        <span className="lp-foot-meta">Built on the Valo security platform</span>
      </footer>
    </div>
  );
}
