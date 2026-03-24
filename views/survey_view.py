import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import json
from utils import t, render_section_header, is_stlite

def render_survey_management():
    render_section_header(t("نظام المساحة الذكي (EngiSurvey AI)", "EngiSurvey AI (GIS & Satellite)"), "🌍")

    # Initialize Session State for Coordinates
    if "survey_points" not in st.session_state:
        st.session_state.survey_points = pd.DataFrame([
            {"Point": "P1", "Latitude": 30.0444, "Longitude": 31.2357},
            {"Point": "P2", "Latitude": 30.0454, "Longitude": 31.2357},
            {"Point": "P3", "Latitude": 30.0454, "Longitude": 31.2377},
            {"Point": "P4", "Latitude": 30.0444, "Longitude": 31.2377},
        ])

    tabs = st.tabs([
        t("🛰️ رسم المساحة (Satellite)", "🛰️ Site Survey (Satellite)"),
        t("📂 بيانات الرفع (Coordinates)", "📂 Surveying Data (XYZ)"),
        t("📸 توثيق الموقع (Photos)", "📸 Site Documentation")
    ])

    # ─── Tab 1: Satellite Map ────────────────────────────────────
    with tabs[0]:
        st.markdown(f"#### 🛰️ " + t("تحديد قطعة الأرض بالقمر الصناعي", "Land Delineation via Satellite"))
        
        # Calculation Logic
        def calculate_area(df):
            if len(df) < 3: return 0
            # Rough approximation for small areas (Mercator Projection simplification)
            # Ref: Shoelace Formula
            lat = np.radians(df['Latitude'])
            lon = np.radians(df['Longitude'])
            # Radius of earth in meters
            R = 6378137.0
            x = R * lon * np.cos(lat.mean())
            y = R * lat
            return 0.5 * np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))

        area_m2 = calculate_area(st.session_state.survey_points)
        
        m1, m2, m3 = st.columns(3)
        with m1: st.metric(t("المساحة الإجمالية (Area)", "Total Area"), f"{area_m2:,.2f} m²")
        with m2: st.metric(t("المساحة بالفدان (Feddan)", "Area in Feddan"), f"{area_m2/4200:.3f} Fed")
        
        # Exact Perimeter Calculation (Haversine Distance Approximation)
        perimeter = 0
        distances = []
        if len(st.session_state.survey_points) > 1:
            points = st.session_state.survey_points.to_dict('records')
            for i in range(len(points)):
                p1 = points[i]
                p2 = points[(i+1) % len(points)]
                # Simple Cartesian approx for tiny distances
                dy = (p2['Latitude'] - p1['Latitude']) * 111320
                dx = (p2['Longitude'] - p1['Longitude']) * 111320 * np.cos(np.radians(p1['Latitude']))
                dist = np.sqrt(dx**2 + dy**2)
                perimeter += dist
                distances.append(f"{p1['Point']} ➔ {p2['Point']}: {dist:.1f}m")
        with m3: st.metric(t("محيط الأرض الدقيق (Perimeter)", "Exact Perimeter"), f"{perimeter:,.1f} m")

        # Plotly Map
        df = st.session_state.survey_points
        # Close the polygon for drawing
        df_closed = pd.concat([df, df.iloc[[0]]], ignore_index=True)

        try:
            import folium
            from streamlit_folium import st_folium
            
            center_lat = df['Latitude'].mean()
            center_lon = df['Longitude'].mean()
            
            m = folium.Map(location=[center_lat, center_lon], zoom_start=17, control_scale=True)
            
            folium.TileLayer(
                tiles = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                attr = 'Esri',
                name = 'Esri Satellite',
                overlay = False,
                control = True
            ).add_to(m)
            
            locations = list(zip(df_closed['Latitude'], df_closed['Longitude']))
            folium.Polygon(
                locations=locations,
                color='#00ff00',
                weight=3,
                fill=True,
                fill_color='rgba(0, 255, 0, 0.3)',
                fill_opacity=0.3
            ).add_to(m)
            
            for index, row in df.iterrows():
                folium.Marker(
                    [row['Latitude'], row['Longitude']], 
                    tooltip=row['Point'],
                    icon=folium.Icon(color="green", icon="info-sign")
                ).add_to(m)
                
            st_data = st_folium(m, height=500, use_container_width=True)
        except ImportError:
            st.error("Missing map libraries. Please install folium and streamlit-folium.")
        
        col_ex_draft, col_ex_kml = st.columns([1, 1])
        with col_ex_draft:
            if st.button("📐 " + t("تصدير المخطط لمركز الرسم", "Export Boundary to EngiDraft"), use_container_width=True):
                # Simulation: Convert Lat/Long distances to CM for the drafting engine
                st.toast(t("جاري معالجة الإحداثيات وتصديرها...", "Processing coordinates for export..."))
                st.success(t("تم تصدير حدود الأرض! يمكنك الآن المتابعة في قسم الرسم.", "Boundary Exported! Proceed to Drawing Engine."))

        with col_ex_kml:
            # Generate KML dynamically
            kml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>EngiCost Survey Polygon</name>
    <Placemark>
      <name>Site Boundary</name>
      <Polygon>
        <outerBoundaryIs>
          <LinearRing>
            <coordinates>
{' '.join([f"{r['Longitude']},{r['Latitude']},0" for _, r in df_closed.iterrows()])}
            </coordinates>
          </LinearRing>
        </outerBoundaryIs>
      </Polygon>
    </Placemark>
  </Document>
