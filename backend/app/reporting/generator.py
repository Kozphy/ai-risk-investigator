from __future__ import annotations

from pathlib import Path
from uuid import UUID

from docx import Document as DocxDocument
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.models import Analysis, Report
from app.models.enums import ReportFormat


class ReportGenerator:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.settings = get_settings()

    async def generate(self, analysis_id: UUID, fmt: ReportFormat, created_by: UUID) -> Report:
        result = await self.db.execute(
            select(Analysis)
            .where(Analysis.id == analysis_id)
            .options(selectinload(Analysis.findings), selectinload(Analysis.document))
        )
        analysis = result.scalar_one()
        out_dir = Path(self.settings.report_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        filename = f"audit-report-{analysis_id}.{fmt.value}"
        path = out_dir / filename

        if fmt == ReportFormat.PDF:
            self._write_pdf(path, analysis)
        else:
            self._write_docx(path, analysis)

        report = Report(
            analysis_id=analysis.id,
            format=fmt.value,
            storage_path=str(path),
            file_size=path.stat().st_size,
            created_by=created_by,
        )
        self.db.add(report)
        await self.db.flush()
        return report

    def _write_pdf(self, path: Path, analysis: Analysis) -> None:
        styles = getSampleStyleSheet()
        doc = SimpleDocTemplate(str(path), pagesize=A4)
        story = [
            Paragraph("AI Risk Investigator — Audit Report", styles["Title"]),
            Spacer(1, 12),
            Paragraph(f"Document: {analysis.document.original_filename}", styles["Normal"]),
            Paragraph(f"Analysis ID: {analysis.id}", styles["Normal"]),
            Spacer(1, 12),
            Paragraph("1. Executive Summary", styles["Heading2"]),
        ]
        summary = analysis.executive_summary or {}
        for key, label in [
            ("top_risks", "Top Risks"),
            ("key_observations", "Key Observations"),
            ("recommended_actions", "Recommended Actions"),
        ]:
            story.append(Paragraph(label, styles["Heading3"]))
            for item in summary.get(key, []) or []:
                story.append(Paragraph(f"• {item}", styles["Normal"]))
        if summary.get("heatmap_summary"):
            story.append(Paragraph("Heatmap Summary", styles["Heading3"]))
            story.append(Paragraph(str(summary["heatmap_summary"]), styles["Normal"]))

        story.append(Spacer(1, 12))
        story.append(Paragraph("2. Findings", styles["Heading2"]))
        data = [["Severity", "Category", "Finding", "Confidence"]]
        for f in analysis.findings:
            data.append([f.severity, f.category, f.finding[:80], f"{f.confidence_score:.2f}"])
        table = Table(data, colWidths=[70, 90, 250, 70])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )
        story.append(table)

        story.append(Spacer(1, 12))
        story.append(Paragraph("3. Recommendations", styles["Heading2"]))
        for f in analysis.findings:
            if f.recommendation:
                story.append(Paragraph(f"• [{f.severity}] {f.recommendation}", styles["Normal"]))

        story.append(Spacer(1, 12))
        story.append(Paragraph("4. Appendix — Evidence Excerpts", styles["Heading2"]))
        for f in analysis.findings:
            story.append(Paragraph(f"<b>{f.finding}</b> (p.{f.page_number})", styles["Normal"]))
            story.append(Paragraph(f.supporting_text[:500], styles["Normal"]))
            story.append(Spacer(1, 6))

        doc.build(story)

    def _write_docx(self, path: Path, analysis: Analysis) -> None:
        doc = DocxDocument()
        doc.add_heading("AI Risk Investigator — Audit Report", 0)
        doc.add_paragraph(f"Document: {analysis.document.original_filename}")
        doc.add_paragraph(f"Analysis ID: {analysis.id}")
        doc.add_heading("Executive Summary", level=1)
        summary = analysis.executive_summary or {}
        for key, label in [
            ("top_risks", "Top Risks"),
            ("key_observations", "Key Observations"),
            ("recommended_actions", "Recommended Actions"),
        ]:
            doc.add_heading(label, level=2)
            for item in summary.get(key, []) or []:
                doc.add_paragraph(item, style="List Bullet")
        doc.add_heading("Findings", level=1)
        for f in analysis.findings:
            doc.add_heading(f"[{f.severity.upper()}] {f.finding}", level=2)
            doc.add_paragraph(f.explanation)
            doc.add_paragraph(f"Evidence (p.{f.page_number}): {f.supporting_text}")
            if f.recommendation:
                doc.add_paragraph(f"Recommendation: {f.recommendation}")
        doc.add_heading("Appendix", level=1)
        doc.add_paragraph("Generated by AI Risk Investigator. Reviewer validation required.")
        doc.save(str(path))
