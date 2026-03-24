import pandas as pd
import io
import os
from fpdf import FPDF
from utils import t
import datetime

import arabic_reshaper
from bidi.algorithm import get_display

class EngiCostPDF(FPDF):
    def footer(self):
        # Position at 1.5 cm from bottom
        self.set_y(-15)
        
        # Determine if we can use Arabic in the footer
        # fpdf2 stores font keys in lowercase
        has_unicode = "amiri" in self.fonts
        
        if has_unicode:
            self.set_font("Amiri", '', 8)
            sig_ar = get_display(arabic_reshaper.reshape("منصة إنجي كوست الهندسية الذكية"))
            footer_text = f"EngiCost AI Platform - {sig_ar}"
        else:
            self.set_font("Arial", 'B', 8)
            footer_text = "EngiCost AI Platform"
            
        self.set_text_color(37, 99, 235) # Corporate Blue
        self.cell(0, 10, footer_text, align='L')
        
        # Page Number - Right
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Page {self.page_no()}", align='R')

class ExportEngine:
    """
    Advanced engine for generating professional, client-ready reports.
    Supports white-labeling and multiple formats.
    """

    @staticmethod
    def _reshape(txt):
        if not txt: return ""
        # Handle Arabic bidirectional display
        try:
            return get_display(arabic_reshaper.reshape(str(txt)))
        except:
            return str(txt)

    @staticmethod
    def generate_professional_pdf(df, project_name="BOQ Project", company_name="EngiCost Partner", logo_path=None, currency_symbol="$"):
        """
        Creates a high-end PDF report with corporate headers and footers on every page.
        """
        font_path = "assets/Amiri-Regular.ttf"
        pdf = EngiCostPDF()
        
        # Register Arabic-capable font
        use_amiri = False
        if os.path.exists(font_path):
            try:
                pdf.add_font("Amiri", "", font_path)
                pdf.set_font("Amiri", size=10)
                use_amiri = True
            except:
                pass
            
        pdf.add_page()
        
        # --- Header Section ---
        if logo_path:
            try:
                pdf.image(logo_path, x=10, y=8, h=20)
            except Exception as e:
                print(f"Logo error: {e}")
        
        # Title (Reshaped)
        if use_amiri: pdf.set_font("Amiri", size=20)
        else: pdf.set_font("Arial", 'B', 20)
        
        pdf.set_text_color(37, 99, 235) # Primary Blue
        pdf.cell(0, 15, txt=ExportEngine._reshape(project_name), ln=True, align='R')
        
        if use_amiri: pdf.set_font("Amiri", size=10)
        else: pdf.set_font("Arial", size=10)
        
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 10, txt=ExportEngine._reshape(f"Prepared by: {company_name}"), ln=True, align='R')
        pdf.cell(0, 5, txt=ExportEngine._reshape(f"Date: {datetime.datetime.now().strftime('%Y-%m-%d')}"), ln=True, align='R')
        pdf.ln(20)
        
        # --- Corporate Intro ---
        if use_amiri: pdf.set_font("Amiri", size=12)
        else: pdf.set_font("Arial", 'B', 12)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 10, txt=ExportEngine._reshape("Bill of Quantities / Project Estimation Summary"), ln=True)
        pdf.set_draw_color(37, 99, 235)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)

        # --- Table Section ---
        pdf.set_fill_color(37, 99, 235)
        pdf.set_text_color(255, 255, 255)
        if use_amiri: pdf.set_font("Amiri", size=10)
        else: pdf.set_font("Arial", 'B', 10)
        
        # Column Widths
        col_widths = [80, 25, 30, 55]
        cols = [
            t("Item Description", "Item Description"),
            t("Unit", "Unit"),
            t("Qty", "Qty"),
            t(f"Price ({currency_symbol})", f"Rate ({currency_symbol})")
        ]
        
        for i, col in enumerate(cols):
            pdf.cell(col_widths[i], 12, ExportEngine._reshape(col), border=1, fill=True, align='C')
        pdf.ln()
        
        pdf.set_text_color(0, 0, 0)
        total_value = 0.0
        for _, row in df.iterrows():
            rate = float(row.get('rate', 0))
            qty = float(row.get('quantity', 1))
            
            # Clip description for table stability and Reshape
            raw_item = row.get('item', '')
            desc = ExportEngine._reshape(str(raw_item)[:45])
            
            pdf.cell(col_widths[0], 10, desc, border=1)
            pdf.cell(col_widths[1], 10, ExportEngine._reshape(row.get('unit', '')), border=1, align='C')
            pdf.cell(col_widths[2], 10, str(qty), border=1, align='C')
            pdf.cell(col_widths[3], 10, f"{currency_symbol}{rate:,.2f}", border=1, align='R')
            pdf.ln()
            total_value += (qty * rate)

        # --- Totals Section ---
        pdf.ln(5)
        if use_amiri: pdf.set_font("Amiri", size=11)
        else: pdf.set_font("Arial", 'B', 11)
        
        pdf.cell(135, 10, ExportEngine._reshape("Subtotal"), border=1, align='R')
        pdf.cell(55, 10, f"{currency_symbol}{total_value:,.2f}", border=1, align='R')
        pdf.ln()
        pdf.cell(135, 10, ExportEngine._reshape("Estimated Taxes / VAT (14%)"), border=1, align='R')
        pdf.cell(55, 10, f"{currency_symbol}{total_value * 0.14:,.2f}", border=1, align='R')
        pdf.ln()
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(135, 12, ExportEngine._reshape("GRAND TOTAL"), border=1, fill=True, align='R')
        pdf.cell(55, 12, f"{currency_symbol}{total_value * 1.14:,.2f}", border=1, fill=True, align='R')
        
        return bytes(pdf.output())

    @staticmethod
    def generate_full_proposal(df, project_name="Technical & Commercial Proposal", company_name="EngiCost Partner", logo_path=None, currency_symbol="$"):
        """
        Generates a comprehensive one-click proposal including Terms & Conditions, Scope of work, etc.
        """
        font_path = "assets/Amiri-Regular.ttf"
        pdf = EngiCostPDF()
        
        use_amiri = False
        if os.path.exists(font_path):
            try:
                pdf.add_font("Amiri", "", font_path)
                pdf.set_font("Amiri", size=10)
                use_amiri = True
            except: pass
            
        pdf.add_page()
        
        if logo_path:
            try:
                pdf.image(logo_path, x=10, y=8, h=25)
            except: pass
            
        pdf.ln(20)
        if use_amiri: pdf.set_font("Amiri", size=24)
        else: pdf.set_font("Arial", 'B', 24)
        pdf.set_text_color(37, 99, 235)
        pdf.cell(0, 15, txt=ExportEngine._reshape(project_name), ln=True, align='C')
        
        pdf.set_font("Amiri", size=14) if use_amiri else pdf.set_font("Arial", 'B', 14)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 10, txt=ExportEngine._reshape(f"Submitted By: {company_name}"), ln=True, align='C')
        pdf.cell(0, 10, txt=ExportEngine._reshape(f"Date: {datetime.datetime.now().strftime('%Y-%m-%d')}"), ln=True, align='C')
        pdf.ln(15)
        
        # Scope of Work
        pdf.set_font("Amiri", size=16) if use_amiri else pdf.set_font("Arial", 'B', 16)
        pdf.set_text_color(37, 99, 235)
        pdf.cell(0, 10, txt=ExportEngine._reshape("1. Scope of Work (نطاق الأعمال)"), ln=True)
        pdf.set_font("Amiri", size=12) if use_amiri else pdf.set_font("Arial", '', 12)
        pdf.set_text_color(0, 0, 0)
        scope_text = "This proposal covers the supply, installation, testing, and commissioning of all materials " \
                     "and equipment listed in the Bill of Quantities below as per the engineering specifications and ECP codes."
        pdf.multi_cell(0, 8, ExportEngine._reshape(scope_text))
        pdf.ln(10)
        
        # Financial Summary
        pdf.set_font("Amiri", size=16) if use_amiri else pdf.set_font("Arial", 'B', 16)
        pdf.set_text_color(37, 99, 235)
        pdf.cell(0, 10, txt=ExportEngine._reshape("2. Financial Summary (الملخص المالي)"), ln=True)
        
        pdf.set_fill_color(37, 99, 235)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Amiri", size=10) if use_amiri else pdf.set_font("Arial", 'B', 10)
        
        col_widths = [80, 25, 30, 55]
        cols = ["Item Description", "Unit", "Qty", f"Total ({currency_symbol})"]
        for i, col in enumerate(cols):
            pdf.cell(col_widths[i], 12, ExportEngine._reshape(col), border=1, fill=True, align='C')
        pdf.ln()
        
        pdf.set_text_color(0, 0, 0)
        total_value = 0.0
        for _, row in df.iterrows():
            rate = float(row.get('rate', 0))
            qty = float(row.get('quantity', 1))
            total = qty * rate
            desc = ExportEngine._reshape(str(row.get('item', ''))[:45])
            
            pdf.cell(col_widths[0], 10, desc, border=1)
            pdf.cell(col_widths[1], 10, ExportEngine._reshape(row.get('unit', '')), border=1, align='C')
            pdf.cell(col_widths[2], 10, str(qty), border=1, align='C')
            pdf.cell(col_widths[3], 10, f"{currency_symbol}{total:,.2f}", border=1, align='R')
            pdf.ln()
            total_value += total
            
        pdf.set_font("Amiri", size=12) if use_amiri else pdf.set_font("Arial", 'B', 12)
        pdf.cell(135, 10, ExportEngine._reshape("Subtotal"), border=1, align='R')
        pdf.cell(55, 10, f"{currency_symbol}{total_value:,.2f}", border=1, align='R')
        pdf.ln()
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(135, 12, ExportEngine._reshape("GRAND TOTAL (Including 14% VAT)"), border=1, fill=True, align='R')
        pdf.cell(55, 12, f"{currency_symbol}{total_value * 1.14:,.2f}", border=1, fill=True, align='R')
        pdf.ln(15)
        
        # Commercial Terms
        pdf.set_font("Amiri", size=16) if use_amiri else pdf.set_font("Arial", 'B', 16)
        pdf.set_text_color(37, 99, 235)
        pdf.cell(0, 10, txt=ExportEngine._reshape("3. Commercial Terms (الشروط التجارية)"), ln=True)
        pdf.set_font("Amiri", size=11) if use_amiri else pdf.set_font("Arial", '', 11)
        pdf.set_text_color(0, 0, 0)
        terms = [
            "1. Validity: This proposal is valid for 15 days from the date of submission.",
            "2. Payment Terms: 40% Advance, 40% Delivery, 20% Testing & Commissioning.",
            "3. Delivery Time: 4-6 weeks from receipt of advance payment.",
            "4. Warranty: 12 months from the date of commissioning."
        ]
        for term in terms:
            pdf.cell(0, 8, txt=ExportEngine._reshape(term), ln=True)
            
        return bytes(pdf.output())

    @staticmethod
    def generate_professional_excel(df, project_name="Project", company_name="Engineer", currency_symbol="$", white_label=False):
        """
        Generates a clean, formatted Excel file with white-label header support.
        """
        output = io.BytesIO()
        if 'rate' in df.columns:
            df = df.rename(columns={'rate': f'Rate ({currency_symbol})'})
            
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Pricing', startrow=3)
            workbook = writer.book
            worksheet = writer.sheets['Pricing']
            
            # --- Document Header Text ---
            title_format = workbook.add_format({'bold': True, 'font_size': 16, 'font_color': '#2563eb'})
            subtitle_format = workbook.add_format({'italic': True, 'font_color': '#555555'})
            
            header_text = f"{company_name} - Project Estimation" if white_label else "EngiCost AI - Project Estimation"
            prepared_by = f"Prepared by: {company_name}" if white_label else f"Prepared via EngiCost AI | For: {company_name}"
            
            worksheet.write('A1', header_text, title_format)
            worksheet.write('A2', f"Project: {project_name}  |  {prepared_by}", subtitle_format)
            
            # --- Table Header ---
            header_format = workbook.add_format({
                'bold': True, 'text_wrap': True, 'valign': 'top',
                'fg_color': '#2563eb', 'font_color': 'white', 'border': 1
            })
            
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(3, col_num, value, header_format)
            
            worksheet.set_column('A:A', 50)
            worksheet.set_column('B:D', 18)

        return output.getvalue()
