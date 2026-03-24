import streamlit as st
import uuid
from utils import t, render_section_header
from config import PLANS, PAYMOB_CARD_INTG_ID, PAYMOB_IFRAME_ID

def render_billing():
    render_section_header(t("الاشتراكات والفواتير", "Billing & Subscriptions"), "💳")

    current_plan = st.session_state.get("plan", "Free")
    username     = st.session_state.get("username", "user")
    user_email   = st.session_state.get("email", f"{username}@engicost.ai")

    # ─── Current Plan Banner ─────────────────────────────────────────────────
    plan_colors = {"Free": "#64748b", "Pro": "#0ea5e9", "Enterprise": "#6366f1"}
    color = plan_colors.get(current_plan, "#0ea5e9")
    st.markdown(f"""
    <div class="glass-card animate-up" style="padding:1rem 1.5rem; border-left:4px solid {color}; margin-bottom:1.5rem;">
        <p style="margin:0; font-size:0.8rem; color:var(--text-secondary);">{t("باقتك الحالية", "Your Current Plan")}</p>
        <h2 style="margin:4px 0 0 0; color:{color};">💎 {current_plan}</h2>
    </div>
    """, unsafe_allow_html=True)

    # ─── Plan Cards ──────────────────────────────────────────────────────────
    col1, col2, col3 = st.columns(3)

    plans_config = [
        {
            "key": "Free",
            "icon": "🆓",
            "color": "#64748b",
            "price_egp": 0,
            "features_ar": ["1 مخطط شهرياً", "1 مقايسة شهرياً", "لوحة القيادة", "أسعار السوق"],
            "features_en": ["1 Blueprint/month", "1 BOQ/month", "Dashboard", "Market Prices"],
        },
        {
            "key": "Pro",
            "icon": "⚡",
            "color": "#0ea5e9",
            "price_egp": 299,
            "popular": True,
            "features_ar": ["50 مخطط شهرياً", "100 مقايسة شهرياً", "كل الأدوات الهندسية", "تصدير PDF/Excel بدون علامة مائية", "متجر العطاءات كاملاً"],
            "features_en": ["50 Blueprints/month", "100 BOQs/month", "All Engineering Tools", "PDF/Excel Export — No Watermark", "Full Tender Hub"],
        },
        {
            "key": "Enterprise",
            "icon": "🏛️",
            "color": "#6366f1",
            "price_egp": 799,
            "features_ar": ["غير محدود", "كل مميزات Pro", "تقارير White-Label بشعار شركتك", "دعم مخصص 24/7", "API مخصص"],
            "features_en": ["Unlimited", "All Pro Features", "White-Label Reports with Your Logo", "Dedicated 24/7 Support", "Custom API"],
        },
    ]

    for col, plan in zip([col1, col2, col3], plans_config):
        key = plan["key"]
        price_egp = plan["price_egp"]
        is_active = current_plan == key
        color = plan["color"]
        border = f"border: 2px solid {color};" if is_active else ""
        scale = "transform: scale(1.03);" if plan.get("popular") else ""
        features = plan["features_ar"] if st.session_state.get("lang", "ar") == "ar" else plan["features_en"]

        feat_html = "".join(f"<p style='margin:4px 0; font-size:0.85rem;'>✅ {f}</p>" for f in features)
        popular_badge = f"""<div style="position:absolute;top:-12px;left:50%;transform:translateX(-50%);background:{color};color:white;padding:3px 14px;border-radius:20px;font-size:0.7rem;font-weight:700;white-space:nowrap;">{'⭐ الأكثر طلباً' if st.session_state.get('lang','ar')=='ar' else '⭐ Most Popular'}</div>""" if plan.get("popular") else ""
        price_display = "مجاناً" if price_egp == 0 else f"{price_egp:,}"
        price_unit_display = '<span style="font-size:0.9rem; color:var(--text-muted)"> EGP/شهر</span>' if price_egp > 0 else ''

        with col:
            st.markdown(f"""<div class="glass-card animate-up" style="text-align:center; position:relative; {border} {scale} padding:1.5rem 1rem;">{popular_badge}<div style="font-size:2rem;">{plan['icon']}</div><h2 style="color:{color}; margin:8px 0;">{key}</h2><h1 style="margin:0; font-size:2.2rem; font-weight:800;">{price_display}{price_unit_display}</h1><hr style="border-color:var(--glass-border); margin:12px 0;">{feat_html}<br></div>""", unsafe_allow_html=True)

            if is_active:
                st.button(t("✅ باقتك الحالية", "✅ Current Plan"), key=f"btn_{key}_active", disabled=True, use_container_width=True)
            elif price_egp == 0:
                st.button(t("الرجوع للمجاني", "Downgrade to Free"), key=f"btn_{key}", disabled=True, use_container_width=True)
            else:
                if st.button(t(f"⚡ ترقية لـ {key}", f"⚡ Upgrade to {key}"), key=f"btn_{key}", type="primary", use_container_width=True):
                    st.session_state[f"upgrade_requested_{key}"] = True

            if st.session_state.get(f"upgrade_requested_{key}"):
                wa_msg = f"مرحباً، أريد ترقية حسابي ({username}) لباقة {key} — {price_egp} EGP/شهر"
                wa_url = f"https://wa.me/201000000000?text={wa_msg.replace(' ', '%20')}"
                st.markdown(f"""
                <a href="{wa_url}" target="_blank">
                    <div style="background:rgba(37,211,102,0.15);border:1px solid #25D366;border-radius:12px;padding:0.8rem;text-align:center;margin-top:0.5rem;">
                        <strong style="color:#25D366;">📱 {t('تواصل عبر WhatsApp للترقية', 'Contact via WhatsApp to Upgrade')}</strong>
                    </div>
                </a>
                """, unsafe_allow_html=True)

    # ─── White-Label Toggle (Pro/Enterprise only) ─────────────────────────────
    if current_plan in ["Pro", "Enterprise"]:
        st.markdown("---")
        st.markdown(f"### 🏷️ {t('إعدادات التقارير المخصصة (White-Label)', 'Custom Report Settings (White-Label)')}")
        wl_enabled = st.toggle(
            t("تفعيل تقارير White-Label (إخفاء EngiCost AI)", "Enable White-Label Reports (Hide EngiCost AI branding)"),
            value=st.session_state.get("white_label_enabled", False),
            key="white_label_toggle"
        )
        st.session_state["white_label_enabled"] = wl_enabled
        if wl_enabled:
            company = st.text_input(t("اسم شركتك على التقارير", "Your company name on reports"),
                                    value=st.session_state.get("company_name_wl", ""),
                                    key="company_name_wl_input")
            st.session_state["company_name_wl"] = company
            st.success(t(f"✅ سيظهر اسم '{company}' على كل التقارير المُصدَّرة.", f"✅ '{company}' will appear on all exported reports."))

    # ─── FAQ / Notes ─────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown(f"### ❓ {t('أسئلة شائعة', 'FAQ')}")

    with st.expander(t("ما هي طرق الدفع المتاحة؟", "What payment methods are available?")):
        st.markdown(t(
            "- **فيزا / ماستركارد** (بطاقات بنكية)\n- **فوري** (دفع نقدي في أي محل فوري)\n- **تحويل بنكي** (عند الطلب)",
            "- **Visa / Mastercard** (Bank cards)\n- **Fawry** (Cash at any Fawry outlet)\n- **Bank Transfer** (on request)"
        ))

    with st.expander(t("هل يمكن إلغاء الاشتراك؟", "Can I cancel my subscription?")):
        st.markdown(t(
            "نعم، يمكنك الإلغاء في أي وقت. الاشتراك يستمر حتى نهاية الفترة المدفوعة.",
            "Yes, you can cancel anytime. Your subscription continues until the end of the paid period."
        ))

    with st.expander(t("هل هناك نسخة تجريبية؟", "Is there a free trial?")):
        st.markdown(t(
            "الباقة المجانية متاحة بشكل دائم بدون بطاقة ائتمان.",
            "The Free plan is permanently available with no credit card required."
        ))

    with st.expander(t("ما الفرق بين Pro و Enterprise؟", "What's the difference between Pro and Enterprise?")):
        st.markdown(t(
            "- **Pro**: مناسب للمهندسين الأفراد والمكاتب الصغيرة\n- **Enterprise**: مناسب للشركات مع دعم مخصص وتقارير بشعار الشركة (White-Label)",
            "- **Pro**: Ideal for individual engineers and small offices\n- **Enterprise**: For companies with dedicated support and branded (White-Label) reports"
        ))

    # ─── WhatsApp Contact ─────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="glass-card animate-up" style="text-align:center; margin-top:1rem; padding:1.2rem; border:1px solid rgba(37,211,102,0.3);">
        <p style="margin:0; color:var(--text-secondary); font-size:0.85rem;">{t('تحتاج مساعدة في الاشتراك؟', 'Need help with your subscription?')}</p>
        <a href="https://chat.whatsapp.com/DAvMR2CeKPWKXHDDseP2sh" target="_blank" style="color:#25D366; font-weight:bold; font-size:1rem; text-decoration:none;">
            📱 {t('انضم لمجموعة الدعم على WhatsApp', 'Join WhatsApp Support Group')}
        </a>
    </div>
    """, unsafe_allow_html=True)


def _initiate_payment(amount_egp: float, plan: str, email: str, username: str):
    """Trigger Paymob checkout and show iframe or redirect."""
    # Check if Paymob is configured
    if not PAYMOB_CARD_INTG_ID:
        st.warning(t(
            "⚠️ بوابة الدفع قيد الإعداد. تواصل معنا عبر WhatsApp لإتمام الاشتراك يدوياً.",
            "⚠️ Payment gateway is being set up. Contact us via WhatsApp to complete your subscription manually."
        ))
        return

    merchant_order_id = f"{username}_{plan}_{uuid.uuid4().hex[:8]}"

    with st.spinner(t("جاري تجهيز بوابة الدفع...", "Preparing payment gateway...")):
        try:
            from paymob_engine import create_checkout_url
            checkout_url = create_checkout_url(
                amount_egp=amount_egp,
                user_email=email,
                user_name=username,
                merchant_order_id=merchant_order_id,
                method="card"
            )
        except Exception as e:
            checkout_url = None

    if checkout_url:
        if PAYMOB_IFRAME_ID:
            # Embed iframe directly
            st.markdown(f"""
            <div style="width:100%; border-radius:16px; overflow:hidden; border:1px solid var(--glass-border); margin-top:1rem;">
                <iframe src="{checkout_url}" width="100%" height="600" frameborder="0" scrolling="no"></iframe>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Open in new tab
            st.markdown(f"""
            <a href="{checkout_url}" target="_blank">
                <div class="glass-card animate-up" style="text-align:center; padding:1.5rem; border:2px solid #0ea5e9; cursor:pointer;">
                    <h3 style="color:#0ea5e9;">💳 {t('اضغط هنا لإتمام الدفع', 'Click here to complete payment')}</h3>
                    <p style="color:var(--text-secondary);">{t('سيتم فتح بوابة Paymob الآمنة', 'Paymob secure gateway will open')}</p>
                </div>
            </a>
            """, unsafe_allow_html=True)
        st.info(t(
            "🔒 بعد إتمام الدفع سيتم تفعيل باقتك خلال دقائق.",
            "🔒 After payment, your plan will be activated within minutes."
        ))
    else:
        st.warning(t(
            "⚠️ تعذر الاتصال ببوابة الدفع. تواصل معنا عبر WhatsApp.",
            "⚠️ Could not connect to payment gateway. Contact us via WhatsApp."
        ))