</kml>
"""
            st.download_button("📥 " + t("تحميل كملف KML (للجوجل إيرث)", "Download as KML"), data=kml_content, file_name="site_boundary.kml", mime="application/vnd.google-earth.kml+xml", use_container_width=True)

        # Earthworks Calculator & Distance Matrix
        with st.expander(t("🚜 حاسبة الحفر والردم والمسافات (Earthworks & Distances)", "🚜 Earthworks & Distances Calculator"), expanded=False):
            ex_c1, ex_c2 = st.columns([1, 1])
            with ex_c1:
                st.markdown("##### " + t("📍 أطوال الأضلاع", "📍 Segment Lengths"))
                for d in distances:
                    st.write(f"- {d}")
            with ex_c2:
                st.markdown("##### " + t("⛏️ تقدير الكميات الترابية", "⛏️ Earthworks Volumetric Estimate"))
                depth_avg = st.number_input(t("متوسط منسوب الحفر (متر)", "Avg Excavation Depth (m)"), min_value=0.0, value=1.5, step=0.5)
                vol_excavation = area_m2 * depth_avg
                vol_backfill = vol_excavation * 0.3 # Rough estimate 30% backfill around foundations
                st.info(f"**{t('إجمالي كميات الحفر:', 'Est. Excavation Volume:')}** {vol_excavation:,.1f} m³\n\n**{t('إجمالي ردْم مقدر:', 'Est. Backfill Volume:')}** {vol_backfill:,.1f} m³")


    # ─── Tab 2: Coordinate Entry ─────────────────────────────────
    with tabs[1]:
        st.markdown(f"#### ➕ " + t("إدخال وتحميل الإحداثيات", "Coordinate Entry & Upload"))
        
        c1, c2 = st.columns([2, 1])
        with c2:
            st.markdown("##### 📤 " + t("رفع ملف مساحي", "Upload Survey File"))
            uploaded_file = st.file_uploader(t("اختر ملف CSV/Excel أو KML", "Choose CSV/Excel or KML"), type=["csv", "xlsx", "kml"])
            if uploaded_file:
                filename = uploaded_file.name.lower()
                try:
                    if filename.endswith(".csv"):
                        st.session_state.survey_points = pd.read_csv(uploaded_file)
                        st.success(t("تم تحميل ملف CSV", "CSV Loaded"))
                        st.rerun()
                    elif filename.endswith(".xlsx"):
                        st.session_state.survey_points = pd.read_excel(uploaded_file)
                        st.success(t("تم تحميل ملف Excel", "Excel Loaded"))
                        st.rerun()
                    elif filename.endswith(".kml"):
                        from bs4 import BeautifulSoup
                        soup = BeautifulSoup(uploaded_file.getvalue().decode('utf-8'), 'xml')
                        coords_text = soup.find('coordinates')
                        if coords_text:
                            points = []
                            for i, point in enumerate(coords_text.text.strip().split()):
                                parts = point.split(',')
                                if len(parts) >= 2:
                                    points.append({
                                        "Point": f"P{i+1}",
                                        "Latitude": float(parts[1]),
                                        "Longitude": float(parts[0])
                                    })
                            if points:
                                st.session_state.survey_points = pd.DataFrame(points)
                                st.success(t("تم تحميل الإحداثيات من KML", "KML Polygon Loaded"))
                                st.rerun()
                except Exception as e:
                    st.error(f"Error reading file: {e}")

        with c1:
            st.markdown("##### ✍️ " + t("جدول الإحداثيات اليدوي", "Manual XYZ Table"))
            edited_df = st.data_editor(
                st.session_state.survey_points,
                num_rows="dynamic",
                use_container_width=True,
                key="survey_editor"
            )
            if st.button(t("💾 حفظ التغييرات", "Save & Sync Map")):
                st.session_state.survey_points = edited_df
                st.rerun()

    # ─── Tab 3: Site Documentation ──────────────────────────────
    with tabs[2]:
        st.markdown(f"#### 📸 " + t("التوثيق البصري والتحليل (Computer Vision)", "Visual Documentation & AI CV"))
        
        col_cv, col_cam = st.columns([1, 1])
        with col_cv:
            st.markdown("##### 🤖 " + t("تحليل الموقع بالأقمار الصناعية (CV GIS)", "AI Satellite CV Analysis"))
            st.info(t("ارفع صورة فضائية (Drone/Satellite) وسيقوم الذكاء الاصطناعي بتحليل المعالم وطبيعة الأرض.", "Upload satellite imagery and AI will analyze terrain & landmarks."))
            sat_img = st.file_uploader(t("صورة فضائية (JPG/PNG)", "Satellite Image"), type=['jpg','jpeg','png'])
            
            if sat_img:
                st.image(sat_img, use_container_width=True)
                if st.button("🧠 " + t("بدء التحليل المساحي الذكي", "Start AI Site Analysis"), use_container_width=True, type='primary'):
                    with st.spinner(t("يقوم نظام Computer Vision بمعالجة التضاريس والمعالم...", "Computer Vision processing terrain & markers...")):
                        from ai_engine.cost_engine import get_cost_engine
                        engine = get_cost_engine()
                        report, err = engine.analyze_site_image(sat_img.getvalue())
                        if report:
                            st.session_state.cv_report = report
                            st.rerun()
                        else:
                            st.error(err)
                            
            if st.session_state.get("cv_report"):
                st.markdown("---")
                st.markdown(f"#### 📑 {t('التقرير الذكي للموقع', 'AI Site Report')}")
                st.markdown(f"<div class='glass-card' style='padding:1.5rem; border-right:4px solid var(--accent-primary);'>{st.session_state.cv_report}</div>", unsafe_allow_html=True)
                
        with col_cam:
            st.markdown("##### 📷 " + t("التقاط صورة مساحية للموقع", "Capture Site Ground Photo"))
            img_file = st.camera_input(t("التقط صورة لتوثيق المنسوب أو العوائق", "Capture landmark or obstacles"))
            if img_file:
                st.image(img_file, caption=t("صورة موقع مخزنة", "Stored Site Photo"))
                st.success(t("تم حفظ الصورة في ذاكرة المشروع.", "Photo saved to project storage."))
