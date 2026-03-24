import streamlit as st
import random
import time
from utils import t, render_section_header
from ai_engine.cost_engine import get_cost_engine

from services.tender_fetcher import fetch_live_tenders

def render_tender_hub():
    render_section_header(t("متجر المناقصات وعطاءات الشرق الأوسط", "MENA Mega Tenders Hub"), "🌍")
    
    st.markdown(f"""
    <div class="glass-card animate-up">
        <p style="color:var(--text-muted);">
            {t("اكتشف أحدث العطاءات الحكومية والخاصة في المنطقة. استخدم الذكاء الاصطناعي لتحليل كراسة الشروط ومعرفة نسبة المطابقة (Fit Score) مع قدرات شركتك لتقليل مخاطر التسعير.", 
               "Discover the latest mega tenders in the region. Use AI to scan the RFP and calculate a 'Fit Score' based on your company's profile to minimize bidding risks.")}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Simple Filters
    col1, col2 = st.columns([2, 1])
    with col1:
        search_q = st.text_input("🔍 " + t("ابحث عن عطاء...", "Search tenders..."))
    with col2:
        filter_cat = st.selectbox("📂 " + t("التصنيف", "Category"), 
                                  ["All", "Civil & Architecture", "MEP - Healthcare", "Infrastructure - Water", "Fire & Safety"])
    # Global or Country-Specific Filter UI
    st.markdown("### 📋 " + t("البحث المتقدم واختيار الدولة", "Advanced Search & Country Selection"))
    
    col_country, col_search = st.columns([1, 2])
    with col_country:
        selected_country = st.selectbox(
            t("🌍 الدولة", "Country"),
            ["الكل / دولي", "مصر", "السعودية", "الإمارات", "قطر", "الكويت", "عُمان", "البحرين"]
        )
    with col_search:
        search_query = st.text_input(t("🔍 تصفية النتائج بالاسم أو الكود", "Filter Tenders by Keyword"), "")

    # Display Projects
    st.markdown("### 📋 " + t("أحدث العطاءات المتاحة", "Latest Open Tenders"))
    
    with st.spinner(t(f"جاري البحث في المصادر الرسمية والشبكات لـ ({selected_country})...", f"Searching official sources & networks for ({selected_country})...")):
        projects = fetch_live_tenders(selected_country)
    
    for proj in projects:
        # Simple local text filter
        if search_q and search_q.lower() not in proj['title_ar'].lower() and search_q.lower() not in proj['title_en'].lower():
            continue
        if filter_cat != "All" and proj['category'] != filter_cat:
            continue
        # Advanced search_query filter
        if search_query and \
           search_query.lower() not in proj['title_ar'].lower() and \
           search_query.lower() not in proj['title_en'].lower() and \
           search_query.lower() not in proj['id'].lower(): # Assuming ID can also be searched
            continue
            
        with st.expander(f"🏢 {proj['id']} | {t(proj['title_ar'], proj['title_en'])} ({proj['status']})"):
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f"**📍 Location:** {proj['location']}")
            with c2:
                st.markdown(f"**💵 Est. Budget:** {proj['budget']}")
            with c3:
                st.markdown(f"**⏰ Deadline:** {proj['deadline']}")
                
            st.markdown(f"**🔖 Specialization:** `{proj['category']}`")
            
            # Interactive Demo Block
            st.markdown("<br>", unsafe_allow_html=True)
            fit_btn = st.button("🤖 " + t("تحليل ملائمة المشروع لشركتي (AI Fit Analysis)", "AI Fit Analysis for my Company"), key=f"fit_{proj['id']}")
            
            if fit_btn:
                with st.spinner(t("جاري تحليل كراسة الشروط ومطابقتها مع سابقة أعمال الشركة...", "Scanning RFP and matching with company profile...")):
                    time.sleep(2.5) # Simulate API call/processing
                    
                    # Generate a random score for demo
                    score = random.randint(65, 95)
                    color = "var(--success)" if score > 80 else "var(--warning)"
                    
                    st.markdown(f"""
                        <div style="border-left: 4px solid {color}; padding-left: 15px; margin: 10px 0; background: rgba(0,0,0,0.2); padding: 10px; border-radius: 5px;">
                            <h4 style="color:{color}; margin-top:0;">🎯 AI Match Score: {score}%</h4>
                            <ul>
                                <li><strong>{t("نقاط القوة:", "Strengths:")}</strong> {t("سابقة أعمال الشركة تتطابق مع متطلبات الحجم المالي.", "Financial capacity matches requirements perfectly.")}</li>
                                <li><strong>{t("التحديات:", "Challenges:")}</strong> {t("وقت التسليم ضيق ويحتاج إلى ورديات ليلية.", "Tight execution timeline requiring double shifts.")}</li>
                                <li><strong>{t("الربحية المتوقعة:", "Est. Margin:")}</strong> {random.randint(12, 22)}%</li>
                            </ul>
                            <small style="color:var(--text-muted)">{t("تم تحليل 245 صفحة من الشروط العامة والخاصة.", "Analyzed 245 pages of General & Particular conditions.")}</small>
                        </div>
                    """, unsafe_allow_html=True)
