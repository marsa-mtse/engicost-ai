import sys

with open(r'd:\engicost-ai\views\drawing_engine_view.py', 'r', encoding='utf-8') as f:
    text = f.read()

target = """                        transfer_text = f\"\"\"[توليد تلقائي من أداة الرسم الذكية]
يرجى عمل مقايسة تقديرية كميات وأسعار شاملة لإنشاء مشروع بناء بالمواصفات التالية:
- طراز المبنى: {style_3d}
- المساحة الإجمالية للمباني: {calc_area} متر مربع
- عدد الأدوار: {floor_count} طوابق
- عدد غرف النوم: {bed_count}
- عدد الحمامات: {bath_count}
- إضافات: {"مسبح، " if pool_opt else ""}{"لاندسكيب وحديقة، " if landscaping else ""}
\"\"\"
                        st.session_state.boq_transfer_data = transfer_text
                        st.session_state.survey_area = calc_area
                        st.toast(t("تم ترحيل البيانات بنجاح! اذهب لتبويب 'Cost Engine' للبدء في التسعير.", "Data transferred successfully! Go to 'Cost Engine' tab to begin pricing."), icon="✅")"""

replacement = """                        try:
                            from ai_engine.drawing_brain import extract_quantities_from_plan
                            if "floors" not in r_data: r_data["floors"] = floor_count
                            transfer_text = extract_quantities_from_plan(r_data, specialty)
                        except Exception as e:
                            transfer_text = f"Extraction Error: {e}"
                        
                        st.session_state.boq_transfer_data = transfer_text
                        st.session_state.survey_area = calc_area
                        st.toast(t("تم ترحيل الكميات الدقيقة بنجاح! افتح تبويب B.O.Q للبدء في التسعير.", "Exact quantities transferred successfully! Open BOQ tab to begin."), icon="✅")"""

if target in text:
    new_text = text.replace(target, replacement)
    with open(r'd:\engicost-ai\views\drawing_engine_view.py', 'w', encoding='utf-8') as f:
        f.write(new_text)
    print('SUCCESS')
else:
    print('TARGET NOT FOUND')
