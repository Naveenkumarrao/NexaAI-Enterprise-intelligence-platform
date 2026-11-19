from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
from pathlib import Path
from datetime import datetime
from typing import Dict, List
from xml.sax.saxutils import escape
from backend.config import settings


def export_pdf(report_data: Dict, filename: str) -> str:
    output_path = settings.REPORTS_DIR / f"{filename}.pdf"
    doc = SimpleDocTemplate(str(output_path), pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Title'],
                                 fontSize=18, textColor=colors.HexColor('#1a237e'),
                                 spaceAfter=12, alignment=TA_CENTER)
    heading_style = ParagraphStyle('Heading', parent=styles['Heading2'],
                                   fontSize=13, textColor=colors.HexColor('#283593'),
                                   spaceBefore=14, spaceAfter=6)
    body_style = ParagraphStyle('Body', parent=styles['Normal'],
                                fontSize=10, leading=16, spaceAfter=8)

    story = []
    story.append(Paragraph(report_data.get("title", "Analysis Report"), title_style))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", body_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#3949ab')))
    story.append(Spacer(1, 0.4*cm))

    for section_key, section_title in [
        ("summary", "Executive Summary"),
        ("analysis", "Analysis"),
        ("key_insights", "Key Insights"),
        ("risks", "Risks & Concerns"),
        ("pros_cons", "Pros & Cons"),
        ("numerical_data", "Numerical Data"),
        ("comparison_strengths_weaknesses", "Comparison Strengths & Weaknesses"),
        ("comparison_risk_assessment", "Comparison Risk Assessment"),
        ("recommendation", "Recommendation"),
        ("analysis_raw", "Full Analysis"),
        ("comparison_raw", "Full Comparison"),
    ]:
        content = report_data.get(section_key, "")
        if content:
            story.append(Paragraph(section_title, heading_style))
            if isinstance(content, list):
                for item in content:
                    story.append(Paragraph(f"• {escape(str(item))}", body_style))
            else:
                safe_content = escape(str(content)).replace("\n", "<br/>")
                story.append(Paragraph(safe_content, body_style))
            story.append(Spacer(1, 0.3*cm))

    comparison_table = report_data.get("comparison_table")
    if comparison_table and isinstance(comparison_table, list) and len(comparison_table) > 0:
        story.append(Paragraph("Comparison Table", heading_style))
        headers = list(comparison_table[0].keys())
        table_data = [headers] + [[str(row.get(h, "")) for h in headers] for row in comparison_table]
        tbl = Table(table_data, repeatRows=1)
        tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3949ab')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#e8eaf6')]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(tbl)
        story.append(Spacer(1, 0.3*cm))

    doc.build(story)
    return str(output_path)


def export_excel(report_data: Dict, filename: str) -> str:
    output_path = settings.REPORTS_DIR / f"{filename}.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Report"

    header_font = Font(bold=True, color="FFFFFF", size=12)
    header_fill = PatternFill("solid", fgColor="3949AB")
    center = Alignment(horizontal="center", vertical="center", wrap_text=True)
    left = Alignment(horizontal="left", vertical="center", wrap_text=True)

    ws.merge_cells("A1:D1")
    ws["A1"] = report_data.get("title", "Analysis Report")
    ws["A1"].font = Font(bold=True, size=14, color="1A237E")
    ws["A1"].alignment = center

    ws.merge_cells("A2:D2")
    ws["A2"] = f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    ws["A2"].alignment = center

    row = 4
    for section_key, section_title in [
        ("summary", "Executive Summary"),
        ("analysis", "Analysis"),
        ("key_insights", "Key Insights"),
        ("risks", "Risks & Concerns"),
        ("pros_cons", "Pros & Cons"),
        ("numerical_data", "Numerical Data"),
        ("comparison_strengths_weaknesses", "Comparison Strengths & Weaknesses"),
        ("comparison_risk_assessment", "Comparison Risk Assessment"),
        ("recommendation", "Recommendation"),
        ("analysis_raw", "Full Analysis"),
        ("comparison_raw", "Full Comparison"),
    ]:
        content = report_data.get(section_key, "")
        if content:
            ws.merge_cells(f"A{row}:D{row}")
            ws[f"A{row}"] = section_title
            ws[f"A{row}"].font = header_font
            ws[f"A{row}"].fill = header_fill
            ws[f"A{row}"].alignment = center
            row += 1
            ws.merge_cells(f"A{row}:D{row}")
            ws[f"A{row}"] = "\n".join(content) if isinstance(content, list) else str(content)
            ws[f"A{row}"].alignment = left
            ws.row_dimensions[row].height = 60
            row += 2

    comparison_table = report_data.get("comparison_table")
    if comparison_table and isinstance(comparison_table, list) and len(comparison_table) > 0:
        ws.merge_cells(f"A{row}:D{row}")
        ws[f"A{row}"] = "Comparison Table"
        ws[f"A{row}"].font = header_font
        ws[f"A{row}"].fill = header_fill
        ws[f"A{row}"].alignment = center
        row += 1
        headers = list(comparison_table[0].keys())
        for col_idx, h in enumerate(headers, 1):
            cell = ws.cell(row=row, column=col_idx, value=h)
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill("solid", fgColor="5C6BC0")
            cell.alignment = center
        row += 1
        for entry in comparison_table:
            for col_idx, h in enumerate(headers, 1):
                ws.cell(row=row, column=col_idx, value=str(entry.get(h, "")))
            row += 1

    for column in range(1, ws.max_column + 1):
        ws.column_dimensions[get_column_letter(column)].width = 30

    wb.save(str(output_path))
    return str(output_path)
