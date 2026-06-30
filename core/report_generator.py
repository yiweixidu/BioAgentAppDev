# core/report_generator.py
"""
BioAgent Report Generator
Produces PI-ready PDF reports for a project's inference results.

Usage:
    from core.report_generator import ReportGenerator
    path = ReportGenerator.generate_project_report("PRJ-101", records, project, grants)
"""

import os
import json
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

# ── Palette (matches Whimsigoth UI) ───────────────────────────
C_NAVY   = colors.HexColor("#111D2E")
C_TEAL   = colors.HexColor("#12A898")
C_AMBER  = colors.HexColor("#C09060")
C_GREEN  = colors.HexColor("#20BB52")
C_RED    = colors.HexColor("#E53E3E")
C_SURF   = colors.HexColor("#1C2D44")
C_MUTED  = colors.HexColor("#4A6880")
C_TEXT   = colors.HexColor("#D5E2EE")
C_WHITE  = colors.white

IP_COLORS = {
    "platform": C_TEAL,
    "lab":      C_AMBER,
    "shared":   C_GREEN,
}


def _styles():
    base = getSampleStyleSheet()
    s = {}
    s["title"] = ParagraphStyle(
        "title", fontSize=22, textColor=C_TEAL,
        fontName="Helvetica-Bold", spaceAfter=4, alignment=TA_LEFT)
    s["subtitle"] = ParagraphStyle(
        "subtitle", fontSize=11, textColor=C_MUTED,
        fontName="Helvetica", spaceAfter=2, alignment=TA_LEFT)
    s["section"] = ParagraphStyle(
        "section", fontSize=13, textColor=C_AMBER,
        fontName="Helvetica-Bold", spaceBefore=14, spaceAfter=6)
    s["body"] = ParagraphStyle(
        "body", fontSize=9, textColor=colors.HexColor("#334455"),
        fontName="Helvetica", leading=14, spaceAfter=4)
    s["mono"] = ParagraphStyle(
        "mono", fontSize=8, textColor=colors.HexColor("#223344"),
        fontName="Courier", leading=12, spaceAfter=2,
        leftIndent=10, backColor=colors.HexColor("#F0F4F8"),
        borderPadding=(4, 6, 4, 6))
    s["label"] = ParagraphStyle(
        "label", fontSize=8, textColor=C_MUTED,
        fontName="Helvetica-Bold", spaceAfter=1,
        letterSpacing=0.5)
    s["ip_platform"] = ParagraphStyle(
        "ip_platform", fontSize=8, textColor=C_TEAL,
        fontName="Helvetica-Bold")
    s["ip_lab"] = ParagraphStyle(
        "ip_lab", fontSize=8, textColor=C_AMBER,
        fontName="Helvetica-Bold")
    s["ip_shared"] = ParagraphStyle(
        "ip_shared", fontSize=8, textColor=C_GREEN,
        fontName="Helvetica-Bold")
    s["footer"] = ParagraphStyle(
        "footer", fontSize=7, textColor=C_MUTED,
        fontName="Helvetica", alignment=TA_CENTER)
    return s


