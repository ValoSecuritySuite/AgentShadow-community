"""Agent security assessment PDF.

Produces a professional, real-world-style "AI Agent Security Assessment"
report modeled on the structure of industry security/risk assessment reports
(e.g. penetration-test and third-party risk reports): branded cover page,
document control, executive summary with a risk meter, scope & methodology
(mapped to OWASP LLM Top 10, MITRE ATLAS and NIST AI RMF), a deterministic risk
scoring breakdown, detailed findings, governance/policy compliance, a
prioritized remediation roadmap, and an appendix.

Built programmatically with ReportLab Platypus (same approach as Valo's
`pdf_report_generator.py`, rebranded for AgentShadow).

Engagement-specific fields (client name, assessor, distribution) can be supplied
via `ReportBranding`; everything else is derived automatically from the agent
assessment data.
"""

import hashlib
import io
from datetime import datetime, timedelta, timezone

from reportlab.graphics.shapes import Drawing, Line, Rect, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas as _canvas
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.schemas import Agent, ReportBranding

# ── Palette ──────────────────────────────────────────────────────────────────
_BRAND = colors.HexColor("#4f46e5")
_BRAND_DK = colors.HexColor("#312e81")
_INK = colors.HexColor("#0f172a")
_DARK = colors.HexColor("#1e293b")
_MUTED = colors.HexColor("#64748b")
_LINE = colors.HexColor("#e2e8f0")
_PANEL = colors.HexColor("#f8fafc")
_PANEL2 = colors.HexColor("#eef2ff")

_RISK_COLORS = {
    "CRITICAL": colors.HexColor("#dc2626"),
    "HIGH": colors.HexColor("#ea580c"),
    "MEDIUM": colors.HexColor("#d97706"),
    "LOW": colors.HexColor("#2563eb"),
    "MINIMAL": colors.HexColor("#16a34a"),
}

_SEVERITY = {
    5: ("Critical", colors.HexColor("#dc2626")),
    4: ("High", colors.HexColor("#ea580c")),
    3: ("Medium", colors.HexColor("#d97706")),
    2: ("Low", colors.HexColor("#2563eb")),
    1: ("Informational", colors.HexColor("#0891b2")),
}

_RISK_IMPACT = {
    "CRITICAL": "poses a critical risk to production systems, credentials, and sensitive data",
    "HIGH": "could materially affect production systems or sensitive data if exploited",
    "MEDIUM": "presents a moderate operational and data-handling risk requiring tracked remediation",
    "LOW": "presents a limited but non-zero risk that should be monitored",
    "MINIMAL": "presents minimal immediate risk under current configuration",
}

_COMPLIANCE_BY_RISK = {
    "CRITICAL": (
        "EU AI Act Art. 9 risk-management for high-impact AI; ISO 27001 A.8.1 asset inventory; "
        "SOC 2 CC7.2 incident response; NIST AI RMF MANAGE-2.3 monitoring."
    ),
    "HIGH": (
        "ISO 27001 A.8.2 privileged access and A.5.23 cloud services; SOC 2 CC6.1 logical access; "
        "NIST AI RMF GOVERN-1.2 and MAP-1.5."
    ),
    "MEDIUM": (
        "NIST AI RMF GOVERN-1.1 agent inventory; ISO 27001 A.5.34 privacy and PII protection; "
        "SOC 2 CC6.6 change management."
    ),
    "LOW": "NIST AI RMF GOVERN-1.1 baseline inventory control; internal AI acceptable-use policy.",
    "MINIMAL": "NIST AI RMF GOVERN-1.1 baseline inventory control; periodic re-assessment recommended.",
}

_REMEDIATION_DAYS = {5: 7, 4: 7, 3: 30, 2: 90, 1: 180}

# Map finding families to recognized industry standards for credibility.
_STANDARDS = {
    "prompt_safety": "OWASP LLM01: Prompt Injection · MITRE ATLAS AML.T0051",
    "secret_exposure": "OWASP LLM06: Sensitive Information Disclosure · CWE-798",
    "dangerous_tool": "OWASP LLM08: Excessive Agency · MITRE ATLAS AML.T0053",
    "autonomy": "OWASP LLM08: Excessive Agency · NIST AI RMF MANAGE-2.1",
    "guardrail": "OWASP LLM02: Insecure Output Handling · NIST AI RMF MAP-2.3",
    "agent_framework": "NIST AI RMF GOVERN-1.1 · Internal Agent Inventory Policy",
}

_RECOMMENDATIONS = {
    "dangerous_tool": "Restrict or sandbox high blast-radius tools (shell, code execution, outbound network). Require explicit allow-lists and least-privilege scoping.",
    "autonomy": "Add a stop condition and human-in-the-loop approval gate for autonomous action loops; cap iterations and spend.",
    "guardrail": "Disable dangerous capabilities by default; gate them behind human approval and add input/output validation.",
    "secret_exposure": "Remove hardcoded credentials; load secrets from a managed vault at runtime and rotate any exposed keys.",
    "prompt_safety": "Harden the system prompt against injection, pin instructions, and add input/output filtering and content policies.",
    "agent_framework": "Document and govern the agent framework usage; register the agent in the approved inventory with an accountable owner.",
}

