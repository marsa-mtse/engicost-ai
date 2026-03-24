import streamlit as st
import pandas as pd
import json
import datetime
import plotly.express as px
import plotly.graph_objects as go
from utils import t, render_section_header
from database import SessionLocal, User, Project

@st.cache_data(ttl=600)
def get_user_projects(username: str):
    """Fetch all saved projects for the logged-in user with caching."""
    try:
        db = SessionLocal()
        user = db.query(User).filter(User.username == username).first()
        if not user:
            return []
        projects = db.query(Project).filter(Project.owner_id == user.id).order_by(Project.created_at.desc()).all()
        return projects
    except Exception:
        return []
    finally:
        db.close()

@st.cache_data(ttl=300)
def get_user_stats(username: str):
    """Fetch user-specific stats with caching."""
    try:
        db = SessionLocal()
        user = db.query(User).filter(User.username == username).first()
        if user:
            return {
                "blueprints": user.blueprints_analyzed,
                "boqs": user.boqs_generated
            }
        return {"blueprints": 0, "boqs": 0}
    except Exception:
        return {"blueprints": 0, "boqs": 0}
    finally:
        db.close()


def render_dashboard():
    render_section_header(t("لوحة القيادة والمشاريع", "Dashboard & Projects"), "📊")

    # ─── V1.6.0: Tender Deadline Alerts Banner ───────────────────
    try:
        from services.tender_fetcher import fetch_live_tenders
        import datetime
        tenders = fetch_live_tenders()
        urgent = [t_item for t_item in tenders if "عاجل" in str(t_item.get("status", ""))]
        closing_soon = [t_item for t_item in tenders if "قريباً" in str(t_item.get("status", ""))]
        
        if urgent:
            names = ", ".join([t_item.get('title_ar', '')[:30] for t_item in urgent[:3]])
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, rgba(239,68,68,0.2), rgba(239,68,68,0.05)); 
                        border: 1px solid rgba(239,68,68,0.5); border-radius: 12px; padding: 0.75rem 1.2rem; 
                        margin-bottom: 1rem; display:flex; align-items:center; gap:1rem;">
                <span style="font-size:1.5rem;">🚨</span>
                <div>
                    <strong style="color:#fca5a5;">{t('عطاء(ت) عاجلة جداً — أقل من 7 أيام!', 'URGENT Tenders — Less than 7 days left!')}</strong><br>
                    <span style="color:#fda4af; font-size:0.85rem;">{names}...</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        elif closing_soon:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, rgba(245,158,11,0.2), rgba(245,158,11,0.05)); 
                        border: 1px solid rgba(245,158,11,0.4); border-radius: 12px; padding: 0.75rem 1.2rem; 
                        margin-bottom: 1rem; display:flex; align-items:center; gap:1rem;">
                <span style="font-size:1.5rem;">⚠️</span>
                <span style="color:#fcd34d;">{t(f'{len(closing_soon)} عطاء تقترب مواعيدها خلال 15 يوم. تحقق من متجر العطاءات!', f'{len(closing_soon)} tenders closing in 15 days. Check Tender Hub!')}</span>
            </div>
            """, unsafe_allow_html=True)
    except Exception:
        pass  # Don't break dashboard if tenders fail


    # ─── Usage Stats & Projects ──────────────────────────────────
    stats = get_user_stats(st.session_state.username)
    b_count = stats["blueprints"]
    boq_count = stats["boqs"]

    projects = get_user_projects(st.session_state.username)
    proj_count = len(projects)

    # KPI Cards
    col1, col2, col3, col4 = st.columns(4)
    kpis = [
        ("📐", t("مخططات محللة", "Blueprints Analyzed"), b_count, "hsl(200, 95%, 60%)", "rgba(14, 165, 233, 0.1)"),
        ("💰", t("مقايسات مسعرة", "Priced BOQs"), boq_count, "hsl(160, 80%, 50%)", "rgba(16, 185, 129, 0.1)"),
        ("📁", t("مشاريع محفوظة", "Saved Projects"), proj_count, "hsl(260, 90%, 70%)", "rgba(167, 139, 250, 0.1)"),
        ("🏆", t("الباقة الحالية", "Current Plan"), st.session_state.plan, "hsl(30, 90%, 60%)", "rgba(251, 146, 60, 0.1)"),
    ]
    for col, (icon, label, val, color, bg) in zip([col1, col2, col3, col4], kpis):
        with col:
            st.markdown(f"""
            <div class="glass-card animate-up" style="text-align:center; padding: 1.5rem 1rem; position:relative; overflow:hidden;">
                <div style="position:absolute; top:-10px; right:-10px; font-size:4rem; opacity:0.05;">{icon}</div>
                <div style="background:{bg}; width:45px; height:45px; border-radius:12px; display:flex; align-items:center; justify-content:center; margin:0 auto 12px auto; border:1px solid {color}33;">
                    <span style="font-size:1.4rem;">{icon}</span>
                </div>
                <h2 style="margin:0; color:{color}; font-size:2.2rem; font-weight:800; font-family:'Outfit';">{val}</h2>
                <p style="margin:4px 0 0 0; color:var(--text-secondary); font-size:0.85rem; font-weight:500;">{label}</p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ─── Quick Project Creation ──────────────────────────────────
    with st.expander(f"➕ {t('إنشاء مشروع جديد سريع', 'Create New Quick Project')}"):
        with st.form("quick_project_form"):
            new_p_name = st.text_input(t("اسم المشروع", "Project Name"), placeholder=t("مثلاً: فيلا التجمع الخامس", "e.g. Fifth Settlement Villa"))
            p_type = st.selectbox(t("نوع المشروع", "Project Type"), options=["BOQ", "Blueprint"])
            
            p_submit = st.form_submit_button(t("حفظ المشروع", "Save Project"))
            if p_submit and new_p_name:
                db = None
                try:
                    db = SessionLocal()
                    user = db.query(User).filter(User.username == st.session_state.username).first()
                    if user:
                        new_project = Project(
                            owner_id=user.id,
                            name=new_p_name,
                            project_type=p_type,
                            result_data="[]", # Empty JSON list
                            created_at=datetime.datetime.utcnow()
                        )
                        db.add(new_project)
                        db.commit()
                        st.success(t(f"✅ تم إنشاء مشروع '{new_p_name}' بنجاح!", f"✅ Project '{new_p_name}' created!"))
                        st.cache_data.clear()
                        st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
                finally:
                    if db: db.close()
    
    st.markdown("<br>", unsafe_allow_html=True)

    # ─── Charts & Activity ───────────────────────────────────────
    if proj_count > 0:
        try:
            # Build data frame from saved projects
            rows = []
            for p in projects:
                rows.append({
                    "name": p.name,
                    "type": p.project_type,
                    "date": p.created_at.strftime("%Y-%m-%d") if p.created_at else "N/A",
                })
            df_proj = pd.DataFrame(rows)

            tab_charts, tab_gantt, tab_history = st.tabs([
                t("📈 الإحصائيات", "📈 Analytics"),
                t("📅 Gantt Chart", "📅 Gantt Chart"),
                t("📁 سجل المشاريع", "📁 Project History")
            ])

            with tab_charts:
                c1, c2 = st.columns(2)
                with c1:
                    # S-Curve (Planned vs Actual)
                    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
                    planned = [5, 12, 25, 40, 55, 68, 80, 88, 94, 98, 100, 100]
                    actual = [4, 10, 20, 35, 48, 60, 70, 75, 80, 85, 90, 95] # lagging slightly
                    
                    df_s = pd.DataFrame({"Month": months, "Planned": planned, "Actual": actual})
                    fig_s = go.Figure()
                    fig_s.add_trace(go.Scatter(x=df_s["Month"], y=df_s["Planned"], mode='lines+markers', name=t("المخطط (Planned)", "Planned"), line=dict(color="#0ea5e9", width=3)))
                    fig_s.add_trace(go.Scatter(x=df_s["Month"], y=df_s["Actual"], mode='lines+markers', name=t("الفعلي (Actual)", "Actual"), line=dict(color="#f43f5e", width=3, dash='dash')))
                    
                    fig_s.update_layout(
                        title=dict(text=t("📈 منحنى الإنجاز (S-Curve)", "Project S-Curve"), font=dict(size=18)),
                        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#f8fafc",
                        margin=dict(t=40, b=10, l=10, r=10),
                        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
                        xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)", range=[0, 105])
                    )
                    st.plotly_chart(fig_s, use_container_width=True, config={'displayModeBar': False})

                with c2:
                    # Cash Flow Curve (Cumulative Cost vs Income)
                    cost = [100, 250, 450, 600, 800, 1050, 1200, 1350, 1500, 1600, 1750, 1900]
                    income = [0, 150, 300, 500, 700, 950, 1100, 1300, 1500, 1700, 1850, 2000]
                    
                    df_c = pd.DataFrame({"Month": months, "Cost": cost, "Income": income})
                    fig_c = go.Figure()
                    fig_c.add_trace(go.Bar(x=df_c["Month"], y=df_c["Cost"], name=t("التكلفة (Cost)", "Cost"), marker_color="#f59e0b"))
                    fig_c.add_trace(go.Scatter(x=df_c["Month"], y=df_c["Income"], mode='lines+markers', name=t("الدخل (Income)", "Income"), line=dict(color="#10b981", width=3)))
                    
                    fig_c.update_layout(
                        title=dict(text=t("💵 التدفق النقدي (Cash Flow)", "Cash Flow Analysis"), font=dict(size=18)),
                        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#f8fafc",
                        margin=dict(t=40, b=10, l=10, r=10),
                        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
                        xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)")
                    )
                    st.plotly_chart(fig_c, use_container_width=True, config={'displayModeBar': False})

            with tab_gantt:
                st.markdown(f"#### 📅 " + t("الجدول الزمني التنفيذي", "Project Timeline (Gantt)"))
                boq_items = st.session_state.get("boq_data", [])
                
                if boq_items and len(boq_items) > 0:
                    # Build Gantt from BOQ items
                    base_date = datetime.datetime.today()
                    gantt_rows = []
                    cursor = base_date
                    for item in boq_items[:20]:
                        qty = float(item.get("quantity", item.get("qty", 1)) or 1)
                        duration_days = max(3, int(qty * 0.5))  # Estimate based on qty
                        gantt_rows.append(dict(
                            Task=str(item.get("item", item.get("description", "Task")))[:40],
                            Start=cursor.strftime("%Y-%m-%d"),
                            Finish=(cursor + datetime.timedelta(days=duration_days)).strftime("%Y-%m-%d"),
                            Category=str(item.get("category", "General"))
                        ))
                        cursor += datetime.timedelta(days=max(1, duration_days // 2))
                    
                    df_gantt = pd.DataFrame(gantt_rows)
                    fig_gantt = px.timeline(
                        df_gantt, x_start="Start", x_end="Finish", y="Task",
                        color="Category", title=t("الجدول الزمني المقدر للمشروع", "Estimated Project Schedule")
                    )
                    fig_gantt.update_yaxes(autorange="reversed")
                    fig_gantt.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                        font_color="#f8fafc", margin=dict(t=40, b=20, l=10, r=10)
                    )
                    st.plotly_chart(fig_gantt, use_container_width=True)
                    
                    # PDF Export button
                    st.markdown("---")
                    c_pdf1, c_pdf2, c_pdf3 = st.columns([1,2,1])
                    with c_pdf2:
                        proj_name_pdf = st.text_input(t("اسم المشروع", "Project Name"), value="My Engineering Project", key="pdf_proj_name")
                        if st.button("📄 " + t("تصدير تقرير شامل PDF", "Export Full PDF Report"), use_container_width=True, type='primary'):
                            with st.spinner(t("جاري بناء التقرير...", "Building report...")):
                                from utils.pdf_report import generate_project_pdf
                                ai_summary = st.session_state.get("ai_project_summary", "")
                                currency = st.session_state.get("currency", "EGP")
                                pdf_bytes = generate_project_pdf(
                                    project_name=proj_name_pdf,
                                    company_name=st.session_state.get("username", "Engineer"),
                                    boq_items=boq_items,
                                    ai_summary=ai_summary,
                                    currency=currency,
                                    white_label=(st.session_state.get("plan", "Free") != "Free")
                                )
                                st.download_button(
                                    label="📥 " + t("تحميل PDF", "Download PDF"),
                                    data=pdf_bytes,
                                    file_name=f"{proj_name_pdf.replace(' ','_')}_Report.pdf",
                                    mime="application/pdf",
                                    use_container_width=True
                                )
                else:
                    st.info(t("لا توجد بنود مقايسة محفوظة في الجلسة. توجه لقسم المقايسة وسعّر مشروع أولاً.", "No BOQ items in session. Price a project first to generate a Gantt Chart."))

            with tab_history:
                st.markdown(f"### {t('المشاريع الأخيرة', 'Recent Projects')}")
                for p in projects[:10]:
                    type_icon = "📐" if p.project_type == "Blueprint" else "💰"
                    with st.expander(f"{type_icon} **{p.name}** — {p.created_at.strftime('%Y-%m-%d') if p.created_at else ''}"):
                        try:
                            data = json.loads(p.result_data) if p.result_data else []
                            if isinstance(data, list) and len(data) > 0:
                                df_show = pd.DataFrame(data)
                                st.dataframe(df_show, use_container_width=True)
                                from ai_engine.export_engine import ExportEngine
                                col_a, col_b = st.columns(2)
                                with col_a:
                                    excel_data = ExportEngine.generate_professional_excel(df_show)
                                    st.download_button(t("📊 Excel", "Excel"), data=excel_data, file_name=f"{p.name}.xlsx", key=f"ex_{p.id}")
                                with col_b:
                                    pdf_data = ExportEngine.generate_professional_pdf(df_show, project_name=p.name)
                                    st.download_button(t("📄 PDF", "PDF"), data=pdf_data, file_name=f"{p.name}.pdf", key=f"pd_{p.id}")
                        except Exception:
                            st.info(t("لا توجد بيانات للعرض", "No data to display"))
        except Exception as e:
            st.error(f"Chart Error: {e}")
    else:
        # Pre-loaded Demo Project for New Users
        st.markdown(f"#### 🚀 {t('مشروع تجريبي: فيلا مودرن', 'Demo Project: Modern Villa')}")
        st.info(t("هذا مشروع تجريبي يوضح لك كيف تبدو الإحصائيات عند إضافة مشاريعك الخاصة.", "This is a demo project to show you how analytics look when you add your own projects."))
        
        tab_charts, tab_gantt = st.tabs([t("📈 الإحصائيات", "📈 Analytics"), t("📅 Gantt Chart", "📅 Gantt Chart")])
        with tab_charts:
            c1, c2 = st.columns(2)
            with c1:
                months = ["Jan", "Feb", "Mar", "Apr"]
                planned = [10, 30, 60, 100]
                actual = [8, 25, 55, 90]
                df_s = pd.DataFrame({"Month": months, "Planned": planned, "Actual": actual})
                fig_s = go.Figure()
                fig_s.add_trace(go.Scatter(x=df_s["Month"], y=df_s["Planned"], mode='lines+markers', name="Planned", line=dict(color="#0ea5e9", width=3)))
                fig_s.add_trace(go.Scatter(x=df_s["Month"], y=df_s["Actual"], mode='lines+markers', name="Actual", line=dict(color="#f43f5e", width=3, dash='dash')))
                fig_s.update_layout(title="Project S-Curve", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#f8fafc", margin=dict(t=40, b=10, l=10, r=10), xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)"))
                st.plotly_chart(fig_s, use_container_width=True, config={'displayModeBar': False})
            with c2:
                cost = [100, 300, 700, 1000]
                income = [0, 200, 500, 1200]
                df_c = pd.DataFrame({"Month": months, "Cost": cost, "Income": income})
                fig_c = go.Figure()
                fig_c.add_trace(go.Bar(x=df_c["Month"], y=df_c["Cost"], name="Cost", marker_color="#f59e0b"))
                fig_c.add_trace(go.Scatter(x=df_c["Month"], y=df_c["Income"], mode='lines+markers', name="Income", line=dict(color="#10b981", width=3)))
                fig_c.update_layout(title="Cash Flow Analysis", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#f8fafc", margin=dict(t=40, b=10, l=10, r=10), xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)"))
                st.plotly_chart(fig_c, use_container_width=True, config={'displayModeBar': False})

    # ─── Market Snapshot ─────────────────────────────
    st.markdown("---")
    st.markdown(f"### 📈 {t('نظرة سريعة على السوق', 'Market Snapshot')}")
    
    # Use pre-fetched session data for performance
    m_data = st.session_state.get("market_data")
    if m_data:
        mcols = st.columns(3)
        prices = m_data.get("prices", {})
        items = list(prices.items())[:3]
        for mcol, (mat, vals) in zip(mcols, items):
            with mcol:
                st.markdown(f"""
                <div class="glass-card animate-up" style="padding:1rem; border-left:4px solid var(--accent-primary);">
                    <p style="margin:0; font-size:0.75rem; color:var(--text-secondary);">{mat}</p>
                    <h3 style="margin:5px 0; color:white;">{vals['egp']:,.0f} <span style="font-size:0.8rem;">EGP</span></h3>
                    <p style="margin:0; font-size:0.7rem; color:var(--success);">$ {vals['usd']:,.2f} USD</p>
                </div>
                """, unsafe_allow_html=True)

    # ─── V1.6.0: AI Project Summary ─────────────────────────────
    st.markdown("---")
    st.markdown(f"### 🧠 {t('ملخص المشروع الذكي', 'AI Project Summary')}")
    col_ai1, col_ai2 = st.columns([2, 1])
    with col_ai1:
        if st.button("🧠 " + t("توليد ملخص تنفيذي ذكي", "Generate AI Executive Summary"), use_container_width=True):
            boq_items = st.session_state.get("boq_data", [])
            if boq_items:
                with st.spinner(t("يحلل الذكاء الاصطناعي مشروعك...", "AI analyzing your project...")):
                    from ai_engine.cost_engine import get_cost_engine
                    engine = get_cost_engine()
                    items_text = "\n".join([f"- {item.get('item','?')} ({item.get('quantity',0)} {item.get('unit','')})" for item in boq_items[:15]])
                    total = sum(float(item.get('Total Cost', item.get('direct_total', 0)) or 0) for item in boq_items)
                    currency = st.session_state.get('currency', 'EGP')
                    prompt = f"""As a Senior Construction Project Manager, write a concise executive summary (max 150 words) for this project in English:

Project BOQ:
{items_text}

Total Estimated Cost: {total:,.0f} {currency}

Include: scope overview, key risk, recommended schedule duration, and readiness level. Be professional and concise."""
                    result, err = engine._call_groq(prompt, expect_json=False)
                    if not result:
                        result, err = engine._call_gemini_text(prompt, expect_json=False)
                    if result:
                        st.session_state.ai_project_summary = result
                        st.rerun()
                    else:
                        st.error(f"AI Error: {err}")
            else:
                st.warning(t("لا توجد بنود مقايسة. سعّر مشروعك أولاً.", "No BOQ items found. Price a project first."))

    if st.session_state.get("ai_project_summary"):
        st.markdown(f"""
        <div class="glass-card" style="padding:1.5rem; border-left:4px solid #0ea5e9; margin-top:0.5rem;">
            <p style="font-size:0.75rem; color:#64748b; margin:0 0 8px 0; text-transform:uppercase; letter-spacing:1px;">AI Executive Summary</p>
            <p style="color:#e2e8f0; line-height:1.8; font-size:0.95rem; margin:0;">{st.session_state.ai_project_summary}</p>
        </div>
        """, unsafe_allow_html=True)

    # ─── Quick Start ─────────────────────────────
    st.markdown("---")
    st.markdown(f"### 🧭 {t('دليل الوصول السريع', 'Quick Access')}")
    guide_steps = [
        ("📐", t("مهندس الرسم", "Drawing Engine"), t("رسم مدعوم بالذكاء الاصطناعي", "AI-powered drafting")),
        ("💰", t("المقايسة", "BOQ Pricing"), t("تسعير دقيق ولحظي", "Accurate real-time pricing")),
        ("🌍", t("متجر العطاءات", "Tender Hub"), t("عطاءات حية بحسب الدولة", "Live tenders by country")),
    ]
    gcols = st.columns(3)
    for gcol, (icon, title, desc) in zip(gcols, guide_steps):
        with gcol:
            st.markdown(f"""
            <div class="glass-card animate-up" style="text-align:center; padding:1.5rem;">
                <div style="font-size:2.5rem; margin-bottom:10px;">{icon}</div>
                <h4 style="color:#0ea5e9; margin:0;">{title}</h4>
                <p style="color:#64748b; font-size:0.8rem; margin:10px 0 0 0;">{desc}</p>
            </div>
            """, unsafe_allow_html=True)
