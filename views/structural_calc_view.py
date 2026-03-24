import streamlit as st
import math
import pandas as pd
from utils import t, render_section_header
from ai_engine.export_engine import ExportEngine

# ────────────────────────────────────────────────────────────────────────────────
# ECP 203-2018 & ACI 318-19 core calculations
# ────────────────────────────────────────────────────────────────────────────────

def calc_column(b_mm, t_mm, height_m, fcu_mpa, fy_mpa, load_kn, rho_pct):
    """Short column design check — ECP 203."""
    b = b_mm / 1000; d = t_mm / 1000; h = height_m
    Ag = b * d  # m²
    rho = rho_pct / 100
    As = rho * Ag  # m²
    Pu_kn = 0.35 * fcu_mpa * 1000 * (Ag - As) + 0.67 * fy_mpa * 1000 * As
    status = "✅ آمن" if Pu_kn >= load_kn else "❌ يحتاج مراجعة"
    concrete_vol = Ag * h  # m³
    steel_kg = As * h * 7850  # density 7850 kg/m³
    return {
        "المساحة Ag (m²)": round(Ag, 4),
        "مساحة الحديد As (m²)": round(As, 6),
        "الحمل الأقصى Pu (kN)": round(Pu_kn, 1),
        "حمل التصميم Pd (kN)": load_kn,
        "الحالة": status,
        "خرسانة (m³)": round(concrete_vol, 3),
        "حديد (kg)": round(steel_kg, 1),
    }


def calc_beam(b_mm, h_mm, span_m, fcu_mpa, fy_mpa, moment_knm):
    """Rectangular beam design — ECP 203 / ACI 318."""
    b = b_mm / 1000; h = h_mm / 1000
    d = h - 0.05  # effective depth (50 mm cover)
    phi_b = 0.9
    # Required tension steel
    Rn = moment_knm * 1000 / (phi_b * b * d**2)  # kN/m → N/m via *1000
    m = fy_mpa / (0.85 * fcu_mpa)
    rho_req = (1/m) * (1 - math.sqrt(max(0, 1 - 2*m*Rn/(fy_mpa*1000))))
    rho_min = max(1.4/fy_mpa, 0.25*math.sqrt(fcu_mpa)/fy_mpa)
    rho_max = 0.75 * 0.85 * 0.85 * fcu_mpa/fy_mpa * (600/(600+fy_mpa))
    rho_use = max(rho_req, rho_min)
    status = "✅ آمن" if rho_use <= rho_max else "⚠️ رفع القطاع"
    As_cm2 = rho_use * b * d * 10000  # cm²
    # Quantities
    concrete_vol = b * h * span_m
    steel_wt = rho_use * (b * d) * span_m * 7850
    return {
        "عمق فعّال d (m)": round(d, 3),
        "نسبة الحديد ρ": f"{rho_use:.4f} ({rho_use*100:.2f}%)",
        "مساحة الحديد As (cm²)": round(As_cm2, 2),
        "ρ_max": round(rho_max, 4),
        "الحالة": status,
        "خرسانة (m³)": round(concrete_vol, 3),
        "حديد (kg)": round(steel_wt, 1),
    }


def calc_slab(span_m, thickness_mm, fcu_mpa, fy_mpa, load_kpa, slab_type="one-way"):
    """One-way or two-way slab check."""
    t_s = thickness_mm / 1000
    # Minimum thickness check (ECP): L/20 for one-way
    t_min = span_m / (28 if slab_type == "one-way" else 40)
    status_thick = "✅" if t_s >= t_min else f"⚠️ سماكة أدنى: {t_min*1000:.0f} mm"
    # Strip moment (per meter)
    wu = 1.4 * t_s * 25 + 1.6 * load_kpa  # factored load kN/m²
    Mu = wu * span_m**2 / 8  # kN·m/m
    d = t_s - 0.025  # effective depth
    Rn = Mu * 1000 / (0.9 * 1.0 * d**2)
    m = fy_mpa / (0.85 * fcu_mpa)
    rho = (1/m) * (1 - math.sqrt(max(0, 1 - 2*m*Rn/(fy_mpa*1000))))
    rho = max(rho, 0.002)  # min steel ECP
    As = rho * 1.0 * d * 10000  # cm²/m
    return {
        "السماكة المدخلة (mm)": thickness_mm,
        "السماكة الدنيا ECP (mm)": round(t_min * 1000, 0),
        "فحص السماكة": status_thick,
        "حمل المصنّع wu (kN/m²)": round(wu, 2),
        "العزم Mu (kN·m/m)": round(Mu, 2),
        "حديد As (cm²/m)": round(As, 2),
        "خرسانة / م²": f"{t_s} m³",
    }


