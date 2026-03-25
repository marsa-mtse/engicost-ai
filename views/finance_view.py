import streamlit as st
import pandas as pd
from database import SessionLocal
from utils import t, render_section_header
from services.finance_service import FinanceService
import json

def render_financial_analysis():
    render_section_header(t("التحليل المالي والأرباح", "Financial Analysis & Profitability"), "💵")
    
    db = SessionLocal()
    try:
        from database import Project
        projects = db.query(Project).all()
        if not projects:
            st.info(t("يرجى إنشاء مشروع أولاً لمشاهدة التحليل المالي.", "Please create a project first to see financial analysis."))
            return
            
        project_options = {p.id: p.name for p in projects}
        selected_project_id = st.selectbox(t("اختر المشروع للتحليل", "Select Project to Analyze"), options=list(project_options.keys()), format_func=lambda x: project_options[x], key="fin_proj")
        
        # --- Financial Analysis via Service ---
        fin = FinanceService.get_project_financials(db, selected_project_id)
        if "error" in fin:
            st.error(fin["error"])
            return

        planned_total = fin["planned_budget"]
        actual_total = fin["actual_total"]
        actual_mat_cost = fin["actual_material_cost"]
        actual_gen_cost = fin["actual_general_cost"]
        profit = fin["profit"]
        profit_pct = fin["profit_pct"]
        
        # --- 3. Overview Metrics ---
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(t("الميزانية المخططة (BOQ)", "Planned Budget (BOQ)"), f"{planned_total:,.2f}")
        with col2:
            st.metric(t("إجمالي الصرف الفعلي", "Total Actual Spending"), f"{actual_total:,.2f}", delta=f"{((planned_total - actual_total) if planned_total > 0 else 0):,.2f}")
        with col3:
            st.metric(t("الربح المتوقع / الهامش", "Expected Profit / Margin"), f"{profit:,.2f}", delta=f"{profit_pct:.1f}%")
            
        st.markdown("---")
        
        # --- 4. Charts/Visuals ---
        c1, c2 = st.columns([1.5, 1])
        with c1:
            st.subheader(t("الميزانية مقابل الفعلي", "Budget vs Actual"))
            import pandas as pd
            comparison_df = pd.DataFrame({
                "Category": [t("مخطط", "Planned"), t("فعلي", "Actual")],
                "Amount": [planned_total, actual_total]
            })
            st.bar_chart(comparison_df.set_index("Category"))
            
        with c2:
            st.subheader(t("توزيع المصاريف", "Expense Distribution"))
            dist_data = {
                "Material": actual_mat_cost,
                "General": actual_gen_cost
            }
            if actual_total > 0:
                st.table(pd.Series(dist_data).reset_index().rename(columns={"index": t("الفئة", "Category"), 0: t("المبلغ", "Amount")}))
            else:
                st.info(t("لا توجد بيانات صرف كافية.", "Not enough spending data yet."))

        # --- 5. Log General Expense Form ---
        st.markdown("---")
        st.subheader(t("تسجيل بند مصروفات عامة", "Log General Expense"))
        with st.expander(t("إضافة مصروف (محروقات، عمالة، إيجارات)", "Add Expense (Fuel, Labor, Rent)")):
            with st.form("gen_expense_form"):
                exp_cat = st.selectbox(t("نوع المصروف", "Category"), options=[
                    t("عمالة", "Labor"), t("محروقات", "Fuel"), t("إيجار معدات", "Equipment Rent"), 
                    t("نثريات", "Office/Site Sundries"), t("تصاريح", "Permits")
                ])
                exp_amt = st.number_input(t("المبلغ", "Amount"), min_value=1.0)
                exp_desc = st.text_area(t("الوصف", "Description"))
                
                exp_submit = st.form_submit_button(t("تسجيل المصروف", "Log Expense"))
                if exp_submit:
                    FinanceService.log_expense(db, selected_project_id, exp_cat, exp_amt, exp_desc)
                    st.success(t("تم تسجيل المصروف بنجاح!", "Expense logged successfully!"))
                    st.rerun()

    finally:
        db.close()
