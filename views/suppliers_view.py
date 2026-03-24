import streamlit as st
import pandas as pd
import json
import datetime
from utils import t, render_section_header
from database import get_engine, SessionLocal, Base, User
from sqlalchemy import Column, Integer, String, DateTime, Text, Float


# ── Suppliers DB model ─────────────────────────────────────────
class Supplier(Base):
    __tablename__ = "suppliers"
    __table_args__ = {'extend_existing': True}
    id          = Column(Integer, primary_key=True, index=True)
    name        = Column(String(150))
    specialty   = Column(String(100))
    governorate = Column(String(80))
    phone       = Column(String(50), nullable=True)
    email       = Column(String(100), nullable=True)
    rating      = Column(Float, default=3.0)
    notes       = Column(Text, nullable=True)
    created_at  = Column(DateTime, default=datetime.datetime.utcnow)


def _ensure_table():
    try:
        from database import get_engine
        engine = get_engine()
        Base.metadata.create_all(bind=engine, tables=[Supplier.__table__])
    except Exception:
        pass


def _get_suppliers(specialty_filter=None, gov_filter=None):
    _ensure_table()
    try:
        db = SessionLocal()
        q = db.query(Supplier)
        if specialty_filter and specialty_filter != t("الكل", "All"):
            q = q.filter(Supplier.specialty == specialty_filter)
        if gov_filter and gov_filter != t("الكل", "All"):
            q = q.filter(Supplier.governorate == gov_filter)
        results = q.order_by(Supplier.rating.desc()).all()
        db.close()
        return results
    except Exception:
        return []


SPECIALTIES = [
    t("الكل", "All"),
    t("حديد تسليح", "Rebar Steel"),
    t("أسمنت وخرسانة", "Cement & Concrete"),
    t("طوب ومباني", "Masonry"),
    t("كهرباء", "Electrical"),
    t("سباكة وصرف", "Plumbing"),
    t("تشطيبات", "Finishes"),
    t("معدات وآليات", "Equipment"),
    t("حديد إنشائي", "Structural Steel"),
    t("أخرى", "Other"),
]

GOVS = [
    t("الكل", "All"), "القاهرة", "الجيزة", "الإسكندرية", "الشرقية",
    "الدقهلية", "القليوبية", "المنيا", "أسوان", "الأقصر", "السويس",
]


