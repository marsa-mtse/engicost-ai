import streamlit as st
import pandas as pd
from database import SessionLocal, InventoryItem, MaterialTransaction, Project
from utils import t, render_section_header
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
            items = db.query(InventoryItem).filter(InventoryItem.project_id == selected_project_id).all()
            if items:
                data = []
                for item in items:
                    data.append({
                        "ID": item.id,
                        "Item": item.name,
                        "Quantity": item.quantity,
                        "Unit": item.unit,
                        "Avg Price": f"{item.avg_price:,.2f}",
                        "Total Value": f"{(item.quantity * item.avg_price):,.2f}",
                        "Last Updated": item.last_updated.strftime("%Y-%m-%d")
                    })
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
                    # Check if item exists
                    item = db.query(InventoryItem).filter(
                        InventoryItem.project_id == selected_project_id,
                        InventoryItem.name == item_name
                    ).first()
                    
                    if not item:
                        item = InventoryItem(
                            project_id=selected_project_id,
                            name=item_name,
                            unit=unit,
                            quantity=0,
                            avg_price=0
                        )
                        db.add(item)
                        db.flush()
                    
                    # Update average price and quantity
                    total_cost = (item.quantity * item.avg_price) + (qty * price)
                    item.quantity += qty
                    item.avg_price = total_cost / item.quantity
                    item.last_updated = datetime.datetime.utcnow()
                    
                    # Log transaction
                    trans = MaterialTransaction(
                        item_id=item.id,
                        type="IN",
                        quantity=qty,
                        unit_price=price,
                        note=note
                    )
                    db.add(trans)
                    db.commit()
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
                        item = db.query(InventoryItem).get(selected_item_id)
                        if item.quantity < issue_qty:
                            st.error(t("الكمية المطلوبة أكبر من المتوفر بالمخزن!", "Requested quantity exceeds available stock!"))
                        else:
                            item.quantity -= issue_qty
                            item.last_updated = datetime.datetime.utcnow()
                            
                            trans = MaterialTransaction(
                                item_id=item.id,
                                type="OUT",
                                quantity=issue_qty,
                                unit_price=item.avg_price, # Issued at avg cost
                                note=issue_note
                            )
                            db.add(trans)
                            db.commit()
                            st.success(t("تم تسجيل الصرف بنجاح.", "Material issued successfully."))
                            st.rerun()

    finally:
        db.close()
