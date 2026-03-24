import streamlit as st
import pandas as pd
from utils import t, render_section_header
from ai_engine.cost_engine import get_cost_engine

def render_boq_comparison():
    render_section_header(t("مقارنة عروض الأسعار", "BOQ Price Comparison Tool"), "⚖️")

    st.markdown(f"""
    <div class="glass-card animate-up">
        <p style="color:var(--text-muted);">
            {t("قارن بين عرضي مقاولين مختلفين لنفس المشروع واعرف الفرق في كل بند بسهولة.",
               "Compare two contractor offers for the same project and see the price difference per item instantly.")}
        </p>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs([
        t("📤 إدخال البيانات", "📤 Input Data"),
        t("📊 نتائج المقارنة", "📊 Comparison Results"),
    ])

    with tab1:
        col_a, col_b = st.columns(2)

        with col_a:
            st.markdown(f"#### 🏗️ {t('العرض الأول', 'Offer A')}")
            label_a = st.text_input(t("اسم المقاول/العرض أ", "Contractor/Offer A Name"), t("المقاول أ", "Contractor A"), key="cmp_label_a")
            boq_text_a = st.text_area(
                t("الصق نص المقايسة أو وصف البنود", "Paste BOQ items or description"),
                height=200, key="cmp_boq_a",
                placeholder=t("مثال:\nخرسانة مسلحة 500 م3\nحديد تسليح 50 طن", "Example:\nReinforced concrete 500 m3\nRebar 50 ton")
            )
            file_a = st.file_uploader(t("أو ارفع ملف Excel/PDF", "Or upload Excel/PDF"), type=["pdf", "xlsx", "txt"], key="cmp_file_a")

        with col_b:
            st.markdown(f"#### 🏗️ {t('العرض الثاني', 'Offer B')}")
            label_b = st.text_input(t("اسم المقاول/العرض ب", "Contractor/Offer B Name"), t("المقاول ب", "Contractor B"), key="cmp_label_b")
            boq_text_b = st.text_area(
                t("الصق نص المقايسة أو وصف البنود", "Paste BOQ items or description"),
                height=200, key="cmp_boq_b",
                placeholder=t("مثال:\nخرسانة مسلحة 500 م3\nحديد تسليح 55 طن", "Example:\nReinforced concrete 500 m3\nRebar 55 ton")
            )
            file_b = st.file_uploader(t("أو ارفع ملف Excel/PDF", "Or upload Excel/PDF"), type=["pdf", "xlsx", "txt"], key="cmp_file_b")

        global_currency = st.session_state.get("currency", "USD")
        currency_options = ["USD", "EGP", "SAR", "AED", "QAR", "GBP", "KWD", "OMR", "BHD", "EUR"]
        
        currency = st.selectbox(
            t("العملة", "Currency"), 
            currency_options,
            index=currency_options.index(global_currency) if global_currency in currency_options else 0,
            key="cmp_currency"
        )
        sym = f" {currency} "

        if st.button(t("🤖 مقارنة بالذكاء الاصطناعي", "🤖 Compare with AI"), use_container_width=True):
            src_a = boq_text_a or (file_a.read().decode("utf-8", errors="ignore") if file_a else "")
            src_b = boq_text_b or (file_b.read().decode("utf-8", errors="ignore") if file_b else "")

            if not src_a or not src_b:
                st.warning(t("الرجاء إدخال بيانات للعرضين.", "Please provide data for both offers."))
            else:
                engine = get_cost_engine()
                with st.spinner(t("جارٍ التحليل والتسعير...", "Analyzing and pricing...")):
                    items_a = engine.suggest_market_prices(engine.extract_boq_items(src_a))
                    items_b = engine.suggest_market_prices(engine.extract_boq_items(src_b))

                    raw_a = engine.extract_boq_items(src_a)
                    raw_b = engine.extract_boq_items(src_b)

                    # Merge by index for comparison
                    rows = []
                    max_len = max(len(raw_a), len(raw_b))
                    for i in range(max_len):
                        ra = raw_a[i] if i < len(raw_a) else {}
                        rb = raw_b[i] if i < len(raw_b) else {}
                        price_a = float(items_a.get(str(i), 0) or 0) * float(ra.get("quantity", 1) or 1)
                        price_b = float(items_b.get(str(i), 0) or 0) * float(rb.get("quantity", 1) or 1)
                        diff = price_b - price_a
                        rows.append({
                            t("البند", "Item"): ra.get("item") or rb.get("item", f"Item {i+1}"),
                            t("الوحدة", "Unit"): ra.get("unit", ""),
                            t("الكمية", "Qty"): ra.get("quantity", 0),
                            f"{label_a} ({sym})": round(price_a, 2),
                            f"{label_b} ({sym})": round(price_b, 2),
                            t("الفرق", "Diff"): round(diff, 2),
                        })

                    st.session_state.cmp_result = {
                        "rows": rows,
                        "label_a": label_a,
                        "label_b": label_b,
                        "sym": sym,
                    }
                st.rerun()

    with tab2:
        if not st.session_state.get("cmp_result"):
            st.info(t("قم بإدخال البيانات وانقر على مقارنة أولاً.", "Enter data and click Compare first."))
        else:
            r = st.session_state.cmp_result
            df = pd.DataFrame(r["rows"])
            sy = r["sym"]
            la, lb = r["label_a"], r["label_b"]

            # Highlight rows where A is cheaper in green, B cheaper in yellow
            diff_col = t("الفرق", "Diff")

            def highlight_row(row):
                color = ""
                if diff_col in row:
                    if row[diff_col] > 0:
                        color = "background-color: rgba(74,222,128,0.12)"  # A is cheaper
                    elif row[diff_col] < 0:
                        color = "background-color: rgba(251,146,60,0.12)"  # B is cheaper
                return [color] * len(row)

            st.dataframe(df.style.apply(highlight_row, axis=1), use_container_width=True)

            # Summary KPIs
            try:
                total_a = df[f"{la} ({sy})"].sum()
                total_b = df[f"{lb} ({sy})"].sum()
                saving = abs(total_b - total_a)
                winner = la if total_a < total_b else lb
            except Exception:
                total_a = total_b = saving = 0
                winner = "N/A"

            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric(f"💰 {la}", f"{sy} {total_a:,.2f}")
            with c2:
                st.metric(f"💰 {lb}", f"{sy} {total_b:,.2f}")
            with c3:
                st.metric(t("🏆 الأوفر", "🏆 Best Value"), winner,
                          delta=f"{sy} {saving:,.2f} {t('فرق', 'difference')}")

            # Export comparison as Excel
            try:
                from ai_engine.export_engine import ExportEngine
                excel_bytes = ExportEngine.generate_professional_excel(df, project_name="BOQ Comparison")
                st.download_button(
                    t("📊 تصدير المقارنة Excel", "📊 Export Comparison Excel"),
                    data=excel_bytes,
                    file_name="BOQ_Comparison.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"Export error: {e}")
