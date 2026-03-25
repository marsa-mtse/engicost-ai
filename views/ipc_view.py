import streamlit as st
import pandas as pd
import datetime
import os
import json
from utils import t, render_section_header
from ai_engine.cost_engine import get_cost_engine
from database import SessionLocal, User, Project


def render_ipc_invoice():
    render_section_header(t("شهادة الدفع الشهرية (IPC)", "Monthly Interim Payment Certificate — IPC"), "🧾")

    st.markdown(f"""
    <div class="glass-card animate-up">
        <p style="color:var(--text-muted);">
            {t("أنشئ شهادات الدفع الشهرية لمقاوليك بناءً على نسب الإنجاز الفعلية مع التصدير الاحترافي.",
               "Generate monthly interim payment certificates for your contractors based on actual progress with professional export.")}
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ─── Header Info ──────────────────────────────────────────────
    st.markdown(f"### 📋 {t('بيانات المشروع والعقد', 'Project & Contract Details')}")
    r1c1, r1c2, r1c3 = st.columns(3)
    with r1c1:
        proj_name = st.text_input(t("اسم المشروع", "Project Name"), t("مشروع إنشائي", "Construction Project"))
        contractor = st.text_input(t("المقاول", "Contractor"), t("شركة البناء", "Building Co."))
    with r1c2:
        client = st.text_input(t("صاحب العمل", "Employer / Client"), t("شركة التطوير", "Developer Co."))
        ipc_no = st.number_input(t("رقم الشهادة", "IPC Number"), min_value=1, value=1, step=1)
    with r1c3:
        issue_date = st.date_input(t("تاريخ الإصدار", "Issue Date"), value=datetime.date.today())
        from_date = st.date_input(t("الفترة من", "Period From"), value=datetime.date.today().replace(day=1))
        to_date = st.date_input(t("الفترة إلى", "Period To"), value=datetime.date.today())

    global_currency = st.session_state.get("currency", "USD")
    
    default_items = [
        {"البند": t("أعمال الحفر",      "Earthworks"),          f"قيمة العقد ({global_currency})": 100000.0, "% سابق": 0.0,  "% حالي": 25.0},
        {"البند": t("خرسانة مسلحة",     "Reinforced Concrete"),  f"قيمة العقد ({global_currency})": 500000.0, "% سابق": 0.0,  "% حالي": 15.0},
        {"البند": t("مباني وتشطيبات",   "Masonry & Finishes"),   f"قيمة العقد ({global_currency})": 200000.0, "% سابق": 0.0,  "% حالي": 0.0},
        {"البند": t("كهرباء وسباكة",    "MEP"),                  f"قيمة العقد ({global_currency})": 150000.0, "% سابق": 0.0,  "% حالي": 0.0},
    ]

    # Session state for IPC items
    if "ipc_items_data" not in st.session_state:
        st.session_state.ipc_items_data = default_items

    col_src1, col_src2 = st.columns([2, 1])
    with col_src1:
        uploaded_boq = st.file_uploader(t("رفع مقايسة لاستخراج البنود (PDF/Excel)", "Upload BOQ (PDF/Excel)"), type=["pdf", "xlsx"])
    with col_src2:
        # Import from DB
        db = SessionLocal()
        user = db.query(User).filter(User.username == st.session_state.username).first()
        saved_projects = []
        if user:
            saved_projects = db.query(Project).filter(Project.owner_id == user.id, Project.project_type == "BOQ").all()
        db.close()
        
        proj_opt = [p.name for p in saved_projects]
        if proj_opt:
            sel_proj = st.selectbox(t("أو استيراد من مشروع محفوظ", "Or Import from Saved Project"), ["---"] + proj_opt)
            if sel_proj != "---":
                target = next(p for p in saved_projects if p.name == sel_proj)
                try:
                    data = json.loads(target.result_data)
                    new_items = []
                    for d in data:
                        new_items.append({
                            "البند": d.get("description", t("بند جديد", "New Item")),
                            f"قيمة العقد ({global_currency})": float(d.get("total_price", 0.0)) or (float(d.get("rate", 0.0)) * float(d.get("quantity", 1.0))),
                            "% سابق": 0.0,
                            "% حالي": 0.0
                        })
                    st.session_state.ipc_items_data = new_items
                    st.success(t("تم استيراد البنود بنجاح!", "Items imported successfully!"))
                except Exception as e:
                    st.error(f"Import Error: {e}")

    if uploaded_boq:
        if st.button(t("🚀 استخراج البنود من الملف المرفوع", "🚀 Extract Items from File"), use_container_width=True):
            with st.spinner(t("جاري تحليل الملف واستخراج البنود...", "Analyzing file and extracting items...")):
                try:
                    engine = get_cost_engine()
                    res = engine.extract_boq_from_file(uploaded_boq.getvalue(), uploaded_boq.type)
                    new_items = []
                    for item in res:
                        new_items.append({
                            "البند": item.get("description", ""),
                            f"قيمة العقد ({global_currency})": float(item.get("total_price", 0.0)) or (float(item.get("rate", 0.0)) * float(item.get("quantity", 1.0))),
                            "% سابق": 0.0,
                            "% حالي": 0.0
                        })
                    st.session_state.ipc_items_data = new_items
                    st.success(t("تم استخراج البنود بنجاح!", "Items extracted successfully!"))
                except Exception as e:
                    st.error(f"Extraction Error: {e}")

    df_items = pd.DataFrame(st.session_state.ipc_items_data)
    edited = st.data_editor(
        df_items, use_container_width=True, num_rows="dynamic",
        column_config={
            f"قيمة العقد ({global_currency})": st.column_config.NumberColumn(min_value=0, format="%.2f"),
            "% سابق": st.column_config.NumberColumn(min_value=0, max_value=100, format="%.1f"),
            "% حالي": st.column_config.NumberColumn(min_value=0, max_value=100, format="%.1f"),
        }
    )
    # Update state whenever edited
    st.session_state.ipc_items_data = edited.to_dict(orient="records")

    # ─── Financial Settings ───────────────────────────────────────
    st.markdown(f"### ⚙️ {t('الشروط المالية', 'Financial Terms')}")
    fc1, fc2, fc3, fc4 = st.columns(4)
    with fc1:
        retention_pct = st.number_input(t("نسبة الضمان %", "Retention %"), 0.0, 20.0, 5.0, 0.5)
    with fc2:
        advance_pct = st.number_input(t("سلفة مدفوعة %", "Advance Paid %"), 0.0, 30.0, 10.0, 0.5)
    with fc3:
        vat_ipc = st.number_input("VAT %", 0.0, 20.0, 14.0, 0.5)
    with fc4:
        currency_options = ["USD", "EGP", "SAR", "AED", "QAR", "GBP", "KWD", "OMR", "BHD", "EUR"]
        currency = st.selectbox(
            t("العملة", "Currency"), 
            currency_options,
            index=currency_options.index(global_currency) if global_currency in currency_options else 0
        )

    # ─── Calculate ────────────────────────────────────────────────
    cal1, cal2 = st.columns(2)
    with cal1:
        generate_btn = st.button(t("🧮 إصدار الشهادة", "🧮 Generate Certificate"), use_container_width=True)
    with cal2:
        sync_gantt_btn = st.button(t("🔄 ربط النسب بـ Gantt", "🔄 Sync % to Gantt"), use_container_width=True)

    if generate_btn:
        rows_out = []
        total_contract = 0; total_prev = 0; total_curr = 0; total_this_period = 0
        for _, row in edited.iterrows():
            contract_val = float(row[f"قيمة العقد ({global_currency})"])
            pct_prev     = float(row["% سابق"]) / 100
            pct_curr     = float(row["% حالي"]) / 100
            val_prev     = contract_val * pct_prev
            val_curr     = contract_val * pct_curr
            this_period  = val_curr - val_prev
            rows_out.append({
                t("البند", "Item"):             row["البند"],
                t("قيمة العقد", "Contract"):   contract_val,
                t("% سابق", "Prev %"):         f"{pct_prev*100:.1f}%",
                t("% حالي", "Curr %"):         f"{pct_curr*100:.1f}%",
                t("مسحوب سابق", "Prev"):       round(val_prev, 2),
                t("تراكمي", "Cumulative"):     round(val_curr, 2),
                t("هذه الفترة", "This Period"): round(this_period, 2),
            })
            total_contract += contract_val
            total_prev     += val_prev
            total_curr     += val_curr
            total_this_period += this_period

        gross          = total_this_period
        retention      = gross * retention_pct / 100
        advance_deduc  = gross * advance_pct / 100
        net_before_vat = gross - retention - advance_deduc
        vat_amount     = net_before_vat * vat_ipc / 100
        net_due        = net_before_vat + vat_amount

        st.session_state.ipc_result = {
            "rows":          rows_out,
            "gross":         gross,
            "retention":     retention,
            "advance_deduc": advance_deduc,
            "net_before_vat":net_before_vat,
            "vat":           vat_amount,
            "net_due":       net_due,
            "total_contract":total_contract,
            "proj":          proj_name,
            "contractor":    contractor,
            "client":        client,
            "ipc_no":        ipc_no,
            "issue_date":    str(issue_date),
            "from_date":     str(from_date),
            "to_date":       str(to_date),
            "currency":      currency,
        }
        st.rerun()

    if sync_gantt_btn:
        from views.gantt_view import GANTT_KEY, _default_tasks
        if GANTT_KEY not in st.session_state:
            st.session_state[GANTT_KEY] = _default_tasks()
        
        g_tasks = st.session_state[GANTT_KEY]
        synced_count = 0
        ipc_map = {str(row["البند"]).strip().lower(): float(row["% حالي"]) for _, row in edited.iterrows()}
        
        for i, tsk in enumerate(g_tasks):
            t_name = str(tsk.get("task", "")).strip().lower()
            if t_name in ipc_map:
                g_tasks[i]["pct"] = int(ipc_map[t_name])
                synced_count += 1
        
        st.session_state[GANTT_KEY] = g_tasks
        st.success(t(f"✅ تم ربط وتحديث الإنجاز المالي بـ {synced_count} بند في الجدول الزمني (Gantt)!", f"✅ Synced financial progress for {synced_count} tasks in Gantt!"))

    # ─── Results ──────────────────────────────────────────────────
    if st.session_state.get("ipc_result"):
        r = st.session_state.ipc_result
        cy = r["currency"]

        st.dataframe(pd.DataFrame(r["rows"]), use_container_width=True)

        # Financial Summary
        st.markdown(f"""
        <div class="glass-card animate-in" style="border-top:3px solid var(--accent-primary); padding:1.5rem;">
            <h4 style="color:var(--accent-primary); margin-bottom:1rem;">
                🧾 {t('شهادة الدفع رقم', 'IPC No.')} {r['ipc_no']} — {r['proj']}
            </h4>
            <table style="width:100%; font-size:0.9rem; border-collapse:collapse;">
                <tr><td style="padding:6px; color:var(--text-muted);">{t('العميل', 'Client')}</td><td style="text-align:right;"><b>{r['client']}</b></td></tr>
                <tr><td style="padding:6px; color:var(--text-muted);">{t('المقاول', 'Contractor')}</td><td style="text-align:right;"><b>{r['contractor']}</b></td></tr>
                <tr><td style="padding:6px; color:var(--text-muted);">{t('الفترة', 'Period')}</td><td style="text-align:right;">{r['from_date']} → {r['to_date']}</td></tr>
                <tr style="border-top:1px solid rgba(255,255,255,0.1);">
                    <td style="padding:6px;">{t('إجمالي المستحق هذه الفترة', 'Gross This Period')}</td>
                    <td style="text-align:right; color:var(--accent-primary);"><b>{cy} {r['gross']:,.2f}</b></td>
                </tr>
                <tr><td style="padding:6px; color:#fb923c;">(-) {t('ضمان حسن التنفيذ', 'Retention')} ({retention_pct}%)</td>
                    <td style="text-align:right; color:#fb923c;">({cy} {r['retention']:,.2f})</td></tr>
                <tr><td style="padding:6px; color:#f87171;">(-) {t('استرداد السلفة', 'Advance Recovery')} ({advance_pct}%)</td>
                    <td style="text-align:right; color:#f87171;">({cy} {r['advance_deduc']:,.2f})</td></tr>
                <tr><td style="padding:6px;">{t('صافي قبل الضريبة', 'Net before VAT')}</td>
                    <td style="text-align:right;"><b>{cy} {r['net_before_vat']:,.2f}</b></td></tr>
                <tr><td style="padding:6px; color:var(--text-muted);">(+) VAT {vat_ipc}%</td>
                    <td style="text-align:right;">{cy} {r['vat']:,.2f}</td></tr>
                <tr style="border-top:2px solid var(--success); background:rgba(74,222,128,0.08);">
                    <td style="padding:12px; font-size:1.1rem; font-weight:bold; color:var(--success);">
                        🏆 {t('صافي المستحق للمقاول', 'NET DUE TO CONTRACTOR')}
                    </td>
                    <td style="text-align:right; font-size:1.1rem; font-weight:bold; color:var(--success);">
                        {cy} {r['net_due']:,.2f}
                    </td>
                </tr>
            </table>
        </div>
        """, unsafe_allow_html=True)

        # ─── Export IPC PDF ───────────────────────────────────────
        if st.button(t("📄 تصدير شهادة الدفع PDF", "📄 Export IPC PDF"), use_container_width=True):
            try:
                from fpdf import FPDF
                import arabic_reshaper
                from bidi.algorithm import get_display

                def ar(txt):
                    try: return get_display(arabic_reshaper.reshape(str(txt)))
                    except: return str(txt)

                class IpcPDF(FPDF):
                    def footer(self):
                        self.set_y(-15)
                        has_amiri = "amiri" in self.fonts
                        self.set_font("Amiri" if has_amiri else "Arial", '', 8)
                        self.set_text_color(37, 99, 235)
                        self.cell(0, 10, "EngiCost AI — المنصة الهندسية", align='R')
                        self.set_text_color(150, 150, 150)
                        self.cell(0, 10, f"Page {self.page_no()}", align='L')

                pdf = IpcPDF()
                font_path = "assets/Amiri-Regular.ttf"
                if os.path.exists(font_path):
                    pdf.add_font("Amiri", "", font_path)
                pdf.add_page()

                fn = "Amiri" if os.path.exists(font_path) else "Arial"
                pdf.set_font(fn, size=18); pdf.set_text_color(37, 99, 235)
                pdf.cell(0, 12, ar(f"شهادة الدفع الشهرية رقم {r['ipc_no']}"), ln=True, align='R')
                pdf.set_font(fn, size=10); pdf.set_text_color(100, 100, 100)
                pdf.cell(0, 7, ar(f"المشروع: {r['proj']}"), ln=True, align='R')
                pdf.cell(0, 7, ar(f"المقاول: {r['contractor']}"), ln=True, align='R')
                pdf.cell(0, 7, ar(f"صاحب العمل: {r['client']}"), ln=True, align='R')
                pdf.cell(0, 7, ar(f"الفترة: {r['from_date']} — {r['to_date']}"), ln=True, align='R')
                pdf.ln(4)

                # Table header
                pdf.set_fill_color(37, 99, 235); pdf.set_text_color(255, 255, 255)
                pdf.set_font(fn, size=9)
                headers = [ar("البند"), ar("قيمة العقد"), ar("% سابق"), ar("% حالي"), ar("هذه الفترة")]
                widths = [60, 35, 20, 20, 35]
                for h, w in zip(headers, widths):
                    pdf.cell(w, 8, h, border=1, fill=True)
                pdf.ln()

                pdf.set_fill_color(255, 255, 255); pdf.set_text_color(0, 0, 0)
                for row in r["rows"]:
                    vals = [ar(row[k]) for k in list(row.keys())]
                    for val, w in zip(vals, widths):
                        pdf.cell(w, 7, str(val), border=1)
                    pdf.ln()

                # Summary
                pdf.ln(4)
                summary_rows = [
                    (ar("إجمالي المستحق"), f"{cy} {r['gross']:,.2f}"),
                    (ar("ضمان حسن التنفيذ"), f"({cy} {r['retention']:,.2f})"),
                    (ar("استرداد السلفة"),    f"({cy} {r['advance_deduc']:,.2f})"),
                    (ar(f"VAT {vat_ipc}%"),   f"{cy} {r['vat']:,.2f}"),
                    (ar("صافي المستحق للمقاول"), f"{cy} {r['net_due']:,.2f}"),
                ]
                for label, val in summary_rows:
                    pdf.cell(120, 9, label, border=1)
                    pdf.cell(60, 9, val, border=1, align='R')
                    pdf.ln()

                pdf_bytes = bytes(pdf.output())
                st.download_button(
                    t("⬇️ تحميل شهادة الدفع PDF", "⬇️ Download IPC PDF"),
                    data=pdf_bytes,
                    file_name=f"IPC_{r['ipc_no']}_{r['proj']}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
                
                from utils import generate_wa_link
                wa_msg = f"مرحباً بك، تم إصدار شهادة الدفع (IPC) رقم {r['ipc_no']} لمشروع {r['proj']}.\nصافي المستحق: {cy} {r['net_due']:,.2f}\nيرجى المراجعة والاستلام."
                wa_url = generate_wa_link(wa_msg)
                st.link_button("🟢 " + t("إرسال إشعار عبر واتساب", "Send Notice via WhatsApp"), wa_url, use_container_width=True)
                
            except Exception as e:
                st.error(f"PDF Error: {e}")
