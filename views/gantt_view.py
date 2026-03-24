import streamlit as st
import pandas as pd
import datetime
import json
from utils import t, render_section_header
from database import SessionLocal, User, Project
from ai_engine.cost_engine import get_cost_engine

# ────────────────────────────────────────────────────────────────────────────────
# Gantt + Progress Tracker combined view
# ────────────────────────────────────────────────────────────────────────────────

GANTT_KEY = "gantt_tasks"

def _default_tasks():
    today = datetime.date.today()
    return [
        {"task": "أعمال الحفر والتسوية",         "start": today,                                  "end": today + datetime.timedelta(days=7),  "pct": 0},
        {"task": "الخرسانة العادية والمسلحة",    "start": today + datetime.timedelta(days=7),  "end": today + datetime.timedelta(days=30), "pct": 0},
        {"task": "المباني والتشطيبات الخارجية",   "start": today + datetime.timedelta(days=25), "end": today + datetime.timedelta(days=55), "pct": 0},
        {"task": "التشطيبات الداخلية",            "start": today + datetime.timedelta(days=50), "end": today + datetime.timedelta(days=80), "pct": 0},
        {"task": "الكهرباء والسباكة",              "start": today + datetime.timedelta(days=60), "end": today + datetime.timedelta(days=90), "pct": 0},
        {"task": "التسليم النهائي",                "start": today + datetime.timedelta(days=88), "end": today + datetime.timedelta(days=95), "pct": 0},
    ]


def _tasks_to_df(tasks: list) -> pd.DataFrame:
    """Convert task list (which may have str or date values) to a DataFrame with proper date types."""
    rows = []
    for t_ in tasks:
        start = t_["start"]
        end   = t_["end"]
        if isinstance(start, str):
            try: start = datetime.date.fromisoformat(start)
            except: start = datetime.date.today()
        if isinstance(end, str):
            try: end = datetime.date.fromisoformat(end)
            except: end = datetime.date.today() + datetime.timedelta(days=7)
        rows.append({"task": t_["task"], "start": start, "end": end, "pct": int(t_.get("pct", 0))})
    return pd.DataFrame(rows)


def _df_to_tasks(df: pd.DataFrame) -> list:
    """Convert DataFrame back to JSON-serialisable task dicts (dates as strings)."""
    tasks = []
    for _, row in df.iterrows():
        start = row["start"]
        end   = row["end"]
        tasks.append({
            "task": str(row["task"]),
            "start": start.isoformat() if hasattr(start, "isoformat") else str(start),
            "end":   end.isoformat()   if hasattr(end,   "isoformat") else str(end),
            "pct":   int(row["pct"]),
        })
    return tasks


