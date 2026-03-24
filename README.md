---
title: EngiCost AI
emoji: 🏗️
colorFrom: blue
colorTo: indigo
sdk: streamlit
app_file: app.py
pinned: false
---
# 🏗️ EngiCost AI — المنصة الهندسية الذكية

<div align="center">

**المنصة الهندسية الأولى في مصر والشرق الأوسط المدعومة بالذكاء الاصطناعي**

[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://engicost.streamlit.app)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Version](https://img.shields.io/badge/Version-1.2.0-0ea5e9?style=for-the-badge)](https://github.com/marsa-mtse/engicost-ai)

</div>

---

## ✨ المنصة في أرقام

| 28+ أداة هندسية | مدعوم بـ Gemini & Groq AI | يعمل أوفلاين (PWA) | أسعار السوق اللحظية |
|:-:|:-:|:-:|:-:|

---

## 🛠️ الأدوات والموديولات

### 🌐 العام والأسواق
| الأداة | الوصف |
|--------|-------|
| 🏠 لوحة القيادة | إحصائيات، مشاريع محفوظة، نظرة سريعة على السوق |
| 📈 أسعار السوق | أسعار مواد البناء اللحظية (حديد، أسمنت، نحاس...) |
| 🌍 متجر العطاءات | مشاريع كبرى وتحليل ملاءمة العطاءات |

### 🧠 الذكاء والتحليل
| الأداة | الوصف |
|--------|-------|
| 🤖 المساعد الذكي | مساعد هندسي بالعربية والإنجليزية |
| 📐 تحليل المخططات | استخراج كميات من المخططات بالـ AI |
| ⚖️ FIDIC Scanner | تحليل مخاطر عقود المقاولة وفق FIDIC |

### 💰 العطاءات والتسعير
| الأداة | الوصف |
|--------|-------|
| 💰 تسعير BOQ | مقايسات دقيقة مع أسعار السوق اللحظية |
| ⚖️ مقارنة العروض | مقارنة عروض الأسعار من موردين مختلفين |
| 💹 حاسبة الربح | حساب هامش الربح والعطاء الأمثل |

### 🏗️ التنفيذ والهندسة
| الأداة | الوصف |
|--------|-------|
| 🏛️ الحسابات الإنشائية | ECP — كود البناء المصري |
| 📐 BBS تفريد الحديد | جداول تفريد الحديد |
| ⚙️ أنظمة MEP | الأنظمة الكهروميكانيكية |
| 📅 جدول جانت | تخطيط ومتابعة المشاريع |
| 📐 محرك الرسم | EngiDraft AI — رسم هندسي ذكي |
| 🌍 رفع مساحي | EngiSurvey AI — GIS وخرائط |
| ✔️ QA/QC | قوائم تفتيش الجودة |
| 🧧 IPC | شهادات الدفع الشهرية |

### 📦 موديولات ERP
| الأداة | الوصف |
|--------|-------|
| 📦 المخازن | إدارة المواد والمستودعات |
| 💵 المالية | تحليل مالي وتتبع الأرباح |
| 👷 الموارد البشرية | إدارة الموظفين والحضور |
| 🚜 الأصول | معدات البناء والأصول |
| 🤝 الموردين | قاعدة موردين وطلبات الأسعار |

---

## 💳 أسعار الاشتراك (EGP)

| الباقة | السعر | الاستخدام |
|--------|-------|-----------|
| 🆓 Free | 0 EGP/شهر | 1 مخطط + 1 مقايسة |
| ⚡ Pro | 299 EGP/شهر | 50 مخطط + 100 مقايسة + جميع الأدوات |
| 🏛️ Enterprise | 799 EGP/شهر | غير محدود + API + دعم أولوية |

---

## 🚀 النشر على Streamlit Cloud

```bash
# 1. Fork أو Clone الـ Repository
git clone https://github.com/marsa-mtse/engicost-ai.git

# 2. ثبّت المتطلبات محلياً
pip install -r requirements.txt

# 3. شغّل محلياً
streamlit run app.py
```

**للنشر على Streamlit Cloud:**
1. اذهب إلى [share.streamlit.io](https://share.streamlit.io)
2. اربط repo `marsa-mtse/engicost-ai`
3. أضف Secrets من `.streamlit/secrets.toml.example`
4. اضغط **Deploy** ✅

**Secrets المطلوبة:**
```toml
GEMINI_API_KEY       = "AIza..."
GROQ_API_KEY         = "gsk_..."
DATABASE_URL         = "postgresql://..."  # من neon.tech
PAYMOB_API_KEY       = "eyJhbGci..."
PAYMOB_HMAC_SECRET   = "..."
PAYMOB_CARD_INTG_ID  = "5586603"
```

---

## 🛡️ الأمان

- تشفير كلمات المرور بـ `bcrypt + SHA-256`
- Secrets بيئية — لا keys مضمّنة في الكود
- HMAC verification لـ Paymob callbacks
- لوحة إدارة مقيّدة للـ Admin فقط

---

## 📞 التواصل

[![WhatsApp](https://img.shields.io/badge/WhatsApp-25D366?style=for-the-badge&logo=whatsapp&logoColor=white)](https://wa.me/201000000000)

---

© 2026 EngiCost AI · جميع الحقوق محفوظة