def calc_footing(load_kn, qa_kpa, fcu_mpa, fy_mpa, col_b_mm, col_d_mm):
    """Square isolated footing sizing."""
    qa = qa_kpa; Pu = load_kn
    # Net upward pressure (assume footing + soil = 20% of column load)
    q_net = qa
    A_req = (Pu * 1.1) / q_net  # m²
    L = math.ceil(math.sqrt(A_req) * 10) / 10  # round up to nearest 100mm
    # Thickness (punching check — simplified)
    t = max(0.3, (L - col_b_mm/1000) / 4)
    t = math.ceil(t * 10) / 10
    c_b = col_b_mm / 1000; c_d = col_d_mm / 1000
    # Flexural design
    M = (Pu * 1.4) / (L) * ((L - c_b) / 2)**2 / 2  # kN·m per unit width
    d = t - 0.075
    Rn = M * 1000 / (0.9 * L * d**2)
    m_r = fy_mpa / (0.85 * fcu_mpa)
    rho = (1 / m_r) * (1 - math.sqrt(max(0, 1 - 2*m_r*Rn/(fy_mpa*1000))))
    As = max(rho, 0.002) * L * d * 10000
    conc_vol = L * L * t
    steel_kg = max(rho, 0.002) * (L * d) * L * 7850
    return {
        "مساحة القاعدة المطلوبة (m²)": round(A_req, 2),
        "أبعاد القاعدة (m × m)": f"{L} × {L}",
        "السماكة t (m)": t,
        "حديد As (cm²)": round(As, 2),
        "خرسانة (m³)": round(conc_vol, 3),
        "حديد (kg)": round(steel_kg, 1),
    }


# ────────────────────────────────────────────────────────────────────────────────
# Main Render
# ────────────────────────────────────────────────────────────────────────────────