def render_suppliers():
    render_section_header(t("قاعدة بيانات الموردين والمقاولين", "Suppliers & Contractors Database"), "🤝")

    _ensure_table()

    tab_list, tab_add, tab_rfq = st.tabs([
        t("📋 قائمة الموردين", "📋 Suppliers List"),
        t("➕ إضافة مورد", "➕ Add Supplier"),
        t("📤 طلب عروض أسعار RFQ", "📤 Request for Quotation"),
    ])

    # ─── List ──────────────────────────────────────────────────────
    with tab_list:
        fc1, fc2 = st.columns(2)
        with fc1:
            spec_filter = st.selectbox(t("تصفية بالتخصص", "Filter by Specialty"), SPECIALTIES)
        with fc2:
            gov_filter = st.selectbox(t("تصفية بالمحافظة", "Filter by Governorate"), GOVS)

        suppliers = _get_suppliers(spec_filter, gov_filter)
        if suppliers:
            rows = [{
                t("الاسم", "Name"):        s.name,
                t("التخصص", "Specialty"):  s.specialty,
                t("المحافظة", "Gov"):      s.governorate,
                t("الهاتف", "Phone"):      s.phone or "",
                t("البريد", "Email"):      s.email or "",
                t("التقييم", "Rating"):    f"{'⭐' * int(s.rating)} ({s.rating})",
                "id": s.id,
            } for s in suppliers]
            df = pd.DataFrame(rows)
            st.dataframe(df.drop(columns=["id"]), use_container_width=True)

            # Inline rating update
            st.markdown(f"#### {t('تحديث التقييم', 'Update Rating')}")
            sel_id = st.selectbox(t("اختر المورد", "Select Supplier"),
                                  options=[s.id for s in suppliers],
                                  format_func=lambda sid: next((s.name for s in suppliers if s.id == sid), str(sid)))
            new_rating = st.slider(t("التقييم الجديد", "New Rating"), 1.0, 5.0, 3.0, 0.5)
            if st.button(t("💾 حفظ التقييم", "💾 Save Rating"), use_container_width=True):
                try:
                    db = SessionLocal()
                    sup = db.query(Supplier).filter(Supplier.id == sel_id).first()
                    if sup:
                        sup.rating = new_rating
                        db.commit()
                    db.close()
                    st.success(t("✅ تم تحديث التقييم!", "✅ Rating updated!"))
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
        else:
            st.info(t("لا يوجد موردين بعد. أضف أول مورد من تبويب 'إضافة'.", "No suppliers yet. Add your first supplier from the 'Add' tab."))

    # ─── Add ──────────────────────────────────────────────────────
    with tab_add:
        st.markdown(f"#### {t('بيانات المورد الجديد', 'New Supplier Details')}")
        ac1, ac2 = st.columns(2)
        with ac1:
            sup_name  = st.text_input(t("اسم الشركة / المورد", "Company / Supplier Name"))
            sup_spec  = st.selectbox(t("التخصص", "Specialty"), SPECIALTIES[1:])
            sup_gov   = st.selectbox(t("المحافظة", "Governorate"), GOVS[1:])
        with ac2:
            sup_phone  = st.text_input(t("رقم الهاتف", "Phone Number"))
            sup_email  = st.text_input(t("البريد الإلكتروني", "Email"))
            sup_rating = st.slider(t("التقييم الأولي", "Initial Rating"), 1.0, 5.0, 3.5, 0.5)
        sup_notes = st.text_area(t("ملاحظات", "Notes"), height=80)

        if st.button(t("➕ إضافة المورد", "➕ Add Supplier"), use_container_width=True):
            if sup_name:
                try:
                    _ensure_table()
                    db = SessionLocal()
                    new_sup = Supplier(
                        name=sup_name, specialty=sup_spec, governorate=sup_gov,
                        phone=sup_phone or None, email=sup_email or None,
                        rating=sup_rating, notes=sup_notes or None
                    )
                    db.add(new_sup); db.commit(); db.close()
                    st.success(t(f"✅ تم إضافة '{sup_name}' بنجاح!", f"✅ '{sup_name}' added!"))
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.warning(t("الرجاء إدخال اسم المورد.", "Please enter supplier name."))

    # ─── RFQ ──────────────────────────────────────────────────────
    with tab_rfq:
        st.markdown(f"#### {t('إرسال طلب عروض أسعار لعدة موردين', 'Send RFQ to Multiple Suppliers')}")
        rfq_project = st.text_input(t("اسم المشروع", "Project Name"), t("مشروع جديد", "New Project"))
        rfq_items   = st.text_area(
            t("البنود المطلوب تسعيرها", "Items to be quoted"),
            height=120,
            placeholder=t("مثال:\n- حديد تسليح Ø16: 50 طن\n- أسمنت بورتلاند: 200 كيس", "e.g.:\n- Rebar Ø16: 50 ton\n- Portland cement: 200 bags")
        )
        rfq_deadline = st.date_input(t("الموعد النهائي للعروض", "Quotation Deadline"), value=datetime.date.today() + datetime.timedelta(days=7))

        suppliers_all = _get_suppliers()
        if suppliers_all:
            sup_ids = st.multiselect(
                t("اختر الموردين المستهدفين", "Select Target Suppliers"),
                options=[s.id for s in suppliers_all],
                format_func=lambda sid: next((f"{s.name} ({s.specialty})" for s in suppliers_all if s.id == sid), str(sid))
            )

            if st.button(t("📤 إنشاء طلب العرض", "📤 Generate RFQ Document"), use_container_width=True):
                selected_sups = [s for s in suppliers_all if s.id in sup_ids]
                if rfq_items and selected_sups:
                    rfq_text = f"""
**{t('طلب عروض أسعار', 'Request for Quotation')}**
{t('المشروع', 'Project')}: {rfq_project}
{t('الموعد النهائي', 'Deadline')}: {rfq_deadline}

{t('البنود المطلوبة', 'Required Items')}:
{rfq_items}

{t('يرجى إرسال عرض السعر على', 'Please send your quotation to')}: support@engicost.ai
"""
                    st.markdown(f"#### 📲 {t('إرسال الطلب للموردين', 'Send to Suppliers')}")
                    for s in selected_sups:
                        c1, c2 = st.columns([3, 1])
                        with c1:
                            st.write(f"✅ **{s.name}** ({s.phone or t('لا يوجد هاتف', 'No phone')})")
                        with c2:
                            if s.phone:
                                clean_phone = "".join(filter(str.isdigit, s.phone))
                                if not clean_phone.startswith("2"): clean_phone = "2" + clean_phone
                                wa_msg = f"تحية طيبة. نرجو منكم توفير عرض سعر للمشروع: {rfq_project}\nالبنود:\n{rfq_items}"
                                wa_url = f"https://wa.me/{clean_phone}?text={wa_msg.replace(' ', '%20')}"
                                st.link_button(f"🟢 WhatsApp", wa_url, use_container_width=True)
                else:
                    st.warning(t("الرجاء تحديد البنود والموردين.", "Please specify items and suppliers."))
        else:
            st.info(t("أضف موردين أولاً من تبويب 'إضافة'.", "Add suppliers first from the 'Add' tab."))
