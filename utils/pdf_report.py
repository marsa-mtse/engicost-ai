"""
PDF Report Generator - V1.6.0
Generates a unified project report combining BOQ data, drawings, and summary.
"""
import io
from datetime import datetime

try:
    from fpdf import FPDF
    FPDF_AVAILABLE = True
except ImportError:
    FPDF_AVAILABLE = False

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    ARABIC_AVAILABLE = True
except ImportError:
    ARABIC_AVAILABLE = False


def _ar(text: str) -> str:
    """Reshape Arabic text for PDF."""
    if ARABIC_AVAILABLE:
        try:
            reshaped = arabic_reshaper.reshape(text)
            return get_display(reshaped)
        except Exception:
            return text
    return text


def generate_project_pdf(
    project_name: str,
    company_name: str,
    boq_items: list,
    ai_summary: str = "",
    currency: str = "EGP",
    white_label: bool = False,
) -> bytes:
    """
    Generates a comprehensive project report as PDF bytes.
    Returns bytes of the PDF file, ready for st.download_button.
    """
    if not FPDF_AVAILABLE:
        raise ImportError("fpdf2 is not installed. Run: pip install fpdf2")

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # --- Header ---
    pdf.set_fill_color(2, 6, 23)    # Dark blue bg
    pdf.rect(0, 0, 210, 35, 'F')
    pdf.set_text_color(14, 165, 233)
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_xy(10, 8)
    
    header_title = f"{company_name} - Project Report" if white_label else "EngiCost AI - Project Report"
    pdf.cell(0, 10, header_title, ln=True, align="L")
    
    pdf.set_text_color(148, 163, 184)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_xy(10, 20)
    pdf.cell(0, 8, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}  |  Prepared by: {company_name}", ln=True)
    pdf.set_text_color(30, 30, 30)

    # --- Project Title ---
    pdf.set_xy(10, 42)
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(0, 10, f"Project: {project_name}", ln=True)
    pdf.ln(3)
    pdf.set_draw_color(14, 165, 233)
    pdf.set_line_width(0.8)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)

    # --- AI Summary Block ---
    if ai_summary:
        pdf.set_fill_color(240, 249, 255)
        pdf.set_text_color(2, 6, 23)
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "Executive Summary (AI Generated)", ln=True, fill=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(51, 65, 85)
        pdf.multi_cell(0, 6, ai_summary[:1000])
        pdf.ln(4)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(4)

    # --- BOQ Table ---
    if boq_items:
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(30, 41, 59)
        pdf.cell(0, 9, "Bill of Quantities (BOQ)", ln=True)
        pdf.ln(2)

        # Table header
        pdf.set_fill_color(14, 165, 233)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 9)
        col_w = [10, 80, 20, 25, 30, 30]
        headers = ["#", "Description", "Unit", "Qty", f"Unit Price ({currency})", f"Total ({currency})"]
        for i, h in enumerate(headers):
            pdf.cell(col_w[i], 8, h, border=1, fill=True, align="C")
        pdf.ln()

        # Table rows
        pdf.set_font("Helvetica", "", 8)
        total_project = 0.0
        for idx, item in enumerate(boq_items):
            pdf.set_text_color(30, 41, 59)
            pdf.set_fill_color(248, 250, 252) if idx % 2 == 0 else pdf.set_fill_color(255, 255, 255)

            desc = str(item.get("item", item.get("description", "—")))[:60]
            unit = str(item.get("unit", "-"))
            qty = float(item.get("quantity", item.get("qty", 0)) or 0)
            unit_price = float(item.get("Unit Price", item.get("base_price", 0)) or 0)
            total = float(item.get("Total Cost", item.get("direct_total", qty * unit_price)) or 0)
            total_project += total

            row = [str(idx + 1), desc, unit, f"{qty:,.1f}", f"{unit_price:,.0f}", f"{total:,.0f}"]
            for i, val in enumerate(row):
                pdf.cell(col_w[i], 7, val, border=1, fill=True, align="C" if i != 1 else "L")
            pdf.ln()

        # Totals row
        pdf.set_fill_color(30, 41, 59)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(sum(col_w[:4]), 8, "TOTAL PROJECT COST", border=1, fill=True, align="R")
        pdf.cell(col_w[4], 8, "", border=1, fill=True)
        pdf.cell(col_w[5], 8, f"{total_project:,.0f} {currency}", border=1, fill=True, align="C")
        pdf.ln(10)

    # --- Footer ---
    pdf.set_y(-20)
    pdf.set_text_color(148, 163, 184)
    pdf.set_font("Helvetica", "I", 8)
    footer_text = company_name if white_label else "EngiCost AI"
    pdf.cell(0, 6, f"{footer_text} — Confidential Project Document — Page {pdf.page_no()}", align="C")

    return bytes(pdf.output())