class ReportGenerator:

    @staticmethod
    def generate_project_report(
        project_id:  str,
        records:     list,       # InferenceRecord objects
        project=None,            # Project model object (optional)
        grants:      list = None,
        hypotheses:  list = None,
        output_dir:  str  = None,
    ) -> str:
        """
        Generate a PDF report for a project.
        Returns the path to the generated PDF.
        """
        output_dir = output_dir or os.path.join(
            os.path.dirname(__file__), "..", "reports")
        os.makedirs(output_dir, exist_ok=True)

        ts       = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"BioAgent_{project_id}_Report_{ts}.pdf"
        filepath = os.path.join(output_dir, filename)

        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            leftMargin=2*cm, rightMargin=2*cm,
            topMargin=2.5*cm, bottomMargin=2*cm,
            title=f"BioAgent Report — {project_id}",
            author="BioAgent Research Management System",
        )

        S   = _styles()
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        story = []

        # ── Cover block ───────────────────────────────────────
        story.append(Paragraph("BioAgent", S["title"]))
        story.append(Paragraph(
            "AI-Assisted Research Report", S["subtitle"]))
        story.append(HRFlowable(
            width="100%", thickness=1.5,
            color=C_TEAL, spaceAfter=10))

        # Project meta table
        pi_name = project.getPi()   if project else "—"
        domain  = project.getDomain() if project else "—"
        status  = project.getStatus() if project else "—"
        title   = project.getTitle()  if project else project_id
        meta_data = [
            ["Project ID", project_id, "Title", title],
            ["PI",         pi_name,    "Domain", domain],
            ["Status",     status,     "Generated", now],
        ]
        meta_tbl = Table(meta_data, colWidths=[3*cm, 6*cm, 3*cm, 5.5*cm])
        meta_tbl.setStyle(TableStyle([
            ("FONTNAME",  (0,0), (-1,-1), "Helvetica"),
            ("FONTSIZE",  (0,0), (-1,-1), 8),
            ("FONTNAME",  (0,0), (0,-1), "Helvetica-Bold"),
            ("FONTNAME",  (2,0), (2,-1), "Helvetica-Bold"),
            ("TEXTCOLOR", (0,0), (0,-1), C_MUTED),
            ("TEXTCOLOR", (2,0), (2,-1), C_MUTED),
            ("TEXTCOLOR", (1,0), (1,-1), colors.HexColor("#223344")),
            ("TEXTCOLOR", (3,0), (3,-1), colors.HexColor("#223344")),
            ("ROWBACKGROUNDS", (0,0), (-1,-1),
             [colors.HexColor("#F7F9FC"), colors.HexColor("#EEF2F7")]),
            ("GRID",      (0,0), (-1,-1), 0.3, colors.HexColor("#C0C8D8")),
            ("PADDING",   (0,0), (-1,-1), 5),
        ]))
        story.append(meta_tbl)
        story.append(Spacer(1, 14))

        # ── IP Notice ─────────────────────────────────────────
        story.append(Paragraph("IP OWNERSHIP NOTICE", S["label"]))
        story.append(Paragraph(
            "Base models (DNABERT-2, ESM-2, PPI, RAG) are exclusive BioAgent platform IP. "
            "Fine-tuned skills annotated as <b>shared</b> are co-owned per the collaboration "
            "agreement. Lab data remains the exclusive property of the laboratory.",
            S["body"]))
        story.append(HRFlowable(
            width="100%", thickness=0.5,
            color=C_MUTED, spaceAfter=8))

        # ── Inference Results ─────────────────────────────────
        story.append(Paragraph("Inference Results", S["section"]))
        story.append(Paragraph(
            f"Total inference jobs for {project_id}: {len(records)}",
            S["body"]))
        story.append(Spacer(1, 6))

        for i, rec in enumerate(records, 1):
            ip      = getattr(rec, 'ip_owner', 'platform')
            ip_style = S.get(f"ip_{ip}", S["ip_platform"])
            conf    = getattr(rec, 'confidence', None)
            conf_str = f"{float(conf):.2f}" if conf else "—"

            block = []

            # Header row for this inference
            hdr_data = [[
                Paragraph(f"#{i}  {rec.getInfId()}", S["label"]),
                Paragraph(rec.getType(), S["label"]),
                Paragraph(rec.getModel(), S["label"]),
                Paragraph(ip.upper(), ip_style),
                Paragraph(f"conf. {conf_str}", S["label"]),
            ]]
            hdr_tbl = Table(hdr_data,
                colWidths=[2.5*cm, 3.5*cm, 4*cm, 2.5*cm, 2.5*cm])
            hdr_tbl.setStyle(TableStyle([
                ("BACKGROUND", (0,0), (-1,-1), colors.HexColor("#E8F0F8")),
                ("FONTSIZE",   (0,0), (-1,-1), 8),
                ("PADDING",    (0,0), (-1,-1), 5),
                ("GRID",       (0,0), (-1,-1), 0.3, colors.HexColor("#C0C8D8")),
            ]))
            block.append(hdr_tbl)

            # Input
            block.append(Spacer(1, 3))
            block.append(Paragraph("INPUT", S["label"]))
            inp_text = (rec.getInput() or "")[:200]
            block.append(Paragraph(inp_text, S["mono"]))

            # Result summary
            block.append(Paragraph("RESULT", S["label"]))
            summary = (rec.getResultSummary() or "").replace("\n", "<br/>")
            block.append(Paragraph(summary, S["body"]))

            # Full output (provenance)
            if hasattr(rec, 'result_full') and rec.result_full:
                try:
                    full = json.loads(rec.result_full)
                    prov = full.get("provenance", [])
                    if prov:
                        block.append(Paragraph("PROVENANCE", S["label"]))
                        block.append(Paragraph(
                            "  ·  ".join(prov), S["body"]))
                except Exception:
                    pass

            # Timestamp
            block.append(Paragraph(
                f"Timestamp: {rec.getTimestamp()}   "
                f"Project: {rec.getProjectId() or '—'}",
                S["footer"]))
            block.append(HRFlowable(
                width="100%", thickness=0.3,
                color=colors.HexColor("#C0C8D8"), spaceAfter=8))

            story.append(KeepTogether(block))

        # ── Hypotheses ────────────────────────────────────────
        if hypotheses:
            story.append(Paragraph("Hypothesis Summary", S["section"]))
            hyp_header = [["ID", "Status", "Confidence", "Text"]]
            hyp_rows   = hyp_header + [
                [h.getHypId(),
                 h.getStatus(),
                 f"{h.getConfidence():.2f}",
                 (h.getText() or "")[:80] + ("…" if len(h.getText() or "") > 80 else "")]
                for h in hypotheses
            ]
            hyp_tbl = Table(hyp_rows,
                colWidths=[2*cm, 2.5*cm, 2.5*cm, 10.5*cm])
            hyp_tbl.setStyle(TableStyle([
                ("BACKGROUND",    (0,0), (-1,0), colors.HexColor("#D0DCF0")),
                ("FONTNAME",      (0,0), (-1,0), "Helvetica-Bold"),
                ("FONTSIZE",      (0,0), (-1,-1), 8),
                ("ROWBACKGROUNDS",(0,1), (-1,-1),
                 [colors.HexColor("#F7F9FC"), colors.HexColor("#EEF2F7")]),
                ("GRID",          (0,0), (-1,-1), 0.3, colors.HexColor("#C0C8D8")),
                ("PADDING",       (0,0), (-1,-1), 5),
            ]))
            story.append(hyp_tbl)
            story.append(Spacer(1, 8))

        # ── Grant Summary ─────────────────────────────────────
        if grants:
            story.append(Paragraph("Grant Status", S["section"]))
            g_header = [["Grant ID", "Type", "Total (CAD)",
                          "Used (CAD)", "Remaining", "Budget %", "Deadline"]]
            g_rows = g_header + [
                [g.getGrantId(), g.getGrantType(),
                 f"${g.getTotal():,.0f}",
                 f"${g.getUsed():,.0f}",
                 f"${g.getRemaining():,.0f}",
                 f"{g.getBudgetPct()}%",
                 g.getDeadline()]
                for g in grants
            ]
            g_tbl = Table(g_rows,
                colWidths=[2*cm, 2*cm, 2.5*cm, 2.5*cm, 2.5*cm, 2*cm, 4*cm])
            g_tbl.setStyle(TableStyle([
                ("BACKGROUND",    (0,0), (-1,0), colors.HexColor("#D0DCF0")),
                ("FONTNAME",      (0,0), (-1,0), "Helvetica-Bold"),
                ("FONTSIZE",      (0,0), (-1,-1), 8),
                ("ROWBACKGROUNDS",(0,1), (-1,-1),
                 [colors.HexColor("#F7F9FC"), colors.HexColor("#EEF2F7")]),
                ("GRID",          (0,0), (-1,-1), 0.3, colors.HexColor("#C0C8D8")),
                ("PADDING",       (0,0), (-1,-1), 5),
            ]))
            story.append(g_tbl)
            story.append(Spacer(1, 8))

        # ── Audit Chain Notice ────────────────────────────────
        story.append(HRFlowable(
            width="100%", thickness=0.5, color=C_MUTED, spaceAfter=6))
        story.append(Paragraph(
            "L0 Compliance: All inference results recorded in SHA-256 "
            "tamper-evident audit chain. Generated by BioAgent Research "
            f"Management System · {now}",
            S["footer"]))

        doc.build(story)
        return filepath
