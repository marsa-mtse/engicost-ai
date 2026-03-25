import streamlit as st
import pandas as pd
from database import SessionLocal, Project
from utils import t, render_section_header
from services.inventory_service import InventoryService
import datetime

def render_inventory_management():
    render_section_header(t("إدارة المخازن والتوريدات", "Inventory & Supply Management"), "📦")
    
    db = SessionLocal()
    try:
        # Project Selection
        projects = db.query(Project).all()
        if not projects:
            st.info(t("يرجى إنشاء مشروع أولاً للبدء في إدارة المخازن.", "Please create a project first to start managing inventory."))
            return
            
        project_options = {p.id: p.name for p in projects}
        selected_project_id = st.selectbox(t("اختر المشروع", "Select Project"), options=list(project_options.keys()), format_func=lambda x: project_options[x])
        
        # Tabs for different inventory actions
        tab1, tab2, tab3 = st.tabs([
            t("📦 حالة المخزن", "📦 Stock Status"),
            t("➕ إضافة توريد", "➕ Log Purchase"),
            t("➖ صرف خامات", "➖ Issue Material")
        ])
        
        with tab1:
            stock = InventoryService.get_stock_status(db, selected_project_id)
            if stock:
                data = [
                    {
                        "ID": item["id"],
                        "Item": item["name"],
                        "Quantity": item["quantity"],
                        "Unit": item["unit"],
                        "Avg Price": f"{item['avg_price']:,.2f}",
                        "Total Value": f"{item['total_value']:,.2f}",
                        "Last Updated": item["last_updated"].strftime("%Y-%m-%d")
                    }
                    for item in stock
                ]
                df = pd.DataFrame(data)
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info(t("لا توجد خامات مسجلة لهذا المشروع بعد.", "No materials registered for this project yet."))
                
        with tab2:
            st.subheader(t("تسجيل فاتورة توريد جديدة", "Log New Purchase Invoice"))
            with st.form("purchase_form"):
                col1, col2 = st.columns(2)
                with col1:
                    item_name = st.text_input(t("اسم الخامة (مثلاً: حديد 12 مم)", "Material Name (e.g. Iron 12mm)"))
                    unit = st.selectbox(t("الوحدة", "Unit"), options=["Ton", "m3", "m2", "kg", "Unit"])
                with col2:
                    qty = st.number_input(t("الكمية", "Quantity"), min_value=0.1)
                    price = st.number_input(t("سعر الوحدة", "Unit Price"), min_value=0.1)
                
                note = st.text_input(t("ملاحظات / رقم الفاتورة", "Notes / Invoice #"))
                submit = st.form_submit_button(t("تسجيل التوريد", "Log Purchase"))
                
                if submit and item_name:
                    InventoryService.log_purchase(
                        db, selected_project_id, item_name, unit, qty, price, note
                    )
                    st.success(t("تم تسجيل التوريد وتحديث المخزن!", "Purchase logged and stock updated!"))
                    st.rerun()

        with tab3:
            st.subheader(t("صرف خامة لموقع التنفيذ", "Issue Material to Site"))
            items = db.query(InventoryItem).filter(InventoryItem.project_id == selected_project_id).all()
            if not items:
                st.warning(t("لا توجد خامات متوفرة للصرف.", "No materials available to issue."))
            else:
                with st.form("issue_form"):
                    selected_item_id = st.selectbox(t("اختر الخامة", "Select Material"), options=[i.id for i in items], format_func=lambda x: next(i.name for i in items if i.id == x))
                    issue_qty = st.number_input(t("الكمية المصروفة", "Quantity to Issue"), min_value=0.1)
                    issue_note = st.text_input(t("الغرض من الصرف / مكان الاستخدام", "Purpose / Location"))
                    
                    issue_submit = st.form_submit_button(t("تأكيد الصرف", "Confirm Issue"))
                    
                    if issue_submit:
                        item, error = InventoryService.issue_material(db, selected_item_id, issue_qty, issue_note)
                        if error:
                            st.error(t(f"خطأ: {error}", f"Error: {error}"))
                        else:
                            st.success(t("تم تسجيل الصرف بنجاح.", "Material issued successfully."))
                            st.rerun()

    finally:
        db.close()
