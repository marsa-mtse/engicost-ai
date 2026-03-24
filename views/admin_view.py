import streamlit as st
import pandas as pd
from utils import t, render_section_header
from database import SessionLocal, User, Inquiry

def render_admin_panel():
    # Security check - ensure only Admin can see this
    if st.session_state.get('role') != "Admin":
        st.error(t("عذراً، لا تملك صلاحية الوصول لهذه الصفحة.", "Sorry, you don't have permission to access this page."))
        return
        
    render_section_header(t("لوحة الإدارة الشاملة", "Master Admin Panel"), "🛡️")
    
    # --- Metrics ---
    db = SessionLocal()
    try:
        users = db.query(User).all()
        total_users = len(users)
        pro_ent_users = len([u for u in users if u.plan in ["Pro", "Enterprise"]])
        
        # New Signups Today (Estimated)
        import datetime
        today = datetime.datetime.utcnow().date()
        new_today = len([u for u in users if u.created_at and u.created_at.date() == today])
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f"""
            <div class="glass-card" style="text-align:center; border-left:4px solid var(--accent-primary);">
                <h3>👥 {total_users}</h3>
                <p style="color:var(--text-muted); font-size:0.8rem;">{t("إجمالي المستخدمين", "Total Users")}</p>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="glass-card" style="text-align:center; border-left:4px solid var(--success);">
                <h3>💎 {pro_ent_users}</h3>
                <p style="color:var(--text-muted); font-size:0.8rem;">{t("مشتركون مدفوعين", "Paid Subscribers")}</p>
            </div>
            """, unsafe_allow_html=True)
        with col3:
             st.markdown(f"""
            <div class="glass-card" style="text-align:center; border-left:4px solid var(--accent-secondary);">
                <h3>✨ {new_today}</h3>
                <p style="color:var(--text-muted); font-size:0.8rem;">{t("مسجلين اليوم", "New Signups Today")}</p>
            </div>
            """, unsafe_allow_html=True)
            
        new_inquiries = db.query(Inquiry).filter(Inquiry.status == "New").count()
        with col4:
            st.markdown(f"""
            <div class="glass-card" style="text-align:center; border-left:4px solid #fb923c;">
                <h3>📩 {new_inquiries}</h3>
                <p style="color:var(--text-muted); font-size:0.8rem;">{t("رسائل جديدة", "New Inquiries")}</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # --- Charts ---
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"##### 📊 {t('توزيع الباقات', 'Plan Distribution')}")
            plan_counts = pd.Series([u.plan for u in users]).value_counts()
            st.bar_chart(plan_counts)
        
        st.markdown("---")
        
        # --- User Management Table ---
        st.subheader(t("إدارة المستخدمين والنشاط", "Users & Activity Management"))
        
        # Search / Filter
        search_query = st.text_input("🔍 " + t("بحث باسم المستخدم أو البريد...", "Search username or email..."))
        
        # Build Data for Display
        user_data = []
        for u in users:
            if search_query.lower() in u.username.lower() or (u.email and search_query.lower() in u.email.lower()):
                user_data.append({
                    "ID": u.id,
                    "Username": u.username,
                    "Plan": u.plan,
                    "Last Login": u.last_login.strftime("%Y-%m-%d %H:%M") if u.last_login else "Never",
                    "Sub Start": u.subscription_start.strftime("%Y-%m-%d") if u.subscription_start else "-",
                    "Sub End": u.subscription_end.strftime("%Y-%m-%d") if u.subscription_end else "Unlimited",
                    "Usage (B/Q)": f"{u.blueprints_analyzed} / {u.boqs_generated}"
                })
        
        if user_data:
            df = pd.DataFrame(user_data)
            # Display DataFrame
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            st.markdown("### " + t("إجراءات سريعة", "Quick Actions"))
            action_col1, action_col2 = st.columns(2)
            
            with action_col1:
                st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                target_user = st.selectbox(t("تعديل باقة المستخدم", "Update User Plan"), options=[u["Username"] for u in user_data], key="sel_user")
                new_plan = st.selectbox(t("الباقة", "Plan"), options=["Free", "Pro", "Enterprise"], key="new_plan")
                if st.button(t("✅ تحديث", "Update"), use_container_width=True):
                    user_to_update = db.query(User).filter(User.username == target_user).first()
                    if user_to_update:
                        user_to_update.plan = new_plan
                        db.commit()
                        st.success(t(f"تم تحديث اشتراك {target_user} بنجاح!", f"Successfully updated subscription for {target_user}"))
                        # Update session state if the admin is updating their own plan for testing
                        if target_user == st.session_state.username:
                            st.session_state.plan = new_plan
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
                
            with action_col2:
                st.markdown('<div class="glass-card" style="border: 1px solid #f87171;">', unsafe_allow_html=True)
                st.markdown(f"**{t('منطقة خطرة', 'Danger Zone')}**", unsafe_allow_html=True)
                target_delete = st.selectbox(t("اختر مستخدم للحذف", "Select user to delete"), options=[u["Username"] for u in user_data if u["Username"] != "admin"], key="del_user")
                if st.button("🗑️ " + t("حذف المستخدم نهائياً", "Delete User Permanently"), type="primary"):
                    user_to_del = db.query(User).filter(User.username == target_delete).first()
                    if user_to_del:
                        db.delete(user_to_del)
                        db.commit()
                        st.success(t(f"تم حذف {target_delete}", f"Deleted {target_delete}"))
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info(t("لا يوجد مستخدمين يطابقون البحث.", "No users match your search."))
            
        st.markdown("---")
        # --- Guest Inquiries Section ---
        st.subheader(t("صندوق رسائل الزوار", "Guest Inquiries Inbox"))
        
        inquiries = db.query(Inquiry).order_by(Inquiry.created_at.desc()).all()
        if inquiries:
            inquiry_data = []
            for i in inquiries:
                inquiry_data.append({
                    "ID": i.id,
                    "Email": i.email,
                    "Subject": i.subject,
                    "Message": i.message,
                    "Status": i.status,
                    "Date": i.created_at.strftime("%Y-%m-%d %H:%M")
                })
            
            inq_df = pd.DataFrame(inquiry_data)
            st.dataframe(inq_df, use_container_width=True, hide_index=True)
            
            # Inquiry Actions
            inq_col1, inq_col2 = st.columns([1, 1])
            with inq_col1:
                st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                sel_inq_id = st.selectbox(t("تحديد رسالة", "Select Message (ID)"), options=[i["ID"] for i in inquiry_data], key="sel_inq")
                if st.button(t("✔️ تحديد كمقروء", "Mark as Read"), use_container_width=True):
                    inq_to_update = db.query(Inquiry).filter(Inquiry.id == sel_inq_id).first()
                    if inq_to_update:
                        inq_to_update.status = "Read"
                        db.commit()
                        st.success(t("تم التحديث!", "Updated!"))
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            with inq_col2:
                st.markdown('<div class="glass-card" style="border: 1px solid #f87171;">', unsafe_allow_html=True)
                del_inq_id = st.selectbox(t("حذف رسالة", "Delete Message (ID)"), options=[i["ID"] for i in inquiry_data], key="del_inq")
                if st.button("🗑️ " + t("حذف الرسالة", "Delete Message"), type="primary"):
                    inq_to_del = db.query(Inquiry).filter(Inquiry.id == del_inq_id).first()
                    if inq_to_del:
                        db.delete(inq_to_del)
                        db.commit()
                        st.success(t("تم الحذف!", "Deleted!"))
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info(t("لا توجد رسائل زوار حالياً.", "No guest inquiries at the moment."))
            
        st.markdown("---")
        # --- System Maintenance ---
        st.subheader(t("صيانة النظام والمزامنة", "System Maintenance & Sync"))
        st.markdown('<div class="glass-card" style="border: 1px solid var(--accent-primary);">', unsafe_allow_html=True)
        st.write(t("استخدم هذا الخيار لتحديث قاعدة البيانات يدوياً في حال إضافة ميزات جديدة أو جداول جديدة.", "Use this option to manually sync the database schema if new features or tables were added."))
        if st.button("🔄 " + t("مزامنة قاعدة البيانات", "Sync Database Schema"), use_container_width=True):
            from database import run_migrations
            with st.spinner(t("جاري المزامنة...", "Syncing...")):
                run_migrations()
                st.success(t("تمت المزامنة بنجاح!", "Database synced successfully!"))
                st.balloons()
        st.markdown('</div>', unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Database Error: {e}")
    finally:
        db.close()
