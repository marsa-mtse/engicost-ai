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

    # Hero Section — inline colors to avoid CSS variable unavailability before auth
    st.markdown(f"""
        <div style="text-align:center; padding: 3rem 1rem; background: radial-gradient(circle at center, rgba(14,165,233,0.18) 0%, transparent 70%); border-radius: 40px; margin-bottom: 2rem;">
            <div style="font-size:4rem; margin-bottom:0.5rem;">🏗️</div>
            <h1 style="font-size: clamp(2rem, 5vw, 3.5rem); font-weight: 900; line-height: 1.1; margin-bottom: 1rem;
                       background: linear-gradient(135deg, #e2e8f0 0%, #0ea5e9 60%, #6366f1 100%);
                       -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                EngiCost AI
            </h1>
            <h2 style="font-size:clamp(1.1rem,2vw,1.5rem); font-weight:600; color:#cbd5e1; margin-bottom:0.75rem;">
                {t("ثورة الذكاء الاصطناعي في الهندسة الإنشائية", "AI Revolution in Construction Engineering")}
            </h2>
            <p style="color:#94a3b8; font-size:clamp(0.9rem, 1.5vw, 1.15rem); max-width:750px; margin:0 auto; line-height:1.7; font-weight:400;">
                {t("المنصة المتكاملة لتحليل المخططات، تسعير المقايسات، ورسم الهندسي بالذكاء الاصطناعي وإدارة المشاريع بدقة متناهية.",
                   "The integrated platform for blueprint analysis, AI-powered BOQ pricing, drawing engine, and project management.")}
            </p>
            <div style="display:flex; justify-content:center; gap:1.5rem; margin-top:1.5rem; flex-wrap:wrap;">
                <span style="background:rgba(14,165,233,0.15); border:1px solid rgba(14,165,233,0.3); padding:0.4rem 1rem; border-radius:999px; color:#7dd3fc; font-size:0.85rem;">🌍 {t("متجر العطاءات الحي", "Live Tender Hub")}</span>
                <span style="background:rgba(99,102,241,0.15); border:1px solid rgba(99,102,241,0.3); padding:0.4rem 1rem; border-radius:999px; color:#a5b4fc; font-size:0.85rem;">📐 {t("مهندس الرسم الذكي", "AI Drawing Engine")}</span>
                <span style="background:rgba(16,185,129,0.15); border:1px solid rgba(16,185,129,0.3); padding:0.4rem 1rem; border-radius:999px; color:#6ee7b7; font-size:0.85rem;">🛰️ {t("الرفع المساحي GIS", "GIS Survey")}</span>
                <span style="background:rgba(245,158,11,0.15); border:1px solid rgba(245,158,11,0.3); padding:0.4rem 1rem; border-radius:999px; color:#fcd34d; font-size:0.85rem;">💰 {t("تسعير آلي للمقايسات", "Auto BOQ Pricing")}</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Main Auth & Info (Converted to Scrolling Landing Page)
    st.markdown("<br>", unsafe_allow_html=True)
    
    if True: # Was tab_auth
        col_auth_l, col_auth_r = st.columns(2)

        with col_auth_l:
            st.markdown(f"""
            <div class="glass-card animate-up" style="padding: 2rem;">
                <h3 style="margin-top:0; color:var(--accent-primary);">{t('تسجيل الدخول', 'Login')}</h3>
                <p style="color:var(--text-muted); font-size:0.85rem; margin-bottom:1.5rem;">{t('أهلاً بك مجدداً في مستقبلك الهندسي', 'Welcome back to your engineering future')}</p>
            """, unsafe_allow_html=True)
            login_user = st.text_input(t("اسم المستخدم", "Username"), key="login_user")
            login_pass = st.text_input(t("كلمة المرور", "Password"), type="password", key="login_pass")
            if st.button(t("دخول", "Login"), use_container_width=True, key="btn_login"):
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
                else: st.warning(t("أدخل البيانات", "Enter credentials"))
            st.markdown('</div>', unsafe_allow_html=True)

        with col_auth_r:
            st.markdown(f"""
            <div class="glass-card animate-up" style="padding: 2rem; border-color: var(--accent-secondary);">
                <h3 style="margin-top:0; color:var(--accent-secondary);">{t('إنشاء حساب', 'Sign Up')}</h3>
                <p style="color:var(--text-muted); font-size:0.85rem; margin-bottom:1.5rem;">{t('انضم لأذكى المهندسين في المنطقة', 'Join the smartest engineers in the region')}</p>
            """, unsafe_allow_html=True)
            new_user = st.text_input(t("اسم المستخدم", "Username"), key="reg_user")
            new_email = st.text_input(t("البريد الإلكتروني", "Email"), key="reg_email")
            new_pass = st.text_input(t("كلمة المرور", "Password"), type="password", key="reg_pass")
            if st.button(t("ابدأ الآن مجاناً", "Start Free Now"), use_container_width=True, key="btn_signup"):
                if new_user and new_email and new_pass:
                    user = create_user(new_user, new_email, new_pass)
                    if user: st.success(t("تم التسجيل بنجاح!", "Registered successfully!"))
                    else: st.error(t("المستخدم موجود بالفعل", "User already exists"))
                else: st.warning(t("يرجى ملء كافة الحقول", "Please fill all fields"))
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br><hr><br>", unsafe_allow_html=True)
    if True: # Was tab_about
        # ── Stats Bar via st.columns ──────────────────────────────
        stat_data = [
            ("V1.6.0", t("الإصدار الحالي", "Current Version")),
            ("8+",     t("وحدات ذكية",    "AI Modules")),
            ("100%",   t("مجاني للبدء",   "Free to Start")),
            ("24/7",   t("دعم مستمر",     "Always On")),
        ]
        s1, s2, s3, s4 = st.columns(4)
        for scol, (val, lbl) in zip([s1, s2, s3, s4], stat_data):
            with scol:
                st.markdown(
                    f'<div style="background:rgba(14,165,233,0.08);border:1px solid rgba(14,165,233,0.25);'
                    f'border-radius:16px;padding:1rem;text-align:center;margin-bottom:0.5rem;">'
                    f'<div style="font-size:1.8rem;font-weight:900;color:#0ea5e9;">{val}</div>'
                    f'<div style="font-size:0.78rem;color:#94a3b8;margin-top:4px;">{lbl}</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )

        # ── Feature Grid (8 cards — 2 rows of 4) ─────────────────
        st.markdown(
            f'<h3 style="color:#e2e8f0;text-align:center;margin:1.5rem 0 1rem;">⚡ '
            f'{t("كل ما تحتاجه في مكان واحد", "Everything You Need in One Place")}</h3>',
            unsafe_allow_html=True
        )
        features = [
            ("📐", t("مهندس الرسم الذكي", "AI Drawing Engine"),
             t("أكتب وصفاً بالعربية واحصل على مخطط SVG مع BOQ مسعَّر فوراً.",
               "Describe a building in Arabic, get an SVG plan + priced BOQ instantly.")),
            ("💰", t("تسعير آلي للمقايسات", "Auto BOQ Pricing"),
             t("ارفع Excel أو PDF ونسعّر الكميات بأسعار السوق الحية.",
               "Upload Excel/PDF — we price quantities with live market rates.")),
            ("🌍", t("متجر العطاءات الحي", "Live Tender Hub"),
             t("40+ عطاء يومياً من مصر والخليج مع فلترة بالدولة.",
               "40+ daily tenders from Egypt & Gulf with country filters.")),
            ("🛰️", t("رؤية حاسوبية GIS", "Computer Vision GIS"),
             t("ارفع صورة فضائية والذكاء الاصطناعي يكتشف التربة والمباني.",
               "Upload a satellite image — AI identifies terrain & structures.")),
            ("📅", t("Gantt Chart تلقائي", "Auto Gantt Chart"),
             t("جدول زمني تنفيذي يتولد تلقائياً من بنود مقايستك.",
               "Project schedule auto-generated from your BOQ items.")),
            ("📄", t("تقرير PDF شامل", "Full PDF Report"),
             t("صدّر رسم + مقايسة + ملخص ذكي في ملف PDF احترافي.",
               "Export drawing + BOQ + AI summary as a professional PDF.")),
            ("🧠", t("ملخص AI التنفيذي", "AI Executive Summary"),
             t("ضغطة زر واحدة — ملخص يشمل النطاق والتكاليف والجدول.",
               "One click — summary covering scope, costs & timeline.")),
            ("📊", t("S-Curve والتدفق النقدي", "S-Curve & Cash Flow"),
             t("رسوم Plotly للإنجاز المخطط مقابل الفعلي والتدفق النقدي.",
               "Plotly charts for planned vs actual & cash flow analysis.")),
        ]
        card_style = (
            'background:rgba(30,41,59,0.55);border:1px solid rgba(255,255,255,0.08);'
            'border-radius:18px;padding:1.2rem;text-align:center;margin-bottom:0.5rem;'
        )
        r1 = st.columns(4)
        r2 = st.columns(4)
        for i, (icon, title, desc) in enumerate(features):
            col = (r1 + r2)[i]
            with col:
                html = (
                    f'<div style="{card_style}">'
                    f'<div style="font-size:2rem;margin-bottom:6px;">{icon}</div>'
                    f'<div style="color:#0ea5e9;font-weight:700;font-size:0.85rem;margin-bottom:6px;">{title}</div>'
                    f'<div style="color:#94a3b8;font-size:0.76rem;line-height:1.5;">{desc}</div>'
                    f'</div>'
                )
                st.markdown(html, unsafe_allow_html=True)

        # ── Pricing Plans via st.columns ──────────────────────────
        st.markdown(
            f'<h3 style="color:#e2e8f0;text-align:center;margin:2rem 0 1rem;">💎 '
            f'{t("خطط الاشتراك", "Subscription Plans")}</h3>',
            unsafe_allow_html=True
        )
        plans = [
            ("🆓", t("مجاني", "Free"), "0", t("جنيه/شهر", "EGP/mo"),
             [t("مخطط واحد/شهر", "1 Drawing/month"), t("مقايسة واحدة/شهر", "1 BOQ/month"),
              t("لوحة التحكم", "Dashboard"), t("أسعار السوق", "Market Prices")],
             "#64748b", False),
            ("⚡", t("برو", "Pro"), "299", t("جنيه/شهر", "EGP/mo"),
             [t("مخططات غير محدودة", "Unlimited Drawings"), t("مقايسات غير محدودة", "Unlimited BOQs"),
              t("Gantt Chart", "Gantt Chart"), t("تصدير PDF/Excel", "PDF & Excel Export"),
              t("متجر العطاءات كاملاً", "Full Tender Hub")],
             "#0ea5e9", True),
            ("🏛️", t("مؤسسي", "Enterprise"), "799", t("جنيه/شهر", "EGP/mo"),
             [t("كل مميزات Pro", "All Pro Features"), t("مساحة عمل الشركة", "Company Workspace"),
              t("دعم مخصص", "Dedicated Support"), t("CV GIS Analysis", "CV GIS Analysis"),
              t("ملخص AI التنفيذي", "AI Executive Summary")],
             "#6366f1", False),
        ]
        p1, p2, p3 = st.columns(3)
        for pcol, (icon, pname, price, period, feats, color, popular) in zip([p1, p2, p3], plans):
            with pcol:
                border_color = color if popular else color + "55"
                popular_badge = (
                    f'<div style="background:{color};color:#fff;font-size:0.68rem;font-weight:800;'
                    f'padding:2px 10px;border-radius:999px;display:inline-block;margin-bottom:6px;">'
                    f'⭐ {t("الأكثر طلباً", "Most Popular")}</div><br>'
                ) if popular else ""
                feat_html = "".join(
                    f'<div style="margin:5px 0;font-size:0.82rem;color:#cbd5e1;text-align:right;">✅ {f}</div>'
                    for f in feats
                )
                plan_html = (
                    f'<div style="background:rgba(30,41,59,0.65);border:2px solid {border_color};'
                    f'border-radius:20px;padding:1.5rem;text-align:center;min-height:280px;">'
                    f'<div style="font-size:2rem;">{icon}</div>'
                    f'<h4 style="color:{color};margin:6px 0;">{pname}</h4>'
                    f'{popular_badge}'
                    f'<div style="font-size:2rem;font-weight:900;color:#f8fafc;">{price}'
                    f'<span style="font-size:0.8rem;color:#94a3b8;margin-right:4px;">{period}</span></div>'
                    f'<hr style="border:none;border-top:1px solid rgba(255,255,255,0.08);margin:10px 0;">'
                    f'{feat_html}'
                    f'</div>'
                )
                st.markdown(plan_html, unsafe_allow_html=True)

        # ── What's New (Changelog) ────────────────────────────────
        st.markdown(
            f'<h3 style="color:#e2e8f0;text-align:center;margin:2rem 0 1rem;">🆕 '
            f'{t("آخر التحديثات", "What\'s New")}</h3>',
            unsafe_allow_html=True
        )
        cl1, cl2, cl3 = st.columns(3)
        changelog = [
            (cl1, "#38bdf8", "V1.6.0",
             t("لوحة التحكم الذكية", "Smart Dashboard"),
             "Gantt Chart · PDF Export · AI Summary · Tender Alerts"),
            (cl2, "#a78bfa", "V1.5.0",
             t("الأتمتة الهندسية", "Engineering Automation"),
             "Auto-Pricing BOQ · Computer Vision GIS · Country Filters"),
            (cl3, "#34d399", "V1.4.0",
             t("البيانات الحية", "Live Data"),
             "Live Tender Hub · Folium Maps · KML Upload"),
        ]
        for col, clr, ver, title_cl, details in changelog:
            with col:
                st.markdown(
                    f'<div style="background:rgba(14,165,233,0.05);border:1px solid rgba(14,165,233,0.15);'
                    f'border-radius:14px;padding:1rem;">'
                    f'<div style="color:{clr};font-weight:700;margin-bottom:4px;">{ver} — {title_cl}</div>'
                    f'<div style="color:#94a3b8;font-size:0.8rem;">{details}</div>'
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
