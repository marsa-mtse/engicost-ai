import streamlit as st
import pandas as pd
from utils import t, render_section_header
from ai_engine.multimodal_processor import get_processor
from limits import check_limit_reached, increment_usage
import io
import ezdxf

def render_blueprint_analysis():
    render_section_header(t("استخبارات المخططات الهندسية", "Blueprint Intelligence"), "📐")
    
    st.markdown(f"""
    <div class="glass-card">
        <p style="color:var(--text-muted);">{t("قم برفع المخططات المعمارية (Image/PDF) أو ملفات الـ CAD (DXF) وسنقوم باستخراج البيانات وحساب الكميات.", "Upload blueprints (Image/PDF) or CAD files (DXF) to extract data and estimate quantities.")}</p>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs([t("🖼️ بصري (AI Vision)", "🖼️ Vision (AI)"), t("🏗️ ملفات CAD (DXF)", "🏗️ CAD Files (DXF)")])

    with tab1:
        if st.session_state.plan == "Free":
            st.warning(t("أنت حالياً على الخطة المجانية. باقتك تسمح بتحليل مخطط واحد فقط.", "You are on the Free plan. Only 1 blueprint analysis allowed."))
        
        b_file = st.file_uploader(t("رفع مخطط (Image/PDF)", "Upload Blueprint"), type=["png", "jpg", "pdf"], key="engicost_b_file")
        
        if b_file and st.button(t("تشغيل التحليل الهندسي", "Run Engineering Analysis"), use_container_width=True):
            if check_limit_reached(st.session_state.username, "blueprints"):
                st.error(t("عذراً، لقد استنفذت الحد المسموح به لتحليل المخططات في باقتك الحالية. الرجاء الترقية للمتابعة.", "Sorry, you have reached the blueprint analysis limit for your plan. Please upgrade to continue."))
            else:
                with st.spinner(t("يتم الآن التحليل باستخدام الذكاء الاصطناعي...", "Analyzing with AI...")):
                    try:
                        processor = get_processor()
                        structured_prompt = f"""
                        Analyze this technical drawing. 
                        Identify all key components, dimensions, and estimated quantities.
                        Return ONLY a JSON array of objects.
                        Each object: {{"item": "Description", "unit": "m2/m3/kg/etc", "quantity": 123.4}}
                        """
                        res = processor.analyze_technical_drawing(b_file.getvalue(), prompt=structured_prompt)
                        
                        from ai_engine.cost_engine import _parse_json_list
                        try:
                            table_data = _parse_json_list(res)
                            st.session_state.engicost_b_table = table_data
                        except:
                            st.session_state.engicost_b_table = None
                            
                        st.session_state.engicost_b_res = res
                        increment_usage(st.session_state.username, "blueprints")
                    except Exception as e:
                        st.error(t(f"حدث خطأ أثناء التحليل: {e}", f"Error during analysis: {e}"))
        
        if st.session_state.get("engicost_b_res"):
            if st.session_state.get("engicost_b_table"):
                st.markdown('### 📊 ' + t("النتائج المنظمة (جدول)", "Structured Results (Table)"))
                b_df = pd.DataFrame(st.session_state.engicost_b_table)
                edited_b_df = st.data_editor(b_df, use_container_width=True)
                
                from ai_engine.export_engine import ExportEngine
                b_excel = ExportEngine.generate_professional_excel(edited_b_df)
                st.download_button(
                    t("📊 تصدير البيانات لـ Excel", "Export Analysis to Excel"),
                    data=b_excel,
                    file_name="Blueprint_Analysis_Results.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
                
                if st.button(t("💰 تحويل إلى تسعير المقايسة", "Convert to BOQ Pricing"), use_container_width=True):
                    st.session_state.engicost_boq_res = st.session_state.engicost_b_table
                    st.success(t("تم إرسال البيانات! انتقل الآن لتبويب 'تسعير المقايسات' واضغط على 'اقتراح الأسعار بالذكاء الاصطناعي' لتسعيرها.", 
                               "Data sent! Now go to 'BOQ Pricing' tab and click 'Suggest Prices with AI' to complete estimation."))
            else:
                st.markdown(f'<div class="glass-card"><h3>{t("النتائج:", "Results:")}</h3>{st.session_state.engicost_b_res}</div>', unsafe_allow_html=True)

    with tab2:
        st.info(t("ارفع ملف DXF لاستخراج طبقات المخطط وحساب كميات العناصر بشكل آلي.", "Upload a DXF file to extract drawing layers and calculate element quantities automatically."))
        dxf_file = st.file_uploader(t("رفع ملف كاد (DXF)", "Upload CAD (DXF)"), type=["dxf"], key="engicost_dxf_file")
        
        if dxf_file:
            try:
                # Load DXF using ezdxf
                dxf_stream = io.StringIO(dxf_file.getvalue().decode("utf-8"))
                doc = ezdxf.read(dxf_stream)
                msp = doc.modelspace()
                
                # Analyze entities
                entities = msp.groupby(dxfattrib="layer")
                takeoff_data = []
                
                for layer, items in entities.items():
                    # Simplified takeoff logic
                    line_count = len([e for e in items if e.dxftype() == "LINE"])
                    circle_count = len([e for e in items if e.dxftype() == "CIRCLE"])
                    text_count = len([e for e in items if e.dxftype() in ("TEXT", "MTEXT")])
                    
                    if line_count > 0 or circle_count > 0:
                        takeoff_data.append({
                            "item": f"Layer: {layer}",
                            "lines": line_count,
                            "circles": circle_count,
                            "annotations": text_count
                        })
                
                if takeoff_data:
                    st.success(t("تم تحليل ملف الكاد بنجاح!", "CAD file analyzed successfully!"))
                    dxf_df = pd.DataFrame(takeoff_data)
                    st.table(dxf_df)
                    
                    # Integration with BOQ Task
                    if st.button(t("💰 تحويل طبقات الكاد لمقايسة", "Convert CAD Layers to BOQ"), use_container_width=True):
                        boq_data = [{"item": d["item"], "unit": "unit", "quantity": d["lines"]} for d in takeoff_data]
                        st.session_state.engicost_boq_res = boq_data
                        st.success(t("تم تحويل الطبقات إلى مسودة مقايسة!", "Layers converted to BOQ draft!"))
                else:
                    st.warning(t("لم يتم العثور على عناصر كافية في هذا الملف.", "No significant entities found in this file."))
                    
            except Exception as e:
                st.error(t(f"خطأ في قراءة ملف الكاد: {e}", f"Error reading CAD file: {e}"))

