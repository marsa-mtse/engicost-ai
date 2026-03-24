import streamlit as st
import pandas as pd
import datetime
from utils import t, render_section_header
from database import SessionLocal, Equipment, EquipmentLog, Project

def render_assets_management():
    render_section_header(t("إدارة المعدات والأصول", "Equipment & Assets"), "🚜")

    db = SessionLocal()
    try:
        # Project Selection
        projects = db.query(Project).all()
        if not projects:
            st.warning(t("يرجى إنشاء مشروع أولاً لإدارة المعدات.", "Please create a project first to manage equipment."))
            return

        project_names = {p.id: p.name for p in projects}
        selected_project_id = st.selectbox(t("اختر المشروع", "Select Project"), options=list(project_names.keys()), format_func=lambda x: project_names[x])

        tab1, tab2, tab3 = st.tabs([
            t("🚜 قائمة المعدات", "🚜 Equipment List"),
            t("📝 سجل التشغيل", "📝 Operation Log"),
            t("➕ إضافة معدة جديدة", "➕ Add New Equipment")
        ])

        with tab1:
            eq_list = db.query(Equipment).filter(Equipment.project_id == selected_project_id).all()
            if eq_list:
                data = []
                for e in eq_list:
                    data.append({
                        "ID": e.id,
                        "Name": e.name,
                        "Type": e.type,
                        "Ownership": e.ownership,
                        "Rate (if rented)": f"{e.daily_rate:,.2f}" if e.daily_rate else "-"
                    })
                st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)
            else:
                st.info(t("لا توجد معدات مسجلة لهذا المشروع.", "No equipment registered for this project."))

        with tab2:
            st.subheader(t("تسجيل ساعات عمل معدة اليوم", "Log Today's Equipment Hours"))
            eq_list = db.query(Equipment).filter(Equipment.project_id == selected_project_id).all()
            
            if not eq_list:
                st.info(t("أضف معدات أولاً لتتمكن من تسجيل التشغيل.", "Add equipment first to record operation logs."))
            else:
                with st.form("equipment_log_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        sel_eq_id = st.selectbox(t("اختر المعدة", "Select Equipment"), options=[e.id for e in eq_list], format_func=lambda x: next(e.name for e in eq_list if e.id == x))
                        work_date = st.date_input(t("التاريخ", "Date"), datetime.date.today())
                    with col2:
                        hours = st.number_input(t("ساعات العمل", "Working Hours"), min_value=0.0)
                        fuel = st.number_input(t("تكلفة الوقود المضافة (إن وجد)", "Fuel Added Cost"), min_value=0.0)
                    
                    operator = st.text_input(t("اسم المشغل / السائق", "Operator Name"))
                    notes = st.text_input(t("ملاحظات / مكان العمل", "Notes / Working Area"))
                    
                    if st.form_submit_button(t("حفظ سجل التشغيل", "Save Log")):
                        new_log = EquipmentLog(
                            equipment_id=sel_eq_id,
                            date=datetime.datetime.combine(work_date, datetime.datetime.now().time()),
                            hours_worked=hours,
                            fuel_cost=fuel,
                            operator_name=operator,
                            notes=notes
                        )
                        db.add(new_log)
                        db.commit()
                        st.success(t("تم حفظ سجل التشغيل بنجاح!", "Operation log saved successfully!"))
                        st.rerun()

        with tab3:
            st.subheader(t("إضافة معدة جديدة للموقع", "Add New Equipment to Site"))
            with st.form("add_equipment_form"):
                e_name = st.text_input(t("اسم المعدة (مثلاً: لودر كوماتسو)", "Equipment Name (e.g. Komatsu Loader)"))
                e_type = st.selectbox(t("نوع المعدة", "Type"), options=["Excavator", "Loader", "Mixer", "Truck", "Generator", "Crane", "Other"])
                e_owner = st.radio(t("الملكية", "Ownership"), options=["Owned", "Rented"])
                e_rate = st.number_input(t("اليومية / الإيجار اليومي (إن وجد)", "Daily Rental Rate"), min_value=0.0)
                
                if st.form_submit_button(t("إضافة للمعدات", "Add to Equipment")) and e_name:
                    new_eq = Equipment(project_id=selected_project_id, name=e_name, type=e_type, ownership=e_owner, daily_rate=e_rate)
                    db.add(new_eq)
                    db.commit()
                    st.success(t(f"تمت إضافة {e_name} بنجاح!", f"Successfully added {e_name}!"))
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