_REMEDIATION_PRIORITY = {5: "P1 — Immediate", 4: "P1 — Immediate", 3: "P2 — Near-term", 2: "P3 — Planned", 1: "P4 — Backlog"}

# Confidentiality / classification applied across the document footer.
_CLASSIFICATION = "CONFIDENTIAL"


# ── Styles ───────────────────────────────────────────────────────────────────
def _styles():
    s = getSampleStyleSheet()
    s.add(ParagraphStyle("CoverKicker", parent=s["Normal"], textColor=colors.white, fontSize=11, alignment=TA_LEFT, leading=14, fontName="Helvetica-Bold"))
    s.add(ParagraphStyle("CoverTitle", parent=s["Title"], textColor=colors.white, fontSize=30, leading=34, alignment=TA_LEFT, spaceAfter=0))
    s.add(ParagraphStyle("CoverSub", parent=s["Normal"], textColor=colors.HexColor("#c7d2fe"), fontSize=13, alignment=TA_LEFT, leading=18))
    s.add(ParagraphStyle("SecNum", parent=s["Heading2"], textColor=_BRAND, fontSize=13, spaceBefore=16, spaceAfter=2, fontName="Helvetica-Bold"))
    s.add(ParagraphStyle("H2", parent=s["Heading2"], textColor=_INK, fontSize=15, spaceBefore=14, spaceAfter=6, fontName="Helvetica-Bold"))
    s.add(ParagraphStyle("H3", parent=s["Heading3"], textColor=_DARK, fontSize=11.5, spaceBefore=10, spaceAfter=3, fontName="Helvetica-Bold"))
    s.add(ParagraphStyle("Body", parent=s["Normal"], fontSize=9.5, textColor=_DARK, leading=14, spaceAfter=4))
    s.add(ParagraphStyle("BodyTight", parent=s["Normal"], fontSize=9, textColor=_DARK, leading=12.5))
    s.add(ParagraphStyle("Small", parent=s["Normal"], fontSize=8, textColor=_MUTED, leading=11))
    s.add(ParagraphStyle("Mono", parent=s["Normal"], fontSize=8, textColor=_DARK, leading=11, fontName="Courier"))
    s.add(ParagraphStyle("CellHead", parent=s["Normal"], fontSize=8.5, textColor=colors.white, fontName="Helvetica-Bold", leading=11))
    s.add(ParagraphStyle("Cell", parent=s["Normal"], fontSize=8.5, textColor=_DARK, leading=11.5))
    s.add(ParagraphStyle("CellMuted", parent=s["Normal"], fontSize=8.5, textColor=_MUTED, leading=11.5))
    s.add(ParagraphStyle("Footer", parent=s["Normal"], fontSize=7.5, textColor=_MUTED, leading=9))
    return s


def _effective_owner(agent: Agent) -> str:
    if agent.owner and agent.owner != "unassigned":
        return agent.owner
    return "Unassigned — requires assignment before production use"


def _prepared_for(agent: Agent, branding: ReportBranding | None) -> str:
    if branding and branding.company_name:
        return branding.company_name
    if agent.owner != "unassigned":
        label = agent.owner.replace("-", " ").replace("_", " ").title()
        return f"{label} · AI Agent Program"
    return "Enterprise AI Agent Security Program"


def _prepared_by(branding: ReportBranding | None) -> str:
    if branding and branding.prepared_by:
        return branding.prepared_by
    return "AgentShadow Automated Assessment Engine"


def _reviewed_by(agent: Agent, branding: ReportBranding | None) -> str:
    if branding and branding.reviewed_by:
        return branding.reviewed_by
    matched = [d for d in agent.policy_decisions if d.matched]
    if matched:
        top = max(matched, key=lambda d: d.severity)
        return f"Governance policy engine · {top.name} ({top.decision.upper()})"
    return "Governance policy engine · no policy violations detected"


def _distribution(agent: Agent, branding: ReportBranding | None) -> str:
    if branding and branding.distribution:
        return branding.distribution
    recipients = []
    if agent.owner != "unassigned":
        recipients.append(f"Agent owner ({agent.owner})")
    recipients.extend([
        "Information security team",
        "AI governance & risk committee",
        "Platform engineering lead",
    ])
    return "; ".join(recipients)