def render_gantt_progress():
    render_section_header(t("جدول المشروع الزمني والإنجاز", "Project Schedule & Progress Tracker"), "📅")

    st.markdown(f"""
    <div class="glass-card animate-up">
        <p style="color:var(--text-muted);">
            {t("أنشئ جدولاً زمنياً للمشروع، تابع نسبة الإنجاز لكل بند، واحصل على صور بيانية تلقائية.",
               "Create a project schedule, track progress per task, and get automatic Gantt and S-curve charts.")}
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ─── Session Init ─────────────────────────────────────────────
    if GANTT_KEY not in st.session_state:
        st.session_state[GANTT_KEY] = _default_tasks()

    tab_sched, tab_progress, tab_charts = st.tabs([
        t("🗓️ إعداد الجدول", "🗓️ Schedule Setup"),
        t("📈 متابعة الإنجاز", "📈 Progress Tracking"),
        t("📊 الرسوم البيانية", "📊 Charts"),
    ])

    # ─── Schedule Setup ───────────────────────────────────────────
    with tab_sched:
        st.markdown(f"#### {t('تنبؤ الجدول الزمني الذكي', 'Smart Schedule Generation')}")
        
        # BOQ Integration
        col_g1, col_g2 = st.columns([2, 1])
        with col_g1:
            uploaded_boq_g = st.file_uploader(t("رفع مقايسة لتحويلها لجدول زمني", "Upload BOQ for Schedule Generation"), type=["pdf", "xlsx"], key="gantt_upload")
        with col_g2:
            db = SessionLocal()
            user = db.query(User).filter(User.username == st.session_state.username).first()
            saved_projects = []
            if user:
                saved_projects = db.query(Project).filter(Project.owner_id == user.id, Project.project_type == "BOQ").all()
            db.close()
            
            proj_opt = [p.name for p in saved_projects]
            if proj_opt:
                sel_proj = st.selectbox(t("استيراد من المقايسات", "Import from BOQs"), ["---"] + proj_opt, key="gantt_import")
                if sel_proj != "---":
                    target = next(p for p in saved_projects if p.name == sel_proj)
                    try:
                        data = json.loads(target.result_data)
                        today = datetime.date.today()
                        new_tasks = []
                        for i, d in enumerate(data):
                            new_tasks.append({
                                "task": d.get("description", t("بند", "Task")),
                                "start": today + datetime.timedelta(days=i*5),
                                "end": today + datetime.timedelta(days=(i+1)*5),
                                "pct": 0
                            })
                        st.session_state[GANTT_KEY] = new_tasks
                        st.success(t("تم استيراد الجدول بنجاح!", "Schedule items imported!"))
                    except: pass

        if uploaded_boq_g:
            if st.button(t("🚀 توليد جدول من المقايسة", "🚀 Generate from BOQ"), use_container_width=True):
                with st.spinner(t("جاري التحليل وتوليد الجدول الزمني...", "Analyzing and generating schedule...")):
                    try:
                        engine = get_cost_engine()
                        res = engine.extract_boq_from_file(uploaded_boq_g.getvalue(), uploaded_boq_g.type)
                        today = datetime.date.today()
                        new_tasks = []
                        for i, item in enumerate(res):
                            new_tasks.append({
                                "task": item.get("description", ""),
                                "start": today + datetime.timedelta(days=i*5),
                                "end": today + datetime.timedelta(days=(i+1)*5),
                                "pct": 0
                            })
                        st.session_state[GANTT_KEY] = new_tasks
                        st.success(t("تم التوليد بنجاح!", "Generated successfully!"))
                    except: pass

        st.markdown(f"#### {t('جدول المشروع — حرر وأضف بنودك', 'Project Schedule — Edit & Add Tasks')}")
        # Convert stored tasks (may have string dates) to proper DataFrame with date types
        df_in = _tasks_to_df(st.session_state[GANTT_KEY])

        edited = st.data_editor(
            df_in, use_container_width=True, num_rows="dynamic",
            column_config={
                "task":  st.column_config.TextColumn(t("اسم البند", "Task Name")),
                "start": st.column_config.DateColumn(t("تاريخ البداية", "Start Date")),
                "end":   st.column_config.DateColumn(t("تاريخ النهاية", "End Date")),
                "pct":   st.column_config.NumberColumn(t("الإنجاز %", "Progress %"), min_value=0, max_value=100, step=5, format="%d%%"),
            }
        )

        col_a, col_b = st.columns(2)
        with col_a:
            if st.button(t("💾 حفظ الجدول", "💾 Save Schedule"), use_container_width=True):
                # Serialize back to string-based dicts for session/DB storage
                st.session_state[GANTT_KEY] = _df_to_tasks(edited)
                # Save to DB
                try:
                    db = SessionLocal()
                    user = db.query(User).filter(User.username == st.session_state.username).first()
                    if user:
                        proj = Project(
                            owner_id=user.id, name=t("جدول المشروع", "Project Schedule"),
                            project_type="Gantt", result_data=json.dumps(st.session_state[GANTT_KEY]),
                            created_at=datetime.datetime.utcnow()
                        )
                        db.add(proj); db.commit()
                    db.close()
                    st.success(t("✅ تم حفظ الجدول!", "✅ Schedule saved!"))
                except Exception as e:
                    st.warning(f"Save warning: {e}")
        with col_b:
            # Export as Excel
            try:
                from ai_engine.export_engine import ExportEngine
                xl = ExportEngine.generate_professional_excel(edited, project_name=t("الجدول الزمني", "Project Schedule"))
                st.download_button(t("📊 تصدير Excel", "📊 Export Excel"), xl, "schedule.xlsx",
                                   "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                   use_container_width=True)
            except Exception as e:
                st.error(f"Export error: {e}")

    # ─── Progress Tracking ────────────────────────────────────────
    with tab_progress:
        st.markdown(f"#### {t('تحديث نسب الإنجاز الفعلية', 'Update Actual Progress %')}")
        tasks = st.session_state[GANTT_KEY]
        changed = False
        for i, task in enumerate(tasks):
            c1, c2 = st.columns([3, 1])
            with c1:
                st.markdown(f"""
                <div style="padding:6px 0;">
                    <b>{task['task']}</b>
                    <div style="background:rgba(255,255,255,0.08); border-radius:10px; margin-top:4px; height:12px; overflow:hidden;">
                        <div style="width:{task['pct']}%; height:100%; background:linear-gradient(90deg,#38bdf8,#818cf8); border-radius:10px;"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            with c2:
                new_pct = st.number_input("", min_value=0, max_value=100, value=int(task['pct']),
                                          key=f"prog_{i}", label_visibility="collapsed")
                if new_pct != task['pct']:
                    tasks[i]['pct'] = new_pct
                    changed = True

        if changed:
            st.session_state[GANTT_KEY] = tasks

        # Summary KPIs
        avg_pct = sum(t_['pct'] for t_ in tasks) / len(tasks) if tasks else 0
        done_count = sum(1 for t_ in tasks if t_['pct'] >= 100)
        st.markdown("<br>", unsafe_allow_html=True)
        k1, k2, k3 = st.columns(3)
        with k1:
            st.metric(t("متوسط الإنجاز الكلي", "Overall Progress"), f"{avg_pct:.1f}%")
        with k2:
            st.metric(t("بنود مكتملة", "Completed Tasks"), f"{done_count} / {len(tasks)}")
        with k3:
            remaining = sum(1 for t_ in tasks if t_['pct'] < 100)
            st.metric(t("بنود متبقية", "Remaining Tasks"), remaining)

    # ─── Charts ───────────────────────────────────────────────────
    with tab_charts:
        tasks = st.session_state[GANTT_KEY]
        try:
            import plotly.graph_objects as go
            import plotly.express as px

            # ── Gantt ──────────────────────────────────────────────
            st.markdown(f"#### 📅 {t('مخطط جانت', 'Gantt Chart')}")
            df_gantt = pd.DataFrame(tasks)
            if not df_gantt.empty and "start" in df_gantt.columns:
                df_gantt["start"] = pd.to_datetime(df_gantt["start"])
                df_gantt["end"] = pd.to_datetime(df_gantt["end"])
                df_gantt["duration"] = (df_gantt["end"] - df_gantt["start"]).dt.days
                df_gantt["color"] = df_gantt["pct"].apply(
                    lambda p: "#4ade80" if p == 100 else "#38bdf8" if p > 50 else "#818cf8"
                )

                fig = go.Figure()
                for _, row in df_gantt.iterrows():
                    fig.add_trace(go.Bar(
                        x=[row["duration"]], y=[row["task"]],
                        base=[row["start"].timestamp() * 1000],
                        orientation='h',
                        marker_color=row["color"],
                        text=f"{row['pct']}%",
                        textposition="inside",
                        name=row["task"],
                        showlegend=False,
                    ))

                fig.update_layout(
                    barmode='overlay',
                    xaxis=dict(type='date', title=t("التاريخ", "Date"), gridcolor="rgba(255,255,255,0.05)"),
                    yaxis=dict(title="", autorange='reversed'),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font_color="#e2e8f0",
                    height=max(300, len(tasks) * 50),
                )
                st.plotly_chart(fig, use_container_width=True)

            # ── S-Curve ────────────────────────────────────────────
            st.markdown(f"#### 📈 {t('منحنى S — الإنجاز التراكمي', 'S-Curve — Cumulative Progress')}")
            
            # Planned vs Actual
            n = len(tasks)
            labels = [t_["task"][:18] for t_ in tasks]
            planned = [(i + 1) / n * 100 for i in range(n)]
            actual_cum = []
            running = 0
            for t_ in tasks:
                running += t_["pct"] / n
                actual_cum.append(min(running, 100))

            fig_s = go.Figure()
            fig_s.add_trace(go.Scatter(x=labels, y=planned, name=t("المخططة", "Planned"), line=dict(color="#818cf8", dash="dash")))
            fig_s.add_trace(go.Scatter(x=labels, y=actual_cum, name=t("الفعلية", "Actual"), line=dict(color="#4ade80"), fill="tozeroy", fillcolor="rgba(74,222,128,0.1)"))
            fig_s.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color="#e2e8f0", height=350,
                xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
                yaxis=dict(gridcolor="rgba(255,255,255,0.05)", range=[0, 105]),
                legend=dict(bgcolor="rgba(0,0,0,0)")
            )
            st.plotly_chart(fig_s, use_container_width=True)

        except ImportError:
            st.warning(t("يرجى تثبيت مكتبة plotly", "Please install plotly library"))
        except Exception as e:
            st.error(f"Chart error: {e}")
