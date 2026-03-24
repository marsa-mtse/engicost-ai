import streamlit as st
import pandas as pd
import json
import datetime
from utils import t, render_section_header

# Pre-defined QA/QC checklist templates by work type
TEMPLATES = {
    t("الحفر والأساسات", "Excavation & Foundations"): [
        t("التحقق من أبعاد الحفر وفق المخططات", "Verify excavation dimensions per drawings"),
        t("فحص طبيعة التربة مع التقرير الجيوتقني", "Inspect soil condition vs geotechnical report"),
        t("التأكد من تصريف المياه الجوفية", "Confirm groundwater dewatering"),
        t("فحص نظافة قاع الحفر قبل الصب", "Check excavation bottom cleanliness before pour"),
        t("اعتماد الخرسانة العادية النظافة", "Approve lean concrete (blinding)"),
    ],
    t("الخرسانة المسلحة", "Reinforced Concrete"): [
        t("التحقق من أقطار الحديد وتفاصيل اللف", "Verify rebar diameters and bending schedule"),
        t("فحص الغطاء الخرساني (Spacers)", "Check concrete cover (spacers in place)"),
        t("التأكد من نظافة القالب وإحكامه", "Confirm formwork cleanliness and tightness"),
        t("اختبار هبوط الخرسانة (Slump Test)", "Perform slump test on concrete"),
        t("أخذ عينات مكعبات اختبار (Cubes)", "Take concrete cube samples (28-day test)"),
        t("التحقق من درجة التدكيك والاهتزاز", "Verify vibration and compaction quality"),
    ],
    t("المباني والتشطيبات", "Masonry & Finishes"): [
        t("التحقق من رأسية وأفقية الجدران", "Check verticality and horizontality of walls"),
        t("فحص سمك الملاط بين الطوب", "Inspect mortar joint thickness"),
        t("التأكد من تنفيذ العوائق الحرارية", "Verify thermal insulation installation"),
        t("فحص سمك الياسو والبلاط", "Check plaster and tile thickness"),
        t("اختبار الصوت على الأرضيات", "Sound test on flooring"),
    ],
    t("الكهرباء والسباكة", "MEP"): [
        t("فحص مواسير الكهرباء المدفونة قبل الخرسانة", "Inspect embedded conduits before concrete pour"),
        t("اختبار الضغط على خطوط المياه", "Pressure test on water lines"),
        t("التحقق من ميل مواسير الصرف", "Verify drainage pipe gradient"),
        t("فحص لوحات الكهرباء والتأريض", "Inspect electrical panels and grounding"),
    ],
}


