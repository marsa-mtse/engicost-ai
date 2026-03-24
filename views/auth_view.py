import streamlit as st
import os
from auth import authenticate_user, create_user
from utils import t, render_section_header
from database import SessionLocal, Inquiry
from ai_engine.cost_engine import get_cost_engine

def render_login_signup():
    # Language Toggle at the very top
    cols_top = st.columns([8, 2])
    with cols_top[1]:
        lang_label = "🇺🇸 English" if st.session_state.lang == "ar" else "🇪🇬 عربي"
        if st.button(lang_label, key="lang_toggle_auth", use_container_width=True):
            st.session_state.lang = "en" if st.session_state.lang == "ar" else "ar"
            st.rerun()

    # Logo & Global Brand
    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        try:
            # We use the new premium logo generated
            st.image("assets/logo.png", use_container_width=True)
        except Exception as e:
            st.markdown(f'<h1 style="text-align:center;">🏗️ EngiCost AI</h1>', unsafe_allow_html=True)

    # Hero Section - V3.1 Modern SaaS Design
    st.markdown(f"""
        <style>
        @keyframes gradientFade {{
            0% {{ background-position: 0% 50%; }}
            50% {{ background-position: 100% 50%; }}
            100% {{ background-position: 0% 50%; }}
        }}
        .hero-container {{
            text-align:center; 
            padding: 4.5rem 2rem; 
            background: linear-gradient(-45deg, rgba(14,165,233,0.08), rgba(99,102,241,0.12), rgba(16,185,129,0.08));
            background-size: 400% 400%;
            animation: gradientFade 15s ease infinite;
            border-radius: 35px; 
            margin-bottom: 3rem;
            position: relative;
            overflow: hidden;
            border: 1px solid rgba(255,255,255,0.06);
            box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5);
        }}
        .hero-title {{
            font-size: clamp(2.8rem, 6vw, 4.8rem); 
            font-weight: 900; 
            line-height: 1.1; 
            margin-bottom: 1.2rem;
            background: linear-gradient(135deg, #ffffff 0%, #38bdf8 50%, #818cf8 100%);
            -webkit-background-clip: text; 
            -webkit-text-fill-color: transparent;
            text-shadow: 0px 4px 25px rgba(56, 189, 248, 0.25);
        }}
        .hero-subtitle {{
            font-size:clamp(1.2rem,2.5vw,1.8rem); 
            font-weight:600; 
            color:#f8fafc; 
            margin-bottom:1.5rem;
            letter-spacing: 0.5px;
        }}
        .hero-text {{
            color:#94a3b8; 
            font-size:clamp(1.05rem, 1.5vw, 1.25rem); 
            max-width:850px; 
            margin:0 auto; 
            line-height:1.8; 
            font-weight:400;
        }}
        .tag-pill {{
            background: rgba(255,255,255,0.03);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255,255,255,0.08);
            padding: 0.6rem 1.4rem;
            border-radius: 999px;
            font-size: 0.95rem;
            font-weight: 500;
            transition: all 0.3s ease;
            cursor: default;
        }}
        .tag-pill:hover {{
            background: rgba(255,255,255,0.1);
            transform: translateY(-3px);
            box-shadow: 0 10px 20px -10px rgba(0,0,0,0.3);
        }}
        </style>
        
        <div class="hero-container">
            <div style="font-size:5rem; margin-bottom:1.5rem; text-shadow: 0 10px 30px rgba(0,0,0,0.3);">🏗️</div>
            <h1 class="hero-title">EngiCost AI</h1>
            <h2 class="hero-subtitle">{t("مستقبل الهندسة الإنشائية والذكاء الاصطناعي", "The Future of Construction & AI")}</h2>
            <p class="hero-text">
                {t("منصتك السحابية الشاملة لتحويل المخططات إلى تسعير دقيق، استخراج كميات، ورسم معماري بالذكاء الاصطناعي في ثوانٍ معدودة.", 
                   "Your all-in-one cloud platform to transform blueprints into precise pricing, BOQ, and AI architectural drawings in seconds.")}
            </p>
            <div style="display:flex; justify-content:center; gap:1.2rem; margin-top:2.5rem; flex-wrap:wrap;">
                <span class="tag-pill" style="color:#7dd3fc; border-color: rgba(14,165,233,0.3);">🌍 {t("متجر العطاءات الحي", "Live Tender Hub")}</span>
                <span class="tag-pill" style="color:#a5b4fc; border-color: rgba(99,102,241,0.3);">📐 {t("مخططات SVG ذكية", "Smart SVG Drawings")}</span>
                <span class="tag-pill" style="color:#6ee7b7; border-color: rgba(16,185,129,0.3);">🛰️ {t("تحليل مساحي GIS", "GIS Survey Analysis")}</span>
                <span class="tag-pill" style="color:#fcd34d; border-color: rgba(245,158,11,0.3);">💰 {t("تسعير BOQ آلي", "Auto BOQ Pricing")}</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Auth System (Tabbed Interface for Modern UX)
    st.markdown("<br>", unsafe_allow_html=True)
    
    auth_col1, auth_col2, auth_col3 = st.columns([1, 2, 1])
    with auth_col2:
        st.markdown(f"""
        <div style="text-align:center; margin-bottom:2rem;">
            <h2 style="margin:0; font-size: 2.2rem; font-weight:800; background: linear-gradient(90deg, #38bdf8, #818cf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{t("بوابتك للهندسة الذكية", "Your Gateway to Smart Engineering")}</h2>
            <p style="color:#94a3b8; font-size:1.05rem; margin-top:0.8rem;">{t("قم بتسجيل الدخول للبدء أو أنشئ حساباً جديداً مجاناً", "Login to begin or create a new free account")}</p>
        </div>
        """, unsafe_allow_html=True)
        
        tab_login, tab_signup = st.tabs(["🔑 " + t("تسجيل الدخول", "Login"), "✨ " + t("حساب جديد", "Sign Up")])
        
        # --- LOGIN TAB ---
        with tab_login:
            st.markdown(f'<div class="glass-card animate-up" style="padding: 2.5rem; border-top: 4px solid #38bdf8; border-radius: 0 0 20px 20px; box-shadow: 0 20px 40px -15px rgba(0,0,0,0.5);">', unsafe_allow_html=True)
            login_user = st.text_input(t("👤 اسم المستخدم", "👤 Username"), key="login_user")
            login_pass = st.text_input(t("🔒 كلمة المرور", "🔒 Password"), type="password", key="login_pass")
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button(t("تسجيل الدخول", "Login"), use_container_width=True, type="primary", key="btn_login"):
                if login_user and login_pass:
                    user = authenticate_user(login_user, login_pass)
                    if user:
                        st.session_state.authenticated = True
                        st.session_state.username = user.username
                        st.session_state.plan = user.plan
                        st.session_state.role = user.role
                        st.session_state.workspace_id = getattr(user, 'workspace_id', None)
                        st.session_state.workspace_role = getattr(user, 'workspace_role', 'Engineer')
                        st.success(f"Welcome {user.username}!")
                        st.rerun()
                    else: st.error(t("بيانات غير صحيحة", "Invalid credentials"))
                else: st.warning(t("أدخل البيانات للمتابعة", "Enter credentials to proceed"))
            st.markdown('</div>', unsafe_allow_html=True)

        # --- SIGNUP TAB ---
        with tab_signup:
            st.markdown(f'<div class="glass-card animate-up" style="padding: 2.5rem; border-top: 4px solid #818cf8; border-radius: 0 0 20px 20px; box-shadow: 0 20px 40px -15px rgba(0,0,0,0.5);">', unsafe_allow_html=True)
            new_user = st.text_input(t("👤 اسم المستخدم", "👤 Username"), key="reg_user")
            new_email = st.text_input(t("📧 البريد الإلكتروني", "📧 Email"), key="reg_email")
            new_pass = st.text_input(t("🔒 كلمة المرور", "🔒 Password"), type="password", key="reg_pass")
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button(t("🌟 ابدأ تجربتك المجانية الآن", "🌟 Start Your Free Trial Now"), use_container_width=True, type="primary", key="btn_signup"):
                if new_user and new_email and new_pass:
                    user = create_user(new_user, new_email, new_pass)
                    if user: st.success(t("تم التسجيل بنجاح! يرجى الانتقال لتبويب الدخول.", "Registered successfully! Switch to Login tab."))
                    else: st.error(t("المستخدم موجود بالفعل", "User already exists"))
                else: st.warning(t("يرجى ملء كافة الحقول", "Please fill all fields"))
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br><hr><br>", unsafe_allow_html=True)
    if True: # Was tab_about
        # ── Global Stats (SaaS Header) ──────────────────────────────
        st.markdown(
            f'<h3 style="color:#e2e8f0;text-align:center;margin-bottom:2rem; font-size:2rem;">'
            f'🚀 {t("منصة متكاملة بقدرات فائقة", "Integrated Platform with Superpowers")}</h3>',
            unsafe_allow_html=True
        )
        
        stat_data = [
            ("⚡ V2.0", t("الإصدار الأقوى", "The Most Powerful Release")),
            ("🧠 10+", t("محركات ذكاء اصطناعي", "AI Precision Engines")),
            ("🌍 40+", t("عطاء يومي", "Daily Regional Tenders")),
            ("⏱️ 90%", t("توفير في الوقت", "Time Savings")),
        ]
        s1, s2, s3, s4 = st.columns(4)
        for scol, (val, lbl) in zip([s1, s2, s3, s4], stat_data):
            with scol:
                st.markdown(
                    f'<div style="background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.08);'
                    f'border-radius:24px; padding:1.5rem; text-align:center; margin-bottom:1.5rem; transition: transform 0.3s;" onmouseover="this.style.transform=\'translateY(-5px)\';" onmouseout="this.style.transform=\'none\';">'
                    f'<div style="font-size:2rem; font-weight:900; background: linear-gradient(135deg, #38bdf8, #818cf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{val}</div>'
                    f'<div style="font-size:0.85rem; color:#94a3b8; margin-top:8px; font-weight:500;">{lbl}</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )

        # ── Feature Bento Grid ─────────────────
        st.markdown("<br>", unsafe_allow_html=True)
        features = [
            ("📐", t("مهندس الرسم V3.0", "AI Drawing V3.0"),
             t("وصفك النصي يتحول لمخطط معماري SVG دقيق مع تفاصيل الجدران والأبواب والتشطيبات.",
               "Your text turns into a precise SVG architectural plan with true wall thickness and door swings.")),
            ("💰", t("تسعير ذكي فوري", "Instant Smart Pricing"),
             t("رفع جداول (Excel/PDF) وربطها أوتوماتيكياً بأسعار السوق الحقيقية لحظة بلحظة.",
               "Upload BOQs to auto-match with live market rates instantly.")),
            ("🌍", t("رادار العطاءات", "Tender Radar"),
             t("أكثر من 40 عطاء جديد يومياً من مصر والخليج مقسمة ذكياً حسب الدولة والمجال.",
               "40+ daily tenders from MENA, intelligently categorized by country.")),
            ("🛰️", t("تحليل التربة GIS", "GIS Terrain Analysis"),
             t("رؤية حاسوبية لتحليل الصور الفضائية واستخراج نسب المباني والنباتات والتربة.",
               "Computer vision for satellite images to analyze structures vs vegetation.")),
            ("📅", t("جدول زمني آلي", "Auto Gantt Chart"),
             t("توليد جداول زمنية للإنشاءات تلقائياً بمجرد رفع بنود المشروع.",
               "Automatically generate construction schedules from project items.")),
            ("🧠", t("المستشار الرقمي", "AI Executive Advisor"),
             t("تحليل شامل واقتراحات لتقليل التكاليف بضغطة زر.",
               "Comprehensive analysis & cost-saving suggestions with one click.")),
        ]
        
        card_hover = (
            'background:rgba(30,41,59,0.4);border:1px solid rgba(255,255,255,0.05);'
            'border-radius:24px;padding:1.8rem;text-align:right;margin-bottom:1rem;'
            'transition:all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);'
            'box-shadow: 0 10px 30px -10px rgba(0,0,0,0.2);'
        )
        # Using a 2x3 grid
        for idx in range(0, 6, 2):
            c1, c2 = st.columns(2)
            with c1:
                i, tlc, dsc = features[idx]
                st.markdown(f"""
                <div style="{card_hover}" onmouseover="this.style.background='rgba(30,41,59,0.8)'; this.style.transform='scale(1.02)';" onmouseout="this.style.background='rgba(30,41,59,0.4)'; this.style.transform='none';">
                    <div style="font-size:3rem; margin-bottom:1rem; text-shadow: 0 0 20px rgba(14,165,233,0.5);">{i}</div>
                    <h4 style="color:#e2e8f0; font-size:1.3rem; margin-bottom:0.5rem; font-weight:700;">{tlc}</h4>
                    <p style="color:#94a3b8; font-size:0.95rem; line-height:1.6; margin:0;">{dsc}</p>
                </div>
                """, unsafe_allow_html=True)
            with c2:
                i, tlc, dsc = features[idx+1]
                st.markdown(f"""
                <div style="{card_hover}" onmouseover="this.style.background='rgba(30,41,59,0.8)'; this.style.transform='scale(1.02)';" onmouseout="this.style.background='rgba(30,41,59,0.4)'; this.style.transform='none';">
                    <div style="font-size:3rem; margin-bottom:1rem; text-shadow: 0 0 20px rgba(99,102,241,0.5);">{i}</div>
                    <h4 style="color:#e2e8f0; font-size:1.3rem; margin-bottom:0.5rem; font-weight:700;">{tlc}</h4>
                    <p style="color:#94a3b8; font-size:0.95rem; line-height:1.6; margin:0;">{dsc}</p>
                </div>
                """, unsafe_allow_html=True)

        # ── Pricing Plans (Neon SaaS UI) ──────────────────────────
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown(
            f'<h3 style="color:#e2e8f0;text-align:center;margin-bottom:3rem; font-size:2.2rem;">'
            f'💎 {t("استثمر في مهندسك الرقمي الثوري", "Invest in your Revolutionary AI Engineer")}</h3>',
            unsafe_allow_html=True
        )
        
        plans = [
            ("🆓", t("الباقة المجانية", "Free Explorer"), "0", t("شهرياً", "mo"),
             [t("1 تجربة محرك الرسم المتقدم", "1 Advanced SVG Drawing"), t("1 تحليل وتسعير مقايسة", "1 Auto BOQ Pricing"),
              t("تصفح المتجر اليومي", "Browse Daily Tenders"), t("رؤية الأسعار اللحظية", "Live Market Prices View")],
             "rgba(100,116,139,0.1)", "#94a3b8", False),
             
            ("⚡", t("الاحترافية برو", "Pro Engineer"), "299", t("جنيه/شهر", "EGP/mo"),
             [t("توليد مخططات لا نهائي", "Unlimited Drawings"), t("تسعير ذكي لامحدود", "Unlimited Auto BOQ"),
              t("واجهة الجدول الزمني", "Gantt Chart Engine"), t("تصدير دقيق للـ Excel & PDF", "Excel & PDF Exports"),
              t("استعراض متجر العطاءات الشامل", "Full Access to Live Tender Hub")],
             "linear-gradient(145deg, rgba(14,165,233,0.15), rgba(99,102,241,0.15))", "#38bdf8", True),
             
            ("🏛️", t("مؤسسات وشركات", "Enterprise"), "799", t("جنيه/شهر", "EGP/mo"),
             [t("مميزات الباقة الاحترافية +", "All Pro Features +"), t("مساحات عمل للفرق الهندسية", "Team Workspaces"),
              t("تحليل صور جوية عبر الـ GIS", "GIS Satellite Imagery CV"), t("تلخيص تفصيلي لملفات الـ DB", "Detailed DB Docs Summaries"),
              t("دعم تقني مدار الساعة", "24/7 Priority Support")],
             "rgba(99,102,241,0.1)", "#818cf8", False),
        ]
        
        p1, p2, p3 = st.columns([1, 1.1, 1])
        for pcol, (icon, pname, price, period, feats, bg, text_color, popular) in zip([p1, p2, p3], plans):
            with pcol:
                glow = "0 0 40px rgba(56,189,248,0.3)" if popular else "none"
                border = "2px solid rgba(56,189,248,0.8)" if popular else "1px solid rgba(255,255,255,0.08)"
                transform = "scale(1.05)" if popular else "scale(1)"
                zindex = "10" if popular else "1"
                
                popular_badge = (
                    f'<div style="background:linear-gradient(90deg, #38bdf8, #818cf8); color:#fff; font-size:0.8rem; font-weight:800;'
                    f'padding:4px 15px; border-radius:999px; display:inline-block; margin-bottom:15px; box-shadow: 0 4px 15px rgba(56,189,248,0.4);">'
                    f'⭐ {t("الخيار المفضل للمهندسين", "Most Popular Choice")}</div><br>'
                ) if popular else "<br><br>"
                
                feat_html = "".join(
                    f'<div style="margin:12px 0; font-size:0.95rem; color:#f8fafc; display:flex; gap:10px; align-items:center;">'
                    f'<span style="color:{text_color}; font-size:1.2rem; font-weight:900;">✓</span> <span>{f}</span></div>'
                    for f in feats
                )
                
                plan_html = (
                    f'<div style="background:{bg}; border:{border}; border-radius:30px; padding:2.5rem; min-height:500px;'
                    f'box-shadow: {glow}; transform: {transform}; position: relative; z-index: {zindex}; '
                    f'backdrop-filter: blur(10px); transition: all 0.3s ease;">'
                    f'<div style="text-align:center;">'
                    f'{popular_badge}'
                    f'<div style="font-size:3.5rem; margin-bottom:10px; text-shadow: 0 10px 20px rgba(0,0,0,0.5);">{icon}</div>'
                    f'<h4 style="color:#f8fafc; font-size:1.8rem; margin:0 0 10px 0; font-weight:800;">{pname}</h4>'
                    f'<div style="font-size:4rem; font-weight:900; color:{text_color}; line-height:1; text-shadow: 0 0 20px {text_color}80;">{price}'
                    f'<span style="font-size:1.2rem; color:#94a3b8; font-weight:500; margin-inline-start:5px;">{period}</span></div>'
                    f'</div>'
                    f'<div style="margin-top:2.5rem; border-top:1px solid rgba(255,255,255,0.1); padding-top:2rem;">'
                    f'{feat_html}'
                    f'</div>'
                    f'</div>'
                )
                st.markdown(plan_html, unsafe_allow_html=True)

        # ── What's New (Changelog) ────────────────────────────────
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown(
            f'<h3 style="color:#e2e8f0;text-align:center;margin:1rem 0 2rem; font-size:2rem;">🆕 '
            f'{t("آخر التحديثات الجوهرية", "Latest Major Updates")}</h3>',
            unsafe_allow_html=True
        )
        cl1, cl2, cl3 = st.columns(3)
        changelog = [
            (cl1, "#38bdf8", "V3.0",
             t("محرك الرسم وتصميم الدخول", "Drawing Engine & UI Overhaul"),
             t("SaaS Login Redesign · SVG 9-Layers · Auto Scaling", "SaaS Login Redesign · SVG 9-Layers · Auto Scaling")),
            (cl2, "#a78bfa", "V2.5",
             t("الأتمتة المعمارية الشاملة", "Architectural Automation"),
             t("GIS Terrain CV · Smart Auto-Pricing · Dynamic Dashboard", "GIS Terrain CV · Smart Auto-Pricing · Dynamic Dashboard")),
            (cl3, "#34d399", "V2.0",
             t("البيانات الحية", "Live Data Engine"),
             t("Live Tender Hub · Cost Market Rates · PDF Exports", "Live Tender Hub · Cost Market Rates · PDF Exports")),
        ]
        for col, clr, ver, title_cl, details in changelog:
            with col:
                st.markdown(
                    f'<div style="background:rgba(30,41,59,0.5); border:1px solid {clr}40; border-right:4px solid {clr};'
                    f'border-radius:16px; padding:1.5rem; transition: all 0.3s ease;" onmouseover="this.style.transform=\'translateY(-3px)\'; this.style.boxShadow=\'0 10px 20px -10px {clr}80\';" onmouseout="this.style.transform=\'none\'; this.style.boxShadow=\'none\';">'
                    f'<div style="color:{clr}; font-weight:800; font-size:1.1rem; margin-bottom:6px;">{ver} <span style="color:#f8fafc; font-weight:600;">— {title_cl}</span></div>'
                    f'<div style="color:#94a3b8; font-size:0.85rem; line-height:1.5;">{details}</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )



    st.markdown("<br><br><br>", unsafe_allow_html=True)
    if True: # Was tab_offline
        st.markdown(f"<h3 style='text-align:center;'>📴 {t('نسخة المواقع والعمل بدون إنترنت', 'Site Edition & Offline Mode')}</h3>", unsafe_allow_html=True)
        st.info(t("هذه النسخة مخصصة للمهندسين في المواقع البعيدة التي لا يتوفر فيها إنترنت.", 
                  "This edition is for engineers in remote sites without internet access."))
        
        col_off1, col_off2 = st.columns([2, 1])
        
        with col_off1:
            st.markdown(f"""
            #### {t('ما المميز في هذه النسخة؟', 'What\'s special about this edition?')}
            *   **{t('ملف واحد فقط', 'Single File')}**: ملف بصيغة HTML يعمل على أي متصفح مباشرة.
            *   **{t('لا يحتاج خادم', 'No Server Needed')}**: لا تحتاج لتثبيت بايثون أو أي برامج أخرى.
            *   **{t('خدمات متاحة أوفلاين', 'Offline Services')}**:
                - {t('تسعير وتحليل المقايسات', 'BOQ Pricing & Analysis')}
                - {t('الحسابات الإنشائية (ECP)', 'Structural Calculations')}
                - {t('جداول الحديد (BBS)', 'Bar Bending Schedules')}
                - {t('موديولات الـ ERP بالكامل', 'Full ERP Resource Modules')}
            """)
            
            # Download Button
            standalone_path = "engicost_site_edition.html"
            if os.path.exists(standalone_path):
                with open(standalone_path, "rb") as file:
                    st.download_button(
                        label="📥 " + t("تحميل نسخة الموقع (Site Edition)", "Download Site Edition (Offline)"),
                        data=file,
                        file_name="EngiCost_Site_Edition.html",
                        mime="text/html",
                        use_container_width=True
                    )
            else:
                st.error("Offline file not found. Please contact support.")

        with col_off2:
            st.markdown(f"""
            <div class="glass-card" style="padding:1.5rem; border-left:4px solid var(--accent-secondary);">
                <h5 style="color:var(--accent-secondary);">{t('تنبيه هام', 'Important Note')}</h5>
                <p style="font-size:0.85rem; color:var(--text-muted);">
                {t('يجب فتح الملف مرة واحدة وأنت متصل بالإنترنت ليقوم المتصفح بتخزين محرك التشغيل. بعد ذلك يمكنك استخدامه أوفلاين تماماً برفع مخططاتك وملفاتك.',
                   'You must open the file once while online for the browser to cache the engine. After that, you can use it entirely offline.')}
                </p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br><hr><br>", unsafe_allow_html=True)
    if True: # Was tab_contact
        st.markdown(f"<h3 style='text-align:center;'>📞 {t('الدعم الفني والتواصل المباشر', 'Technical Support & Direct Contact')}</h3>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        col_c1, col_c2 = st.columns([1, 1])
        
        with col_c1:
            # (Existing contact code...)
            wa_label = t("💬 مجموعة واتساب — دعم مباشر", "💬 WhatsApp Group — Direct Support")
            st.markdown(f"""
            <a href="https://chat.whatsapp.com/DAvMR2CeKPWKXHDDseP2sh?mode=gi_t" target="_blank" style="text-decoration:none;">
                <div style="padding:1rem; border-radius:12px; border-left:4px solid #25D366; background:rgba(37,211,102,0.08); margin-bottom:10px;">
                    <p style="margin:0; font-weight:bold; color:#25D366;">{wa_label}</p>
                    <p style="margin:0; color:#94a3b8; font-size:0.8rem;">{t("انضم لمجتمعنا الهندسي للدعم الفوري", "Join our community for instant support")}</p>
                </div>
            </a>
            """, unsafe_allow_html=True)

            # Email (Existing...)
            email_label = t("✉️ البريد الإلكتروني", "✉️ Email Support")
            st.markdown(f"""
            <div style="padding:1rem; border-radius:12px; border-left:4px solid #2563eb; background:rgba(37,99,235,0.08); margin-bottom:10px;">
                <p style="margin:0; font-weight:bold; color:#60a5fa;">{email_label}</p>
                <p style="margin:0; color:#94a3b8; font-size:0.8rem;">engicost151@gmail.com</p>
            </div>
            """, unsafe_allow_html=True)

            # Working Hours
            st.markdown(f"""
            <div style="padding:1rem; border-radius:12px; border-left:4px solid #fb923c; background:rgba(251,146,60,0.08);">
                <p style="margin:0; font-weight:bold; color:#fb923c;">{t("🕐 ساعات العمل", "🕐 Working Hours")}</p>
                <p style="margin:0; color:#94a3b8; font-size:0.8rem;">{t("خدمة 24 ساعة - طوال أيام الأسبوع", "24/7 Support - Every Day")}</p>
            </div>
            """, unsafe_allow_html=True)

        with col_c2:
            st.markdown(f"#### {t('أرسل استفساراً سريعاً', 'Quick Inquiry')}")
            with st.form("guest_contact_form"):
                contact_email = st.text_input(t("بريدك الإلكتروني", "Your Email"), placeholder="name@example.com")
                msg_subject = st.text_input(t("الموضوع", "Subject"), placeholder=t("استفسار عن اشتراك", "Subscription inquiry"))
                msg_body = st.text_area(t("الرسالة", "Message"), height=100)
                
                if st.form_submit_button(t("📤 إرسال المسج", "Send Message"), use_container_width=True):
                    if contact_email and msg_body:
                        try:
                            db = SessionLocal()
                            new_inquiry = Inquiry(
                                email=contact_email,
                                subject=msg_subject,
                                message=msg_body
                            )
                            db.add(new_inquiry)
                            db.commit()
                            db.close()
                            st.success(t("✅ تم استلام رسالتك! سنتواصل معك قريباً.", "✅ Message received! We'll contact you soon."))
                        except Exception as e:
                            st.error(f"Error: {e}")
                    else:
                        st.error(t("الرجاء إدخال البريد والرسالة", "Please enter email and message"))

    st.markdown("---")
    # Chatbot logic remains same
    st.markdown(f"### 🤖 {t('المساعد الذكي (قبل الدخول)', 'AI Support Assistant (Pre-login)')}")
    if "guest_messages" not in st.session_state:
        st.session_state.guest_messages = []
    for gmsg in st.session_state.guest_messages:
        with st.chat_message(gmsg["role"]):
            st.markdown(gmsg["content"])
    if gprompt := st.chat_input(t("اسألني عن المنصة...", "Ask about the platform...")):
        st.chat_message("user").markdown(gprompt)
        st.session_state.guest_messages.append({"role": "user", "content": gprompt})
        with st.chat_message("assistant"):
            try:
                engine = get_cost_engine()
                ai_prompt = f"Guest user question: {gprompt}. Provide info about EngiCost AI."
                response_text, _ = engine._call_groq(ai_prompt, expect_json=False)
                st.markdown(response_text)
                st.session_state.guest_messages.append({"role": "assistant", "content": response_text})
            except Exception as e: st.error(f"AI Error: {e}")
