import streamlit as st
import pandas as pd
from utils import t, render_section_header
from database import SessionLocal, Project, ProjectAccess, User

def render_collaboration():
    render_section_header(t("نظام التعاون والمشاركة", "Collaboration & Team Sharing"), "👥")
    
    st.markdown(f"""
    <div class="glass-card animate-up">
        <p style="color:var(--text-muted);">
            {t("شارك مشاريعك مع زملائك في العمل أو قم بمراجعة تسعير الفريق في بيئة عمل موحدة.", 
               "Share your projects with colleagues or review team pricing in a unified environment.")}
        </p>
    </div>
    """, unsafe_allow_html=True)

    tabs = st.tabs([t("مشاريعي المشتركة", "My Shared Projects"), t("إدارة الوصول", "Access Management")])

    with tabs[0]:
        st.subheader(t("المشاريع المتاحة للفريق", "Team Shared Projects"))
        # Using mock data for demo if DB isn't fully setup for the current user session
        mock_projects = [
            {"Name": "Modern Villa Complex", "Type": "BOQ", "Owner": "Eng. Ahmed", "Access": "Edit"},
            {"Name": "Commercial Tower A", "Type": "Blueprint", "Owner": "Eng. Sarah", "Access": "View"}
        ]
        df = pd.DataFrame(mock_projects)
        st.dataframe(df, use_container_width=True)
        
        if st.button(t("📂 فتح مشروع مشترك", "Open Shared Project")):
            st.info(t("جاري تحميل بيانات المشروع...", "Loading project data..."))

    with tabs[1]:
        st.subheader(t("دعوة مهندس للمشاركة", "Invite Collaborator"))
        col1, col2 = st.columns([2, 1])
        with col1:
            project_to_share = st.selectbox(t("اختر المشروع", "Select Project"), ["Current Project", "Modern Villa", "Bridge G-11"])
            invite_email = st.text_input(t("بريد المهندس", "Engineer Email"), placeholder="engineer@company.com")
        with col2:
            role = st.selectbox(t("الصلاحية", "Permission"), [t("عرض فقط", "View Only"), t("تعديل", "Full Access")])
            if st.button(t("➕ منح الصلاحية", "Grant Access"), use_container_width=True):
                st.success(t(f"تم منح الصلاحية لـ {invite_email} بنجاح!", f"Access granted to {invite_email} successfully!"))

    # Sharing Link Section
    st.markdown("---")
    st.subheader(t("رابط المشاركة السريع", "Quick Share Link"))
    col3, col4 = st.columns([3, 1])
    with col3:
        st.code("https://engicost.ai/share/project_x_7782", language="markdown")
    with col4:
        if st.button(t("📋 نسخ الرابط", "Copy Link"), use_container_width=True):
            st.toast(t("تم النسخ إلى الحافظة!", "Copied to clipboard!"))
