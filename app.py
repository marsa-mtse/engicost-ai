import streamlit as st
import time
import sys
import os

# Ensure the root directory is in the path to fix any "Import Error" on cloud
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import auth
import utils.__init__ as utils
from utils import t
import database
from ai_engine.market_api import MarketEngine

# Initialize Configuration
st.set_page_config(
    page_title="EngiCost AI | المنصة الهندسية للذكاء الاصطناعي",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply PWA & CSS
st.markdown('<link rel="manifest" href="./static/manifest.json">', unsafe_allow_html=True)
st.markdown('<meta name="google" content="notranslate">', unsafe_allow_html=True)
st.markdown(utils.get_theme_css(), unsafe_allow_html=True)

# Main execution
def main():
    start_time = time.time()
    # Initialize DB (creates sqlite file locally the first time)
    database.init_db()
    
    # Initialize session
    auth.init_session()
    
    from utils import inject_react_translation_fix
    inject_react_translation_fix()
    
    if not st.session_state.authenticated:
        from views import auth_view
        auth_view.render_login_signup()
    else:
        render_app()
    
    # Speed Monitor at the very bottom of sidebar
    duration = time.time() - start_time
    with st.sidebar:
        with st.expander("⚡ " + t("مراقب السرعة", "Speed Monitor"), expanded=False):
            st.write(f"⏱️ {t('وقت التجزئة:', 'Last Render:')} `{duration:.3f}s`")
            if duration > 1.0:
                st.warning(t("تنبيه: الأداء بطيء قليلاً", "Notice: Performance is slightly slow"))
            else:
                st.success(t("الأداء ممتاز", "Performance: Excellent"))

def render_app():
    # --- Navigation Definitions ---
    nav_options = {
        "dashboard":  t("🏠 لوحة القيادة",         "🏠 Dashboard"),
        "market":     t("📈 اتجاهات السوق (Live)",  "📈 Market Trends (Live)"),
        "tender":     t("🌍 متجر العطاءات (Hub)",  "🌍 Tender Hub"),
        "assistant":  t("🤖 المساعد الذكي",         "🤖 AI Assistant"),
        "blueprint":  t("📐 تحليل المخططات",       "📐 Blueprint Analysis"),
        "fidic":      t("⚖️ محلل الفيديك הדقيق",  "⚖️ FIDIC Risk Scanner"),
        "fidic_letters": t("✍️ خطابات الفيديك الذكية", "✍️ Smart FIDIC Letters"),
        "boq":        t("💰 تسعير المقايسات (Pro)",  "💰 BOQ Pricing (Pro)"),
        "compare":    t("⚖️ مقارنة عروض الأسعار",   "⚖️ BOQ Comparison"),
        "profit":     t("💹 حاسبة العطاء والربح",   "💹 Profit & Tender Calc"),
        "structural": t("🏛️ حسابات إنشائية (ECP)",  "🏛️ Structural Calc (ECP)"),
        "bbs":        t("📐 مساعد التفريد (BBS)",   "📐 Bar Bending Schedule"),
        "mep":        t("⚙️ الأنظمة الكهروميكانيكية", "⚙️ MEP Systems"),
        "gantt":      t("📅 جدول وإنجاز المشروع",  "📅 Schedule & Progress"),
        "drafting":   t("📐 محرك الرسم (EngiDraft)", "📐 Drawing Engine (AI)"),
        "survey":     t("🌍 الرفع المساحي (GIS)",   "🌍 Site Survey (GIS)"),
        "qaqc":       t("✔️ جودة وفحص الموقع",   "✔️ QA/QC Checklist"),
        "ipc":        t("🧧 شهادة الدفع الشهري",   "🧧 IPC Invoice"),
        "suppliers":  t("🤝 قاعدة الموردين",       "🤝 Suppliers & RFQ"),
        "collab":     t("🤝 نظام المشاركة",       "🤝 Collaboration"),
        "workspace":  t("🏢 مساحة عمل الشركة",      "🏢 Company Workspace"),
        "billing":    t("💳 الاشتراكات",            "💳 Billing"),
        "settings":   t("⚙️ الإعدادات والدعم",     "⚙️ Settings & Support"),
        "inventory":  t("📦 إدارة المخازن",          "📦 Inventory Mgmt"),
        "finance":    t("💵 المالية والأرباح",      "💵 Finance & Profit"),
        "hr":         t("👷 الموارد البشرية",       "👷 HR & Personnel"),
        "assets":     t("🚜 المعدات والأصول",      "🚜 Assets & Equipment"),
    }
    
    nav_options["brain"] = t("🧠 العقل الهندسي (RAG)", "🧠 AI Engineering Brain")

    categories = {
        t("🌐 العام والأسواق", "🌐 Public & Markets"): ["dashboard", "market", "tender"],
        t("🧠 الذكاء والتحليل", "🧠 AI & Analysis"): ["brain", "assistant", "blueprint", "fidic", "fidic_letters"],
        t("💰 العطاءات والتسعير", "💰 Bidding & Pricing"): ["boq", "compare", "profit"],
        t("🏗️ التنفيذ والهندسة", "🏗️ Engineering"): ["structural", "bbs", "mep", "gantt", "drafting", "survey", "qaqc", "ipc"],
        t("📦 موديولات الـ ERP", "📦 ERP Resources"): ["inventory", "finance", "hr", "assets", "suppliers"],
    }
    
    # Add Admin-only section
    admin_keys = ["workspace", "collab", "billing", "settings", "legal"]
    if st.session_state.get("role") == "Admin":
        nav_options["admin"] = t("🛡️ لوحة الإدارة", "🛡️ Master Admin")
        admin_keys.insert(0, "admin")
        
    nav_options["legal"] = t("⚖️ الخصوصية والشروط", "⚖️ Privacy & Terms")
    categories[t("⚙️ الإدارة والنظام", "⚙️ Admin & System")] = admin_keys

    # --- AI Bridge Jump Logic (MUST BE BEFORE WIDGETS) ---
    if st.session_state.get("ai_bridge_jump"):
        st.session_state.ai_bridge_jump = False
        # Initialize search state if it doesn't exist to prevent errors
        if "global_search" not in st.session_state:
            st.session_state.global_search = ""
        st.session_state.global_search = "" # Clear search
        
        # Find and set manual navigation targets
        for cat, keys in categories.items():
            if "assistant" in keys:
                st.session_state.selected_cat_manual = cat
                # Use current key for safety
                st.session_state.nav_selection_manual = nav_options["assistant"]
                st.toast(t("🚀 جاري تحويلك للمساعد الذكي...", "🚀 Transferring to AI Assistant..."))
                break

    # --- Performance Optimization: Centralized Market Data ---
    if "market_data" not in st.session_state or st.session_state.get("force_market_refresh"):
        st.session_state.market_data = MarketEngine.get_live_prices()
        st.session_state.force_market_refresh = False

    with st.sidebar:
        # Premium Sidebar Header V4
        st.markdown(f"""
        <div style="text-align: center; padding: 1.5rem 0 1rem 0;">
            <div style="background: linear-gradient(145deg, rgba(15,23,42,0.6), rgba(30,41,59,0.8)); 
                        border: 1px solid rgba(255,255,255,0.1); border-top: 1px solid rgba(255,255,255,0.2);
                        border-radius: 20px; padding: 1.2rem; box-shadow: 0 10px 25px -5px rgba(0,0,0,0.5), inset 0 2px 5px rgba(255,255,255,0.05);">
        """, unsafe_allow_html=True)
        
        try:
            st.image("assets/logo.png", use_container_width=True)
        except:
            st.markdown(f'<h2 style="margin:0; font-size: 1.4rem; font-weight:800; background: linear-gradient(90deg, #38bdf8, #818cf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">🏗️ EngiCost AI</h2>', unsafe_allow_html=True)
            
        st.markdown(f"""
                <p style="margin:5px 0 0 0; font-size: 0.65rem; color: #94a3b8; letter-spacing: 2px; text-transform: uppercase;">
                    {t("حلول هندسية ذكية", "Smart Engineering Solutions")}
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # User Info Card V4
        st.markdown(f"""
            <div style='padding: 12px 15px; border-radius:16px; border:1px solid rgba(255,255,255,0.08); margin-bottom:20px; 
                        background: linear-gradient(135deg, rgba(56,189,248,0.1) 0%, rgba(99,102,241,0.05) 100%);
                        box-shadow: inset 0 1px 0 rgba(255,255,255,0.1); display: flex; align-items:center; justify-content: space-between;'>
                <div>
                    <p style='margin:0; font-size:0.85rem; color:#e2e8f0;'>👤 <b style='font-weight:600;'>{st.session_state.username}</b></p>
                    <p style='margin:2px 0 0 0; font-size:0.75rem; color:#38bdf8; font-weight:500; letter-spacing: 0.5px;'>💎 {st.session_state.plan} Plan</p>
                </div>
                <div style='width:35px; height:35px; border-radius:50%; background:rgba(255,255,255,0.1); display:flex; align-items:center; justify-content:center; border:1px solid rgba(255,255,255,0.1);'>
                    <span style='font-size:1.2rem;'>👷</span>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        from utils import is_stlite
        if is_stlite():
            st.markdown(f"""
                <div style='margin-bottom:20px; padding:8px 15px; background:rgba(16, 185, 129, 0.15); border-radius:12px; border:1px solid rgba(16,185,129,0.3); text-align:center; box-shadow: 0 4px 15px rgba(16,185,129,0.2);'>
                    <span style='color:#34d399; font-weight:700; font-size:0.8rem; letter-spacing:0.5px;'>🔒 {t("نسخة الموقع (أوفلاين)", "Site Edition (Offline)")}</span>
                </div>
            """, unsafe_allow_html=True)

        # Handle search clear flag before rendering the widget
        if st.session_state.get("clear_search_flag"):
            st.session_state.global_search = ""
            st.session_state.clear_search_flag = False

        # Global Search Bar
        search_query = st.text_input("🔍 " + t("البحث السريع...", "Global Search..."), key="global_search", placeholder=t("ابحث عن أداة...", "Search for a tool..."))
        
        # API Key Warnings
        from utils import check_api_keys
        missing_keys = check_api_keys()
        if missing_keys:
            with st.expander("⚠️ " + t("تنبيه الإعدادات", "Config Alert"), expanded=True):
                st.error(t("مفاتيح API مفقودة:", "Missing API Keys:"))
                for key in missing_keys:
                    st.write(f"- `{key}`")
                st.info(t("يرجى إضافتها في secrets.toml للعمل بكامل المزايا.", "Please add them to secrets.toml for full features."))
        
        # Filtering logic for Search
        filtered_cats = {}
        for cat, keys in categories.items():
            valid_keys = [k for k in keys if search_query.lower() in nav_options[k].lower()]
            if valid_keys:
                filtered_cats[cat] = valid_keys


        if filtered_cats:
            # Persistent selection with manual override support
            cat_list = list(filtered_cats.keys())
            curr_cat_idx = 0
            if "selected_cat_manual" in st.session_state and st.session_state.selected_cat_manual in cat_list:
                curr_cat_idx = cat_list.index(st.session_state.selected_cat_manual)
                st.session_state.selected_cat_manual = None # Clear after use
                
            selected_cat = st.selectbox(t("القسم الرئيسي", "Section"), cat_list, index=curr_cat_idx)
            sub_options = [nav_options[k] for k in filtered_cats[selected_cat]]
            
            curr_nav_idx = 0
            if "nav_selection_manual" in st.session_state and st.session_state.nav_selection_manual in sub_options:
                curr_nav_idx = sub_options.index(st.session_state.nav_selection_manual)
                st.session_state.nav_selection_manual = None # Clear after use

            nav_selection = st.radio("Navigation", sub_options, index=curr_nav_idx, label_visibility="collapsed")
        else:
            st.warning(t("لا توجد نتائج!", "No results!"))
            nav_selection = nav_options["dashboard"]

        # Performance optimized ticker (Pass pre-fetched data)
        MarketEngine.render_ticker_from_data(st.session_state.market_data)
        
        st.markdown("---")
        from sync_engine import render_sync_indicator
        render_sync_indicator()
        
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            lang_btn = "🇺🇸 EN" if st.session_state.lang == "ar" else "🇪🇬 AR"
            if st.button(lang_btn, use_container_width=True):
                st.session_state.lang = "en" if st.session_state.lang == "ar" else "ar"
                st.rerun()
        with col_c2:
            if st.button("🚪", use_container_width=True):
                logout()

    # Optimized View Routing
    # Reverse lookup for selected key
    current_key = next((k for k, v in nav_options.items() if v == nav_selection), "dashboard")
    
    # Render with fade-in animation container
    # translate="no" is a high-level hint to browsers to skip this div during auto-translation
    st.markdown('<div class="animate-up" translate="no">', unsafe_allow_html=True)
    
    try:
        if current_key == "dashboard":
            from views import dashboard_view
            dashboard_view.render_dashboard()
        elif current_key == "admin":
            from views import admin_view
            admin_view.render_admin_panel()
        elif current_key == "market":
            from views import forecasting_view
            forecasting_view.render_forecasting()
        elif current_key == "tender":
            from views import tender_hub_view
            tender_hub_view.render_tender_hub()
        elif current_key == "assistant":
            from views import ai_assistant_view
            ai_assistant_view.render_ai_assistant()
        elif current_key == "blueprint":
            from views import blueprint_view
            blueprint_view.render_blueprint_analysis()
        elif current_key == "fidic":
            from views import fidic_scanner_view
            fidic_scanner_view.render_fidic_scanner()
        elif current_key == "fidic_letters":
            from views import fidic_letters_view
            fidic_letters_view.render_fidic_generator()
        elif current_key == "boq":
            from views import boq_view
            boq_view.render_boq_pricing()
        elif current_key == "compare":
            from views import compare_view
            compare_view.render_boq_comparison()
        elif current_key == "profit":
            from views import profit_calculator_view
            profit_calculator_view.render_profit_calculator()
        elif current_key == "structural":
            from views import structural_calc_view
            structural_calc_view.render_structural_calc()
        elif current_key == "bbs":
            from views import bbs_view
            bbs_view.render_bbs_assistant()
        elif current_key == "mep":
            from views import mep_view
            mep_view.render_mep_systems()
        elif current_key == "gantt":
            from views import gantt_view
            gantt_view.render_gantt_progress()
        elif current_key == "drafting":
            from views import drawing_engine_view
            drawing_engine_view.render_drawing_engine()
        elif current_key == "survey":
            from views import survey_view
            survey_view.render_survey_management()
        elif current_key == "ipc":
            from views import ipc_view
            ipc_view.render_ipc_invoice()
        elif current_key == "suppliers":
            from views import suppliers_view
            suppliers_view.render_suppliers()
        elif current_key == "qaqc":
            from views import qaqc_view
            qaqc_view.render_qaqc()
        elif current_key == "collab":
            from views import collaboration_view
            collaboration_view.render_collaboration()
        elif current_key == "workspace":
            from views import workspace_view
            workspace_view.render_workspace()
        elif current_key == "billing":
            from views import billing_view
            billing_view.render_billing()
        elif current_key == "inventory":
            from views import inventory_view
            inventory_view.render_inventory_management()
        elif current_key == "finance":
            from views import finance_view
            finance_view.render_financial_analysis()
        elif current_key == "hr":
            from views import hr_view
            hr_view.render_hr_management()
        elif current_key == "assets":
            from views import assets_view
            assets_view.render_assets_management()
        elif current_key == "settings":
            from views import settings_view
            settings_view.render_settings()
        elif current_key == "legal":
            from views import legal_view
            legal_view.render_legal()
        elif current_key == "brain":
            from views import ai_brain_view
            ai_brain_view.render_ai_brain()
    except Exception as e:
        st.error(t("عذراً، حدث خطأ غير متوقع أثناء معالجة هذه الصفحة.", "An unexpected error occurred while processing this page."))
        with st.expander(t("تفاصيل فنية (Technical Details)", "Technical Details")):
            st.error(str(e))
        st.info(t("يرجى المحاولة مرة أخرى أو العودة للوحة القيادة.", "Please try again or return to the dashboard."))

    st.markdown('</div>', unsafe_allow_html=True)

    # --- AI Bridge Button & Interaction (Native & Robust) ---
    st.markdown('<div class="floating-ai-bridge">', unsafe_allow_html=True)
    if st.button("🤖", key="floating_ai_btn_native", help=t("مساعد المهندس الذكي", "AI Engineering Assistant")):
        st.session_state.ai_bridge_jump = True
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
