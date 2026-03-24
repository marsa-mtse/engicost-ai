import streamlit as st
from utils import t, render_section_header


def render_legal():
    render_section_header(t("الإطار القانوني", "Legal & Compliance"), "⚖️")

    tab_privacy, tab_terms = st.tabs([
        "🔐 " + t("سياسة الخصوصية", "Privacy Policy"),
        "📜 " + t("شروط الاستخدام", "Terms of Service"),
    ])

    with tab_privacy:
        st.markdown(f"""
<div style="max-width:760px; margin:auto; line-height:1.8; color:var(--text-primary);">

<h3 style="color:#0ea5e9;">🔐 {t('سياسة الخصوصية', 'Privacy Policy')}</h3>
<p style="color:var(--text-muted); font-size:0.85rem;">{t('آخر تحديث: مارس 2025', 'Last updated: March 2025')}</p>

<h4>1. {t('ما البيانات التي نجمعها؟', 'What data do we collect?')}</h4>
<ul>
  <li>{t('اسم المستخدم والبريد الإلكتروني عند التسجيل.', 'Username and email address on registration.')}</li>
  <li>{t('بيانات المشاريع والمقايسات التي تُدخلها في المنصة.', 'Project and BOQ data you enter into the platform.')}</li>
  <li>{t('بيانات الاستخدام والتحليلات (بشكل مجهول الهوية).', 'Usage analytics data (anonymized).')}</li>
</ul>

<h4>2. {t('كيف نستخدم بياناتك؟', 'How do we use your data?')}</h4>
<ul>
  <li>{t('لتقديم خدمات المنصة وتشغيل حسابك.', 'To provide platform services and operate your account.')}</li>
  <li>{t('لتحسين الأداء وتطوير الميزات.', 'To improve performance and develop features.')}</li>
  <li>{t('لا نبيع بياناتك لأي طرف ثالث.', 'We do NOT sell your data to any third party.')}</li>
</ul>

<h4>3. {t('كيف نحمي بياناتك؟', 'How do we protect your data?')}</h4>
<p>{t('نستخدم تشفير HTTPS لجميع الاتصالات. يتم تخزين كلمات المرور بشكل مشفر ولا يمكن استرجاعها.', 'We use HTTPS encryption for all communications. Passwords are stored encrypted and cannot be retrieved.')}</p>

<h4>4. {t('هل نستخدم ملفات تعريف الارتباط (Cookies)؟', 'Do we use Cookies?')}</h4>
<p>{t('نستخدم ملفات تعريف الارتباط الأساسية فقط للحفاظ على جلستك. لا نستخدم ملفات تعريف الارتباط الإعلانية.', 'We only use essential session cookies. We do not use advertising cookies.')}</p>

<h4>5. {t('التواصل بخصوص الخصوصية', 'Privacy Contact')}</h4>
<p>{t('للاستفسار عن بياناتك أو طلب حذفها:', 'For inquiries about your data or deletion requests:')} <strong>engicost151@gmail.com</strong></p>

</div>
        """, unsafe_allow_html=True)

    with tab_terms:
        st.markdown(f"""
<div style="max-width:760px; margin:auto; line-height:1.8; color:var(--text-primary);">

<h3 style="color:#6366f1;">📜 {t('شروط الاستخدام', 'Terms of Service')}</h3>
<p style="color:var(--text-muted); font-size:0.85rem;">{t('آخر تحديث: مارس 2025', 'Last updated: March 2025')}</p>

<h4>1. {t('القبول بالشروط', 'Acceptance of Terms')}</h4>
<p>{t('باستخدامك لمنصة EngiCost AI، فإنك توافق على هذه الشروط. إذا كنت لا توافق، يُرجى عدم استخدام المنصة.', 'By using EngiCost AI, you agree to these terms. If you disagree, please do not use the platform.')}</p>

<h4>2. {t('استخدام مقبول', 'Acceptable Use')}</h4>
<ul>
  <li>{t('يُسمح باستخدام المنصة للأغراض الهندسية والمهنية القانونية فقط.', 'The platform may only be used for lawful engineering and professional purposes.')}</li>
  <li>{t('يُحظر محاولة اختراق أو إساءة استخدام أنظمة المنصة.', 'Attempting to hack or abuse platform systems is strictly prohibited.')}</li>
  <li>{t('يُحظر إعادة بيع خدمات المنصة دون إذن كتابي.', 'Reselling platform services without written permission is prohibited.')}</li>
</ul>

<h4>3. {t('القيود والإخلاء من المسؤولية', 'Limitation of Liability')}</h4>
<p>{t('تُقدِّم المنصة نتائج AI بصفة إرشادية. يتحمل المستخدم المسؤولية الكاملة عن أي قرارات هندسية مبنية على هذه النتائج. ننصح دائماً بمراجعة مهندس مختص.', 'The platform provides AI-driven results for guidance only. The user bears full responsibility for any engineering decisions based on these results. We always advise consulting a licensed engineer.')}</p>

<h4>4. {t('الملكية الفكرية', 'Intellectual Property')}</h4>
<p>{t('جميع كودات وتصاميم المنصة محمية. المحتوى الذي تُنشئه بالمنصة (مقايسات ومخططات) يظل ملكاً لك.', 'All platform code and designs are protected. Content you create on the platform (BOQs and drawings) remains yours.')}</p>

<h4>5. {t('التعديل على الشروط', 'Changes to Terms')}</h4>
<p>{t('نحتفظ بحق تحديث هذه الشروط في أي وقت. سيتم إخطارك بأي تغييرات جوهرية عبر البريد الإلكتروني.', 'We reserve the right to update these terms at any time. You will be notified of material changes by email.')}</p>

<h4>6. {t('التواصل', 'Contact')}</h4>
<p>{t('لأي استفسارات قانونية:', 'For legal inquiries:')} <strong>engicost151@gmail.com</strong></p>

</div>
        """, unsafe_allow_html=True)
