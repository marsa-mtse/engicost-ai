import streamlit as st
from utils import t, render_section_header
from database import SessionLocal, User

def render_settings():
    render_section_header(t("الإعدادات والتفضيلات", "Settings & Preferences"), "⚙️")
    
    tabs = st.tabs([
        t("🎨 المظهر", "🎨 Appearance"),
        t("👤 الملف الشخصي", "👤 Profile"),
        t("🔔 الإشعارات", "🔔 Notifications"),
        t("📞 الدعم الفني", "📞 Support"),
    ])
    
    # ─── Appearance Tab ─────────────────────────────────────────
    with tabs[0]:
        st.markdown(f"#### {t('تفضيلات العرض', 'Display Preferences')}")
        
        # Language toggle
        current_lang = st.session_state.get("lang", "ar")
        lang_choice = st.radio(
            t("اللغة", "Language"),
            options=["🇪🇬 العربية", "🇺🇸 English"],
            index=0 if current_lang == "ar" else 1,
            horizontal=True
        )
        if "العربية" in lang_choice:
            st.session_state.lang = "ar"
        else:
            st.session_state.lang = "en"
        
        st.markdown("---")
        
        # Region and Currency Settings
        st.markdown(f"#### {t('المنطقة والعملة (Global)', 'Region & Currency')}")
        
        current_region = st.session_state.get("region", "Global")
        region_options = ["Global", "Egypt", "Saudi Arabia", "UAE", "Qatar", "USA", "United Kingdom", "Kuwait", "Oman", "Bahrain"]
        selected_region = st.selectbox(
            t("الدولة / المنطقة", "Country / Region"),
            options=region_options,
            index=region_options.index(current_region) if current_region in region_options else 0
        )
        st.session_state.region = selected_region
        
        # Default Currency
        current_currency = st.session_state.get("currency", "USD")
        currency_options = ["USD", "EGP", "SAR", "AED", "QAR", "GBP", "KWD", "OMR", "BHD", "EUR"]
        selected_currency = st.selectbox(
            t("العملة الافتراضية للمنصة", "Platform Default Currency"),
            options=currency_options,
            index=currency_options.index(current_currency) if current_currency in currency_options else 0
        )
        st.session_state.currency = selected_currency
        
        st.markdown("---")
        
        # Theme preview card
        st.markdown(f"""
        <div class="glass-card animate-in" style="padding:1.5rem; border-left:4px solid var(--accent-primary);">
            <h4 style="margin:0 0 0.5rem; color:var(--accent-primary);">{t('معاينة المظهر الحالي', 'Current Theme Preview')}</h4>
            <p style="color:var(--text-secondary); margin:0;">{t('المنصة تستخدم المظهر الداكن الاحترافي — مُحسّن للعمل الليلي والضغط البصري المنخفض.', 'Platform uses professional dark theme — optimized for night work and low visual strain.')}</p>
            <br>
            <div style="display:flex; gap:10px; flex-wrap:wrap;">
                <div style="width:30px;height:30px;border-radius:50%;background:var(--accent-primary);"></div>
                <div style="width:30px;height:30px;border-radius:50%;background:var(--success);"></div>
                <div style="width:30px;height:30px;border-radius:50%;background:#a78bfa;"></div>
                <div style="width:30px;height:30px;border-radius:50%;background:#fb923c;"></div>
                <div style="width:30px;height:30px;border-radius:50%;background:#f87171;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button(t("💾 حفظ التفضيلات", "Save Preferences"), use_container_width=True):
            st.success(t("✅ تم حفظ التفضيلات!", "✅ Preferences saved!"))
            st.rerun()
    
    # ─── Profile Tab ─────────────────────────────────────────────
    with tabs[1]:
        st.markdown(f"#### {t('معلوماتك الشخصية', 'Your Profile Info')}")
        
        try:
            db = SessionLocal()
            user = db.query(User).filter(User.username == st.session_state.username).first()
            if user:
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"""
                    <div class="glass-card" style="padding:1rem;">
                        <p style="margin:0; color:var(--text-muted); font-size:0.8rem;">{t('اسم المستخدم', 'Username')}</p>
                        <h3 style="margin:0; color:var(--accent-primary);">👤 {user.username}</h3>
                    </div>
                    """, unsafe_allow_html=True)
                with col2:
                    st.markdown(f"""
                    <div class="glass-card" style="padding:1rem;">
                        <p style="margin:0; color:var(--text-muted); font-size:0.8rem;">{t('الباقة', 'Plan')}</p>
                        <h3 style="margin:0; color:var(--success);">🏆 {user.plan}</h3>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
                new_email = st.text_input(t("البريد الإلكتروني", "Email"), value=user.email or "")
                if st.button(t("📧 تحديث البريد الإلكتروني", "Update Email"), use_container_width=True):
                    try:
                        user.email = new_email
                        db.commit()
                        st.success(t("✅ تم التحديث!", "✅ Updated!"))
                    except Exception as e:
                        st.error(f"Error: {e}")
            db.close()
        except Exception as e:
            st.error(f"Error loading profile: {e}")
    
    # ─── Notifications Tab ────────────────────────────────────────
    with tabs[2]:
        st.markdown(f"#### {t('إعدادات الإشعارات', 'Notification Settings')}")
        
        st.toggle(t("📈 تنبيهات تحركات السوق اليومية", "📈 Daily market movement alerts"), value=True)
        st.toggle(t("🎉 إشعارات تحديثات المنصة", "🎉 Platform update notifications"), value=True)
        st.toggle(t("📋 ملخص أسبوعي لمشاريعي", "📋 Weekly projects summary"), value=False)
        
        st.markdown("---")
        email_notif = st.text_input(
            t("📧 بريد إلكتروني للإشعارات (قادم قريباً)", "📧 Email for notifications (coming soon)"),
            placeholder="your@email.com"
        )
        
        if st.button("🧪 " + t("إرسال تنبيه تجريبي للأسعار", "Send Test Price Alert")):
            st.toast(t("تم إرسال تنبيه: ارتفاع سعر حديد عز بمقدار 500 ج.م", "Alert sent: Ezz Steel price increased by 500 EGP"), icon="📈")
            
        st.caption(t("⚙️ ميزة الإشعارات البريدية قيد التطوير.", "⚙️ Email notification feature is under development."))
    
    # ─── Support Tab ─────────────────────────────────────────────
    with tabs[3]:
        st.markdown(f"#### {t('الدعم الفني والتواصل', 'Technical Support & Contact')}")
        
        # WhatsApp Group
        wa_label = t("💬 مجموعة واتساب — دعم مباشر ومجتمع هندسي", "💬 WhatsApp Group — Direct Support")
        wa_sub   = t("انضم الآن للدعم الفوري والمجتمع الهندسي", "Join now for instant support and engineering community")
        st.markdown(f"""
<a href="https://chat.whatsapp.com/DAvMR2CeKPWKXHDDseP2sh?mode=gi_t" target="_blank" style="text-decoration:none; display:block; margin-bottom:10px;">
  <div style="padding:1rem; border-radius:12px; border-left:4px solid #25D366; background:rgba(37,211,102,0.08); display:flex; align-items:center; gap:15px; cursor:pointer;">
    <span style="font-size:2rem;">💬</span>
    <div style="flex:1;"><p style="margin:0; font-weight:bold; color:#25D366;">{wa_label}</p>
    <p style="margin:0; color:#94a3b8; font-size:0.83rem;">{wa_sub}</p></div>
    <span style="color:#25D366; font-size:1.4rem;">&#8594;</span>
  </div>
</a>
""", unsafe_allow_html=True)

        # Email
        email_label = t("✉️ البريد الإلكتروني", "✉️ Email Support")
        st.markdown(f"""
<a href="mailto:support@engicost.ai" style="text-decoration:none; display:block; margin-bottom:10px;">
  <div style="padding:1rem; border-radius:12px; border-left:4px solid #2563eb; background:rgba(37,99,235,0.08); display:flex; align-items:center; gap:15px; cursor:pointer;">
    <span style="font-size:2rem;">✉️</span>
    <div><p style="margin:0; font-weight:bold; color:#60a5fa;">{email_label}</p>
    <p style="margin:0; color:#94a3b8; font-size:0.83rem;">support@engicost.ai</p></div>
  </div>
</a>
""", unsafe_allow_html=True)

        # Working Hours
        hours_label = t("🕐 ساعات العمل", "🕐 Working Hours")
        hours_val   = t("السبت – الخميس، ٩ص – ٦م (توقيت القاهرة)", "Sat – Thu, 9AM – 6PM (Cairo Time)")
        st.markdown(f"""
<div style="padding:1rem; border-radius:12px; border-left:4px solid #fb923c; background:rgba(251,146,60,0.08); display:flex; align-items:center; gap:15px; margin-bottom:10px;">
  <span style="font-size:2rem;">🕐</span>
  <div><p style="margin:0; font-weight:bold; color:#fb923c;">{hours_label}</p>
  <p style="margin:0; color:#94a3b8; font-size:0.83rem;">{hours_val}</p></div>
</div>
""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"#### {t('أرسل رسالة مباشرة', 'Send a Direct Message')}")
        msg_subject = st.text_input(t("الموضوع", "Subject"), placeholder=t("استفسار عن المقايسات", "Inquiry about BOQ pricing"))
        msg_body = st.text_area(t("الرسالة", "Message"), height=100, placeholder=t("اكتب رسالتك هنا...", "Write your message here..."))
        if st.button(t("📤 إرسال الرسالة", "Send Message"), use_container_width=True):
            if msg_body.strip():
                st.success(t("✅ تم استقبال رسالتك! سنرد خلال 24 ساعة.", "✅ Message received! We'll respond within 24 hours."))
            else:
                st.warning(t("الرجاء كتابة رسالة أولاً.", "Please write a message first."))
