import streamlit as st
from utils import t, render_section_header
from ai_engine.cost_engine import get_cost_engine

def render_fidic_generator():
    render_section_header(t("مولد خطابات الفيديك الذكي", "Smart FIDIC E-Letters"), "⚖️")
    st.markdown(f"<p style='color:var(--text-muted);'>{t('محامي عقود افتراضي لصياغة خطابات المطالبات والتنبيهات للمقاول بدقة قانونية.', 'Virtual contract lawyer to draft claims and notifications with legal precision.')}</p>", unsafe_allow_html=True)

    col_info, col_form = st.columns([1, 2])
    
    with col_info:
         st.markdown(f"""
         <div class="glass-card" style="padding: 1.5rem; background: rgba(56, 189, 248, 0.05); border: 1px solid var(--accent-primary);">
            <h4 style="color: var(--accent-primary); margin-top:0;">🤖 {t('كيف تعمل الأداة؟', 'How does it work?')}</h4>
            <p>{t('اكتب المشكلة باللغة التي تريحك (عربي عامي، فصحى، إلخ) وسيقوم الذكاء الاصطناعي بصياغة خطاب رسمي باللغة الإنجليزية للمهندس الاستشاري.', 'Write your issue in your preferred language (Arabic, English, etc.) and the AI will draft a formal English letter to the Engineer/Client.')}</p>
            <ul>
                <li>{t('يستند إلى شروط الفيديك (Red Book).', 'Based on FIDIC conditions (Red Book).')}</li>
                <li>{t('يستحدث ديباجة رسمية.', 'Generates a formal preamble.')}</li>
                <li>{t('يستشهد بأرقام المواد (Clauses) الصحيحة.', 'Cites correct Clause numbers.')}</li>
            </ul>
         </div>
         """, unsafe_allow_html=True)
         
    with col_form:
        st.markdown(f"#### 📝 {t('بيانات المشكلة', 'Issue Details')}")
        project_name = st.text_input(t("اسم المشروع (اختياري)", "Project Name (Optional)"), placeholder="e.g. Cairo Monorail Project")
        issue_desc = st.text_area(
            t("اشرح المشكلة أو الموقف (بالعربية أو الإنجليزية)", "Describe the issue or situation"), 
            placeholder=t("مثال: الاستشاري اتأخر في تسليم المخططات التنفيذية للمبنى رقم 3 لمدة أسبوعين وده مأثر على صب السقف.", "Example: The consultant delayed delivering shop drawings for Building 3 for 2 weeks, affecting the slab casting."),
            height=150
        )
        
        if st.button("🪄 " + t("صياغة الخطاب الآن", "Draft Letter Now"), use_container_width=True, type="primary"):
            if not issue_desc:
                st.warning(t("الرجاء كتابة تفاصيل المشكلة أولاً.", "Please write the issue details first."))
            else:
                with st.spinner(t("يقوم محامي العقود الافتراضي بكتابة الخطاب واستخراج مواد الفيديك...", "Virtual lawyer is drafting and citing FIDIC clauses...")):
                    engine = get_cost_engine()
                    letter_result = engine.generate_fidic_letter(issue_desc, project_info=f"Project: {project_name}")
                    st.session_state.fidic_letter_result = letter_result
    
    if st.session_state.get("fidic_letter_result"):
        st.markdown("---")
        st.markdown(f"### 📄 {t('الخطاب المقترح', 'Drafted Letter')}")
        letter = st.session_state.fidic_letter_result
        
        # Display the letter in a nice text area
        edited_letter = st.text_area(
            t("يمكنك تعديل الخطاب قبل نسخه:", "You can edit the letter before copying:"), 
            value=letter, 
            height=400
        )
        
        # Action buttons
        st.download_button(
            label="📥 " + t("تحميل كملف نصي", "Download as Text"),
            data=edited_letter,
            file_name="FIDIC_Letter_Draft.txt",
            mime="text/plain",
            use_container_width=True
        )
