"""
NEXORA Phase 8 - PDF Export Utility.
Builds high-contrast, clean operational PDF documents using ReportLab Platypus.
Features:
- Multi-page tables with repeated header row.
- Numbered canvas for "Page X of Y" pagination.
- Operational metadata block and summary KPI metrics.
- Prototype decision-support disclaimer on all pages.
- Cell wrapping using Paragraphs to prevent overflow.
"""

import io
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether,
)
from reportlab.pdfgen import canvas


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas to dynamically compute and print 'Page X of Y'."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, total_pages: int):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#4D4947"))

        # Footer divider line
        self.setStrokeColor(colors.HexColor("#D1CECB"))
        self.setLineWidth(0.5)
        self.line(36, 36, self._pagesize[0] - 36, 36)

        # Footer text
        footer_text = (
            "NEXORA Operational Decision Support — Simulation & Prototype Records. "
            "Not an automated 911/emergency dispatch system."
        )
        self.drawString(36, 24, footer_text)

        # Page number on right
        page_str = f"Page {self._pageNumber} of {total_pages}"
        self.drawRightString(self._pagesize[0] - 36, 24, page_str)

        self.restoreState()


def build_pdf_document(
    report_title: str,
    metadata: Dict[str, Any],
    summary_metrics: Optional[Dict[str, Any]],
    columns: List[str],
    records: List[Dict[str, Any]],
    disclaimer: Optional[str] = None,
    orientation: Optional[str] = None,
) -> bytes:
    """
    Generate a professional operational PDF report from structured records.
    Returns bytes of the compiled PDF.
    """
    buffer = io.BytesIO()
    if orientation is None:
        orientation = "landscape" if len(columns) > 5 else "portrait"
    pagesize = landscape(letter) if orientation == "landscape" else letter
    doc = SimpleDocTemplate(
        buffer,
        pagesize=pagesize,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=48,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=16,
        leading=20,
        textColor=colors.HexColor("#101010"),
    )
    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#EE6018"),
    )
    meta_style = ParagraphStyle(
        "ReportMeta",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#4D4947"),
    )
    meta_bold = ParagraphStyle(
        "ReportMetaBold",
        parent=meta_style,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#1D1A18"),
    )
    th_style = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#FAFAFA"),
        alignment=0,
    )
    td_style = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#1D1A18"),
        wordWrap="CJK",
    )
    kpi_title_style = ParagraphStyle(
        "KPITitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7,
        leading=9,
        textColor=colors.HexColor("#8A8380"),
    )
    kpi_val_style = ParagraphStyle(
        "KPIVal",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=14,
        textColor=colors.HexColor("#101010"),
    )
    disclaimer_style = ParagraphStyle(
        "NoticeBox",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#3D3A39"),
    )

    story = []

    # 1. Header Banner
    story.append(Paragraph("NEXORA — CROWD SAFETY INTELLIGENCE & INCIDENT RESPONSE", subtitle_style))
    story.append(Spacer(1, 2))
    story.append(Paragraph(report_title.upper(), title_style))
    story.append(Spacer(1, 8))

    # 2. Metadata Block
    gen_time = metadata.get("generated_at", datetime.now(timezone.utc).isoformat())
    period_str = metadata.get("period", "all")
    start_time = metadata.get("start_time") or "N/A"
    end_time = metadata.get("end_time") or "N/A"
    filters = metadata.get("filters_applied") or {}
    filter_desc = ", ".join(f"{k}={v}" for k, v in filters.items()) if filters else "None"

    meta_table_data = [
        [
            Paragraph("Generated At:", meta_bold),
            Paragraph(f"{gen_time} (UTC)", meta_style),
            Paragraph("Period Covered:", meta_bold),
            Paragraph(f"{period_str} [{start_time} -> {end_time}]", meta_style),
        ],
        [
            Paragraph("Active Filters:", meta_bold),
            Paragraph(filter_desc, meta_style),
            Paragraph("Record Count:", meta_bold),
            Paragraph(f"{len(records)} records", meta_style),
        ],
    ]
    meta_table = Table(meta_table_data, colWidths=[80, 220, 80, None])
    meta_table.setStyle(
        TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F7F6F5")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#D1CECB")),
            ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#EAE7E4")),
        ])
    )
    story.append(meta_table)
    story.append(Spacer(1, 10))

    # 3. Optional Summary Metrics KPI row
    if summary_metrics:
        kpi_cells = []
        for key, val in summary_metrics.items():
            kpi_cells.append([
                [Paragraph(key.replace("_", " ").title(), kpi_title_style)],
                [Paragraph(str(val) if val is not None else "—", kpi_val_style)],
            ])
        # Arrange in rows of up to 4
        chunk_size = 4
        for i in range(0, len(kpi_cells), chunk_size):
            chunk = kpi_cells[i : i + chunk_size]
            kpi_row = []
            for item in chunk:
                cell_table = Table(item)
                cell_table.setStyle(
                    TableStyle([
                        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FFFFFF")),
                        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#D1CECB")),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                        ("LEFTPADDING", (0, 0), (-1, -1), 6),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ])
                )
                kpi_row.append(cell_table)
            kpi_container = Table([kpi_row], colWidths=[(pagesize[0] - 72) / len(chunk)] * len(chunk))
            kpi_container.setStyle(
                TableStyle([
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ])
            )
            story.append(kpi_container)
        story.append(Spacer(1, 8))

    # 4. Prototype Disclaimer Notice
    disc_text = disclaimer or (
        "NOTICE: NEXORA is a prototype decision-support system. All simulated resources and routes "
        "are for operational demonstration. Sampled-frame detections reflect bounding box counts from recorded video."
    )
    disc_table = Table([[Paragraph(disc_text, disclaimer_style)]], colWidths=[pagesize[0] - 72])
    disc_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FFF7ED")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#FDBA74")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ])
    )
    story.append(disc_table)
    story.append(Spacer(1, 10))

    # 5. Data Records Table
    if not columns or not records:
        empty_p = Paragraph("No records matched the selected reporting filters and period.", meta_bold)
        story.append(Table([[empty_p]], colWidths=[pagesize[0] - 72]))
    else:
        table_data = []
        # Header row
        header_row = [Paragraph(c.replace("_", " ").title(), th_style) for c in columns]
        table_data.append(header_row)

        # Body rows
        for rec in records:
            row_cells = []
            for col in columns:
                val = rec.get(col)
                if val is None:
                    cell_val = "—"
                elif isinstance(val, (dict, list)):
                    cell_val = str(val)
                elif isinstance(val, bool):
                    cell_val = "Yes" if val else "No"
                else:
                    cell_val = str(val)
                row_cells.append(Paragraph(cell_val, td_style))
            table_data.append(row_cells)

        # Distribute available page width among columns
        available_width = pagesize[0] - 72
        col_width = available_width / len(columns)
        doc_table = Table(table_data, colWidths=[col_width] * len(columns), repeatRows=1)
        doc_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1D1A18")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#FAFAFA")),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#EAE7E4")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#3D3A39")),
                # Alternate row shading
                *[
                    ("BACKGROUND", (0, r), (-1, r), colors.HexColor("#F9F9F8"))
                    for r in range(2, len(table_data), 2)
                ],
            ])
        )
        story.append(doc_table)

    # Build the PDF
    doc.build(story, canvasmaker=NumberedCanvas)
    buffer.seek(0)
    return buffer.getvalue()
