import streamlit as st
import time
from utils import t, render_section_header

try:
    from ai_engine.rag_engine import retrieve_context, build_rag_prompt, get_template_for_project
    RAG_AVAILABLE = True
except Exception as e:
    RAG_AVAILABLE = False
    _rag_error = str(e)

try:
    from ai_engine.cost_engine import CostEngine
    _cost_engine = CostEngine()
except Exception:
    _cost_engine = None


def render_ai_brain():
    render_section_header(t("العقل الهندسي الذكي", "AI Engineering Brain"), "🧠")

    lang = st.session_state.get("lang", "ar")

    # ── Header Badge ──────────────────────────────────────────────────────────
    st.markdown(f"""
    <div style="display:flex; align-items:center; gap:1rem; margin-bottom:1.5rem; flex-wrap:wrap;">
        <div style="background:linear-gradient(135deg,rgba(14,165,233,0.15),rgba(99,102,241,0.15));
                    border:1px solid rgba(14,165,233,0.4); border-radius:12px; padding:0.6rem 1.2rem;">
            <span style="color:#0ea5e9; font-weight:700; font-size:0.85rem;">⚡ RAG Engine v1.0</span>
        </div>
        <div style="background:rgba(16,185,129,0.1); border:1px solid rgba(16,185,129,0.3);
                    border-radius:12px; padding:0.6rem 1.2rem;">
            <span style="color:#10b981; font-size:0.85rem;">
                📚 {t('قاعدة معرفة: أسعار 2026 + ECP 203 + قوالب مقايسات + أسئلة شائعة',
                       'Knowledge Base: 2026 Prices + ECP 203 + BOQ Templates + FAQs')}
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if not RAG_AVAILABLE:
        st.error(f"⚠️ RAG Engine Error: {_rag_error}")
        return

    # ── Tabs ──────────────────────────────────────────────────────────────────
    tab_chat, tab_boq_gen, tab_kb = st.tabs([
        "🧠 " + t("دردشة هندسية", "Engineering Chat"),
        "📋 " + t("مقايسة من وصف", "BOQ from Description"),
        "📚 " + t("قاعدة المعرفة", "Knowledge Base"),
    ])

    # ════════════════════════════════════════════════════════════════════════
    # TAB 1 — ENGINEERING CHAT
    # ════════════════════════════════════════════════════════════════════════
    with tab_chat:
        st.markdown(f"##### 💬 {t('اسأل أي سؤال هندسي...', 'Ask any engineering question...')}")

        # Suggested questions
        st.markdown(f"**{t('أسئلة مقترحة:', 'Suggested questions:')}**")
        cols = st.columns(3)
        suggestions_ar = [
            "ما سعر متر الخرسانة M300 الآن؟",
            "كم يجب أن يكون الغطاء الخرساني؟",
            "ما تكلفة بناء فيلا 200م2؟",
            "ما نسبة حديد الأعمدة؟",
            "ما سعر طن الحديد 2026؟",
            "ما أجر المهندس المشرف؟"
        ]
        suggestions_en = [
            "What is M300 concrete price now?",
            "What is the required concrete cover?",
            "How much to build a 200m2 villa?",
            "What is the column steel ratio?",
            "What is rebar price in 2026?",
            "What is a site engineer's salary?"
        ]
        suggestions = suggestions_ar if lang == "ar" else suggestions_en

        for i, (col, sug) in enumerate(zip(cols * 2, suggestions)):
            with col:
                if st.button(sug, key=f"sug_{i}", use_container_width=True):
                    st.session_state["brain_prefill"] = sug

        st.markdown("---")

        # Chat history init
        if "brain_chat" not in st.session_state:
            st.session_state.brain_chat = []

        # Display chat history
        for msg in st.session_state.brain_chat:
            role = msg["role"]
            with st.chat_message(role, avatar="🧠" if role == "assistant" else "👤"):
                st.markdown(msg["content"])
                if role == "assistant" and msg.get("sources"):
                    _render_sources(msg["sources"])

        # Input
        prefill = st.session_state.pop("brain_prefill", "")
        query = st.chat_input(
            t("اكتب سؤالك الهندسي هنا...", "Type your engineering question here..."),
            key="brain_input"
        )
        if prefill:
            query = prefill

        if query:
            # Add user message
            st.session_state.brain_chat.append({"role": "user", "content": query})
            with st.chat_message("user", avatar="👤"):
                st.markdown(query)

            # RAG Retrieval
            with st.chat_message("assistant", avatar="🧠"):
                with st.spinner(t("🔎 جاري البحث في قاعدة المعرفة...", "🔎 Searching knowledge base...")):
                    context, sources = retrieve_context(query, lang=lang)

                if sources:
                    st.caption(t(
                        f"✅ تم العثور على {len(sources)} مصدر هندسي متعلق",
                        f"✅ Found {len(sources)} relevant engineering sources"
                    ))

                # Build RAG prompt and call LLM
                rag_prompt = build_rag_prompt(query, context, lang=lang)

                with st.spinner(t("🤖 العقل يُفكر ويُحلل...", "🤖 Thinking and analyzing...")):
                    answer = _call_llm(rag_prompt)

                st.markdown(answer)
                if sources:
                    _render_sources(sources)

                st.session_state.brain_chat.append({
                    "role": "assistant",
                    "content": answer,
                    "sources": sources
                })

        # Clear chat button
        if st.session_state.brain_chat:
            if st.button(t("🗑️ مسح المحادثة", "🗑️ Clear Chat"), key="clear_brain_chat"):
                st.session_state.brain_chat = []
                st.rerun()

    # ════════════════════════════════════════════════════════════════════════
    # TAB 2 — Auto BOQ Generator
    # ════════════════════════════════════════════════════════════════════════
    with tab_boq_gen:
        st.markdown(f"##### 📋 {t('توليد مقايسة تلقائية من وصف المشروع', 'Auto-generate BOQ from project description')}")

        st.info(t(
            "✏️ اكتب وصفاً للمشروع وسيولّد العقل مقايسة تقديرية كاملة تلقائياً",
            "✏️ Describe your project and the AI Brain will auto-generate a full BOQ"
        ))

        col1, col2 = st.columns([3, 1])
        with col1:
            project_desc = st.text_area(
                t("وصف المشروع", "Project Description"),
                placeholder=t(
                    "مثال: فيلا سكنية 300م2 طابقين، تشطيب كامل، مدخل شمالي، حمامان...",
                    "Example: 300m2 residential villa, 2 floors, full finish, north entrance, 2 bathrooms..."
                ),
                height=100,
                key="boq_desc_input"
            )
        with col2:
            area_m2 = st.number_input(
                t("المساحة الإجمالية (م2)", "Total Area (m2)"),
                min_value=50, max_value=10000, value=200, step=50,
                key="boq_area"
            )
            floors = st.number_input(
                t("عدد الطوابق", "Number of Floors"),
                min_value=1, max_value=20, value=2, step=1,
                key="boq_floors"
            )

        if st.button(t("🚀 توليد المقايسة الآن", "🚀 Generate BOQ Now"), type="primary", use_container_width=True, key="gen_boq_brain"):
            if project_desc:
                with st.spinner(t("🧠 العقل يحلل المشروع ويولد المقايسة...", "🧠 Brain analyzing project and generating BOQ...")):
                    template = get_template_for_project(project_desc)

                if template:
                    st.success(t(
                        f"✅ تم تحديد قالب: **{template.get('name_ar', '')}**",
                        f"✅ Template matched: **{template.get('name_en', '')}**"
                    ))

                    # Calculate items using template formulas
                    items_data = []
                    total_cost = 0
                    for tmpl_item in template.get("items", []):
                        try:
                            formula = tmpl_item.get("quantity_formula", "0")
                            qty = float(eval(formula, {"area_m2": area_m2, "floors": floors, "__builtins__": {}}))
                            rate = float(tmpl_item.get("rate_egp", 0))
                            total_item = qty * rate
                            total_cost += total_item
                            items_data.append({
                                t("البند", "Item"): tmpl_item.get("item", ""),
                                t("الوحدة", "Unit"): tmpl_item.get("unit", ""),
                                t("الكمية", "Qty"): round(qty, 2),
                                t("السعر (EGP)", "Rate (EGP)"): f"{rate:,.0f}",
                                t("الإجمالي (EGP)", "Total (EGP)"): f"{total_item:,.0f}"
                            })
                        except Exception:
                            continue

                    if items_data:
                        import pandas as pd
                        df = pd.DataFrame(items_data)
                        st.dataframe(df, use_container_width=True, hide_index=True)

                        # Summary
                        vat = total_cost * 0.14
                        grand = total_cost + vat
                        colA, colB, colC = st.columns(3)
                        colA.metric(t("الإجمالي قبل الضريبة", "Subtotal"), f"{total_cost:,.0f} EGP")
                        colB.metric(t("ضريبة القيمة 14%", "VAT 14%"), f"{vat:,.0f} EGP")
                        colC.metric(t("الإجمالي الكلي", "Grand Total"), f"{grand:,.0f} EGP")

                        st.caption(t(
                            "⚠️ هذه أرقام تقديرية بناءً على قوالب معيارية. استخدم أداة المقايسة الكاملة للتسعير الدقيق.",
                            "⚠️ These are estimates based on standard templates. Use the full BOQ tool for accurate pricing."
                        ))
                else:
                    st.warning(t(
                        "لم يُعثَر على قالب مناسب. جرّب وصفاً أوضح مثل: فيلا، عمارة، مستودع، محل تجاري",
                        "No matching template found. Try: villa, building, warehouse, retail"
                    ))
            else:
                st.warning(t("يرجى كتابة وصف للمشروع أولاً", "Please enter a project description first"))

    # ════════════════════════════════════════════════════════════════════════
    # TAB 3 — Knowledge Base Explorer
    # ════════════════════════════════════════════════════════════════════════
    with tab_kb:
        st.markdown(f"##### 📚 {t('استعراض قاعدة المعرفة الهندسية', 'Browse Engineering Knowledge Base')}")

        import json, os
        kb_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "knowledge")

        kb_files = {
            "💰 " + t("أسعار مواد البناء 2026", "Construction Prices 2026"): "prices.json",
            "📐 " + t("كود البناء المصري ECP 203", "Egyptian Building Code ECP 203"): "ecp_codes.json",
            "📋 " + t("قوالب المقايسات", "BOQ Templates"): "boq_templates.json",
            "❓ " + t("أسئلة شائعة", "FAQs"): "faqs.json",
        }

        selected = st.selectbox(t("اختر قاعدة المعرفة", "Select Knowledge Base"), list(kb_files.keys()), key="kb_selector")
        filename = kb_files[selected]

        try:
            with open(os.path.join(kb_dir, filename), "r", encoding="utf-8") as f:
                kb_data = json.load(f)

            st.caption(f"📁 {filename} | {t('المصدر:', 'Source:')} {kb_data.get('source', kb_data.get('description', '-'))}")

            if filename == "prices.json":
                for cat_key, cat in kb_data.get("categories", {}).items():
                    with st.expander(f"{cat.get('label_ar', cat_key)} | {cat.get('label_en', '')}"):
                        rows = []
                        for item in cat.get("items", []):
                            rows.append({
                                t("الصنف", "Item"): item.get("name_ar", ""),
                                t("الوحدة", "Unit"): item.get("unit", ""),
                                t("أدنى", "Min"): f"{item.get('price_min', 0):,}",
                                t("متوسط", "Avg"): f"{item.get('price_avg', 0):,}",
                                t("أعلى", "Max"): f"{item.get('price_max', 0):,}",
                            })
                        if rows:
                            import pandas as pd
                            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

            elif filename == "faqs.json":
                for faq in kb_data.get("faqs", []):
                    with st.expander(faq.get("question_ar", "")):
                        st.markdown(faq.get("answer_ar", ""))
                        st.caption(f"📌 {faq.get('source', '')}")

            elif filename == "ecp_codes.json":
                for sec_key, section in kb_data.get("sections", {}).items():
                    with st.expander(f"📐 {section.get('title_ar', sec_key)}"):
                        for rule in section.get("rules", []):
                            st.markdown(f"- **[{rule.get('id', '')}]** {rule.get('rule_ar', '')}")
                            st.caption(f"  📖 {rule.get('reference', '')}")

            else:
                st.json(kb_data)

        except Exception as e:
            st.error(f"Error loading {filename}: {e}")


# ── Helpers ────────────────────────────────────────────────────────────────────

def _render_sources(sources: list):
    """Render source citations for an AI answer."""
    if not sources:
        return
    cols = st.columns(min(len(sources), 3))
    for i, src in enumerate(sources[:3]):
        with cols[i]:
            st.markdown(f"""
            <div style="background:rgba(14,165,233,0.08); border:1px solid rgba(14,165,233,0.25);
                        border-radius:10px; padding:0.5rem 0.7rem; font-size:0.78rem; margin-top:0.5rem;">
                <b>{src.get('icon', '📌')} {src.get('type', 'مصدر')}</b><br>
                {src.get('title', '')[:50]}...<br>
                <span style="color:#64748b; font-size:0.7rem;">📁 {src.get('source', '')}</span>
            </div>
            """, unsafe_allow_html=True)


def _call_llm(prompt: str) -> str:
    """Call the LLM with the RAG-enriched prompt."""
    if _cost_engine is None:
        return t(
            "⚠️ محرك الذكاء الاصطناعي غير متاح. تحقق من إعداد المفاتيح في الإعدادات.",
            "⚠️ AI engine unavailable. Check API keys in Settings."
        )

    try:
        result, error = _cost_engine._call_groq(prompt, expect_json=False)
        if result:
            return str(result)
        if error:
            # Fallback to Gemini
            result2, error2 = _cost_engine._call_gemini(prompt, expect_json=False) if hasattr(_cost_engine, '_call_gemini') else (None, "No Gemini")
            if result2:
                return str(result2)
            return t(
                f"⚠️ تعذّر الحصول على إجابة: {error}",
                f"⚠️ Could not get answer: {error}"
            )
    except AttributeError:
        # Fallback: try calling generically
        try:
            import groq as g
            import os
            key = os.environ.get("GROQ_API_KEY") or ""
            if key:
                client = g.Groq(api_key=key)
                resp = client.chat.completions.create(
                    model="llama-3.1-70b-versatile",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=1000
                )
                return resp.choices[0].message.content
        except Exception as e:
            return t(f"⚠️ خطأ في الاتصال: {str(e)}", f"⚠️ Connection error: {str(e)}")

    return t("⚠️ لم يتم الحصول على إجابة.", "⚠️ No answer received.")
