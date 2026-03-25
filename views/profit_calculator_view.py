import streamlit as st
import pandas as pd
from utils import t, render_section_header
from ai_engine.export_engine import ExportEngine
from services.cost_service import CostService
import datetime

def render_profit_calculator():
    render_section_header(t("حاسبة هامش الربح والعطاء", "Profit Margin & Tender Calculator"), "💹")

    st.markdown(f"""
    <div class="glass-card animate-up">
        <p style="color:var(--text-muted);">
            {t("أدخل تكاليف المشروع الفعلية وهامش الربح المطلوب للحصول على سعر العطاء النهائي مع تقرير قابل للتصدير.",
               "Enter actual project costs and desired profit margin to get the final tender price with an exportable offer sheet.")}
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ─── Project Info ────────────────────────────────────────────
    col1, col2 = st.columns(2)
    with col1:
        project_name = st.text_input(t("اسم المشروع", "Project Name"), t("مشروع إنشائي", "Construction Project"))
        client_name  = st.text_input(t("اسم العميل / الجهة", "Client / Entity"), t("شركة الأعمال", "Business Corp."))
    with col2:
        global_currency = st.session_state.get("currency", "USD")
        currency_options = ["USD", "EGP", "SAR", "AED", "QAR", "GBP", "KWD", "OMR", "BHD", "EUR"]
        currency = st.selectbox(
            t("العملة", "Currency"), 
            currency_options,
            index=currency_options.index(global_currency) if global_currency in currency_options else 0
        )
        sym = currency
        offer_date = st.date_input(t("تاريخ العرض", "Offer Date"), value=datetime.date.today())

    st.markdown(f"### {t('تفاصيل التكاليف المباشرة', 'Direct Cost Breakdown')}")

    # ─── Cost Items ──────────────────────────────────────────────
    default_items = [
        {"البند": t("مواد (حديد، أسمنت، خرسانة)", "Materials (Steel, Cement, Concrete)"), "التكلفة": 0.0},
        {"البند": t("أيدي عاملة",  "Labor"), "التكلفة": 0.0},
        {"البند": t("معدات وآليات", "Equipment & Machinery"), "التكلفة": 0.0},
        {"البند": t("إدارة الموقع وإشراف", "Site Management & Supervision"), "التكلفة": 0.0},
        {"البند": t("مقاولو الباطن", "Subcontractors"), "التكلفة": 0.0},
        {"البند": t("مصاريف نقل ولوجستيات", "Transport & Logistics"), "التكلفة": 0.0},
    ]
    df_costs = pd.DataFrame(default_items)
    edited = st.data_editor(
        df_costs, use_container_width=True, num_rows="dynamic",
        column_config={"التكلفة": st.column_config.NumberColumn(f"التكلفة ({sym})", min_value=0.0, format="%.2f")}
    )

    # ─── Overhead & Contingency ───────────────────────────────────
    st.markdown(f"### {t('المصاريف العامة والطوارئ', 'Overhead & Contingency')}")
    c1, c2, c3 = st.columns(3)
    with c1:
        overhead_pct = st.number_input(t("مصاريف عامة %", "Overhead %"), min_value=0.0, max_value=50.0, value=10.0, step=0.5)
    with c2:
        contingency_pct = st.number_input(t("احتياطي طوارئ %", "Contingency %"), min_value=0.0, max_value=30.0, value=5.0, step=0.5)
    with c3:
        profit_pct = st.number_input(t("هامش الربح %", "Profit Margin %"), min_value=0.0, max_value=100.0, value=15.0, step=0.5)

    # ─── Tax ─────────────────────────────────────────────────────
    vat_pct = st.number_input(t("ضريبة القيمة المضافة % (VAT)", "VAT %"), min_value=0.0, max_value=30.0, value=14.0, step=0.5)

    # ─── Calculate & Display ─────────────────────────────────────
    if st.button(t("🧮 احسب سعر العطاء", "🧮 Calculate Tender Price"), use_container_width=True):
        direct_cost = edited["التكلفة"].sum()
        res = CostService.calculate_tender_price(
            direct_cost, overhead_pct, contingency_pct, profit_pct, vat_pct
        )
        
        st.session_state.calc_result = {
            "direct": res["direct_cost"],
            "overhead": res["overhead_val"],
            "contingency": res["contingency_val"],
            "subtotal": res["subtotal"],
            "profit": res["profit_val"],
            "pre_vat": res["pre_vat"],
            "vat": res["vat_val"],
            "grand": res["grand_total"],
            "sym": sym,
            "project": project_name,
            "client": client_name,
            "date": str(offer_date),
            "items": edited.to_dict(orient="records"),
        }
        st.rerun()

    if st.session_state.get("calc_result"):
        r = st.session_state.calc_result
        s = r["sym"]

        st.markdown(f"---\n### 📋 {t('ملخص سعر العطاء', 'Tender Price Summary')}")
        st.markdown(f"""
        <div class="glass-card animate-in" style="border-top:3px solid var(--accent-primary);">
        <table style="width:100%; border-collapse:collapse; font-size:0.95rem;">
          <tr><td style="padding:8px; color:var(--text-muted);">{t('التكلفة المباشرة الإجمالية','Total Direct Cost')}</td>
              <td style="text-align:right; font-weight:bold;">{s} {r['direct']:,.2f}</td></tr>
          <tr><td style="padding:8px; color:var(--text-muted);">{t('المصاريف العامة','Overhead')} ({overhead_pct}%)</td>
              <td style="text-align:right;">{s} {r['overhead']:,.2f}</td></tr>
          <tr><td style="padding:8px; color:var(--text-muted);">{t('احتياطي الطوارئ','Contingency')} ({contingency_pct}%)</td>
              <td style="text-align:right;">{s} {r['contingency']:,.2f}</td></tr>
          <tr style="border-top:1px solid rgba(255,255,255,0.1);">
              <td style="padding:8px; font-weight:bold;">{t('الإجمالي قبل الربح','Subtotal')}</td>
              <td style="text-align:right; font-weight:bold; color:var(--accent-primary);">{s} {r['subtotal']:,.2f}</td></tr>
          <tr><td style="padding:8px; color:var(--success);">{t('هامش الربح','Profit Margin')} ({profit_pct}%)</td>
              <td style="text-align:right; color:var(--success);">{s} {r['profit']:,.2f}</td></tr>
          <tr><td style="padding:8px; color:var(--text-muted);">{t('السعر قبل الضريبة','Pre-VAT Price')}</td>
              <td style="text-align:right;">{s} {r['pre_vat']:,.2f}</td></tr>
          <tr><td style="padding:8px; color:var(--text-muted);">VAT ({vat_pct}%)</td>
              <td style="text-align:right;">{s} {r['vat']:,.2f}</td></tr>
          <tr style="border-top:2px solid var(--success); background:rgba(74,222,128,0.08);">
              <td style="padding:12px; font-size:1.2rem; font-weight:bold; color:var(--success);">🏆 {t('السعر النهائي للعطاء','FINAL TENDER PRICE')}</td>
              <td style="text-align:right; font-size:1.2rem; font-weight:bold; color:var(--success);">{s} {r['grand']:,.2f}</td></tr>
        </table>
        </div>
        """, unsafe_allow_html=True)

        # ─── Export Offer Sheet as PDF ───────────────────────────
        try:
            import io, datetime as dt
            from fpdf import FPDF
            import arabic_reshaper
            from bidi.algorithm import get_display
            import os

            class OfferPDF(FPDF):
                def footer(self):
                    self.set_y(-15)
                    has_unicode = "amiri" in self.fonts
                    if has_unicode:
                        self.set_font("Amiri", '', 8)
                    else:
                        self.set_font("Arial", 'B', 8)
                    self.set_text_color(37, 99, 235)
                    self.cell(0, 10, "EngiCost AI Platform", align='L')
                    self.set_text_color(150, 150, 150)
                    self.cell(0, 10, f"Page {self.page_no()}", align='R')

            def ar(txt):
                try: return get_display(arabic_reshaper.reshape(str(txt)))
                except: return str(txt)

            pdf = OfferPDF()
            font_path = "assets/Amiri-Regular.ttf"
            if os.path.exists(font_path):
                pdf.add_font("Amiri", "", font_path)
            pdf.add_page()
            pdf.set_font("Amiri" if os.path.exists(font_path) else "Arial", size=18)
            pdf.set_text_color(37, 99, 235)
            pdf.cell(0, 15, ar(f"عرض سعر — {r['project']}"), ln=True, align='R')
            pdf.set_font("Amiri" if os.path.exists(font_path) else "Arial", size=10)
            pdf.set_text_color(100, 100, 100)
            pdf.cell(0, 8, ar(f"العميل: {r['client']}"), ln=True, align='R')
            pdf.cell(0, 5, ar(f"التاريخ: {r['date']}"), ln=True, align='R')
            pdf.ln(5)

            rows = [
                (t("التكلفة المباشرة", "Direct Cost"), r['direct']),
                (t("مصاريف عامة", "Overhead"), r['overhead']),
                (t("احتياطي الطوارئ", "Contingency"), r['contingency']),
                (t("هامش الربح", "Profit"), r['profit']),
                (f"VAT ({vat_pct}%)", r['vat']),
                (t("السعر النهائي", "FINAL PRICE"), r['grand']),
            ]
            for label, val in rows:
                pdf.set_text_color(0, 0, 0)
                pdf.cell(120, 10, ar(label), border=1)
                pdf.cell(70, 10, f"{s} {val:,.2f}", border=1, align='R')
                pdf.ln()

            pdf_bytes = bytes(pdf.output())
            st.download_button(
                label=t("📄 تصدير عرض السعر PDF", "📄 Export Offer Sheet PDF"),
                data=pdf_bytes,
                file_name=f"Tender_Offer_{r['project']}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"PDF Error: {e}")