def _business_impact(agent: Agent) -> str:
    parts = [
        f"At {agent.risk_level} risk ({agent.risk_score:.0f}/100), this agent "
        f"{_RISK_IMPACT.get(agent.risk_level, 'should be monitored')}.",
    ]
    if agent.autonomy_level in ("high", "medium"):
        parts.append(
            f"It operates at {agent.autonomy_level} autonomy, so actions may proceed with "
            "limited human oversight between discovery cycles."
        )
    if agent.tools:
        shown = ", ".join(agent.tools[:6])
        extra = f" (+{len(agent.tools) - 6} more)" if len(agent.tools) > 6 else ""
        parts.append(
            f"Tools in scope ({agent.tool_count}): {shown}{extra}. Each capability expands "
            "the blast radius of a compromised or misdirected agent."
        )
    families = {f.family for f in agent.findings if f.family}
    if "secret_exposure" in families:
        parts.append("Exposed credentials could enable unauthorized API access and lateral movement.")
    if "dangerous_tool" in families:
        parts.append("Shell, code execution, or network tools could allow unintended system changes or data exfiltration.")
    if "prompt_safety" in families:
        parts.append("Prompt-injection weaknesses could cause the agent to bypass intended guardrails.")
    if agent.final_decision == "deny":
        parts.append("Governance verdict DENY — block deployment or continued operation until remediated.")
    elif agent.final_decision == "warn":
        parts.append("Governance verdict WARN — compensating controls and human review required before production use.")
    return " ".join(parts)


def _assessment_window(agent: Agent, now: datetime) -> str:
    if agent.first_seen.date() == agent.last_seen.date() == now.date():
        return (
            f"{agent.first_seen.strftime('%d %B %Y %H:%M')} — "
            f"{now.strftime('%H:%M')} UTC (assessment snapshot)"
        )
    return (
        f"{agent.first_seen.strftime('%d %B %Y %H:%M')} — "
        f"{now.strftime('%d %B %Y %H:%M')} UTC"
    )


def _environment(agent: Agent) -> str:
    if agent.source == "runtime":
        endpoint = agent.discovery_path or "live runtime API"
        return f"Production / live runtime · {endpoint}"
    env_hint = agent.metadata.get("environment") if agent.metadata else None
    if env_hint:
        return str(env_hint)
    path = agent.discovery_path or "path not recorded"
    return f"Source repository · static code analysis ({path})"


def _out_of_scope() -> str:
    return (
        "Dynamic exploitation, adversarial red-team testing, runtime behavioural fuzzing, "
        "underlying cloud infrastructure, and third-party LLM provider security are out of scope "
        "unless explicitly contracted separately."
    )


def _remediation_owner(agent: Agent) -> str:
    return agent.owner if agent.owner != "unassigned" else "Platform / security team"


def _target_date(severity: int, now: datetime) -> str:
    days = _REMEDIATION_DAYS.get(severity, 90)
    return (now + timedelta(days=days)).strftime("%Y-%m-%d")


def _compliance_mapping(agent: Agent) -> str:
    parts = [_COMPLIANCE_BY_RISK.get(agent.risk_level, _COMPLIANCE_BY_RISK["MINIMAL"])]
    for d in agent.policy_decisions:
        if d.matched:
            parts.append(f"{d.name}: {d.decision.upper()} — {d.message}")
    return " ".join(parts)


def _finding_remediation(agent: Agent, now: datetime, severity: int) -> str:
    return f"{_remediation_owner(agent)} · target {_target_date(severity, now)}"


def _report_id(agent: Agent, now: datetime) -> str:
    digest = hashlib.sha1(agent.agent_id.encode("utf-8")).hexdigest()[:6].upper()
    return f"AS-{now:%Y%m%d}-{digest}"


# ── Small visual helpers ─────────────────────────────────────────────────────
def _risk_meter(score: float, level_color: colors.Color, width: float = 150 * mm) -> Drawing:
    """A 0-100 horizontal risk meter with band gradient stops and a marker."""
    h = 16
    d = Drawing(width, 40)
    bands = [
        (0, 20, colors.HexColor("#16a34a")),
        (20, 40, colors.HexColor("#2563eb")),
        (40, 60, colors.HexColor("#d97706")),
        (60, 80, colors.HexColor("#ea580c")),
        (80, 100, colors.HexColor("#dc2626")),
    ]
    for lo, hi, c in bands:
        x = (lo / 100.0) * width
        w = ((hi - lo) / 100.0) * width
        d.add(Rect(x, 8, w, h, fillColor=c, strokeColor=colors.white, strokeWidth=0.6))
    mx = max(0.0, min(100.0, score)) / 100.0 * width
    d.add(Line(mx, 5, mx, 28, strokeColor=_INK, strokeWidth=1.8))
    lx = min(max(mx, 9), width - 9)
    d.add(String(lx, 31, f"{score:.0f}", fontSize=9, fillColor=_INK, textAnchor="middle", fontName="Helvetica-Bold"))
    d.add(String(0, 0, "0", fontSize=6.5, fillColor=_MUTED))
    d.add(String(width, 0, "100", fontSize=6.5, fillColor=_MUTED, textAnchor="end"))
    return d


