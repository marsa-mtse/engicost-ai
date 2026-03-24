import streamlit as st
from utils import t, render_section_header
from database import SessionLocal, User, Workspace
import string
import random
import datetime

def generate_join_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

def render_workspace():
    render_section_header(t("مساحة عمل الشركة", "Company Workspace"), "🏢")
    st.markdown(f"<p style='color:var(--text-muted);'>{t('إدارة فريق العمل، الدعوات، والمشاريع المشتركة للشركة.', 'Manage your team, invites, and shared company projects.')}</p>", unsafe_allow_html=True)

    if "workspace_id" not in st.session_state:
        st.session_state.workspace_id = None
    if "workspace_role" not in st.session_state:
        st.session_state.workspace_role = "Member"

    # Quick DB check to sync session state
    db = SessionLocal()
    user = db.query(User).filter(User.username == st.session_state.username).first()
    if user:
        st.session_state.workspace_id = user.workspace_id
        st.session_state.workspace_role = user.workspace_role
    
    workspace = None
    if user and user.workspace_id:
        workspace = db.query(Workspace).filter(Workspace.id == user.workspace_id).first()

    if not workspace:
        # State: User has no workspace
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"### 🏢 {t('إنشاء مساحة عمل جديدة', 'Create New Workspace')}")
            st.info(t("بإنشاء مساحة عمل، ستتمكن من دعوة فريقك ومشاركة المشاريع تلقائياً.", "By creating a workspace, you can invite your team and share projects automatically."))
            with st.form("create_workspace_form"):
                ws_name = st.text_input(t("اسم الشركة / الفريق", "Company / Team Name"))
                if st.form_submit_button(t("إنشاء مساحة العمل", "Create Workspace"), use_container_width=True):
                    if ws_name and user:
                        new_ws = Workspace(
                            name=ws_name,
                            join_code=generate_join_code(),
                            owner_id=user.id
                        )
                        db.add(new_ws)
                        db.commit()
                        db.refresh(new_ws)
                        
                        user.workspace_id = new_ws.id
                        user.workspace_role = "Owner"
                        db.commit()
                        st.session_state.workspace_id = new_ws.id
                        st.session_state.workspace_role = "Owner"
                        st.success(t("تم إنشاء مساحة العمل بنجاح!", "Workspace created successfully!"))
                        db.close()
                        st.rerun()

        with col2:
            st.markdown(f"### 🤝 {t('الانضمام لمساحة عمل', 'Join a Workspace')}")
            st.info(t("أدخل رمز الدعوة (Join Code) الذي أعطاه لك مدير الشركة للانضمام لفريقه.", "Enter the Join Code given by your company manager to join their team."))
            with st.form("join_workspace_form"):
                join_code = st.text_input(t("رمز الدعوة (Join Code)", "Join Code"))
                if st.form_submit_button(t("انضمام", "Join"), use_container_width=True):
                    if join_code and user:
                        target_ws = db.query(Workspace).filter(Workspace.join_code == join_code).first()
                        if target_ws:
                            user.workspace_id = target_ws.id
                            user.workspace_role = "Member"
                            db.commit()
                            st.session_state.workspace_id = target_ws.id
                            st.session_state.workspace_role = "Member"
                            st.success(t("تم الانضمام بنجاح!", "Joined successfully!"))
                            db.close()
                            st.rerun()
                        else:
                            st.error(t("الرمز غير صحيح.", "Invalid join code."))
        db.close()
        return

    # State: User is in a workspace
    st.markdown(f"### {workspace.name}")
    
    col_info, col_action = st.columns([3, 1])
    with col_info:
        st.markdown(f"""
        <div style="padding: 1rem; border-radius: 12px; background: rgba(14, 165, 233, 0.1); border: 1px solid var(--accent-primary);">
            <h4 style="margin:0; color:var(--accent-primary);">رمز الدعوة للموظفين (Join Code): <code style="font-size:1.5rem;">{workspace.join_code}</code></h4>
            <p style="margin:0; font-size: 0.9rem; color: var(--text-muted);">أعطِ هذا الرمز للمهندسين في شركتك ليدخلوا به عند التسجيل.</p>
        </div>
        """, unsafe_allow_html=True)

    with col_action:
        if st.session_state.workspace_role in ["Owner", "Admin"]:
            if st.button("🔄 " + t("تغيير الرمز", "Reset Code"), use_container_width=True):
                workspace.join_code = generate_join_code()
                db.commit()
                st.rerun()
        if st.button("🚪 " + t("مغادرة مساحة العمل", "Leave Workspace"), use_container_width=True):
            user.workspace_id = None
            user.workspace_role = "Engineer"
            db.commit()
            st.rerun()

    st.markdown("---")
    st.markdown(f"### 👥 {t('أعضاء الفريق', 'Team Members')}")
    
    members = db.query(User).filter(User.workspace_id == workspace.id).all()
    
    # Render members nicely
    cols = st.columns(4)
    for idx, member in enumerate(members):
        with cols[idx % 4]:
            role_badge = "👑 Owner" if member.workspace_role == "Owner" else ("🛡️ Admin" if member.workspace_role == "Admin" else "👤 Member")
            st.markdown(f"""
            <div style="padding: 1.5rem; border-radius: 12px; border: 1px solid var(--glass-border); background: var(--bg-secondary); margin-bottom: 1rem; text-align: center;">
                <h4 style="margin:0;">{member.username}</h4>
                <p style="color: var(--text-muted); font-size: 0.8rem; margin: 0.5rem 0;">{member.email}</p>
                <span style="background: rgba(255,255,255,0.1); padding: 0.2rem 0.5rem; border-radius: 20px; font-size: 0.8rem;">{role_badge}</span>
            </div>
            """, unsafe_allow_html=True)
            
            # Simple kick logic for Owners
            if st.session_state.workspace_role == "Owner" and member.id != user.id:
                if st.button("❌ " + t("إزالة", "Remove"), key=f"kick_{member.id}", use_container_width=True):
                    member.workspace_id = None
                    member.workspace_role = "Engineer"
                    db.commit()
                    st.toast(t("تمت الإزالة.", "Removed."))
                    st.rerun()

    db.close()