def render_qaqc():
    render_section_header(t("سجل فحص الجودة (QA/QC)", "Quality Inspection Log (QA/QC)"), "✔️")

    st.markdown(f"""
    <div class="glass-card animate-up">
        <p style="color:var(--text-muted);">
            {t("أنشئ قوائم الفحص الميدانية، وثّق التفتيش، صوّر الملاحظات بكاميرا الجوال، ووقّع عليها هندسياً ثم احفظها.", 
               "Create mobile-first field checklists, document inspections, capture snags via camera, sign-off, and save.")}
        </p>
    </div>
    """, unsafe_allow_html=True)

    tab_new, tab_history = st.tabs([
        t("📝 فحص جديد", "📝 New Inspection"),
        t("📁 سجل الفحوصات", "📁 Inspection History"),
    ])

    with tab_new:
        c1, c2, c3 = st.columns(3)
        with c1:
            insp_project = st.text_input(t("المشروع", "Project"), t("المشروع الإنشائي", "Construction Project"))
            insp_date    = st.date_input(t("تاريخ الفحص", "Inspection Date"), value=datetime.date.today())
        with c2:
            insp_location = st.text_input(t("الموقع / المحور", "Location / Grid"), "Block A - Level 2")
            insp_by       = st.text_input(t("المفتش", "Inspected By"), st.session_state.get("username", "Engineer"))
        with c3:
            work_type     = st.selectbox(t("نوع العمل", "Work Type"), list(TEMPLATES.keys()))
            overall_status = st.selectbox(t("الحكم العام", "Overall Decision"),
                                          [t("مقبول ✅", "Accepted ✅"),
                                           t("مقبول مشروط ⚠️", "Conditionally Accepted ⚠️"),
                                           t("مرفوض ❌", "Rejected ❌")])

        st.markdown(f"#### 📋 {t('بنود الفحص', 'Inspection Items')} — {work_type}")
        items = TEMPLATES.get(work_type, [])
        results = []
        for i, item in enumerate(items):
            ci1, ci2, ci3 = st.columns([4, 2, 2])
            with ci1:
                st.markdown(f"<p style='padding:8px 0; margin:0;'>{item}</p>", unsafe_allow_html=True)
            with ci2:
                status = st.selectbox("", [t("مطابق ✅", "Pass ✅"), t("لا ينطبق ➖", "N/A ➖"), t("غير مطابق ❌", "Fail ❌")],
                                      key=f"qc_{i}", label_visibility="collapsed")
            with ci3:
                note = st.text_input("", key=f"qc_note_{i}", placeholder=t("ملاحظة...", "Note..."),
                                     label_visibility="collapsed")
            results.append({"item": item, "status": status, "note": note})

        # Custom additional items
        # Custom additional items
        st.markdown(f"**{t('إضافة بند مخصص', 'Add Custom Item')}**")
        custom_item = st.text_input(t("البند المخصص", "Custom item"), key="custom_qc", label_visibility="collapsed")
        if custom_item:
            results.append({"item": custom_item, "status": t("مطابق ✅", "Pass ✅"), "note": ""})

        st.markdown("---")
        st.markdown(f"#### 📸 {t('توثيق الموقع (Site Snags)', 'Site Snag Documentation')}")
        
        show_camera = st.checkbox(t("تفعيل الكاميرا لالتقاط صورة", "Enable Camera to capture photo"), key="enable_cam")
        if show_camera:
            snag_photo = st.camera_input(t("التقط صورة للملاحظة بالموقع", "Capture Site Snag Photo"))
            if snag_photo:
                st.toast(t("تم التقاط وحفظ الصورة بنجاح!", "Photo captured successfully!"), icon="📸")
        else:
            snag_photo = None
            
        insp_notes = st.text_area(t("ملاحظات إضافية عامة", "General Additional Notes"), height=80)

        # Summary
        pass_count = sum(1 for r in results if "✅" in r["status"])
        fail_count = sum(1 for r in results if "❌" in r["status"])
        na_count   = sum(1 for r in results if "➖" in r["status"])

        sc1, sc2, sc3 = st.columns(3)
        with sc1: st.metric(t("مطابق", "Pass"), pass_count, delta_color="normal")
        with sc2: st.metric(t("غير مطابق", "Fail"), fail_count, delta_color="inverse")
        with sc3: st.metric(t("لا ينطبق", "N/A"), na_count)

        if st.button(t("💾 حفظ سجل الفحص", "💾 Save Inspection Record"), use_container_width=True):
            record = {
                "project":  insp_project,
                "date":     str(insp_date),
                "location": insp_location,
                "by":       insp_by,
                "work_type":work_type,
                "overall":  overall_status,
                "items":    results,
                "notes":    insp_notes,
                "pass_count": pass_count,
                "fail_count": fail_count,
            }
            if "qaqc_history" not in st.session_state:
                st.session_state.qaqc_history = []
            st.session_state.qaqc_history.append(record)
            st.success(t(f"✅ تم حفظ سجل الفحص ({insp_date})!", f"✅ Inspection record saved ({insp_date})!"))

        # PDF Export
        if st.button(t("📄 تصدير تقرير الفحص PDF", "📄 Export Inspection Report PDF"), use_container_width=True):
            try:
                import os
                from fpdf import FPDF
                import arabic_reshaper
                from bidi.algorithm import get_display

                def ar(txt):
                    try: return get_display(arabic_reshaper.reshape(str(txt)))
                    except: return str(txt)

                class QcPDF(FPDF):
                    def footer(self):
                        self.set_y(-15)
                        fn = "Amiri" if "amiri" in self.fonts else "Arial"
                        self.set_font(fn, '', 8)
                        self.set_text_color(37, 99, 235)
                        self.cell(0, 10, "EngiCost AI — المنصة الهندسية", align='R')

                pdf = QcPDF()
                fp = "assets/Amiri-Regular.ttf"
                if os.path.exists(fp):
                    pdf.add_font("Amiri", "", fp)
                fn = "Amiri" if os.path.exists(fp) else "Arial"
                pdf.add_page()

                pdf.set_font(fn, size=16); pdf.set_text_color(37, 99, 235)
                pdf.cell(0, 12, ar(f"تقرير فحص الجودة — {insp_project}"), ln=True, align='R')
                pdf.set_font(fn, size=9); pdf.set_text_color(80, 80, 80)
                pdf.cell(0, 7, ar(f"التاريخ: {insp_date} | المحور: {insp_location} | المفتش: {insp_by}"), ln=True, align='R')
                pdf.cell(0, 7, ar(f"نوع العمل: {work_type} | الحكم العام: {overall_status}"), ln=True, align='R')
                pdf.ln(4)

                pdf.set_fill_color(37, 99, 235); pdf.set_text_color(255, 255, 255); pdf.set_font(fn, size=9)
                pdf.cell(120, 8, ar("البند"), border=1, fill=True)
                pdf.cell(30, 8, ar("النتيجة"), border=1, fill=True)
                pdf.cell(40, 8, ar("الملاحظة"), border=1, fill=True)
                pdf.ln()

                pdf.set_text_color(0, 0, 0)
                for r in results:
                    clr = (0, 150, 80) if "✅" in r["status"] else (200, 30, 30) if "❌" in r["status"] else (100, 100, 100)
                    pdf.set_text_color(*clr)
                    pdf.cell(120, 7, ar(r["item"][:60]), border=1)
                    pdf.cell(30,  7, ar(r["status"][:6]), border=1)
                    pdf.cell(40,  7, ar(r["note"][:20] if r["note"] else "—"), border=1)
                    pdf.ln()

                pdf.set_text_color(0, 0, 0)
                pdf.ln(4)
                pdf.cell(0, 7, ar(f"ملاحظات عامة: {insp_notes}"), ln=True, align='R')
                pdf.ln(10)
                pdf.cell(90, 7, ar("توقيع المفتش: _________________"), ln=False)
                pdf.cell(90, 7, ar("توقيع المشرف: _________________"), ln=True)

                pdf_bytes = bytes(pdf.output())
                st.download_button(t("⬇️ تحميل تقرير الفحص", "⬇️ Download Inspection Report"),
                                   data=pdf_bytes, file_name=f"QC_{insp_project}_{insp_date}.pdf",
                                   mime="application/pdf", use_container_width=True)
            except Exception as e:
                st.error(f"PDF Error: {e}")

    with tab_history:
        history = st.session_state.get("qaqc_history", [])
        if history:
            for i, rec in enumerate(reversed(history)):
                status_icon = "✅" if t("مقبول ✅", "Accepted ✅") in rec["overall"] else "❌"
                with st.expander(f"{status_icon} {rec['project']} — {rec['date']} — {rec['work_type']}"):
                    pc, fc = rec.get("pass_count", 0), rec.get("fail_count", 0)
                    st.markdown(f"**{t('المفتش', 'Inspector')}:** {rec['by']} | **{t('المحور', 'Location')}:** {rec['location']}")
                    st.markdown(f"✅ {t('مطابق', 'Pass')}: **{pc}** | ❌ {t('غير مطابق', 'Fail')}: **{fc}**")
                    if rec.get("notes"):
                        st.markdown(f"📝 {rec['notes']}")
        else:
            st.info(t("لا توجد سجلات فحص بعد. أجرِ أول فحص من التبويب الأول.", "No inspection records yet. Start your first inspection."))