def _badge(text: str, bg: colors.Color, fg: colors.Color = colors.white) -> Table:
    t = Table([[text]], colWidths=[len(text) * 5.4 + 14])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("TEXTCOLOR", (0, 0), (-1, -1), fg),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return t


def _kv_table(rows, s, col0=42 * mm, col1=132 * mm, highlight_row=None, highlight_color=None):
    data = [[Paragraph(k, s["CellMuted"]), v if hasattr(v, "wrap") else Paragraph(str(v), s["Cell"])] for k, v in rows]
    t = Table(data, colWidths=[col0, col1])
    style = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LINEBELOW", (0, 0), (-1, -2), 0.4, _LINE),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
    ]
    if highlight_row is not None and highlight_color is not None:
        style.append(("TEXTCOLOR", (1, highlight_row), (1, highlight_row), highlight_color))
    t.setStyle(TableStyle(style))
    return t


def _section(num: str, title: str, s) -> Paragraph:
    return Paragraph(f'<font color="#4f46e5">{num}</font>&nbsp;&nbsp;{title}', s["H2"])


# ── Page furniture (header / footer / page numbers) ──────────────────────────
def _make_canvas(report_id: str, agent_name: str):
    class _NumberedCanvas(_canvas.Canvas):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._saved = []

        def showPage(self):  # noqa: N802
            self._saved.append(dict(self.__dict__))
            self._startPage()

        def save(self):
            total = len(self._saved)
            for idx, state in enumerate(self._saved, start=1):
                self.__dict__.update(state)
                self._draw_furniture(idx, total)
                super().showPage()
            super().save()

        def _draw_furniture(self, page_no: int, total: int):
            w, h = A4
            # Running header (skip cover page 1)
            if page_no > 1:
                self.setFont("Helvetica-Bold", 8)
                self.setFillColor(_BRAND)
                self.drawString(18 * mm, h - 12 * mm, "AgentShadow")
                self.setFont("Helvetica", 8)
                self.setFillColor(_MUTED)
                self.drawRightString(w - 18 * mm, h - 12 * mm, f"AI Agent Security Assessment · {agent_name}")
                self.setStrokeColor(_LINE)
                self.setLineWidth(0.5)
                self.line(18 * mm, h - 13.5 * mm, w - 18 * mm, h - 13.5 * mm)
            # Footer on all pages
            self.setStrokeColor(_LINE)
            self.setLineWidth(0.5)
            self.line(18 * mm, 13 * mm, w - 18 * mm, 13 * mm)
            self.setFont("Helvetica-Bold", 7.5)
            self.setFillColor(_RISK_COLORS["CRITICAL"])
            self.drawString(18 * mm, 9 * mm, _CLASSIFICATION)
            self.setFont("Helvetica", 7.5)
            self.setFillColor(_MUTED)
            self.drawCentredString(w / 2, 9 * mm, f"Report {report_id}")
            self.drawRightString(w - 18 * mm, 9 * mm, f"Page {page_no} of {total}")

    return _NumberedCanvas


