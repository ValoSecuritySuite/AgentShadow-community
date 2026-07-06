import Link from "next/link";
import { ArrowRight, Check, Minus } from "lucide-react";

interface Tier {
  name: string;
  price: string;
  cadence?: string;
  tagline: string;
  featured?: boolean;
  current?: boolean;
  cta: { label: string; href: string };
  features: { label: string; included: boolean }[];
}

const TIERS: Tier[] = [
  {
    name: "Community",
    price: "Free",
    tagline: "Discover and score agents in your own code, forever free.",
    current: true,
    cta: { label: "You're using it", href: "/dashboard" },
    features: [
      { label: "Source-code agent discovery", included: true },
      { label: "Deterministic risk scoring", included: true },
      { label: "Agent inventory + dashboard", included: true },
      { label: "Governance policy viewing", included: true },
      { label: "Runtime & SaaS connectors", included: false },
      { label: "PDF assessment reports", included: false },
      { label: "Correlation engine feed", included: false },
    ],
  },
  {
    name: "Pro",
    price: "$—",
    cadence: "/mo",
    tagline: "Live cloud discovery and audit-ready reporting for security teams.",
    featured: true,
    cta: { label: "Upgrade to Pro", href: "#contact" },
    features: [
      { label: "Everything in Community", included: true },
      { label: "Runtime & SaaS connectors", included: true },
      { label: "Live OpenAI Assistants discovery", included: true },
      { label: "Branded PDF assessment reports", included: true },
      { label: "API access control", included: true },
      { label: "Hot-reloadable rules & policies", included: true },
      { label: "Correlation engine feed", included: false },
    ],
  },
  {
    name: "Enterprise",
    price: "Custom",
    tagline: "Org-wide governance wired into the shared Valo security graph.",
    cta: { label: "Contact sales", href: "#contact" },
    features: [
      { label: "Everything in Pro", included: true },
      { label: "Cross-tool correlation graph", included: true },
      { label: "SSO & role-based access", included: true },
      { label: "Custom connectors & rules", included: true },
      { label: "Priority support & SLAs", included: true },
      { label: "On-prem / private cloud deploy", included: true },
      { label: "Dedicated success engineer", included: true },
    ],
  },
];

export function PricingSection({ id = "pricing" }: { id?: string }) {
  return (
    <section className="lp-pricing" id={id}>
      <div className="lp-showcase-head">
        <span className="lp-eyebrow">Plans</span>
        <h2>
          Start free, <span className="lp-accent">upgrade when you scale</span>
        </h2>
        <p className="lp-sub lp-showcase-sub">
          You are running the Community Edition. Unlock live connectors, PDF reporting and
          correlation with Pro and Enterprise.
        </p>
      </div>

      <div className="lp-tiers">
        {TIERS.map((tier) => (
          <div
            key={tier.name}
            className={`lp-tier${tier.featured ? " lp-tier-featured" : ""}`}
          >
            {tier.featured && <span className="lp-tier-flag">Most popular</span>}
            <div className="lp-tier-name">{tier.name}</div>
            <div className="lp-tier-price">
              {tier.price}
              {tier.cadence && <span className="lp-tier-cadence">{tier.cadence}</span>}
            </div>
            <p className="lp-tier-tagline">{tier.tagline}</p>
            <Link
              className={`lp-btn ${tier.featured ? "lp-btn-primary" : "lp-btn-ghost"} lp-tier-cta`}
              href={tier.cta.href}
            >
              {tier.cta.label} <ArrowRight size={15} />
            </Link>
            <ul className="lp-tier-features">
              {tier.features.map((f) => (
                <li key={f.label} className={f.included ? "" : "lp-tier-off"}>
                  {f.included ? (
                    <Check size={15} className="lp-tier-check" />
                  ) : (
                    <Minus size={15} className="lp-tier-minus" />
                  )}
                  {f.label}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </section>
  );
}
