import streamlit as st
import json
import pandas as pd
from database import SessionLocal, Project, User
from utils import t

def render_shared_project(token: str):
    """Render a read-only public project link."""
    st.markdown("<style>#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}</style>", unsafe_allow_html=True)
    
    db = SessionLocal()
    try:
        project = db.query(Project).filter(Project.share_token == token, Project.is_public == True).first()
        
        if not project:
            st.error(t("الرابط غير صالح أو المشروع غير متاح للعامة.", "Invalid link or project is not public."))
            return
            
        owner = db.query(User).get(project.owner_id) if project.owner_id else None
        owner_name = owner.username if owner else "Unknown"

        st.markdown(f"""
        <div style="background: linear-gradient(135deg, rgba(14,165,233,0.1), rgba(15,23,42,0.8)); 
                    padding: 2rem; border-radius: 20px; border-top: 2px solid #0ea5e9; margin-bottom: 2rem;">
            <p style="margin:0; color:#0ea5e9; font-weight:700; letter-spacing:1px; text-transform:uppercase;">{t("مستند هندسي (EngiCost AI)", "Engineering Document (EngiCost AI)")}</p>
            <h1 style="margin:10px 0; font-size:2.5rem; color:#f8fafc;">{project.name}</h1>
            <p style="margin:0; color:#94a3b8; font-size:0.95rem;">الموثق: {owner_name} | التاريخ: {project.created_at.strftime('%Y-%m-%d')}</p>
        </div>
        """, unsafe_allow_html=True)
        
        if project.project_type == "BOQ":
            st.markdown(f"### 💰 {t('جدول الكميات والتسعير', 'Bill of Quantities (BOQ)')}")
            data = json.loads(project.result_data) if project.result_data else []
            if data:
                df = pd.DataFrame(data)
                st.dataframe(df, use_container_width=True)
                
                # Show Total
                try:
                    total_cost = sum([float(str(i).replace(',', '')) if str(i).strip() else 0 for i in df.get("Total Cost", df.get("total", []))])
                    st.info(f"**{t('التكلفة الإجمالية:', 'Total Cost:')}** {total_cost:,.2f}")
                except:
                    pass
            else:
                st.info(t("المشروع فارغ", "Project is empty"))
                
        elif project.project_type == "Blueprint":
            st.markdown(f"### 📐 {t('تحليل المخطط', 'Blueprint Analysis')}")
            st.info(t("تمت مشاركة هذا المخطط للرؤية فقط.", "This blueprint is shared for view only."))
            try:
                data = json.loads(project.result_data)
                # Show basic counts
                st.json(data)
            except:
                st.write(project.result_data)
                
    finally:
        db.close()
