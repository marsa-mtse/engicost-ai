import streamlit as st
import PyPDF2
from utils import t, render_section_header
from ai_engine.cost_engine import get_cost_engine

def extract_text_from_pdf(file):
    reader = PyPDF2.PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

def render_fidic_scanner():
    render_section_header(t("محلل العقود وحقول الفيديك (FIDIC Scanner)", "FIDIC Contract Risk Scanner"), "⚖️")
    
    st.markdown(f"""
    <div class="glass-card animate-up">
        <p style="color:var(--text-muted);">
            {t("ارفع مسودة الشروط التعاقدية (PDF) أو الصق النصوص هنا. سيقوم الذكاء الاصطناعي بمسح العقد بحثاً عن الثغرات القانونية، والشروط المجحفة، وغرامات التأخير غير المنطقية بناءً على معايير عقود الفيديك (FIDIC).", 
               "Upload the contract draft (PDF) or paste the text here. The AI will scan the contract for legal loopholes, unfair clauses, and unreasonable delay penalties based on FIDIC standards.")}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    engine = get_cost_engine()
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown(f"#### 📄 {t('إدخال العقد', 'Contract Input')}")
        input_method = st.radio(t("طريقة الإدخال", "Input Method"), ["Upload PDF", "Paste Text"], horizontal=True)
        
        contract_text = ""
        if input_method == "Upload PDF":
            uploaded_file = st.file_uploader(t("اختر ملف العقد (PDF)", "Choose Contract File (PDF)"), type="pdf")
            if uploaded_file is not None:
                with st.spinner(t("جاري استخراج النص...", "Extracting text...")):
                    try:
                        contract_text = extract_text_from_pdf(uploaded_file)
                        st.success(t("تم استخراج النص بنجاح!", "Text extracted successfully!"))
                    except Exception as e:
                        st.error(f"Error parsing PDF: {e}")
        else:
            contract_text = st.text_area(t("النص التعاقدي", "Contract Text"), height=300, placeholder=t("الصق الشروط الخاصة أو العامة هنا...", "Paste particular or general conditions here..."))
            
        analyze_btn = st.button("🚨 " + t("مسح المخاطر التعاقدية (Risk Scan)", "Run Contract Risk Scan"), use_container_width=True, type="primary")

    with col2:
        st.markdown(f"#### 🔍 {t('تقرير المخاطر (AI Report)', 'Risk Report (AI)')}")
        
        if analyze_btn:
            if not contract_text or len(contract_text.strip()) < 50:
                st.warning(t("يرجى إدخال نص عقد كافٍ (أكثر من 50 حرف).", "Please input sufficient contract text (more than 50 characters)."))
            else:
                with st.spinner(t("يقوم الذكاء الاصطناعي الآن بمقارنة البنود مع كود الفيديك العالمي...", "AI is currently cross-referencing clauses with international FIDIC standards...")):
                    
                    # Ensure prompt is not too long for the model
                    truncated_text = contract_text[:12000] # roughly 4000 tokens limit safe zone
                    
                    prompt = f"""
                    You are a highly experienced Construction Contract Manager and FIDIC Expert.
                    Analyze the following contract excerpts. 
                    Identify any major risks for the CONTRACTOR, such as:
                    1. Severe Delay Penalties (Liquidated Damages).
                    2. Unfair Payment Terms (Retention money, delayed payments).
                    3. Vague Scope of Work or variations clauses.
                    4. Termination clauses.
                    
                    CONTRACT TEXT:
                    \"\"\"{truncated_text}\"\"\"
                    
                    Provide a structured markdown report in Arabic. 
                    Use 🔴 for High Risk, 🟡 for Medium Risk, and 🟢 for Fair clauses.
                    Format it professionally with bullet points.
                    """
                    
                    response_text, err = engine._call_groq(prompt, expect_json=False)
                    if not response_text:
                         response_text, err = engine._call_gemini_text(prompt, expect_json=False)
                         
                    if response_text:
                        st.markdown(f"""
                        <div class="glass-card" style="border-right: 4px solid var(--danger);">
                            {response_text}
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # --- New LOI/Draft Generation ---
                        st.markdown("---")
                        st.markdown(f"#### 📄 {t('توليد وثائق رد (Response Documents)', 'Generate Response Documents')}")
                        col_loi1, col_loi2 = st.columns(2)
                        
                        with col_loi1:
                            if st.button("📑 " + t("توليد خطاب نوايا (LOI)", "Generate Letter of Intent"), use_container_width=True):
                                loi_prompt = f"Write a professional Letter of Intent (LOI) in Arabic for a contractor to submit based on this risk analysis: {response_text}. Keep it formal and standard."
                                loi_resp, _ = engine._call_gemini_text(loi_prompt, expect_json=False)
                                if loi_resp:
                                    st.text_area("LOI Draft", value=loi_resp, height=300)
                                    st.download_button(t("تحميل الخطاب", "Download Letter"), loi_resp, file_name="LOI_Draft.txt")
                        
                        with col_loi2:
                            if st.button("📧 " + t("خطاب توضيح فني", "Technical Clarification Letter"), use_container_width=True):
                                clar_prompt = f"Write a formal clarification request letter in Arabic addressing the risks identified here: {response_text}. Focus on negotiating unfair clauses."
                                clar_resp, _ = engine._call_gemini_text(clar_prompt, expect_json=False)
                                if clar_resp:
                                    st.text_area("Clarification Draft", value=clar_resp, height=300)
                                    st.download_button(t("تحميل طلب التوضيح", "Download Clarification"), clar_resp, file_name="Clarification_Request.txt")
                    else:
                        st.error(t("عذراً، المحرك غير متاح حالياً.", "Sorry, the engine is currently unavailable."))
        else:
            st.info(t("التقرير سيظهر هنا بعد التحليل.", "The report will appear here after analysis."))
