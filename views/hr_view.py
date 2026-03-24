import streamlit as st
import pandas as pd
import datetime
from utils import t, render_section_header
from database import SessionLocal, Staff, Attendance, Project

def render_hr_management():
    render_section_header(t("إدارة الموارد البشرية والموقع", "HR & Site Personnel"), "👷")

    db = SessionLocal()
    try:
        # Project Selection
        projects = db.query(Project).all()
        if not projects:
            st.warning(t("يرجى إنشاء مشروع أولاً لإدارة العمالة.", "Please create a project first to manage personnel."))
            return

        project_names = {p.id: p.name for p in projects}
        selected_project_id = st.selectbox(t("اختر المشروع", "Select Project"), options=list(project_names.keys()), format_func=lambda x: project_names[x])

        tab1, tab2, tab3 = st.tabs([
            t("👥 سجل العاملين", "👥 Staff Directory"),
            t("📅 سجل الحضور", "📅 Attendance Log"),
            t("➕ إضافة عامل جديد", "➕ Add New Personnel")
        ])

        with tab1:
            staff_list = db.query(Staff).filter(Staff.project_id == selected_project_id).all()
            if staff_list:
                data = []
                for s in staff_list:
                    data.append({
                        "ID": s.id,
                        "Name": s.name,
                        "Role": s.role,
                        "Rate": f"{s.salary_rate:,.2f}",
                        "Status": "Active" if s.is_active else "Inactive"
                    })
                st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)
            else:
                st.info(t("لا يوجد عاملين مسجلين لهذا المشروع.", "No staff registered for this project."))

        with tab2:
            st.subheader(t("تسجيل حضور اليوم", "Record Today's Attendance"))
            staff_list = db.query(Staff).filter(Staff.project_id == selected_project_id, Staff.is_active == True).all()
            
            if not staff_list:
                st.info(t("أضف عاملين أولاً لتتمكن من تسجيل الحضور.", "Add staff first to record attendance."))
            else:
                with st.form("attendance_form"):
                    date_val = st.date_input(t("التاريخ", "Date"), datetime.date.today())
                    
                    # Attendance checklist
                    attendance_rows = []
                    for s in staff_list:
                        col_a, col_b, col_c = st.columns([2, 1, 1])
                        with col_a:
                            st.write(f"**{s.name}** ({s.role})")
                        with col_b:
                            status = st.selectbox(f"Status_{s.id}", options=["Present", "Absent", "Leave"], key=f"status_{s.id}", label_visibility="collapsed")
                        with col_c:
                            hours = st.number_input(f"Hours_{s.id}", min_value=0.0, max_value=24.0, value=8.0, key=f"hours_{s.id}", label_visibility="collapsed")
                        attendance_rows.append((s.id, status, hours))
                    
                    if st.form_submit_button(t("حفظ السجل", "Save Attendance")):
                        for s_id, stat, hrs in attendance_rows:
                            # Avoid duplicate entries for same day/staff
                            existing = db.query(Attendance).filter(
                                Attendance.staff_id == s_id,
                                # Simple day check
                                Attendance.date >= datetime.datetime.combine(date_val, datetime.time.min),
                                Attendance.date <= datetime.datetime.combine(date_val, datetime.time.max)
                            ).first()
                            
                            if existing:
                                existing.status = stat
                                existing.hours = hrs
                            else:
                                new_att = Attendance(staff_id=s_id, date=datetime.datetime.combine(date_val, datetime.datetime.now().time()), status=stat, hours=hrs)
                                db.add(new_att)
                        
                        db.commit()
                        st.success(t("تم حفظ سجل الحضور بنجاح!", "Attendance saved successfully!"))

        with tab3:
            st.subheader(t("إضافة عضو جديد للفريق", "Add New Team Member"))
            with st.form("add_staff_form"):
                s_name = st.text_input(t("الاسم المباشر", "Full Name"))
                s_role = st.selectbox(t("الوظيفة / الدور", "Role"), options=["Engineer", "Foreman", "Technician", "Skilled Labor", "General Labor"])
                s_rate = st.number_input(t("اليومية / الراتب (EGP)", "Daily Rate / Salary"), min_value=0.0)
                
                if st.form_submit_button(t("إضافة للفريق", "Add to Team")) and s_name:
                    new_staff = Staff(project_id=selected_project_id, name=s_name, role=s_role, salary_rate=s_rate)
                    db.add(new_staff)
                    db.commit()
                    st.success(t(f"تمت إضافة {s_name} بنجاح!", f"Successfully added {s_name}!"))
                    st.rerun()

    except Exception as e:
        if "ProgrammingError" in str(type(e)) or "relation" in str(e):
             st.error(t("خطأ في بنية قاعدة البيانات. يرجى المزامنة.", "Database schema lag detected."))
             if st.button(t("🔄 مزامنة الجداول الآن", "Sync Tables Now")):
                 from database import run_migrations
                 run_migrations()
                 st.rerun()
        else:
             st.error(f"Error: {e}")
    finally:
        db.close()