# ── Report ───────────────────────────────────────────────────────────────────
def generate_agent_report(agent: Agent, branding: ReportBranding | None = None) -> bytes:
    """Render an AgentShadow assessment PDF for a single agent; return bytes."""
    buf = io.BytesIO()
    now = datetime.now(timezone.utc)
    report_id = _report_id(agent, now)
    prepared_for = _prepared_for(agent, branding)
    prepared_by = _prepared_by(branding)
    reviewed_by = _reviewed_by(agent, branding)
    distribution = _distribution(agent, branding)
    accountable_owner = _effective_owner(agent)
    business_impact = _business_impact(agent)
    assessment_window = _assessment_window(agent, now)
    environment = _environment(agent)
    out_of_scope = _out_of_scope()
    compliance = _compliance_mapping(agent)
    remediation_owner = _remediation_owner(agent)
    s = _styles()
    risk_color = _RISK_COLORS.get(agent.risk_level, _MUTED)
    content_w = 174 * mm

    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm, topMargin=22 * mm, bottomMargin=18 * mm,
        title=f"AI Agent Security Assessment — {agent.name}",
        author="AgentShadow", subject="AI Agent Security Assessment",
    )
    story: list = []

    # ── COVER ────────────────────────────────────────────────────────────────
    band = Table(
        [[Paragraph("AGENTSHADOW  ·  AI AGENT SECURITY POSTURE MANAGEMENT", s["CoverKicker"])],
         [Paragraph("AI Agent Security Assessment", s["CoverTitle"])],
         [Paragraph(f"Subject agent: <b>{agent.name}</b>", s["CoverSub"])]],
        colWidths=[content_w],
    )
    band.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), _BRAND_DK),
        ("LEFTPADDING", (0, 0), (-1, -1), 18),
        ("RIGHTPADDING", (0, 0), (-1, -1), 18),
        ("TOPPADDING", (0, 0), (0, 0), 22),
        ("BOTTOMPADDING", (-1, -1), (-1, -1), 22),
        ("TOPPADDING", (0, 1), (-1, 2), 4),
        ("BOTTOMPADDING", (0, 0), (0, 1), 4),
    ]))
    story.append(band)
    story.append(Spacer(1, 4))

    rating = Table(
        [[Paragraph("OVERALL RISK RATING", s["CellHead"]), ""],
         [Paragraph(f"{agent.risk_score:.0f}", ParagraphStyle("score", parent=s["Title"], textColor=colors.white, fontSize=34, leading=36)),
          Paragraph(f"<b>{agent.risk_level}</b><br/><font size=8>Posture grade {agent.posture_grade} · Governance verdict {agent.final_decision.upper()}</font>",
                    ParagraphStyle("rl", parent=s["Normal"], textColor=colors.white, fontSize=14, leading=18))]],
        colWidths=[40 * mm, content_w - 40 * mm],
    )
    rating.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), risk_color),
        ("SPAN", (0, 0), (-1, 0)),
        ("VALIGN", (0, 1), (-1, 1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 16),
        ("TOPPADDING", (0, 0), (0, 0), 8),
        ("TOPPADDING", (0, 1), (-1, 1), 6),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 12),
    ]))
    story.append(rating)
    story.append(Spacer(1, 14))

    meta_rows = [
        ("Report reference", report_id),
        ("Subject agent", agent.name),
        ("Agent identifier", Paragraph(agent.agent_id, s["Mono"])),
        ("Framework", agent.framework),
        ("Discovery source", agent.source),
        ("Accountable owner", accountable_owner),
        ("Classification", Paragraph(f'<b><font color="#dc2626">{_CLASSIFICATION}</font></b> — internal distribution only', s["Cell"])),
        ("Date of issue", now.strftime("%d %B %Y")),
        ("Report version", "1.0"),
        ("Prepared for", prepared_for),
        ("Prepared by", prepared_by),
        ("Reviewed / approved by", reviewed_by),
    ]
    story.append(_kv_table(meta_rows, s))
    story.append(Spacer(1, 16))
    story.append(HRFlowable(width="100%", thickness=0.6, color=_LINE))
    story.append(Paragraph(
        "<b>Confidentiality notice.</b> This report contains a security assessment of an AI agent and is classified "
        f"{_CLASSIFICATION}. It is intended solely for the named recipient and authorized personnel. Findings reflect "
        "the agent configuration observed at the time of assessment and should be revalidated after any change.",
        s["Small"],
    ))
    story.append(PageBreak())

    # ── DOCUMENT CONTROL + CONTENTS ──────────────────────────────────────────
    story.append(_section("0", "Document Control", s))
    dc = Table(
        [[Paragraph(c, s["CellHead"]) for c in ["Version", "Date", "Author", "Status", "Description"]],
         [Paragraph("1.0", s["Cell"]), Paragraph(now.strftime("%Y-%m-%d"), s["Cell"]),
          Paragraph("AgentShadow Platform", s["Cell"]), Paragraph("Final", s["Cell"]),
          Paragraph("Automated assessment generated from discovery + deterministic scoring.", s["Cell"])]],
        colWidths=[18 * mm, 24 * mm, 42 * mm, 22 * mm, content_w - 106 * mm],
    )
    dc.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), _BRAND),
        ("GRID", (0, 0), (-1, -1), 0.3, _LINE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, _PANEL]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(dc)
    story.append(Spacer(1, 6))
    story.append(Paragraph(f"<b>Distribution list:</b> {distribution}", s["Body"]))

    story.append(_section("", "Contents", s))
    for line in [
        "1.  Executive Summary",
        "2.  Scope &amp; Methodology",
        "3.  Risk Assessment &amp; Scoring",
        "4.  Detailed Findings",
        "5.  Governance &amp; Policy Compliance",
        "6.  Remediation Roadmap",
        "7.  Appendix — Agent Profile &amp; References",
    ]:
        story.append(Paragraph(line, s["Body"]))
    story.append(PageBreak())

    # ── 1. EXECUTIVE SUMMARY ─────────────────────────────────────────────────
    story.append(_section("1", "Executive Summary", s))
    summary = (
        f"AgentShadow assessed the AI agent <b>{agent.name}</b>, built on the <b>{agent.framework}</b> framework and "
        f"discovered via <b>{agent.source}</b> discovery. The agent operates at an estimated <b>{agent.autonomy_level}</b> "
        f"autonomy level with <b>{agent.tool_count}</b> tool(s) in scope. Applying its deterministic risk engine, "
        f"AgentShadow assigned an overall risk score of <b>{agent.risk_score:.1f} / 100</b>, placing the agent in the "
        f"<b>{agent.risk_level}</b> risk band, and identified <b>{agent.finding_count}</b> finding(s). The resulting "
        f"governance verdict is <b>{agent.final_decision.upper()}</b>."
    )
    story.append(Paragraph(summary, s["Body"]))
    story.append(Spacer(1, 6))
    story.append(_risk_meter(agent.risk_score, risk_color, width=content_w))
    story.append(Spacer(1, 8))

    # Severity summary
    sev_counts = {sev: 0 for sev in _SEVERITY}
    for f in agent.findings:
        sev_counts[f.severity] = sev_counts.get(f.severity, 0) + 1
    story.append(Paragraph("Findings by severity", s["H3"]))
    head = [Paragraph("Critical", s["CellHead"]), Paragraph("High", s["CellHead"]), Paragraph("Medium", s["CellHead"]),
            Paragraph("Low", s["CellHead"]), Paragraph("Informational", s["CellHead"])]
    vals = [str(sev_counts.get(sev, 0)) for sev in (5, 4, 3, 2, 1)]
    sev_table = Table([head, vals], colWidths=[content_w / 5] * 5)
    sev_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), _SEVERITY[5][1]),
        ("BACKGROUND", (1, 0), (1, 0), _SEVERITY[4][1]),
        ("BACKGROUND", (2, 0), (2, 0), _SEVERITY[3][1]),
        ("BACKGROUND", (3, 0), (3, 0), _SEVERITY[2][1]),
        ("BACKGROUND", (4, 0), (4, 0), _SEVERITY[1][1]),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTSIZE", (0, 1), (-1, 1), 16), ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
        ("TEXTCOLOR", (0, 1), (-1, 1), _INK),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.white),
        ("ROWBACKGROUNDS", (0, 1), (-1, 1), [_PANEL]),
        ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(sev_table)
    story.append(Spacer(1, 8))
    story.append(Paragraph("Business impact context", s["H3"]))
    story.append(Paragraph(business_impact, s["Body"]))
    story.append(PageBreak())

    # ── 2. SCOPE & METHODOLOGY ───────────────────────────────────────────────
    story.append(_section("2", "Scope &amp; Methodology", s))
    story.append(Paragraph(
        "AgentShadow discovers AI agents from source code and runtime connectors, then scores each agent with a "
        "deterministic engine and evaluates it against governance policy. This assessment covers a single agent and "
        "its observable configuration; it does not execute the agent or perform dynamic exploitation.", s["Body"]))
    story.append(Paragraph("Assessment scope", s["H3"]))
    scope_rows = [
        ("In scope", f"Agent '{agent.name}' ({agent.framework}); discovery location below."),
        ("Discovery location", Paragraph(agent.discovery_path or "n/a", s["Mono"])),
        ("Assessment window", assessment_window),
        ("Environment", environment),
        ("Out of scope", out_of_scope),
    ]
    story.append(_kv_table(scope_rows, s))
    story.append(Paragraph("Methodology &amp; reference frameworks", s["H3"]))
    story.append(Paragraph(
        "Findings are produced by static analysis of the agent definition (framework usage, tools/capabilities, "
        "system prompt, autonomy signals and secret exposure) and mapped to recognized industry standards:", s["Body"]))
    for item in [
        "<b>OWASP Top 10 for LLM Applications</b> — prompt injection, sensitive information disclosure, excessive agency.",
        "<b>MITRE ATLAS</b> — adversarial tactics and techniques for AI-enabled systems.",
        "<b>NIST AI Risk Management Framework (AI RMF 1.0)</b> — Govern / Map / Measure / Manage functions.",
    ]:
        story.append(Paragraph(f"&bull;&nbsp; {item}", s["Body"]))
    story.append(Paragraph(
        "Risk scores are deterministic: identical agent configurations always yield identical scores, making results "
        "reproducible and audit-friendly.", s["Body"]))
    story.append(PageBreak())

    # ── 3. RISK ASSESSMENT & SCORING ─────────────────────────────────────────
    story.append(_section("3", "Risk Assessment &amp; Scoring", s))
    story.append(Paragraph(
        "The overall risk score aggregates the severity and weight of each finding, the agent's autonomy level and "
        "the blast radius of its tools. The breakdown below shows the factors that drove this agent's rating.", s["Body"]))
    max_sev_label = _SEVERITY.get(agent.max_severity, ("None", _MUTED))[0]
    score_rows = [
        ("Overall risk score", Paragraph(f'<b><font color="#{risk_color.hexval()[2:]}">{agent.risk_score:.1f} / 100</font></b>', s["Cell"])),
        ("Risk band", Paragraph(f'<b><font color="#{risk_color.hexval()[2:]}">{agent.risk_level}</font></b>', s["Cell"])),
        ("Posture grade", agent.posture_grade),
        ("Highest finding severity", f"{max_sev_label} ({agent.max_severity}/5)"),
        ("Total findings", str(agent.finding_count)),
        ("Autonomy level", agent.autonomy_level),
        ("Tools / capabilities in scope", str(agent.tool_count)),
        ("Governance verdict", agent.final_decision.upper()),
    ]
    story.append(_kv_table(score_rows, s))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "<b>Interpretation.</b> Scores of 80–100 are CRITICAL and warrant immediate action; 60–79 HIGH; 40–59 MEDIUM; "
        "20–39 LOW; 0–19 MINIMAL. Bands align to the governance enforcement thresholds in Section 5.", s["Small"]))
    story.append(PageBreak())

    # ── 4. DETAILED FINDINGS ─────────────────────────────────────────────────
    story.append(_section("4", "Detailed Findings", s))
    if not agent.findings:
        story.append(Paragraph("No risk findings were detected for this agent at the time of assessment.", s["Body"]))
    else:
        story.append(Paragraph(
            f"{agent.finding_count} finding(s) are detailed below, ordered by severity. Each finding is mapped to an "
            "industry standard and includes the supporting evidence and a recommended remediation.", s["Body"]))
        story.append(Spacer(1, 4))
        ordered = sorted(agent.findings, key=lambda f: (-f.severity, f.rule_id))
        for i, f in enumerate(ordered, start=1):
            sev_label, sev_color = _SEVERITY.get(f.severity, ("Info", _MUTED))
            fid = f"F-{i:02d}"
            std = _STANDARDS.get(f.family or "", "—")
            rec = _RECOMMENDATIONS.get(f.family or "", "Review the finding and apply appropriate controls.")
            header = Table(
                [[Paragraph(f"<b>{fid}</b>&nbsp;&nbsp;{f.rule_id}", ParagraphStyle("fh", parent=s["Cell"], fontSize=10, textColor=colors.white)),
                  Paragraph(f"<b>{sev_label.upper()}</b>", ParagraphStyle("fs", parent=s["Cell"], fontSize=9, textColor=colors.white, alignment=TA_RIGHT))]],
                colWidths=[content_w - 30 * mm, 30 * mm],
            )
            header.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), sev_color),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (0, 0), 8), ("RIGHTPADDING", (-1, -1), (-1, -1), 8),
            ]))
            detail = Table(
                [[Paragraph("Category", s["CellMuted"]), Paragraph(f.family or "general", s["Cell"])],
                 [Paragraph("Severity", s["CellMuted"]), Paragraph(f"{sev_label} ({f.severity}/5) · detection weight {f.weight:g}", s["Cell"])],
                 [Paragraph("Mapped standard", s["CellMuted"]), Paragraph(std, s["Cell"])],
                 [Paragraph("Evidence", s["CellMuted"]), Paragraph((f.evidence or "—")[:300], s["Mono"])],
                 [Paragraph("Recommendation", s["CellMuted"]), Paragraph(rec, s["Cell"])],
                 [Paragraph("Remediation owner", s["CellMuted"]), Paragraph(_finding_remediation(agent, now, f.severity), s["Cell"])]],
                colWidths=[34 * mm, content_w - 34 * mm],
            )
            detail.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BACKGROUND", (0, 0), (0, -1), _PANEL),
                ("GRID", (0, 0), (-1, -1), 0.3, _LINE),
                ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ]))
            story.append(KeepTogether([header, detail, Spacer(1, 8)]))
    story.append(PageBreak())

    # ── 5. GOVERNANCE & POLICY COMPLIANCE ────────────────────────────────────
    story.append(_section("5", "Governance &amp; Policy Compliance", s))
    story.append(Paragraph(
        f"AgentShadow evaluated this agent against the active governance policy set. The aggregate verdict is "
        f"<b>{agent.final_decision.upper()}</b>.", s["Body"]))
    if agent.policy_decisions:
        rows = [[Paragraph(c, s["CellHead"]) for c in ["Policy", "Decision", "Sev", "Rationale"]]]
        dec_color = {"deny": _RISK_COLORS["CRITICAL"], "warn": _RISK_COLORS["MEDIUM"], "allow": _RISK_COLORS["MINIMAL"]}
        decision_cells = []
        for d in agent.policy_decisions:
            status = d.decision.upper() if d.matched else "PASS"
            color = dec_color.get(d.decision, _MUTED) if d.matched else _RISK_COLORS["MINIMAL"]
            decision_cells.append(color)
            rows.append([
                Paragraph(f"<b>{d.name}</b><br/><font size=7 color='#64748b'>{d.policy_id}</font>", s["Cell"]),
                Paragraph(f"<b>{status}</b>", ParagraphStyle("d", parent=s["Cell"], textColor=color)),
                Paragraph(str(d.severity), s["Cell"]),
                Paragraph(d.message if d.matched else "Policy condition not met.", s["Cell"]),
            ])
        pol = Table(rows, colWidths=[46 * mm, 22 * mm, 12 * mm, content_w - 80 * mm])
        pol.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), _BRAND),
            ("GRID", (0, 0), (-1, -1), 0.3, _LINE),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, _PANEL]),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(pol)
    else:
        story.append(Paragraph("No governance policies were evaluated or triggered for this agent.", s["Body"]))
    story.append(Spacer(1, 6))
    story.append(Paragraph(f"<b>Compliance mapping:</b> {compliance}", s["Body"]))
    story.append(PageBreak())

    # ── 6. REMEDIATION ROADMAP ───────────────────────────────────────────────
    story.append(_section("6", "Remediation Roadmap", s))
    story.append(Paragraph(
        "Recommended actions are prioritized by the severity of the finding that drives them. Assign an owner and "
        "target date to each item to track remediation to closure.", s["Body"]))
    fam_max_sev: dict[str, int] = {}
    for f in agent.findings:
        fam = f.family or "general"
        fam_max_sev[fam] = max(fam_max_sev.get(fam, 0), f.severity)
    items = []
    for fam, sev in sorted(fam_max_sev.items(), key=lambda kv: -kv[1]):
        if fam in _RECOMMENDATIONS:
            items.append((sev, _REMEDIATION_PRIORITY.get(sev, "P3 — Planned"), _RECOMMENDATIONS[fam]))
    if agent.owner == "unassigned":
        items.append((4, "P1 — Immediate", "Assign an accountable owner to this agent for governance and audit."))
    if not items:
        items.append((1, "P4 — Backlog", "Maintain current guardrails and re-scan after any configuration change."))
    rows = [[Paragraph(c, s["CellHead"]) for c in ["#", "Priority", "Recommended action", "Owner", "Target date", "Status"]]]
    for i, (sev, prio, action) in enumerate(items, start=1):
        rows.append([
            Paragraph(str(i), s["Cell"]),
            Paragraph(prio, s["Cell"]),
            Paragraph(action, s["Cell"]),
            Paragraph(remediation_owner, s["Cell"]),
            Paragraph(_target_date(sev, now), s["Cell"]),
            Paragraph("Open", s["Cell"]),
        ])
    rm = Table(rows, colWidths=[8 * mm, 24 * mm, content_w - 110 * mm, 24 * mm, 22 * mm, 16 * mm])
    rm.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), _BRAND),
        ("GRID", (0, 0), (-1, -1), 0.3, _LINE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, _PANEL]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(rm)
    story.append(PageBreak())

    # ── 7. APPENDIX ──────────────────────────────────────────────────────────
    story.append(_section("7", "Appendix — Agent Profile &amp; References", s))
    story.append(Paragraph("A. Agent technical profile", s["H3"]))
    appendix_rows = [
        ("Agent identifier", Paragraph(agent.agent_id, s["Mono"])),
        ("Framework", agent.framework),
        ("Model", agent.model or "unknown"),
        ("Discovery source", agent.source),
        ("Discovery location", Paragraph(agent.discovery_path or "n/a", s["Mono"])),
        ("Tools / capabilities", ", ".join(agent.tools) if agent.tools else "none detected"),
        ("Autonomy level", agent.autonomy_level),
        ("First seen", agent.first_seen.strftime("%Y-%m-%d %H:%M UTC")),
        ("Last seen", agent.last_seen.strftime("%Y-%m-%d %H:%M UTC")),
        ("Times observed", str(agent.scan_count)),
    ]
    story.append(_kv_table(appendix_rows, s))
    story.append(Paragraph("B. References", s["H3"]))
    for ref in [
        "OWASP Top 10 for Large Language Model Applications — owasp.org/www-project-top-10-for-large-language-model-applications",
        "MITRE ATLAS (Adversarial Threat Landscape for AI Systems) — atlas.mitre.org",
        "NIST AI Risk Management Framework (AI RMF 1.0) — nist.gov/itl/ai-risk-management-framework",
    ]:
        story.append(Paragraph(f"&bull;&nbsp; {ref}", s["Small"]))
    story.append(Paragraph("C. Glossary", s["H3"]))
    story.append(Paragraph(
        "<b>Autonomy level</b> — the degree to which the agent acts without human approval. "
        "<b>Blast radius</b> — the potential impact of a tool the agent can invoke. "
        "<b>Deterministic score</b> — a reproducible 0–100 risk value derived from the agent configuration.", s["Small"]))
    story.append(Spacer(1, 14))
    story.append(HRFlowable(width="100%", thickness=0.5, color=_LINE))
    story.append(Paragraph(
        "Generated by AgentShadow — deterministic AI agent risk scoring, reusing the Valo scoring engine. "
        "This report reflects the agent configuration observed at assessment time; re-scan after any change.",
        ParagraphStyle("end", parent=s["Small"], alignment=TA_CENTER)))

    doc.build(story, canvasmaker=_make_canvas(report_id, agent.name))
    return buf.getvalue()
