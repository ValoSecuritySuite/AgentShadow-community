import Image from "next/image";
import Link from "next/link";
import { ArrowRight, Bot, Sparkles } from "lucide-react";
import { PricingSection } from "./pricing-section";
import "@/styles/landing.css";

const STEPS = [
  { verb: "Discover", body: "Scan code + sync runtime connectors" },
  { verb: "Score", body: "Deterministic 0–100 risk rating" },
  { verb: "Govern", body: "YAML policy: allow / warn / deny" },
];

const SCAN_LINES = [
  { label: "payments-orchestrator", framework: "LangChain", score: 92, band: "crit" },
  { label: "sre-incident-responder", framework: "AutoGen", score: 71, band: "high" },
  { label: "support-assistant", framework: "OpenAI Assistants", score: 34, band: "ok" },
];

const SHOWCASE = [
  {
    src: "/screenshots/dashboard.png",
    alt: "AgentShadow executive dashboard showing risk distribution and framework breakdown",
    eyebrow: "Executive dashboard",
    title: "Org-wide posture at a glance",
    body: "Total agents, high-risk count, average score and risk distribution — the board-ready view of your AI agent fleet.",
  },
  {
    src: "/screenshots/agents.png",
    alt: "AgentShadow discovered agents inventory with risk scores and policy verdicts",
    eyebrow: "Discovered agents",
    title: "Every agent, scored and governed",
    body: "A unified inventory across code and runtime — framework, owner, autonomy, deterministic risk score and the policy verdict for each.",
  },
  {
    src: "/screenshots/discovery.png",
    alt: "AgentShadow discovery screen with code scan and runtime connectors",
    eyebrow: "Discovery",
    title: "Scan code, sync connectors",
    body: "Detect LangChain, CrewAI, AutoGPT, AutoGen and OpenAI Assistants in your repos, or pull live agents straight from provider APIs.",
  },
  {
    src: "/screenshots/governance.png",
    alt: "AgentShadow governance policies with allow, warn and deny verdicts",
    eyebrow: "Governance",
    title: "Policy as code: allow / warn / deny",
    body: "Human-readable YAML policies evaluated against every agent — block high-risk or unmanaged agents and flag shell-capable ones for review.",
  },
];

export function LandingPage() {
  return (
    <div className="lp" id="top">
      <div className="lp-glow" />

      <header className="lp-header">
        <a className="lp-logo" href="#top">
          <span className="lp-logo-mark">
            <Bot size={18} strokeWidth={2.4} />
          </span>
          <span className="lp-logo-word">
            Agent<span className="lp-accent">Shadow</span>
          </span>
          <span className="lp-badge">Community Edition</span>
        </a>
        <div className="lp-cta-row" style={{ margin: 0 }}>
          <a className="lp-btn" href="#pricing">
            Pricing
          </a>
          <Link className="lp-btn" href="/dashboard">
            Open dashboard <ArrowRight size={15} />
          </Link>
        </div>
      </header>

      <main className="lp-main">
        <section className="lp-hero">
          <span className="lp-eyebrow">Free · Open · Self-hosted</span>
          <h1>
            Scan your code for AI agents,
            <br />
            <span className="lp-accent">score them free.</span>
          </h1>
          <p className="lp-sub">
            Shadow agents are multiplying across your code and SaaS — with shell access, unbounded
            autonomy and no owner. The AgentShadow Community Edition finds them in your source and
            scores their risk for free. Upgrade for live cloud discovery, PDF reporting and
            correlation.
          </p>
          <div className="lp-cta-row">
            <Link className="lp-btn lp-btn-primary" href="/dashboard">
              Open the dashboard <ArrowRight size={16} />
            </Link>
            <a className="lp-btn lp-btn-ghost" href="#pricing">
              <Sparkles size={16} /> See Pro &amp; Enterprise
            </a>
          </div>

          <div className="lp-scan" aria-hidden>
            <div className="lp-scan-bar">
              <span className="lp-dot" />
              <span className="lp-dot" />
              <span className="lp-dot" />
              <span className="lp-scan-title">agentshadow · live scan</span>
            </div>
            <div className="lp-scan-body">
              {SCAN_LINES.map((a) => (
                <div className="lp-scan-row" key={a.label}>
                  <span className="lp-scan-name">{a.label}</span>
                  <span className="lp-scan-fw">{a.framework}</span>
                  <span className={`lp-score lp-score-${a.band}`}>{a.score}</span>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="lp-how" id="how">
          {STEPS.map((s, i) => (
            <div className="lp-step" key={s.verb}>
              <span className="lp-step-n">{String(i + 1).padStart(2, "0")}</span>
              <h3>{s.verb}</h3>
              <p>{s.body}</p>
            </div>
          ))}
        </section>

        <section className="lp-showcase" id="product">
          <div className="lp-showcase-head">
            <span className="lp-eyebrow">See it in action</span>
            <h2>The whole product, end to end</h2>
            <p className="lp-sub lp-showcase-sub">
              From discovery to scoring to governance — every screen of AgentShadow, built on the
              proven Valo security platform.
            </p>
          </div>

          {SHOWCASE.map((shot, i) => (
            <div className={`lp-shot${i % 2 === 1 ? " lp-shot-rev" : ""}`} key={shot.src}>
              <div className="lp-shot-copy">
                <span className="lp-step-n">{shot.eyebrow}</span>
                <h3>{shot.title}</h3>
                <p>{shot.body}</p>
              </div>
              <div className="lp-shot-frame">
                <span className="lp-shot-bar">
                  <span className="lp-dot" />
                  <span className="lp-dot" />
                  <span className="lp-dot" />
                </span>
                <Image
                  src={shot.src}
                  alt={shot.alt}
                  width={1440}
                  height={1100}
                  className="lp-shot-img"
                  sizes="(max-width: 880px) 100vw, 560px"
                />
              </div>
            </div>
          ))}

          <div className="lp-showcase-cta">
            <Link className="lp-btn lp-btn-primary" href="/dashboard">
              Open the live dashboard <ArrowRight size={16} />
            </Link>
          </div>
        </section>

        <PricingSection />
      </main>

      <footer className="lp-footer">
        <span>© AgentShadow Community Edition · AI Agent Security Posture Management</span>
        <span className="lp-foot-meta">Built on the Valo security platform</span>
      </footer>
    </div>
  );
}
