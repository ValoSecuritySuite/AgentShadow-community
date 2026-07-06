"""Generate the AgentShadow one-page sales/positioning PDF.

Reuses the same ReportLab-based approach as the existing Valo proposal scripts
under plan/. Run from the AgentShadow/ directory with the venv active:

    python marketing/build_one_pager.py
"""

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    ListFlowable,
    ListItem,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

_BRAND = colors.HexColor("#4f46e5")
_DARK = colors.HexColor("#1e293b")
_MUTED = colors.HexColor("#64748b")
OUTPUT = Path(__file__).resolve().parent / "AgentShadow_One_Pager.pdf"


def _styles():
    s = getSampleStyleSheet()
    s.add(ParagraphStyle("Brand", parent=s["Title"], textColor=_BRAND, fontSize=28, spaceAfter=2))
    s.add(ParagraphStyle("Tag", parent=s["Normal"], textColor=_MUTED, fontSize=12, alignment=TA_CENTER))
    s.add(ParagraphStyle("H", parent=s["Heading2"], textColor=_DARK, fontSize=13, spaceBefore=12, spaceAfter=4))
    s.add(ParagraphStyle("Body", parent=s["Normal"], fontSize=10, textColor=_DARK, leading=14))
    return s


def build() -> Path:
    doc = SimpleDocTemplate(
        str(OUTPUT), pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm, topMargin=18 * mm, bottomMargin=16 * mm,
        title="AgentShadow One-Pager",
    )
    s = _styles()
    story: list = []

    story.append(Paragraph("AgentShadow", s["Brand"]))
    story.append(Paragraph("Discover, score &amp; govern every AI agent in your organization", s["Tag"]))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=2, color=_BRAND))
    story.append(Spacer(1, 8))

    story.append(Paragraph("The problem", s["H"]))
    story.append(Paragraph(
        "AI agents are proliferating across codebases and SaaS stacks - LangChain, CrewAI, AutoGPT, "
        "AutoGen, OpenAI Assistants. Most are invisible to security teams: no inventory, no risk rating, "
        "no governance. A single shell-capable, unowned, high-autonomy agent is a material breach risk.",
        s["Body"],
    ))

    story.append(Paragraph("What AgentShadow does", s["H"]))
    story.append(ListFlowable(
        [
            ListItem(Paragraph("<b>Discover</b> agents via code scanning <i>and</i> runtime/SaaS connectors.", s["Body"])),
            ListItem(Paragraph("<b>Inventory</b> them in a single Discovered Agents view (owner, framework, tools, autonomy).", s["Body"])),
            ListItem(Paragraph("<b>Score</b> each agent 0-100 with a deterministic, auditable risk engine.", s["Body"])),
            ListItem(Paragraph("<b>Govern</b> with YAML policies: allow / warn / deny, with full decision trails.", s["Body"])),
            ListItem(Paragraph("<b>Report</b> branded PDF assessments and feed the cross-tool correlation graph.", s["Body"])),
        ],
        bulletType="bullet", leftIndent=12,
    ))

    story.append(Paragraph("What we detect", s["H"]))
    rows = [
        ["Frameworks", "LangChain/LangGraph, CrewAI, AutoGPT, AutoGen, OpenAI Assistants, LlamaIndex, Semantic Kernel"],
        ["Risk signals", "Shell/code execution, unbounded autonomy, missing approval gates, hardcoded secrets, exfiltration tools"],
        ["Governance", "Score thresholds, capability gates, ownership/accountability requirements"],
    ]
    table = Table(rows, colWidths=[35 * mm, 130 * mm])
    table.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1), _BRAND),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("TEXTCOLOR", (1, 0), (1, -1), _DARK),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LINEBELOW", (0, 0), (-1, -2), 0.4, colors.HexColor("#e2e8f0")),
    ]))
    story.append(table)

    story.append(Paragraph("Built on a proven platform", s["H"]))
    story.append(Paragraph(
        "AgentShadow reuses battle-tested engines from the Valo security ecosystem - LLMShadow framework "
        "detection, the Valo deterministic scoring and governance policy engines, Valo ReportLab reporting, "
        "and SaaSShadow inventory UI - registering as a first-class source in the shared correlation graph. "
        "New detection content, not a new architecture.",
        s["Body"],
    ))

    story.append(Spacer(1, 14))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e2e8f0")))
    story.append(Paragraph("AgentShadow &middot; AI Agent Security Posture Management", s["Tag"]))

    doc.build(story)
    return OUTPUT


if __name__ == "__main__":
    path = build()
    print(f"Wrote {path}")
