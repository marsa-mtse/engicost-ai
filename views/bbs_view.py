import streamlit as st
import pandas as pd
from utils import t, render_section_header
from ai_engine.cost_engine import get_cost_engine

def render_bbs_assistant():
    render_section_header(t("مساعد الشوب دروينج وتفريد الحديد (BBS)", "Shop Drawing & BBS Assistant"), "📐")
    
    st.markdown(f"""
    <div class="glass-card animate-up">
        <p style="color:var(--text-muted);">
            {t("ارفع المخططات الإنشائية أو جداول تفريد الحديد (BBS) ليقوم الذكاء الاصطناعي باستخراج وتحليل أقطار، أطوال، وأوزان التسليح المطلوبة ومطابقتها مع الكود الإنشائي.", 
               "Upload structural blueprints or Bar Bending Schedules (BBS). The AI will extract and analyze rebar diameters, lengths, and weights, matching them with structural codes.")}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    col1, col2 = st.columns([1, 1.5])
    
    with col1:
        st.markdown(f"#### 📤 {t('إدخال البيانات', 'Input Data')}")
        upload_mode = st.radio("Upload Type", ["PDF Blueprint / BBS Table", "Manual Input"], horizontal=True, label_visibility="collapsed")
        
        raw_text = ""
        if "PDF" in upload_mode:
            uploaded_file = st.file_uploader(t("ارفع المخطط (PDF)", "Upload Blueprint (PDF)"), type=["pdf", "dxf"])
            if uploaded_file:
                st.info(t("تم استلام الملف. الذكاء الاصطناعي يستخرج الجداول...", "File received. AI is extracting tables..."))
                # Mock extraction for the demo
                raw_text = "Bar Mark: B1, Type: T16, Count: 12, Length: 4.5m, Shape: U-Bar\nBar Mark: B2, Type: T12, Count: 24, Length: 3.2m, Shape: L-Bar"
        else:
            raw_text = st.text_area(t("معلومات التسليح", "Rebar Info"), height=200, placeholder="E.g., 10 bars of 16mm diameter, length 5m, L-shape...")
            
        analyze_btn = st.button("🏗️ " + t("تحليل التسليح (Analyze Rebar)", "Analyze Rebar Parameters"), use_container_width=True, type="primary")

    with col2:
        st.markdown(f"#### 📊 {t('نتائج تحليل تفريد الحديد', 'BBS Analysis Results')}")
        
        if analyze_btn:
            if not raw_text:
                st.warning(t("يرجى إدخال بيانات التفريد أولاً.", "Please input bending schedule data first."))
            else:
                with st.spinner(t("جاري حساب الأوزان وتقييم الهالك (Waste)...", "Calculating weights and estimating waste...")):
                    engine = get_cost_engine()
                    prompt = f"""
                    You are a highly skilled Structural Engineer doing Bar Bending Schedule (BBS) calculations.
                    Based on the following rebar data, extract it into a neat table format showing:
                    - Bar Mark
                    - Diameter (mm)
                    - Number of Bars
                    - Cut Length (m)
                    - Total Length (m)
                    - Total Weight (kg) [Assume density 7850 kg/m3]
                    
                    REBAR DATA:
                    {raw_text}
                    
                    Respond ONLY with the markdown table, and give a 1-sentence English/Arabic recommendation on waste optimization.
                    """
                    
                    response_text, err = engine._call_groq(prompt, expect_json=False)
                    if not response_text:
                         response_text, err = engine._call_gemini_text(prompt, expect_json=False)
                         
                    if response_text:
                        st.markdown(f"""
                        <div class="glass-card" style="border-top: 4px solid var(--primary);">
                            {response_text}
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.error("Engine unavailable.")
        else:
            st.info(t("ستظهر الجداول المستخرجة وحسابات الأوزان هنا.", "Extracted tables and weight calculations will appear here."))
