import streamlit as st
import pandas as pd
import json
from utils import t, render_section_header
from ai_engine.cost_engine import get_cost_engine
from ai_engine.market_api import MarketEngine
from ai_engine.export_engine import ExportEngine
from limits import check_limit_reached, increment_usage
from database import SessionLocal, User, Project
import datetime

def render_boq_pricing():
    # Only allow Admin, Enterprise, and Pro to access BOQ
    allowed_plans = ["Enterprise", "Pro"]
    if st.session_state.plan not in allowed_plans and st.session_state.get('role') != 'Admin':
         st.warning(t("⚠️ للوصول إلى هذه الميزة، يرجى ترقية حسابك إلى باقة Pro أو Enterprise.", "⚠️ To use this feature, please upgrade to Enterprise or Professional package."))
         return

    render_section_header(t("محرك التكاليف الاحترافي", "Professional Cost Engine & BOQ"), "💵")
    
    # 1. Primary Settings Row: Currency (High Visibility)
    st.markdown(f"#### 🌐 {t('إعدادات المقايسة', 'BOQ Settings')}")
    col_curr, col_empty = st.columns([1, 3])
    with col_curr:
        global_currency = st.session_state.get("currency", "USD")
        
        currency_options = ["USD", "EGP", "SAR", "AED", "QAR", "GBP", "KWD", "OMR", "BHD", "EUR"]
        currency = st.selectbox(
            t("العملة الأساسية", "Primary Currency"), 
            currency_options,
            index=currency_options.index(global_currency) if global_currency in currency_options else 0
        )
        
        # UI Display Symbol
        currency_symbol = f" {currency} "
        # PDF/Excel Safe Code
        pdf_symbol = currency
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 2. Branding & Info Row
    col_info, col_brand = st.columns([2, 1])
    
    with col_brand:
        white_label = st.checkbox(t("تصدير بهوية الشركة (White-label)", "White-label Export"), value=True)
        user_logo = None
        if white_label:
            company_name = st.text_input(t("اسم الشركة", "Company Name"), "My Engineering Firm")
            user_logo = st.file_uploader(t("رفع لوجو شركتك (اختياري)", "Upload Company Logo (Optional)"), type=["png", "jpg", "jpeg"])
        else:
            company_name = "EngiCost AI"
            
        st.markdown(f"""
        <div class='glass-card' style='padding:10px; border-top:2px solid var(--accent-primary);'>
            <p style='margin:0; font-size:0.8rem;'>📞 {t("للدعم الفني:", "Technical Support:")} +20 123 456 789</p>
            <p style='margin:0; font-size:0.8rem;'>✉️ support@engicost.ai</p>
        </div>
        """, unsafe_allow_html=True)

    with col_info:
        st.markdown(f"""
        <div class="glass-card animate-up" style="padding: 1.2rem; margin-bottom: 0;">
            <p style="color:var(--text-secondary); margin:0; font-size: 0.9rem;">
                {t("اختر العملة أولاً، ثم ارفع ملف المقايسة (Excel/PDF/Word) لاستخراج الأسعار بدقة.", 
                   "Select currency first, then upload your BOQ (Excel/PDF/Word) for accurate pricing.")}
            </p>
        </div>
        """, unsafe_allow_html=True)

    # File Uploader
    uploaded_file = st.file_uploader(t("رفع ملف المقايسة", "Upload BOQ File"), type=["pdf", "xlsx", "docx", "txt"])
    
    # Text area as fallback/manual entry
    default_boq = ""
    if st.session_state.get("boq_transfer_data"):
        default_boq = st.session_state.boq_transfer_data

    boq_input = st.text_area(t("أو الصق النص هنا", "Or Paste Text Here"), value=default_boq, height=150, key="engicost_boq_input")
    
    if st.button(t("🚀 تحليل وتسعير احترافي", "Analyze & Professional Pricing"), use_container_width=True):
        content_source = None
        if uploaded_file:
            content_source = uploaded_file.getvalue()
            file_type = uploaded_file.type
        elif boq_input:
            content_source = boq_input
            file_type = "text/plain"

        if content_source:
            if check_limit_reached(st.session_state.username, "boqs"):
                st.error(t("عذراً، لقد استنفذت الحد المسموح به.", "Sorry, you have reached the limit."))
            else:
                with st.spinner(t("جاري معالجة البيانات باستخدام الذكاء الاصطناعي...", "AI analyzing and pricing items...")):
                    try:
                        engine = get_cost_engine()
                        if uploaded_file:
                            res = engine.extract_boq_from_file(content_source, file_type)
                        else:
                            res = engine.extract_boq_items(content_source)
                        
                        # Add suggested rates from MarketEngine/AI
                        market_data = st.session_state.get("market_data", MarketEngine.get_live_prices())
                        market_rates = engine.suggest_market_prices(res)
                        rate = market_data.get('rate', 48.0)
                        
                        for i, item in enumerate(res):
                            if str(i) in market_rates:
                                p_usd = float(market_rates[str(i)])
                                # If currency is USD, just use the USD rate. Otherwise, use local rate.
                                item['rate'] = p_usd if currency == "USD" else p_usd * rate
                            else:
                                item['rate'] = 0.0

                        st.session_state.engicost_boq_res = res
                        if res and isinstance(res, list) and "error" in res[0]:
                            st.error(res[0]["error"])
                        else:
                            st.success(t("تم استخراج وتسعير البنود بنجاح!", "Items extracted and priced successfully!"))
                        increment_usage(st.session_state.username, "boqs")
                    except Exception as e:
                        st.error(t(f"خطأ: {e}", f"Error: {e}"))
        else:
            st.warning(t("الرجاء توفير بيانات المقايسة", "Please provide BOQ data"))
    
    if st.session_state.get("engicost_boq_res"):
        res = st.session_state.engicost_boq_res
        if isinstance(res, list) and len(res) > 0 and isinstance(res[0], dict) and "error" in res[0]:
            st.error(res[0]["error"])
        else:
            # Ensure all items have a 'rate' key
            for item in res:
                if 'rate' not in item:
                    item['rate'] = 0.0
                    
            df = pd.DataFrame(res)
            st.markdown('### 📊 ' + t("تحليل التكاليف المستخرج", "Extracted Cost Analysis"))
            
            # Action Row above the table
            col_act1, col_act2 = st.columns([2, 1])
            with col_act1:
                st.markdown(f"**{t('قم بتعديل الأسعار والمقادير أدناه:', 'Edit rates and quantities below:')}** ({currency_symbol})")
            with col_act2:
                if st.button("🪄 " + t("تسعير ذكي تلقائي", "Smart Auto-Match"), use_container_width=True, type="primary"):
                    with st.spinner(t("جاري مطابقة بنودك مع أسعار البورصة لحظياً...", "Matching your items with live market rates...")):
                        try:
                            engine = get_cost_engine()
                            market_data = st.session_state.get("market_data", MarketEngine.get_live_prices())
                            # Use dual-currency logic
                            rate = market_data.get('rate', 1.0)
                            prices = market_data.get('prices', {})
                            
                            # Find actual column names (handle casing)
                            cols = df.columns.tolist()
                            desc_col = next((c for c in cols if c.lower() == 'description'), None)
                            unit_col = next((c for c in cols if c.lower() == 'unit'), None)
                            
                            if not desc_col:
                                st.error(t("خطأ: لم يتم العثور على عمود الوصف في البيانات.", "Error: Description column not found in data."))
                                return

                            # Smart matching prompt
                            match_prompt = f"""
                            Match these BOQ items to the current market prices.
                            Market Prices (EGP): {json.dumps({k: v['egp'] for k, v in prices.items()})}
                            Items to match: {df[[desc_col, unit_col] if unit_col else [desc_col]].to_json()}
                            
                            Return a JSON dictionary where key is the index and value is the best matched EGP price per unit.
                            If no match, estimate based on item complexity.
                            """
                            match_res, _ = engine._call_gemini_text(match_prompt, expect_json=True)
                            
                            if match_res:
                                for i, item in enumerate(res):
                                    idx_str = str(i)
                                    if idx_str in match_res:
                                        p_egp = float(match_res[idx_str])
                                        item['rate'] = p_egp if currency == "EGP" else p_egp / rate
                                st.session_state.engicost_boq_res = res
                                st.rerun()
                        except Exception as e:
                            st.error(f"Auto-match error: {e}")

            # Allow editing rates in a data editor for pro users
            st.markdown(f"**{t('قم بتعديل الأسعار والمقادير أدناه:', 'Edit rates and quantities below:')}** ({currency_symbol})")
            edited_df = st.data_editor(df, use_container_width=True, num_rows="dynamic")
            
            st.markdown("---")

            # Project Name Input for saving
            proj_name_input = st.text_input(
                t("📌 اسم المشروع (للحفظ)", "📌 Project Name (for saving)"),
                value=t("مشروعي الهندسي", "My Engineering Project"),
                key="boq_proj_name"
            )
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button(t("💾 حفظ المشروع", "Save Project"), use_container_width=True):
                    db = None
                    try:
                        db = SessionLocal()
                        user = db.query(User).filter(User.username == st.session_state.username).first()
                        if user:
                            new_proj = Project(
                                owner_id=user.id,
                                name=proj_name_input,
                                project_type="BOQ",
                                result_data=json.dumps(edited_df.to_dict(orient="records")),
                                created_at=datetime.datetime.utcnow(),
                            )
                            db.add(new_proj)
                            db.commit()
                            st.success(t(f"✅ تم حفظ '{proj_name_input}' بنجاح!", f"✅ '{proj_name_input}' saved successfully!"))
                            # Clear cache for user projects since a new one was added
                            st.cache_data.clear()
                        else:
                            st.error(t("لم يتم العثور على المستخدم", "User not found"))
                    except Exception as e:
                        st.error(f"Save error: {e}")
                    finally:
                        if db:
                            db.close()
            
            with col2:
                 from utils.excel_exporter import export_boq_branded
                 excel_buffer = export_boq_branded(
                     edited_df, 
                     company_name=company_name,
                     project_name=proj_name_input,
                     author_name=st.session_state.username
                 )
                 st.download_button(
                     label=t("📊 تصدير Excel احترافي", "Export Pro Excel"),
                     data=excel_buffer.getvalue(),
                     file_name=f"BOQ_Export_{pdf_symbol}.xlsx",
                     mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                     use_container_width=True
                 )
                 
            with col3:
                 try:
                     logo_path = "assets/logo.png" if white_label else None
                     # If user uploaded a logo, use it instead of default
                     active_logo = user_logo if user_logo else logo_path
                     
                     pdf_data = ExportEngine.generate_professional_pdf(
                         edited_df, 
                         project_name="BOQ Estimation Report",
                         company_name=company_name,
                         logo_path=active_logo,
                         currency_symbol=pdf_symbol
                     )
                     st.download_button(
                         label=t("📄 تصدير PDF للمالك", "Export PDF for Client"),
                         data=pdf_data,
                         file_name="BOQ_Professional_Report.pdf",
                         mime="application/pdf",
                         use_container_width=True
                     )
                 except Exception as e:
                     st.error(t(f"خطأ في التصدير: {e}", f"Export error: {e}"))
                     
            with col4:
                 try:
                     logo_path = "assets/logo.png" if white_label else None
                     active_logo = user_logo if user_logo else logo_path
                     
                     proposal_data = ExportEngine.generate_full_proposal(
                         edited_df, 
                         project_name=f"عرض السعر الفني والمالي - {proj_name_input}",
                         company_name=company_name,
                         logo_path=active_logo,
                         currency_symbol=pdf_symbol
                     )
                     st.download_button(
                         label=t("📑 توليد عرض فني وتجاري (PDF)", "Generate Full Proposal (PDF)"),
                         data=proposal_data,
                         file_name="Full_Proposal.pdf",
                         mime="application/pdf",
                         use_container_width=True,
                         type="primary"
                     )
                 except Exception as e:
                     st.error(f"Proposal error: {e}")
