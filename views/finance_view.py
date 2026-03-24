import streamlit as st
import pandas as pd
from database import SessionLocal, InventoryItem, MaterialTransaction, Expense, Project
from utils import t, render_section_header
import json

def render_financial_analysis():
    render_section_header(t("التحليل المالي والأرباح", "Financial Analysis & Profitability"), "💵")
    
    db = SessionLocal()
    try:
        # Project Selection
        projects = db.query(Project).all()
        if not projects:
            st.info(t("يرجى إنشاء مشروع أولاً لمشاهدة التحليل المالي.", "Please create a project first to see financial analysis."))
            return
            
        project_options = {p.id: p.name for p in projects}
        selected_project_id = st.selectbox(t("اختر المشروع للتحليل", "Select Project to Analyze"), options=list(project_options.keys()), format_func=lambda x: project_options[x], key="fin_proj")
        
        project = db.query(Project).get(selected_project_id)
        
        # --- 1. BOQ Budget (Planned) ---
        planned_total = 0
        if project.project_type == "BOQ" and project.result_data:
            try:
                res_data = json.loads(project.result_data)
                # Try to sum up the Total Cost from BOQ
                if isinstance(res_data, list):
                    for row in res_data:
                        total_str = str(row.get("Total Cost", "0")).replace(",", "")
                        try: planned_total += float(total_str)
                        except: pass
            except: pass
            
        # --- 2. Actual Spending (Inventory Purchases + Expenses) ---
        # Material Spending (All IN transactions)
        mat_spending = db.query(MaterialTransaction).join(InventoryItem).filter(
            InventoryItem.project_id == selected_project_id,
            MaterialTransaction.type == "IN"
        ).all()
        actual_mat_cost = sum(t.quantity * (t.unit_price or 0) for t in mat_spending)
        
        # General Expenses
        expenses = db.query(Expense).filter(Expense.project_id == selected_project_id).all()
        actual_gen_cost = sum(e.amount for e in expenses)
        
        actual_total = actual_mat_cost + actual_gen_cost
        
        # --- 3. Overview Metrics ---
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(t("الميزانية المخططة (BOQ)", "Planned Budget (BOQ)"), f"{planned_total:,.2f}")
        with col2:
            st.metric(t("إجمالي الصرف الفعلي", "Total Actual Spending"), f"{actual_total:,.2f}", delta=f"{((planned_total - actual_total) if planned_total > 0 else 0):,.2f}")
        with col3:
            profit = planned_total - actual_total
            profit_pct = (profit / planned_total * 100) if planned_total > 0 else 0
            st.metric(t("الربح المتوقع / الهامش", "Expected Profit / Margin"), f"{profit:,.2f}", delta=f"{profit_pct:.1f}%")
            
        st.markdown("---")
        
        # --- 4. Charts/Visuals ---
        c1, c2 = st.columns([1.5, 1])
        with c1:
            st.subheader(t("الميزانية مقابل الفعلي", "Budget vs Actual"))
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
            # Only show chart if there's data to avoid errors
            if actual_total > 0:
                # Use a small dataframe for table
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
                    new_exp = Expense(
                        project_id=selected_project_id,
                        category=exp_cat,
                        amount=exp_amt,
                        description=exp_desc
                    )
                    db.add(new_exp)
                    db.commit()
                    st.success(t("تم تسجيل المصروف بنجاح!", "Expense logged successfully!"))
                    st.rerun()

    finally:
        db.close()