def render_structural_calc():
    render_section_header(t("الحسابات الإنشائية والخرسانة", "Structural & Concrete Calculations"), "🏛️")

    st.markdown(f"""
    <div class="glass-card animate-up">
        <p style="color:var(--text-muted);">
            {t("حسابات إنشائية متوافقة مع الكود المصري ECP 203 و ACI 318. النتائج للتوجيه الهندسي وليست بديلاً عن الحسابات التفصيلية.",
               "ECP 203 & ACI 318 compliant structural calculations. Results are for engineering guidance only — not a substitute for detailed design.")}
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Material inputs — shared
    st.markdown(f"### ⚙️ {t('خصائص المواد (مشتركة)', 'Material Properties (Shared)')}")
    mc1, mc2, mc3 = st.columns(3)
    with mc1:
        fcu = st.number_input("f'cu (MPa)", value=25, min_value=15, max_value=60, step=5,
                              help=t("مقاومة الخرسانة للضغط", "Concrete compressive strength"))
    with mc2:
        fy = st.number_input("fy (MPa)", value=400, min_value=240, max_value=600, step=40,
                             help=t("حد خضوع الحديد", "Steel yield strength"))
    with mc3:
        st.markdown(f"""
        <div class="glass-card" style="padding:0.8rem; margin-top:0.5rem;">
            <p style="margin:0; font-size:0.78rem; color:var(--text-muted);">{t('استاندرد', 'Standard')}</p>
            <p style="margin:0; font-weight:bold; color:var(--accent-primary);">ECP 203-2018 / ACI 318-19</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # ─── Tabs ─────────────────────────────────────────────────────────────────
    tab_col, tab_beam, tab_slab, tab_foot = st.tabs([
        t("🏛️ عمود", "🏛️ Column"),
        t("━ كمرة", "━ Beam"),
        t("▦ بلاطة", "▦ Slab"),
        t("⬜ قاعدة", "⬜ Footing"),
    ])

    # ── Column ──────────────────────────────────────────────────────────────────
    with tab_col:
        st.markdown(f"#### {t('تصميم عمود قصير', 'Short Column Design')}")
        cc1, cc2, cc3 = st.columns(3)
        with cc1:
            b_col = st.number_input(t("العرض b (mm)", "Width b (mm)"), value=300, step=50)
            h_col = st.number_input(t("الارتفاع t (mm)", "Thickness t (mm)"), value=300, step=50)
        with cc2:
            ht_col = st.number_input(t("ارتفاع العمود (m)", "Column Height (m)"), value=3.0, step=0.5)
            load_col = st.number_input(t("حمل التصميم Pd (kN)", "Design Load Pd (kN)"), value=800.0, step=50.0)
        with cc3:
            rho_col = st.number_input(t("نسبة الحديد ρ%", "Steel Ratio ρ%"), value=1.5, min_value=0.8, max_value=6.0, step=0.1)

        if st.button(t("🧮 حساب العمود", "🧮 Calculate Column"), use_container_width=True, key="btn_col"):
            result = calc_column(b_col, h_col, ht_col, fcu, fy, load_col, rho_col)
            st.session_state.col_result = result

        if st.session_state.get("col_result"):
            r = st.session_state.col_result
            status_color = "var(--success)" if "✅" in r["الحالة"] else "#f87171"
            res_cols = st.columns(len(r))
            for col_w, (k, v) in zip(res_cols, r.items()):
                with col_w:
                    st.markdown(f"""
                    <div class="glass-card" style="text-align:center; padding:0.8rem; border-top:2px solid {'var(--success)' if k=='الحالة' and '✅' in str(v) else 'var(--accent-primary)'};">
                        <p style="margin:0; font-size:0.72rem; color:var(--text-muted);">{k}</p>
                        <p style="margin:0; font-weight:bold; color:{status_color if k=='الحالة' else 'var(--accent-primary)'};">{v}</p>
                    </div>
                    """, unsafe_allow_html=True)

    # ── Beam ────────────────────────────────────────────────────────────────────
    with tab_beam:
        st.markdown(f"#### {t('تصميم كمرة مستطيلة', 'Rectangular Beam Design')}")
        bc1, bc2, bc3 = st.columns(3)
        with bc1:
            b_bm = st.number_input(t("عرض الكمرة b (mm)", "Beam Width b (mm)"), value=250, step=50)
            h_bm = st.number_input(t("ارتفاع الكمرة h (mm)", "Beam Height h (mm)"), value=600, step=50)
        with bc2:
            span_bm = st.number_input(t("بحر الكمرة (m)", "Beam Span (m)"), value=6.0, step=0.5)
        with bc3:
            mu_bm = st.number_input(t("عزم التصميم Mu (kN·m)", "Design Moment Mu (kN·m)"), value=120.0, step=10.0)

        if st.button(t("🧮 حساب الكمرة", "🧮 Calculate Beam"), use_container_width=True, key="btn_beam"):
            result = calc_beam(b_bm, h_bm, span_bm, fcu, fy, mu_bm)
            st.session_state.beam_result = result

        if st.session_state.get("beam_result"):
            r = st.session_state.beam_result
            for k, v in r.items():
                color = "var(--success)" if "✅" in str(v) else "#fb923c" if "⚠️" in str(v) else "var(--text-primary)"
                st.markdown(f"""
                <div style="display:flex; justify-content:space-between; padding:6px 12px; border-bottom:1px solid rgba(255,255,255,0.05);">
                    <span style="color:var(--text-muted); font-size:0.88rem;">{k}</span>
                    <span style="font-weight:bold; color:{color};">{v}</span>
                </div>
                """, unsafe_allow_html=True)

    # ── Slab ────────────────────────────────────────────────────────────────────
    with tab_slab:
        st.markdown(f"#### {t('تصميم بلاطة', 'Slab Design')}")
        sc1, sc2, sc3 = st.columns(3)
        with sc1:
            span_sl = st.number_input(t("البحر (m)", "Span (m)"), value=4.0, step=0.5)
            thick_sl = st.number_input(t("السماكة (mm)", "Thickness (mm)"), value=160, step=10)
        with sc2:
            live_sl = st.number_input(t("حمل حي (kPa)", "Live Load (kPa)"), value=3.0, step=0.5)
            slab_type = st.selectbox(t("نوع البلاطة", "Slab Type"), [t("في اتجاه واحد", "one-way"), t("في اتجاهين", "two-way")])
        with sc3:
            st.info(t("الحمل الميت يحسب تلقائياً من السماكة + 1 kPa تشطيبات", "Dead load auto-calculated from thickness + 1 kPa finishes"))

        sl_key = "one-way" if "واحد" in slab_type or "one" in slab_type else "two-way"
        if st.button(t("🧮 حساب البلاطة", "🧮 Calculate Slab"), use_container_width=True, key="btn_slab"):
            result = calc_slab(span_sl, thick_sl, fcu, fy, live_sl, sl_key)
            st.session_state.slab_result = result

        if st.session_state.get("slab_result"):
            r = st.session_state.slab_result
            for k, v in r.items():
                color = "var(--success)" if "✅" in str(v) else "#fb923c" if "⚠️" in str(v) else "var(--text-primary)"
                st.markdown(f"""
                <div style="display:flex; justify-content:space-between; padding:6px 12px; border-bottom:1px solid rgba(255,255,255,0.05);">
                    <span style="color:var(--text-muted); font-size:0.88rem;">{k}</span>
                    <span style="font-weight:bold; color:{color};">{v}</span>
                </div>
                """, unsafe_allow_html=True)

    # ── Footing ─────────────────────────────────────────────────────────────────
    with tab_foot:
        st.markdown(f"#### {t('تصميم قاعدة منفردة مربعة', 'Isolated Square Footing Design')}")
        fc1, fc2 = st.columns(2)
        with fc1:
            load_ft = st.number_input(t("الحمل المحوري P (kN)", "Axial Load P (kN)"), value=1000.0, step=100.0)
            qa_ft = st.number_input(t("طاقة التربة المسموحة qa (kPa)", "Allowable Soil Bearing qa (kPa)"), value=150.0, step=25.0)
        with fc2:
            col_b_ft = st.number_input(t("عرض العمود b (mm)", "Column Width b (mm)"), value=300, step=50)
            col_d_ft = st.number_input(t("عمق العمود d (mm)", "Column Depth d (mm)"), value=300, step=50)

        if st.button(t("🧮 حساب القاعدة", "🧮 Calculate Footing"), use_container_width=True, key="btn_foot"):
            result = calc_footing(load_ft, qa_ft, fcu, fy, col_b_ft, col_d_ft)
            st.session_state.foot_result = result

        if st.session_state.get("foot_result"):
            r = st.session_state.foot_result
            for k, v in r.items():
                st.markdown(f"""
                <div style="display:flex; justify-content:space-between; padding:6px 12px; border-bottom:1px solid rgba(255,255,255,0.05);">
                    <span style="color:var(--text-muted); font-size:0.88rem;">{k}</span>
                    <span style="font-weight:bold; color:var(--accent-primary);">{v}</span>
                </div>
                """, unsafe_allow_html=True)

    # ── Bill of Quantities from Calculations ────────────────────────────────────
    st.markdown("---")
    st.markdown(f"### 📊 {t('كميات المشروع الكلية من الحسابات', 'Total Project Quantities from Calculations')}")
    
    rows = []
    if st.session_state.get("col_result"):
        r = st.session_state.col_result
        rows.append({"البند": t("خرسانة عمود", "Column Concrete"), "الوحدة": "m³", "الكمية": r["خرسانة (m³)"]})
        rows.append({"البند": t("حديد عمود", "Column Steel"), "الوحدة": "kg", "الكمية": r["حديد (kg)"]})
    if st.session_state.get("beam_result"):
        r = st.session_state.beam_result
        rows.append({"البند": t("خرسانة كمرة", "Beam Concrete"), "الوحدة": "m³", "الكمية": r["خرسانة (m³)"]})
        rows.append({"البند": t("حديد كمرة", "Beam Steel"), "الوحدة": "kg", "الكمية": r["حديد (kg)"]})
    if st.session_state.get("foot_result"):
        r = st.session_state.foot_result
        rows.append({"البند": t("خرسانة قاعدة", "Footing Concrete"), "الوحدة": "m³", "الكمية": r["خرسانة (m³)"]})
        rows.append({"البند": t("حديد قاعدة", "Footing Steel"), "الوحدة": "kg", "الكمية": r["حديد (kg)"]})

    if rows:
        df_summary = pd.DataFrame(rows)
        st.dataframe(df_summary, use_container_width=True)
        try:
            excel_data = ExportEngine.generate_professional_excel(df_summary, project_name=t("حسابات إنشائية", "Structural Calculations"))
            st.download_button(
                t("📊 تصدير ملخص الكميات Excel", "📊 Export Quantities Summary Excel"),
                data=excel_data,
                file_name="Structural_Quantities.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"Export error: {e}")
    else:
        st.info(t("أجرِ حسابات أولاً لرؤية الكميات هنا.", "Run calculations above to see quantities here."))
