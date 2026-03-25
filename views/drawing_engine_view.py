import streamlit as st
import pandas as pd
import json
import plotly.graph_objects as go
import re
from utils import t, render_section_header, is_stlite

def _render_drawing_engine_internal():
    render_section_header(t("محرك الرسم الهندسي الذكي", "EngiDraft AI Drawing Engine"), "📐")

    # Initialize Session State
    if "current_rooms" not in st.session_state: st.session_state.current_rooms = []
    if "analysis_items" not in st.session_state: st.session_state.analysis_items = []

    # Global Settings
    with st.sidebar:
        st.subheader(t("⚙️ الإعدادات العامة", "⚙️ Global Settings"))
        specialty = st.selectbox(t("التخصص الهندسي", "Specialty"), [
            t("معماري", "Architectural"), t("إنشائي", "Structural"),
            t("معدني (Steel)", "Metal/Steel Structure"),
            t("تكييف وتهوية", "HVAC"), t("كهرباء", "Electrical"),
            t("سباكة وصحي", "Plumbing & Fire"), t("لاندسكيب", "Landscaping")
        ])

    tabs = st.tabs([
        t("📐 لوحة الرسم الذكية (Ultra)", "📐 AI Drafting Board (Ultra)"),
        t("🏗️ قطاعات إنشائية (أوفلاين)", "🏗️ Structural Sections (Offline)"),
        t("📏 منظور هندسي (Perspective)", "📏 Perspective Drawing"),
        t("🧱 الواجهات المعمارية (Elevations)", "🧱 Elevation Views"),
        t("📷 رفع مخطط وتحليله (AI Scanner)", "📷 AI Plan Scanner")
    ])

    # ─── Tab 1: AI Drafting Board (BIM-Lite) ──────────────────────
    with tabs[0]:
        st.markdown(f"#### 🤖 {t('توليد مخططات تخصصية', 'AI Specialty Plan Generation')}")
        
        if is_stlite():
            st.warning(t("⚠️ هذه الميزة تتطلب اتصالاً بالإنترنت.", "⚠️ This feature requires internet connection."))
        
        # --- Inline Visual Controls ---
        c1, c2, c3, c4 = st.columns([1.5, 1, 1, 1])
        with c1:
            zoom_level = st.slider(t("حجم الرسمة (Zoom)", "Zoom Level"), 0.5, 3.0, 1.0, 0.1)
        with c2:
            show_3d = st.toggle(t("مجسم 3D (ماكيت)", "3D Maquette"), value=False)
        with c3:
            theme = st.selectbox(t("ستايل اللوحة", "Theme"), ["AutoCAD Dark", "Blueprint", "Modern Light"])
        with c4:
            st.write("") # Spacer
            if st.button(t("🔄 مسح", "Clear")):
                st.session_state.current_rooms = []
                st.session_state.analysis_items = []
                st.session_state.finishings_concept = None
                st.rerun()

        # --- Client Custom Requirements (V1.7.5) ---
        with st.expander(t("💎 متطلبات العميل المخصصة (Rooms, Floors, Style)", "💎 Custom Client Requirements"), expanded=True):
            r1, r2, r3, r4 = st.columns(4)
            with r1:
                bed_count = st.number_input(t("غرف النوم", "Bedrooms"), 1, 10, 3)
                floor_count = st.number_input(t("عدد الأدوار", "Floors"), 1, 5, 1)
            with r2:
                bath_count = st.number_input(t("الحمامات", "Bathrooms"), 1, 10, 2)
                style_3d = st.selectbox(t("طراز التشطيب", "Finishing Style"), ["Modern (Gray/Glass)", "Classic (Beige/Stone)", "Luxury (Gold/Marble)", "Industrial (Brick/Steel)"])
            with r3:
                balcony_count = st.number_input(t("البلكونات", "Balconies"), 0, 5, 1)
                landscaping = st.toggle(t("لاندسكيب ومساحات خضراء", "Landscaping & Greenery"), value=True)
            with r4:
                pool_opt = st.toggle(t("مسبح خاص", "Private Pool"), value=False)
                creative_mode = st.toggle(t("💡 ابتكار 9D (تصاميم غير تقليدية)", "💡 9D Innovation"), value=False)

        prompt = st.text_area(t("صِف المخطط المطلوب لهذا التخصص", f"Describe the {specialty} plan details"),
                               placeholder=t("مثال: فيلا سكنية مودرن بمدخل واسع...", "e.g., Modern residential villa with a wide entrance..."))

        if st.button(t("🪄 إنشاء وتصميم المخطط المخصص (V1.7.5 Pro)", "🪄 Generate & Design Custom Plan"), key="gen_btn", use_container_width=True):
            if not is_stlite():
                with st.spinner(t("جاري العصف الذهني وتصميم المساحات (Ultra AI)...", "AI brainstorming and designing spaces...")):
                    try:
                        from ai_engine.drawing_brain import generate_layout_from_prompt
                        
                        rooms_data, raw_res, fallback_used = generate_layout_from_prompt(
                            prompt=prompt,
                            specialty=specialty,
                            style_3d=style_3d,
                            bed_count=bed_count,
                            bath_count=bath_count,
                            balcony_count=balcony_count,
                            floor_count=floor_count,
                            landscaping=landscaping,
                            pool_opt=pool_opt,
                            creative_mode=creative_mode
                        )
                        
                        if fallback_used:
                             st.toast(t("تم استخدام المحرك الاحتياطي للخطة.", "Fallback layout engine used."))
                             
                        res = raw_res # Keep variable for diagnostic expander
                            
                        # --- Dynamic Algorithmic Generator (If AI API fails or returns garbage) ---
                        if not rooms_data["walls"]:
                            st.info(t("يتم التوليد التحليلي (Algorithmic Generation)...", "Using Algorithmic Engine..."))
                            
                            w_total = 800 + (bed_count * 150)
                            h_total = 800 + (bath_count * 100)
                            
                            rooms_data = {
                                "project_title": f"Dynamic {style_3d} Villa",
                                "floors": floor_count,
                                "walls": [],
                                "openings": [],
                                "furniture": [],
                                "labels": [{"text": f"Main Hall", "x": w_total/2, "y": h_total - 200}]
                            }
                            
                            # Exterior Walls
                            rooms_data["walls"].extend([
                                {"x": 0, "y": 0, "w": 20, "h": h_total, "is_exterior": True},
                                {"x": 0, "y": 0, "w": w_total, "h": 20, "is_exterior": True},
                                {"x": w_total, "y": 0, "w": 20, "h": h_total, "is_exterior": True},
                                {"x": 0, "y": h_total, "w": w_total+20, "h": 20, "is_exterior": True},
                            ])
                            
                            # Main Door
                            rooms_data["openings"].append({"name": "Entrance", "type": "door", "x": w_total/2 - 60, "y": h_total, "w": 120, "h": 20})
                            
                            # Procedural Bedrooms (Algorithmically arrange them)
                            for b in range(bed_count):
                                bx = 20 + (b % 2) * (w_total/2)
                                by = 20 + (b // 2) * 300
                                b_width = (w_total/2) - 40
                                rooms_data["walls"].extend([
                                    {"x": bx, "y": by, "w": 20, "h": 250},
                                    {"x": bx, "y": by, "w": b_width, "h": 20},
                                    {"x": bx+b_width, "y": by, "w": 20, "h": 250},
                                    {"x": bx, "y": by+250, "w": b_width, "h": 20}
                                ])
                                rooms_data["openings"].append({"name": "Door", "type": "door", "x": bx+(b_width/2)-40, "y": by+250, "w": 80, "h": 20})
                                rooms_data["furniture"].append({"name": "Bed", "type": "bed", "x": bx+50, "y": by+50, "w": 140, "h": 180})
                                rooms_data["labels"].append({"text": f"Bed {b+1}", "x": bx+(b_width/2), "y": by+150})
                                
                            # Bathrooms
                            for ba in range(bath_count):
                                bax = w_total - 250
                                bay = h_total - 300 - (ba * 200)
                                if bay < 0: bay = 20 # Prevent overflow
                                rooms_data["walls"].extend([
                                    {"x": bax, "y": bay, "w": 20, "h": 150},
                                    {"x": bax, "y": bay, "w": 200, "h": 20},
                                    {"x": bax+200, "y": bay, "w": 20, "h": 150},
                                    {"x": bax, "y": bay+150, "w": 200, "h": 20}
                                ])
                                rooms_data["labels"].append({"text": f"Bath {ba+1}", "x": bax+100, "y": bay+75})

                            # Pool and Landscaping
                            if pool_opt:
                                rooms_data["furniture"].append({"name": "Pool", "type": "pool", "x": w_total + 100, "y": 100, "w": 300 + (bed_count*20), "h": 600})
                            if landscaping:
                                rooms_data["furniture"].append({"name": "Garden", "type": "greenery", "x": -300, "y": 100, "w": 250, "h": h_total-200})


                        st.session_state.current_rooms = rooms_data
                        st.session_state.analysis_items = []
                        st.session_state.last_raw_res = str(res) # Store for debug
                        st.toast(t("تم إنشاء التصميم بنجاح!", "Design created successfully!"))
                        st.rerun()

                    except Exception as e:
                        st.error(f"Generation Error: {e}")
            else:
                st.error(t("وضع الأوفلاين نشط.", "Offline mode active."))

        with st.expander(t("🛠️ تشخيص بيانات AI", "🛠️ AI Diagnostics")):
            if "last_raw_res" in st.session_state:
                st.code(st.session_state.last_raw_res, language="json")
            else:
                st.write(t("لا توجد بيانات سابقة.", "No previous data."))

        # --- Display Section (Persistent) ---
        if st.session_state.current_rooms:
            r_data = st.session_state.current_rooms
            total_elements = len(r_data.get('walls',[])) + len(r_data.get('openings',[])) + len(r_data.get('furniture',[]))
            
            if show_3d:
                # --- 3D Finished Maquette (V1.7.5) ---
                st.markdown(f"### 🏗️ " + t("ماكيت معماري 10D مُشطب بالكامل", "Interactive 10D Finished Architectural Maquette"))
                fig3d = go.Figure()
                
                # Material Colors based on Style
                is_classic = "Classic" in style_3d
                is_luxury = "Luxury" in style_3d
                wall_color = "#f5f5dc" if is_classic else "#e5e3d7" if is_luxury else "#e5e7eb"
                base_color = "#4c6b22" if landscaping else "#262626"
                
                walls_list = r_data.get('walls', []) if isinstance(r_data.get('walls'), list) else []
                furn_list = r_data.get('furniture', []) if isinstance(r_data.get('furniture'), list) else []
                all_wb = walls_list + furn_list
                
                min_x = min([w.get('x',0) for w in all_wb] + [0]) - 500
                max_x = max([w.get('x',0)+w.get('w',0) for w in all_wb] + [1200]) + 500
                min_y = min([w.get('y',0) for w in all_wb] + [0]) - 500
                max_y = max([w.get('y',0)+w.get('h',0) for w in all_wb] + [1200]) + 500
                
                # Landscape/Base (Finished Look)
                fig3d.add_trace(go.Mesh3d(
                    x=[min_x, max_x, max_x, min_x, min_x, max_x, max_x, min_x],
                    y=[min_y, min_y, max_y, max_y, min_y, min_y, max_y, max_y],
                    z=[-20, -20, -20, -20, 0, 0, 0, 0],
                    i=[7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2],
                    j=[3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3],
                    k=[0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6],
                    color=base_color, name="Site/Landscape", flatshading=True
                ))
                
                # Multi-Story Integration
                actual_floors = r_data.get('floors', floor_count)
                for f_idx in range(actual_floors):
                    z_off = f_idx * 320
                    # Walls
                    for w in r_data.get('walls', []):
                        wx, wy, ww, wh = w.get('x',0), w.get('y',0), max(w.get('w',20),10), max(w.get('h',20),10)
                        fig3d.add_trace(go.Mesh3d(
                            x=[wx, wx+ww, wx+ww, wx, wx, wx+ww, wx+ww, wx],
                            y=[wy, wy, wy+wh, wy+wh, wy, wy, wy+wh, wy+wh],
                            z=[z_off, z_off, z_off, z_off, z_off+300, z_off+300, z_off+300, z_off+300],
                            i=[7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2],
                            j=[3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3],
                            k=[0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6],
                            color=wall_color, name=f"Wall F{f_idx+1}", flatshading=True,
                            opacity=1.0 if f_idx == 0 else 0.7
                        ))
                    # Ceiling/Floor Slab
                    fig3d.add_trace(go.Mesh3d(
                        x=[min_x/4, max_x/4+500, max_x/4+500, min_x/4], # Simplified slab
                        y=[min_y/4, min_y/4, max_y/4+500, max_y/4+500],
                        z=[z_off+300, z_off+300, z_off+300, z_off+300],
                        color="#d1d5db", opacity=0.4, name=f"Slab F{f_idx+1}"
                    ))

                # Special elements (Pool, Greenery)
                for f in r_data.get('furniture', []):
                    fx, fy, fw, fh = f.get('x',0), f.get('y',0), max(f.get('w',50),20), max(f.get('h',50),20)
                    ft = str(f.get('type','')).lower()
                    if "pool" in ft:
                        fig3d.add_trace(go.Mesh3d(
                            x=[fx, fx+fw, fx+fw, fx], y=[fy, fy, fy+fh, fy+fh], z=[-10, -10, -10, -10],
                            color="#00d4ff", opacity=0.8, name="Pool Water"
                        ))
                    elif "green" in ft or "land" in ft:
                        fig3d.add_trace(go.Mesh3d(
                            x=[fx, fx+fw, fx+fw, fx], y=[fy, fy, fy+fh, fy+fh], z=[5, 5, 5, 5],
                            color="#22c55e", opacity=0.8, name="Greenhouse/Garden"
                        ))
                
                fig3d.update_layout(
                    scene=dict(
                        aspectmode='data', 
                        xaxis=dict(visible=False), yaxis=dict(visible=False), zaxis=dict(visible=False),
                        camera=dict(eye=dict(x=-1.2, y=-1.2, z=1.0))
                    ),
                    paper_bgcolor="#111111", height=700, margin=dict(l=0,r=0,b=0,t=0)
                )
                st.plotly_chart(fig3d, use_container_width=True)
                
            else:
                # ─── V3.0 World-Class 2D Architectural Plan ───────────────────────
                st.markdown(f"### 🏛️ " + t("مسقط أفقي هندسي احترافي (V3.0 World-Class)", "Professional Architectural Floor Plan (V3.0)"))

                # === THEME COLORS ===
                if theme == "AutoCAD Dark":
                    bg_color, line_color = "#0d0d0d", "#e8e8e8"
                    wall_fill_color, wall_stroke_col = "#2a2a2a", "#cccccc"
                    dim_color, label_color = "#00d4ff", "#ffffff"
                elif theme == "Blueprint":
                    bg_color, line_color = "#0a2744", "#dce8f5"
                    wall_fill_color, wall_stroke_col = "#1a3a5c", "#90c4e8"
                    dim_color, label_color = "#ffdd57", "#ffffff"
                else:  # Modern Light
                    bg_color, line_color = "#f0f2f5", "#1a1a2e"
                    wall_fill_color, wall_stroke_col = "#c8cdd6", "#1a1a2e"
                    dim_color, label_color = "#1565c0", "#1a1a2e"

                # === ROOM TYPE COLORS (professional fill palette) ===
                ROOM_COLORS = {
                    "bedroom": "#d4e8f5" if theme == "Modern Light" else "#1a3a52",
                    "bathroom": "#d4f5f0" if theme == "Modern Light" else "#1a3d3a",
                    "kitchen": "#fff3d4" if theme == "Modern Light" else "#3d3010",
                    "living": "#f5f5d4" if theme == "Modern Light" else "#2d2d10",
                    "corridor": "#e8e8e8" if theme == "Modern Light" else "#222222",
                    "garage": "#e0ddd8" if theme == "Modern Light" else "#252015",
                    "pool": "#b3e5fc" if theme == "Modern Light" else "#003355",
                    "garden": "#c8e6c9" if theme == "Modern Light" else "#0a2d0a",
                    "hall": "#eeddf5" if theme == "Modern Light" else "#2a1040",
                    "office": "#e8f5e9" if theme == "Modern Light" else "#0d260d",
                    "default": "#e8e8e8" if theme == "Modern Light" else "#1e1e2e",
                }
                ROOM_LABEL_COLORS = {
                    "bedroom": "#0d47a1", "bathroom": "#006064", "kitchen": "#e65100",
                    "living": "#558b2f", "corridor": "#444", "garage": "#5d4037",
                    "pool": "#0277bd", "garden": "#2e7d32", "hall": "#6a1b9a",
                    "office": "#1b5e20", "default": label_color,
                }

                # === ELEMENT BOUNDARIES ===
                r_data = st.session_state.current_rooms
                rooms_list = r_data.get('rooms', [])
                w_list = r_data.get('walls', []) or []
                o_list = r_data.get('openings', []) or []
                f_list = r_data.get('furniture', []) or []
                lbl_list = r_data.get('labels', []) or []
                all_elements = w_list + o_list + f_list

                if not all_elements:
                    st.warning(t("لا توجد بيانات رسم. يرجى توليد مخطط أولاً.", "No drawing data. Please generate a plan first."))
                else:
                    min_x = min([e.get('x', 0) for e in all_elements] + [0])
                    max_x = max([e.get('x', 0) + e.get('w', 0) for e in all_elements] + [1200])
                    min_y = min([e.get('y', 0) for e in all_elements] + [0])
                    max_y = max([e.get('y', 0) + e.get('h', 0) for e in all_elements] + [1200])

                    # Padding for dimension lines
                    PAD = max((max_x - min_x), (max_y - min_y)) * 0.18
                    vb_x0 = min_x - PAD
                    vb_y0 = min_y - PAD
                    vb_w = (max_x - min_x + PAD * 2) / zoom_level
                    vb_h = (max_y - min_y + PAD * 2) / zoom_level

                    svg = [f'<svg viewBox="{vb_x0} {vb_y0} {vb_w} {vb_h}" width="100%" height="auto" '
                           f'style="background:{bg_color}; border:3px solid {wall_stroke_col}; border-radius:10px; display:block; max-height:85vh;" '
                           f'xmlns="http://www.w3.org/2000/svg">']

                    # === DEFS: Patterns & Markers ===
                    svg.append('<defs>')
                    # Grid pattern
                    grid_col = "#ffffff" if theme != "Modern Light" else "#000000"
                    svg.append(f'<pattern id="grPt" width="100" height="100" patternUnits="userSpaceOnUse">'
                               f'<path d="M 100 0 L 0 0 0 100" fill="none" stroke="{grid_col}" stroke-opacity="0.06" stroke-width="1"/>'
                               f'</pattern>')
                    # Wall concrete hatch (diagonal lines)
                    svg.append(f'<pattern id="concreteHatch" width="8" height="8" patternTransform="rotate(45 0 0)" patternUnits="userSpaceOnUse">'
                               f'<line x1="0" y1="0" x2="0" y2="8" stroke="{wall_stroke_col}" stroke-opacity="0.5" stroke-width="2"/>'
                               f'</pattern>')
                    # Tile hatch (bathroom/kitchen)
                    svg.append(f'<pattern id="tileHatch" width="30" height="30" patternUnits="userSpaceOnUse">'
                               f'<rect x="0" y="0" width="29" height="29" fill="none" stroke="{line_color}" stroke-opacity="0.15" stroke-width="1"/>'
                               f'<line x1="15" y1="0" x2="15" y2="30" stroke="{line_color}" stroke-opacity="0.08" stroke-width="0.5"/>'
                               f'<line x1="0" y1="15" x2="30" y2="15" stroke="{line_color}" stroke-opacity="0.08" stroke-width="0.5"/>'
                               f'</pattern>')
                    # Dimension arrow markers
                    svg.append(f'<marker id="arrowStart" markerWidth="8" markerHeight="8" refX="0" refY="3" orient="auto">'
                               f'<path d="M8,0 L0,3 L8,6" fill="none" stroke="{dim_color}" stroke-width="1.5"/></marker>')
                    svg.append(f'<marker id="arrowEnd" markerWidth="8" markerHeight="8" refX="8" refY="3" orient="auto">'
                               f'<path d="M0,0 L8,3 L0,6" fill="none" stroke="{dim_color}" stroke-width="1.5"/></marker>')
                    svg.append('</defs>')

                    # Background + grid
                    svg.append(f'<rect x="{vb_x0}" y="{vb_y0}" width="{vb_w}" height="{vb_h}" fill="{bg_color}"/>')
                    svg.append(f'<rect x="{vb_x0}" y="{vb_y0}" width="{vb_w}" height="{vb_h}" fill="url(#grPt)"/>')

                    # === LAYER 1: ROOM FILLS (color-coded by type) ===
                    # Each room from the rooms list gets a colored fill
                    for room in rooms_list:
                        rx = float(room.get('x_m', room.get('x', 0))) * 100
                        ry = float(room.get('y_m', room.get('y', 0))) * 100
                        rw = float(room.get('width_m', room.get('w', 4))) * 100
                        rh = float(room.get('height_m', room.get('h', 4))) * 100
                        rtype = str(room.get('type', 'default')).lower()

                        # Determine room color
                        fill_c = ROOM_COLORS.get(rtype, ROOM_COLORS['default'])
                        for key in ROOM_COLORS:
                            if key in rtype:
                                fill_c = ROOM_COLORS[key]
                                break

                        # Determine fill pattern
                        fill_pattern = "none"
                        if "bathroom" in rtype or "toilet" in rtype or "حمام" in rtype:
                            fill_pattern = "url(#tileHatch)"
                        elif "kitchen" in rtype or "مطبخ" in rtype:
                            fill_pattern = "url(#tileHatch)"

                        svg.append(f'<rect x="{rx}" y="{ry}" width="{rw}" height="{rh}" '
                                   f'fill="{fill_c}" fill-opacity="0.9" rx="0"/>')
                        if fill_pattern != "none":
                            svg.append(f'<rect x="{rx}" y="{ry}" width="{rw}" height="{rh}" '
                                       f'fill="{fill_pattern}" fill-opacity="0.6"/>')

                    # === LAYER 2: LANDSCAPE / POOL / FURNITURE ===
                    for f in f_list:
                        fx, fy, fw, fh = f.get('x', 0), f.get('y', 0), max(f.get('w', 50), 20), max(f.get('h', 50), 20)
                        fname = f.get('name', '')
                        ftype = str(f.get('type', '')).lower()
                        fs = max(16 / zoom_level, 8)

                        if 'pool' in ftype or 'water' in ftype:
                            # Realistic pool with lane lines
                            svg.append(f'<rect x="{fx}" y="{fy}" width="{fw}" height="{fh}" fill="#0288d1" fill-opacity="0.6" stroke="#01579b" stroke-width="4" rx="20"/>')
                            svg.append(f'<rect x="{fx+8}" y="{fy+8}" width="{fw-16}" height="{fh-16}" fill="none" stroke="#29b6f6" stroke-width="2" rx="15" stroke-dasharray="20 10"/>')
                            svg.append(f'<text x="{fx+fw/2}" y="{fy+fh/2}" font-family="Arial" font-size="{fs}" fill="#e1f5fe" text-anchor="middle" dominant-baseline="middle" font-weight="bold">{fname}</text>')
                        elif 'green' in ftype or 'land' in ftype or 'garden' in ftype:
                            # Garden with tree symbols
                            svg.append(f'<rect x="{fx}" y="{fy}" width="{fw}" height="{fh}" fill="#2e7d32" fill-opacity="0.25" stroke="#388e3c" stroke-width="3" stroke-dasharray="15 5" rx="8"/>')
                            # Draw tree circles in a grid
                            tree_spacing = max(fw, fh) / 4
                            for ti in range(3):
                                for tj in range(3):
                                    tx = fx + tree_spacing * (ti + 0.5)
                                    ty = fy + tree_spacing * (tj + 0.5)
                                    if tx < fx + fw - 20 and ty < fy + fh - 20:
                                        tr = tree_spacing * 0.3
                                        svg.append(f'<circle cx="{tx}" cy="{ty}" r="{tr}" fill="#43a047" fill-opacity="0.6" stroke="#2e7d32" stroke-width="2"/>')
                                        svg.append(f'<circle cx="{tx}" cy="{ty}" r="{tr*0.4}" fill="#1b5e20" fill-opacity="0.8"/>')
                            svg.append(f'<text x="{fx+fw/2}" y="{fy+fh/2}" font-family="Arial" font-size="{fs}" fill="#1b5e20" text-anchor="middle" dominant-baseline="middle" font-weight="bold">{fname}</text>')
                        elif 'car' in ftype or 'park' in ftype or 'garage' in ftype:
                            svg.append(f'<rect x="{fx}" y="{fy}" width="{fw}" height="{fh}" fill="#90a4ae" fill-opacity="0.2" stroke="#607d8b" stroke-width="2" stroke-dasharray="10 5"/>')
                            svg.append(f'<text x="{fx+fw/2}" y="{fy+fh/2}" font-family="Arial" font-size="{fs}" fill="{label_color}" text-anchor="middle" dominant-baseline="middle">{fname}</text>')
                        elif 'bed' in ftype or 'نوم' in fname:
                            # Bed symbol
                            bw, bh = min(fw * 0.6, 160), min(fh * 0.5, 200)
                            bx, by = fx + fw/2 - bw/2, fy + fh/2 - bh/2
                            svg.append(f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" fill="#90caf9" fill-opacity="0.4" stroke="#42a5f5" stroke-width="2" rx="8"/>')
                            svg.append(f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh*0.25}" fill="#e3f2fd" fill-opacity="0.6" stroke="none" rx="4"/>')  # pillow
                            svg.append(f'<text x="{fx+fw/2}" y="{fy+fh*0.85}" font-family="Arial" font-size="{fs*0.8}" fill="{label_color}" text-anchor="middle" opacity="0.6">{fname}</text>')
                        elif 'kitchen' in ftype or 'مطبخ' in fname:
                            # Counter L-shape
                            counter_d = min(fw, fh) * 0.18
                            svg.append(f'<rect x="{fx}" y="{fy}" width="{fw}" height="{counter_d}" fill="#ffcc80" fill-opacity="0.5" stroke="#ef6c00" stroke-width="2"/>')
                            svg.append(f'<rect x="{fx}" y="{fy}" width="{counter_d}" height="{fh}" fill="#ffcc80" fill-opacity="0.5" stroke="#ef6c00" stroke-width="2"/>')
                        elif 'bath' in ftype or 'toilet' in ftype or 'حمام' in fname:
                            # Toilet + tub symbols
                            svg.append(f'<ellipse cx="{fx+fw*0.3}" cy="{fy+fh*0.7}" rx="{fw*0.18}" ry="{fh*0.22}" fill="#b2ebf2" fill-opacity="0.6" stroke="#00acc1" stroke-width="2"/>')
                            svg.append(f'<rect x="{fx+fw*0.12}" y="{fy+fh*0.55}" width="{fw*0.36}" height="{fh*0.15}" fill="#80deea" fill-opacity="0.6" stroke="#00acc1" stroke-width="1.5" rx="3"/>')
                        else:
                            if fname:
                                svg.append(f'<rect x="{fx}" y="{fy}" width="{fw}" height="{fh}" fill="{line_color}" fill-opacity="0.04" stroke="{line_color}" stroke-opacity="0.3" stroke-width="1.5" stroke-dasharray="8 4" rx="4"/>')
                                svg.append(f'<text x="{fx+fw/2}" y="{fy+fh/2}" font-family="Arial" font-size="{fs*0.8}" fill="{label_color}" text-anchor="middle" dominant-baseline="middle" opacity="0.7">{fname}</text>')

                    # === LAYER 3: WALLS (double-line with concrete fill) ===
                    for w in w_list:
                        wx, wy = w.get('x', 0), w.get('y', 0)
                        ww, wh = max(w.get('w', 20), 8), max(w.get('h', 20), 8)
                        is_ext = w.get('is_exterior', False)
                        s_width = "4" if is_ext else "2.5"
                        # Concrete-filled wall
                        svg.append(f'<rect x="{wx}" y="{wy}" width="{ww}" height="{wh}" '
                                   f'fill="url(#concreteHatch)" stroke="{wall_stroke_col}" stroke-width="{s_width}"/>')

                    # === LAYER 4: OPENINGS (doors with swing arcs + windows with triple lines) ===
                    import math
                    for o in o_list:
                        ox, oy = o.get('x', 0), o.get('y', 0)
                        ow, oh = max(o.get('w', 20), 8), max(o.get('h', 20), 8)
                        otype = str(o.get('type', '')).lower()
                        swing_angle = o.get('swing', 90)

                        if 'door' in otype:
                            # Clear the wall gap (with bg color)
                            svg.append(f'<rect x="{ox}" y="{oy}" width="{ow}" height="{oh}" fill="{bg_color}"/>')
                            # Determine orientation
                            is_horiz = ow >= oh
                            door_len = ow if is_horiz else oh

                            if is_horiz:
                                # Door leaf: line across
                                svg.append(f'<line x1="{ox}" y1="{oy+oh/2}" x2="{ox+door_len}" y2="{oy+oh/2}" '
                                           f'stroke="#ffd54f" stroke-width="3" stroke-linecap="round"/>')
                                # 90° swing arc
                                svg.append(f'<path d="M {ox} {oy+oh/2} A {door_len} {door_len} 0 0 1 {ox+door_len} {oy+oh/2+door_len}" '
                                           f'fill="none" stroke="#ffd54f" stroke-width="1.5" stroke-dasharray="8 4" opacity="0.8"/>')
                                # Hinge dot
                                svg.append(f'<circle cx="{ox}" cy="{oy+oh/2}" r="4" fill="#ffd54f" opacity="0.9"/>')
                            else:
                                # Vertical wall door
                                svg.append(f'<line x1="{ox+ow/2}" y1="{oy}" x2="{ox+ow/2}" y2="{oy+door_len}" '
                                           f'stroke="#ffd54f" stroke-width="3" stroke-linecap="round"/>')
                                svg.append(f'<path d="M {ox+ow/2} {oy} A {door_len} {door_len} 0 0 1 {ox+ow/2+door_len} {oy+door_len}" '
                                           f'fill="none" stroke="#ffd54f" stroke-width="1.5" stroke-dasharray="8 4" opacity="0.8"/>')
                                svg.append(f'<circle cx="{ox+ow/2}" cy="{oy}" r="4" fill="#ffd54f" opacity="0.9"/>')

                        else:  # Window
                            # Clear wall gap
                            svg.append(f'<rect x="{ox}" y="{oy}" width="{ow}" height="{oh}" fill="{bg_color}"/>')
                            wc = "#4dd0e1"
                            is_horiz = ow >= oh
                            if is_horiz:
                                mid = oy + oh / 2
                                # Triple line window symbol (architectural standard)
                                svg.append(f'<line x1="{ox}" y1="{oy+2}" x2="{ox+ow}" y2="{oy+2}" stroke="{wc}" stroke-width="2.5"/>')
                                svg.append(f'<line x1="{ox}" y1="{mid}" x2="{ox+ow}" y2="{mid}" stroke="{wc}" stroke-width="2" stroke-dasharray="15 0"/>')
                                svg.append(f'<line x1="{ox}" y1="{oy+oh-2}" x2="{ox+ow}" y2="{oy+oh-2}" stroke="{wc}" stroke-width="2.5"/>')
                                # Glass shine effect
                                svg.append(f'<rect x="{ox}" y="{oy}" width="{ow}" height="{oh}" fill="{wc}" fill-opacity="0.08"/>')
                            else:
                                mid = ox + ow / 2
                                svg.append(f'<line x1="{ox+2}" y1="{oy}" x2="{ox+2}" y2="{oy+oh}" stroke="{wc}" stroke-width="2.5"/>')
                                svg.append(f'<line x1="{mid}" y1="{oy}" x2="{mid}" y2="{oy+oh}" stroke="{wc}" stroke-width="2"/>')
                                svg.append(f'<line x1="{ox+ow-2}" y1="{oy}" x2="{ox+ow-2}" y2="{oy+oh}" stroke="{wc}" stroke-width="2.5"/>')
                                svg.append(f'<rect x="{ox}" y="{oy}" width="{ow}" height="{oh}" fill="{wc}" fill-opacity="0.08"/>')

                    # === LAYER 5: ROOM LABELS AND DIMENSIONS ===
                    WALL_T = 20  # average wall thickness in cm
                    for lbl in lbl_list:
                        lx, ly = lbl.get('x', 0), lbl.get('y', 0)
                        txt = lbl.get('text', '')
                        area = lbl.get('area_m2', '')
                        fs_lbl = max(22 / zoom_level, 10)
                        fs_area = max(16 / zoom_level, 8)

                        # Determine room type color for label
                        lbl_col = label_color
                        for key, col in ROOM_LABEL_COLORS.items():
                            if key in txt.lower():
                                lbl_col = col
                                break

                        # Room name with shadow-like effect
                        svg.append(f'<text x="{lx+1}" y="{ly-8}" font-family="Arial" font-weight="800" '
                                   f'font-size="{fs_lbl}" fill="#000000" fill-opacity="0.3" text-anchor="middle">{txt}</text>')
                        svg.append(f'<text x="{lx}" y="{ly-9}" font-family="Arial" font-weight="800" '
                                   f'font-size="{fs_lbl}" fill="{lbl_col}" text-anchor="middle">{txt}</text>')
                        if area:
                            svg.append(f'<text x="{lx}" y="{ly+fs_lbl*0.6}" font-family="monospace" '
                                       f'font-size="{fs_area}" fill="{lbl_col}" fill-opacity="0.75" text-anchor="middle">{area} m²</text>')

                    # === LAYER 6: PROFESSIONAL DIMENSION LINES ===
                    doff = PAD * 0.45  # offset from building edge
                    ds = max(16 / zoom_level, 7)
                    total_w_m = round((max_x - min_x) / 100, 1)
                    total_h_m = round((max_y - min_y) / 100, 1)

                    # Top horizontal dimension
                    dy_top = min_y - doff
                    svg.append(f'<g stroke="{dim_color}" fill="{dim_color}">')
                    svg.append(f'<line x1="{min_x}" y1="{dy_top}" x2="{max_x}" y2="{dy_top}" stroke-width="2" '
                               f'marker-start="url(#arrowStart)" marker-end="url(#arrowEnd)"/>')
                    svg.append(f'<line x1="{min_x}" y1="{min_y - doff*0.2}" x2="{min_x}" y2="{dy_top + doff*0.2}" stroke-width="1.5"/>')
                    svg.append(f'<line x1="{max_x}" y1="{min_y - doff*0.2}" x2="{max_x}" y2="{dy_top + doff*0.2}" stroke-width="1.5"/>')
                    svg.append(f'<rect x="{(min_x+max_x)/2 - ds*2.5}" y="{dy_top - ds*1.2}" width="{ds*5}" height="{ds*1.5}" fill="{bg_color}" rx="2"/>')
                    svg.append(f'<text x="{(min_x+max_x)/2}" y="{dy_top - ds*0.1}" font-family="Arial" font-size="{ds}" '
                               f'fill="{dim_color}" text-anchor="middle" font-weight="bold">{total_w_m} م</text>')
                    svg.append('</g>')

                    # Left vertical dimension
                    dx_left = min_x - doff
                    svg.append(f'<g stroke="{dim_color}" fill="{dim_color}">')
                    svg.append(f'<line x1="{dx_left}" y1="{min_y}" x2="{dx_left}" y2="{max_y}" stroke-width="2" '
                               f'marker-start="url(#arrowStart)" marker-end="url(#arrowEnd)"/>')
                    svg.append(f'<line x1="{min_x - doff*0.2}" y1="{min_y}" x2="{dx_left + doff*0.2}" y2="{min_y}" stroke-width="1.5"/>')
                    svg.append(f'<line x1="{min_x - doff*0.2}" y1="{max_y}" x2="{dx_left + doff*0.2}" y2="{max_y}" stroke-width="1.5"/>')
                    mid_yr = (min_y + max_y) / 2
                    svg.append(f'<rect x="{dx_left - ds*1.5}" y="{mid_yr - ds*2.5}" width="{ds*5}" height="{ds*1.5}" fill="{bg_color}" rx="2" '
                               f'transform="rotate(-90 {dx_left} {mid_yr})"/>')
                    svg.append(f'<text x="{dx_left - ds*0.5}" y="{mid_yr}" font-family="Arial" font-size="{ds}" '
                               f'fill="{dim_color}" text-anchor="middle" font-weight="bold" '
                               f'transform="rotate(-90 {dx_left-ds*0.5} {mid_yr})">{total_h_m} م</text>')
                    svg.append('</g>')

                    # Per-room dimension labels (inside room, small)
                    for room in rooms_list:
                        rx = float(room.get('x_m', room.get('x', 0))) * 100
                        ry = float(room.get('y_m', room.get('y', 0))) * 100
                        rw = float(room.get('width_m', room.get('w', 4))) * 100
                        rh = float(room.get('height_m', room.get('h', 4))) * 100
                        w_m = round(rw / 100, 1)
                        h_m = round(rh / 100, 1)
                        fs_d = max(11 / zoom_level, 6)
                        # Small width dim at top of room
                        svg.append(f'<text x="{rx+rw/2}" y="{ry+fs_d*1.5}" font-family="monospace" font-size="{fs_d}" '
                                   f'fill="{dim_color}" text-anchor="middle" opacity="0.7">{w_m}م</text>')
                        # Small height dim at left of room (rotated)
                        svg.append(f'<text x="{rx+fs_d*1.5}" y="{ry+rh/2}" font-family="monospace" font-size="{fs_d}" '
                                   f'fill="{dim_color}" text-anchor="middle" opacity="0.7" '
                                   f'transform="rotate(-90 {rx+fs_d*1.5} {ry+rh/2})">{h_m}م</text>')

                    # === LAYER 7: NORTH ARROW ===
                    na_x, na_y, na_r = vb_x0 + vb_w * 0.06, vb_y0 + vb_h * 0.07, vb_w * 0.025
                    svg.append(f'<g transform="translate({na_x},{na_y})">')
                    svg.append(f'<circle r="{na_r}" fill="{bg_color}" stroke="{line_color}" stroke-width="2" opacity="0.9"/>')
                    svg.append(f'<polygon points="0,{-na_r*0.85} {na_r*0.3},0 0,{na_r*0.3}" fill="{dim_color}" opacity="0.95"/>')
                    svg.append(f'<polygon points="0,{-na_r*0.85} {-na_r*0.3},0 0,{na_r*0.3}" fill="{line_color}" fill-opacity="0.5"/>')
                    svg.append(f'<text y="{-na_r*1.25}" font-family="Arial Black" font-size="{na_r*0.7}" fill="{dim_color}" text-anchor="middle" font-weight="900">N</text>')
                    svg.append('</g>')

                    # === LAYER 8: SCALE BAR ===
                    scale_w_m = max(5, int(total_w_m / 4))
                    scale_px = scale_w_m * 100
                    sb_x = max_x + PAD * 0.05
                    sb_y = max_y + PAD * 0.3
                    sb_seg = scale_px / 5
                    svg.append(f'<g stroke="{line_color}" fill="{line_color}">')
                    for si in range(5):
                        seg_fill = line_color if si % 2 == 0 else bg_color
                        svg.append(f'<rect x="{sb_x + si*sb_seg}" y="{sb_y}" width="{sb_seg}" height="{scale_px*0.06}" '
                                   f'fill="{seg_fill}" stroke="{line_color}" stroke-width="1.5"/>')
                    svg.append(f'<text x="{sb_x}" y="{sb_y - 8}" font-family="monospace" font-size="{ds}" fill="{line_color}" text-anchor="start">0</text>')
                    svg.append(f'<text x="{sb_x + scale_px}" y="{sb_y - 8}" font-family="monospace" font-size="{ds}" fill="{line_color}" text-anchor="end">{scale_w_m}م</text>')
                    svg.append(f'<text x="{sb_x + scale_px/2}" y="{sb_y + scale_px*0.06 + ds*1.3}" font-family="monospace" font-size="{ds*0.85}" fill="{line_color}" text-anchor="middle" opacity="0.7">مقياس رسم 1:100</text>')
                    svg.append('</g>')

                    # === LAYER 9: PROFESSIONAL TITLE BLOCK ===
                    proj_info = r_data.get('project_info', {})
                    proj_title = proj_info.get('title', t('مشروع سكني', 'Residential Project'))
                    proj_style = proj_info.get('style', style_3d)
                    total_area = proj_info.get('total_area', round(total_w_m * total_h_m, 0))
                    tb_w = vb_w * 0.25
                    tb_h = vb_h * 0.15
                    tb_x = vb_x0 + vb_w - tb_w - vb_w * 0.01
                    tb_y = vb_y0 + vb_h - tb_h - vb_h * 0.01
                    tfs = max(ds * 0.85, 6)
                    svg.append(f'<rect x="{tb_x}" y="{tb_y}" width="{tb_w}" height="{tb_h}" fill="{bg_color}" fill-opacity="0.95" stroke="{wall_stroke_col}" stroke-width="3"/>')
                    svg.append(f'<line x1="{tb_x}" y1="{tb_y + tb_h*0.28}" x2="{tb_x+tb_w}" y2="{tb_y + tb_h*0.28}" stroke="{line_color}" stroke-width="2.5"/>')
                    svg.append(f'<line x1="{tb_x}" y1="{tb_y + tb_h*0.60}" x2="{tb_x+tb_w}" y2="{tb_y + tb_h*0.60}" stroke="{line_color}" stroke-width="1.5"/>')
                    svg.append(f'<line x1="{tb_x + tb_w*0.5}" y1="{tb_y + tb_h*0.28}" x2="{tb_x + tb_w*0.5}" y2="{tb_y + tb_h}" stroke="{line_color}" stroke-width="1.5"/>')
                    svg.append(f'<text x="{tb_x + tb_w/2}" y="{tb_y + tb_h*0.2}" font-family="Arial Black" font-size="{tfs*1.2}" fill="{dim_color}" text-anchor="middle" font-weight="900" letter-spacing="1">EngiCost AI V3.0 PRO 🏆</text>')
                    svg.append(f'<text x="{tb_x + tb_w*0.25}" y="{tb_y + tb_h*0.47}" font-family="Arial" font-size="{tfs}" fill="{line_color}" text-anchor="middle">{proj_title[:20]}</text>')
                    svg.append(f'<text x="{tb_x + tb_w*0.75}" y="{tb_y + tb_h*0.47}" font-family="Arial" font-size="{tfs}" fill="{line_color}" text-anchor="middle">{proj_style[:15]}</text>')
                    svg.append(f'<text x="{tb_x + tb_w*0.25}" y="{tb_y + tb_h*0.78}" font-family="Arial" font-size="{tfs}" fill="{line_color}" text-anchor="middle">{bed_count} نوم / {bath_count} حمام</text>')
                    svg.append(f'<text x="{tb_x + tb_w*0.75}" y="{tb_y + tb_h*0.78}" font-family="Arial" font-size="{tfs}" fill="{line_color}" text-anchor="middle">مساحة: {total_area} م²</text>')
                    svg.append(f'<text x="{tb_x + tb_w/2}" y="{tb_y + tb_h*0.95}" font-family="monospace" font-size="{tfs*0.75}" fill="{line_color}" fill-opacity="0.55" text-anchor="middle">المساقط الأفقية — مقياس 1:100</text>')

                    svg.append('</svg>')
                    final_svg = "\n".join(svg)
                    st.session_state.last_svg = final_svg

                    import streamlit.components.v1 as components
                    components.html(final_svg, height=max(700, int(vb_h * zoom_level * 0.55)), scrolling=True)

                    # --- EXPORT AND INTEGRATION BUTTONS ---
                    col_dxf, col_svg, col_pdf, col_boq = st.columns([1, 1, 1, 1.5])
                    with col_svg:
                        st.download_button(t("📥 SVG", "SVG"), data=final_svg, file_name="engi_plan.svg", mime="image/svg+xml", use_container_width=True)

                
                with col_dxf:
                    try:
                        from ai_engine.dxf_generator import generate_dxf_from_json
                        dxf_bytes = generate_dxf_from_json(r_data)
                        st.download_button(t("📐 DXF", "DXF"), data=dxf_bytes, file_name="engi_plan.dxf", mime="application/dxf", use_container_width=True)
                    except Exception as e:
                        st.error(f"DXF Error: {e}")
                        
                with col_pdf:
                    try:
                         from ai_engine.pdf_generator import generate_pdf_report
                         ptype = r_data.get("project_info", {}).get("project_type", specialty)
                         pdf_bytes = generate_pdf_report(final_svg, r_data, ptype, st.session_state.get('finishings_concept', ''))
                         st.download_button(t("📄 PDF التقرير", "PDF Report"), data=pdf_bytes, file_name="engi_plan.pdf", mime="application/pdf", use_container_width=True)
                    except Exception as e:
                         st.error(f"PDF Error: {e}")
                
                with col_boq:
                    # Area Calculation for BOQ Integration
                    walls = r_data.get('walls', [])
                    if walls:
                        min_w = min((w.get("x", 0) for w in walls), default=0)
                        max_w = max((w.get("x", 0) + w.get("w", 0) for w in walls), default=800)
                        min_h = min((w.get("y", 0) for w in walls), default=0)
                        max_h = max((w.get("y", 0) + w.get("h", 0) for w in walls), default=800)
                        # Scale: 100 units = 1 meter approx. 
                        w_m = abs(max_w - min_w) / 100.0
                        h_m = abs(max_h - min_h) / 100.0
                        calc_area = round((w_m * h_m) * float(floor_count))
                        if calc_area < 50: calc_area = 150 * floor_count
                    else:
                        calc_area = 150 * floor_count
                        
                    btn_text_ar = f"💰 تسعير هذا المخطط (المساحة المبدئية: {calc_area} م²)"
                    btn_text_en = f"💰 Calculate BOQ (Est. Area: {calc_area} m²)"
                    if st.button(t(btn_text_ar, btn_text_en), type="primary", use_container_width=True):
                        # Construct a dynamic prompt insert for the AI BOQ parser
                        transfer_text = f"""[توليد تلقائي من أداة الرسم الذكية]
يرجى عمل مقايسة تقديرية كميات وأسعار شاملة لإنشاء مشروع بناء بالمواصفات التالية:
- طراز المبنى: {style_3d}
- المساحة الإجمالية للمباني: {calc_area} متر مربع
- عدد الأدوار: {floor_count} طوابق
- عدد غرف النوم: {bed_count}
- عدد الحمامات: {bath_count}
- إضافات: {"مسبح، " if pool_opt else ""}{"لاندسكيب وحديقة، " if landscaping else ""}
"""
                        st.session_state.boq_transfer_data = transfer_text
                        st.session_state.survey_area = calc_area
                        st.toast(t("تم ترحيل البيانات بنجاح! اذهب لتبويب 'Cost Engine' للبدء في التسعير.", "Data transferred successfully! Go to 'Cost Engine' tab to begin pricing."), icon="✅")


            # --- Concept Finishes & Decor (4D/9D) ---
            st.markdown("---")
            if st.button(t("✨ اقتراح تصميم التشطيبات والديكورات (Interior & Decor Concept)", "Suggest Interior & Decor Concept"), use_container_width=True):
                with st.spinner(t("يتم تصميم الديكورات وتوزيع الخامات عبر الذكاء الاصطناعي...", "Designing decors and mapping materials...")):
                    layout_str = str(r_data)[:2000]
                    prompt_decor = f"Based on this layout: {layout_str}. Provide a comprehensive interior design and finishes concept for the key areas. Suggest specific materials (e.g. Carrara Marble, Oak Wood), lighting concepts, and color palettes. Be very professional and describe the aesthetic."
                    try:
                        from ai_engine.cost_engine import get_cost_engine
                        res_decor, _ = get_cost_engine()._call_gemini_text(prompt_decor)
                        st.session_state.finishings_concept = res_decor
                    except Exception as ed:
                        st.error(f"Decor Error: {ed}")
                        
            if st.session_state.get('finishings_concept'):
                st.markdown(f"#### ✨ " + t("رؤية التصميم والتشطيبات", "Decor & Finishings Vision"))
                st.info(st.session_state.finishings_concept)

                # --- BIM Summary & Analysis ---
                st.markdown("---")
                st.markdown(f"#### 🧺 " + t("استخراج الكميات والتحليل الهندسي", "BIM Quantification & Analysis"))
                
                total_area = sum([(w.get('w',0)*w.get('h',0))/10000 for w in r_data.get('walls', [])])
                
                q1, q2, q3 = st.columns(3)
                with q1: st.metric(t("المساحة التقريبية للمكونات", "Est. Area"), f"{total_area:.2f} m²")
                with q2: st.metric(t("المكونات", "Components"), total_elements)
                with q3: st.metric(t("محيط مبدئي", "Est. Perimeter"), f"{(total_area**0.5)*4:.1f} m")
                
                if st.button(t("🧠 تحليل المخطط هندسياً (EngiAnalysis AI)", "Run EngiAnalysis AI"), use_container_width=True):
                    with st.spinner(t("جاري تحليل المخطط وتفكيك البنود...", "Analyzing plan...")):
                        try:
                            from ai_engine.cost_engine import get_cost_engine
                            engine = get_cost_engine()
                            analysis_prompt = f"""
                            Analyze this layout for {specialty}: {json.dumps(r_data)}
                            Original: {prompt}
                            Generate BOQ list in JSON format: [{{ "description": "Item Name (Ar/En)", "unit": "unit", "quantity": float, "category": "{specialty}" }}]
                            Include: Concrete, Rebar weight, Finishing layers, Doors, Windows, and other relevant items.
                            """
                            analysis_res, _ = engine._call_groq(analysis_prompt, expect_json=True)
                            
                            items = []
                            if isinstance(analysis_res, str):
                                json_match = re.search(r'\[.*\]', analysis_res, re.DOTALL)
                                items = json.loads(json_match.group(0)) if json_match else []
                            else:
                                items = analysis_res if isinstance(analysis_res, list) else []
                            
                            st.session_state.analysis_items = items
                            st.rerun() # Refresh to show table
                        except Exception as ae:
                            st.error(f"Analysis Error: {ae}")

                # --- Analysis Results Display ---
                if st.session_state.analysis_items:
                    st.markdown(f"#### 📋 " + t("نتائج الحصر والتسعير الآلي", "Auto-Quantification & Pricing"))
                    
                    if "priced_analysis" not in st.session_state:
                         st.session_state.priced_analysis = None
                         st.session_state.analysis_total_cost = 0.0
                         
                    # Auto Price Button
                    if st.button("💲 " + t("تسعير هذا الحصر آلياً", "Auto-Price BOQ"), use_container_width=True):
                         with st.spinner(t("جاري تسعير البنود من أسعار السوق...", "Fetching live market prices...")):
                             from ai_engine.cost_engine import get_cost_engine
                             engine = get_cost_engine()
                             prices = engine.suggest_market_prices(st.session_state.analysis_items)
                             
                             priced_items = []
                             total_project_cost = 0.0
                             for idx, item in enumerate(st.session_state.analysis_items):
                                 price = float(prices.get(str(idx), 0))
                                 qty = float(item.get("quantity", 0))
                                 cost = price * qty
                                 total_project_cost += cost
                                 
                                 new_item = item.copy()
                                 new_item["Unit Price"] = price
                                 new_item["Total Cost"] = cost
                                 priced_items.append(new_item)
                                 
                             st.session_state.priced_analysis = priced_items
                             st.session_state.analysis_total_cost = total_project_cost
                             st.rerun()

                    if st.session_state.priced_analysis:
                        st.info(f"💰 **{t('إجمالي التكلفة التقريبية:', 'Total Estimated Cost:')} {st.session_state.analysis_total_cost:,.2f}**")
                        df_ana = pd.DataFrame(st.session_state.priced_analysis)
                    else:
                        df_ana = pd.DataFrame(st.session_state.analysis_items)
                        
                    st.dataframe(df_ana, use_container_width=True)
                    
                    if st.button(t("🚀 تصدير كافة البنود للمقايسة", "Export All Items to BOQ"), use_container_width=True):
                        current_boq = st.session_state.get("boq_data", [])
                        if not isinstance(current_boq, list): current_boq = []
                        current_boq.extend(st.session_state.analysis_items)
                        st.session_state.boq_data = current_boq
                        
                        # Set flag to clear search to ensure target category is visible
                        st.session_state.clear_search_flag = True
                        
                        # Use standardized navigation jump
                        st.session_state.selected_cat_manual = t("💰 العطاءات والتسعير", "💰 Bidding & Pricing")
                        st.session_state.nav_selection_manual = t("💰 تسعير المقايسات (Pro)", "💰 BOQ Pricing (Pro)")
                        
                        st.success(t("تم التصدير! جاري الانتقال للتسعير...", "Exported! Redirecting..."))
                        st.rerun()

                # --- AI Photorealistic Concept Render (8K) ---
                st.markdown("---")
                st.markdown(f"#### 📸 " + t("الريندر الاحترافي ثلاثي الأبعاد (DALL-E 3 / Nano-Render)", "Professional 3D Render (DALL-E 3 / Nano-Render)"))
                
                view_type = st.radio(t("نوع اللقطة (View Type)", "View Type"), 
                                     ["Isometric (مسقط ثلاثي الأبعاد)", "Perspective (منظور خارجي)", "Interior (منظور داخلي)"], 
                                     horizontal=True)
                
                render_prompt_custom = st.text_input(
                    t("تخصيص اللقطة (إضاءة، تفاصيل، ليلية/نهارية...)", "Customize Shot (Lighting, Details, Day/Night...)"), 
                    placeholder=t("مثال: لقطة ليلية مع إضاءة دافئة وعدسة سينمائية...", "e.g., Night shot with warm lighting and cinematic lens...")
                )
                
                if st.button("✨ " + t("توليد الريندر ثلاثي الأبعاد الآن", "Generate 3D Render Now"), use_container_width=True, type="secondary"):
                    with st.spinner(t("جاري بناء المشهد ورندرة الإضاءة والخامات بجودة فائقة (قد يستغرق 30 ثانية)...", "Rendering scene lighting and materials in ultra-high quality...")):
                        from ai_engine.drawing_brain import generate_3d_render
                        
                        prompt_context = render_prompt_custom
                        if st.session_state.get('finishings_concept'):
                            fc = str(st.session_state.get('finishings_concept', ''))[:150]
                            prompt_context += f" | Interior/Exterior Concept: {fc}"
                            
                        # Clean view_type name for API
                        vt_api = "Isometric" if "Isometric" in view_type else "Perspective" if "Perspective" in view_type else "Interior"
                        
                        img_url = generate_3d_render(
                            prompt=prompt_context,
                            style=style_3d,
                            view_type=vt_api,
                            specialty=specialty
                        )
                        
                        st.session_state.last_render_url = img_url
                        
                if "last_render_url" in st.session_state:
                    st.image(st.session_state.last_render_url, use_container_width=True)
                    col_dl, col_blank = st.columns([1, 2])
                    with col_dl:
                        st.markdown(f"<a href='{st.session_state.last_render_url}' download='EngiCost_Render.jpg' target='_blank' style='display: block; text-align: center; background-color: #0ea5e9; color: white; padding: 10px; border-radius: 8px; text-decoration: none; font-weight: bold;'>📥 {t('تحميل بجودة 8K', 'Download 8K Resolution')}</a>", unsafe_allow_html=True)

    # ─── Tab 3: Perspective Drawing ──────────────────────────────
    with tabs[2]:
        _render_perspective_tab(t, zoom_level, theme, st.session_state.get('current_rooms'))

    # ─── Tab 4: Elevation Views ────────────────────────────────────
    with tabs[3]:
        _render_elevation_tab(t, zoom_level, theme, st.session_state.get('current_rooms'), floor_count if 'floor_count' in dir() else 1)

    # ─── Tab 5: AI Plan Scanner ────────────────────────────────────
    with tabs[4]:
        _render_ai_scanner_tab(t)

    # ─── Tab 2: Structural Sections (Offline) ────────────────────
    with tabs[1]:
        st.markdown(f"#### 🏗️ {t('توليد تفاصيل إنشائية احترافية (CAD Style)', 'Automated Offline Structural Detailing')}")
        
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            m_type = st.selectbox(t("نوع العنصر", "Element Type"), [t("عمود (Column)", "Column"), t("كمرة (Beam)", "Beam"), t("قاعدة منفصلة (Footing)", "Isolated Footing"), t("بلاطة (Solid Slab)", "Solid Slab")], key="sc_mtype")
        with c2:
            w_val = st.number_input(t("العرض B (mm)", "Width (mm)"), value=300, step=50, max_value=5000)
            cover = st.number_input(t("الغطاء (Cover mm)", "Cover (mm)"), value=25, min_value=15, max_value=75)
        with c3:
            d_val = st.number_input(t("العمق/السمك T (mm)", "Depth/Thickness (mm)"), value=600, step=50, max_value=5000)
            rebar_dia = st.number_input(t("قطر السيخ Φ (mm)", "Rebar Dia (mm)"), value=16, step=2)
        with c4:
            bars_count = st.number_input(t("عدد الأسياخ (n)", "Bars Count"), value=6, min_value=2)
            if t("قاعدة", "Footing") in m_type or t("بلاطة", "Slab") in m_type:
                bars_y = st.number_input(t("أسياخ الاتجاه الآخر", "Transverse Bars"), value=6, min_value=2)
            else:
                stirrup_dia = st.number_input(t("قطر الكانة (mm)", "Stirrup Dia (mm)"), value=8, step=2)

        if st.button(t("🖋️ توليد لوحة التسليح (Generate CAD Detail)", "🖋️ Generate CAD Detail"), type="primary", use_container_width=True):
            fig = go.Figure()

            # Colors for CAD Style
            c_conc = "#ffffff"  # Concrete Outline
            c_rebar = "#00ff00" # Main Rebar
            c_sec = "#ffff00"   # Secondary/Stirrups
            c_dim = "#00ffff"   # Dimensions
            
            # --- Draw Concrete Outline ---
            fig.add_shape(type="rect", x0=0, y0=0, x1=w_val, y1=d_val, line=dict(color=c_conc, width=3))
            
            # --- Draw Internal Details based on Element ---
            if t("عمود", "Column") in m_type or t("كمرة", "Beam") in m_type:
                # 1. Stirrup
                fig.add_shape(type="rect", x0=cover, y0=cover, x1=w_val-cover, y1=d_val-cover, line=dict(color=c_sec, width=2), rx=5, ry=5)
                # Stirrup Locks (Hooks)
                fig.add_shape(type="line", x0=cover, y0=d_val-cover, x1=cover+40, y1=d_val-cover-40, line=dict(color=c_sec, width=2))
                fig.add_shape(type="line", x0=cover, y0=d_val-cover, x1=cover+40, y1=d_val-cover+10, line=dict(color=c_sec, width=2))

                # 2. Main Rebars
                top_bars = bars_count // 2
                bot_bars = bars_count - top_bars
                
                # Bottom Bars
                if bot_bars > 1:
                    spacing_x = (w_val - 2*cover - rebar_dia) / (bot_bars - 1)
                    for i in range(bot_bars):
                        bx = cover + (rebar_dia/2) + (i * spacing_x)
                        by = cover + (rebar_dia/2)
                        fig.add_shape(type="circle", x0=bx-rebar_dia/2, y0=by-rebar_dia/2, x1=bx+rebar_dia/2, y1=by+rebar_dia/2, fillcolor=c_rebar, line_color=c_rebar)
                
                # Top Bars
                if top_bars > 1:
                    spacing_x = (w_val - 2*cover - rebar_dia) / (top_bars - 1)
                    for i in range(top_bars):
                        bx = cover + (rebar_dia/2) + (i * spacing_x)
                        by = d_val - cover - (rebar_dia/2)
                        fig.add_shape(type="circle", x0=bx-rebar_dia/2, y0=by-rebar_dia/2, x1=bx+rebar_dia/2, y1=by+rebar_dia/2, fillcolor=c_rebar, line_color=c_rebar)

            elif t("قاعدة", "Footing") in m_type:
                # Draw Plain Concrete (PC) below Reinforced Concrete (RC)
                pc_thick = 100
                pc_offset = 100
                fig.add_shape(type="rect", x0=-pc_offset, y0=-pc_thick, x1=w_val+pc_offset, y1=0, line=dict(color="#888888", width=2, dash="dashdot"))
                fig.add_annotation(x=w_val/2, y=-pc_thick/2, text="P.C. Footing", showarrow=False, font=dict(color="#8888"))
                
                # Bottom Mesh (X direction - Dots)
                spacing_x = (w_val - 2*cover) / max((bars_count - 1), 1)
                for i in range(bars_count):
                    bx = cover + (i * spacing_x)
                    by = cover + (rebar_dia/2)
                    fig.add_shape(type="circle", x0=bx-rebar_dia/2, y0=by-rebar_dia/2, x1=bx+rebar_dia/2, y1=by+rebar_dia/2, fillcolor=c_rebar, line_color=c_rebar)
                    
                # Bottom Mesh (Y direction - Line)
                fig.add_shape(type="line", x0=cover, y0=cover+rebar_dia*1.5, x1=w_val-cover, y1=cover+rebar_dia*1.5, line=dict(color=c_sec, width=3))
                # U-Shape Hooks
                fig.add_shape(type="line", x0=cover, y0=cover+rebar_dia*1.5, x1=cover, y1=d_val-cover, line=dict(color=c_sec, width=3))
                fig.add_shape(type="line", x0=w_val-cover, y0=cover+rebar_dia*1.5, x1=w_val-cover, y1=d_val-cover, line=dict(color=c_sec, width=3))
                
                # Column neck stub
                fig.add_shape(type="line", x0=w_val/2-150, y0=d_val, x1=w_val/2-150, y1=d_val+500, line=dict(color=c_conc, width=2))
                fig.add_shape(type="line", x0=w_val/2+150, y0=d_val, x1=w_val/2+150, y1=d_val+500, line=dict(color=c_conc, width=2))
                # Column dowels
                fig.add_shape(type="line", x0=w_val/2-100, y0=cover+rebar_dia*2, x1=w_val/2-100, y1=d_val+600, line=dict(color="#ff00ff", width=3))
                fig.add_shape(type="line", x0=w_val/2+100, y0=cover+rebar_dia*2, x1=w_val/2+100, y1=d_val+600, line=dict(color="#ff00ff", width=3))
                fig.add_shape(type="line", x0=w_val/2-100, y0=cover+rebar_dia*2, x1=w_val/2-250, y1=cover+rebar_dia*2, line=dict(color="#ff00ff", width=3)) # Dowel leg
                fig.add_shape(type="line", x0=w_val/2+100, y0=cover+rebar_dia*2, x1=w_val/2+250, y1=cover+rebar_dia*2, line=dict(color="#ff00ff", width=3)) # Dowel leg

            elif t("بلاطة", "Slab") in m_type:
                # Draw Bottom Mesh
                fig.add_shape(type="line", x0=0, y0=cover, x1=w_val, y1=cover, line=dict(color=c_rebar, width=3))
                spacing_x = w_val / max((bars_count - 1), 1)
                for i in range(bars_count):
                    bx = (i * spacing_x)
                    by = cover + rebar_dia
                    fig.add_shape(type="circle", x0=bx-rebar_dia/2, y0=by-rebar_dia/2, x1=bx+rebar_dia/2, y1=by+rebar_dia/2, fillcolor=c_sec, line_color=c_sec)
                
                # Draw Top Mesh (if thickness > 160mm typically)
                if d_val >= 160:
                    fig.add_shape(type="line", x0=0, y0=d_val-cover, x1=w_val, y1=d_val-cover, line=dict(color=c_rebar, width=3))
                    for i in range(bars_count):
                        bx = (i * spacing_x)
                        by = d_val - cover - rebar_dia
                        fig.add_shape(type="circle", x0=bx-rebar_dia/2, y0=by-rebar_dia/2, x1=bx+rebar_dia/2, y1=by+rebar_dia/2, fillcolor=c_sec, line_color=c_sec)

            # --- Add Dimensions (CAD Line) ---
            # Horizontal
            fig.add_shape(type="line", x0=0, y0=-80, x1=w_val, y1=-80, line=dict(color=c_dim, width=1))
            fig.add_shape(type="line", x0=0, y0=-100, x1=0, y1=0, line=dict(color=c_dim, width=1))
            fig.add_shape(type="line", x0=w_val, y0=-100, x1=w_val, y1=0, line=dict(color=c_dim, width=1))
            fig.add_annotation(x=w_val/2, y=-110, text=f"B = {w_val} mm", showarrow=False, font=dict(color=c_dim, size=14))
            
            # Vertical
            fig.add_shape(type="line", x0=-80, y0=0, x1=-80, y1=d_val, line=dict(color=c_dim, width=1))
            fig.add_shape(type="line", x0=-100, y0=0, x1=0, y1=0, line=dict(color=c_dim, width=1))
            fig.add_shape(type="line", x0=-100, y0=d_val, x1=0, y1=d_val, line=dict(color=c_dim, width=1))
            fig.add_annotation(x=-110, y=d_val/2, text=f"T = {d_val} mm", showarrow=False, font=dict(color=c_dim, size=14), textangle=-90)

            # Render
            max_dim = max(w_val, d_val)
            padding = max_dim * 0.2
            fig.update_layout(
                paper_bgcolor="#000000", plot_bgcolor="#000000", font_family="monospace",
                height=600, margin=dict(l=50, r=50, t=50, b=50),
                xaxis=dict(showgrid=False, zeroline=False, visible=False, range=[-padding, w_val+padding]), 
                yaxis=dict(showgrid=False, zeroline=False, visible=False, scaleanchor="x", scaleratio=1, range=[-padding, d_val+padding])
            )
            
            st.plotly_chart(fig, use_container_width=True)
            st.info(f"💡 **CAD Detail:** Generated {m_type} reinforcement section with {bars_count}Φ{rebar_dia} main bars and {cover}mm cover.")

    # ─── Export Section ───
    st.markdown("---")
    if "last_svg" in st.session_state and st.session_state.last_svg:
        st.download_button("📤 " + t("تحميل التصميم المعماري (SVG/CAD)", "Download Architectural Design (SVG/CAD)"), 
                           st.session_state.last_svg, "engi_draft.svg", "image/svg+xml", use_container_width=True)

# ══════════════════════════════════════════════════════════════════
# TAB 3: PERSPECTIVE DRAWING ENGINE
# ══════════════════════════════════════════════════════════════════
def _render_perspective_tab(t, zoom_level, theme, rooms_data):
    st.markdown(f"#### 📏 {t('محرك المنظور الهندسي ثنائي نقطة التلاشي (2-Point Perspective)', 'Two-Point Perspective Drawing Engine')}")
    st.caption(t("يرسم المنظور الهندسي الاحترافي بنقطتي تلاشي تلقائياً من بيانات المخطط أو بإدخال يدوي.",
                 "Automatically generates a professional two-point perspective from plan data or manual input."))

    # Controls
    pc1, pc2, pc3, pc4, pc5 = st.columns(5)
    with pc1:
        bld_width = st.number_input(t("عرض المبنى (م)", "Building Width (m)"), 5.0, 50.0, 12.0, 1.0)
    with pc2:
        bld_depth = st.number_input(t("عمق المبنى (م)", "Building Depth (m)"), 5.0, 50.0, 10.0, 1.0)
    with pc3:
        bld_height = st.number_input(t("ارتفاع الطابق (م)", "Floor Height (m)"), 2.5, 6.0, 3.5, 0.5)
    with pc4:
        num_floors = st.number_input(t("عدد الأدوار", "Floors"), 1, 8, 2)
    with pc5:
        persp_angle = st.slider(t("زاوية الرؤية°", "View Angle°"), 10, 80, 40)

    # Window count row
    wc1, wc2, wc3, wc4 = st.columns(4)
    with wc1: win_front = st.number_input(t("نوافذ الواجهة الأمامية", "Front Windows"), 0, 10, 3)
    with wc2: win_side = st.number_input(t("نوافذ الواجهة الجانبية", "Side Windows"), 0, 6, 2)
    with wc3: has_balcony = st.toggle(t("شرفة/بلكونة", "Balcony"), value=True)
    with wc4: has_entrance = st.toggle(t("مدخل رئيسي بارز", "Main Entrance"), value=True)

    if theme == "AutoCAD Dark":
        p_bg, p_line, p_vp, p_dim, p_win = "#0d0d0d", "#cccccc", "#00d4ff", "#ffff00", "#4dd0e1"
    elif theme == "Blueprint":
        p_bg, p_line, p_vp, p_dim, p_win = "#0a2744", "#dce8f5", "#ffdd57", "#fbbf24", "#29b6f6"
    else:
        p_bg, p_line, p_vp, p_dim, p_win = "#f8f9fa", "#1a1a2e", "#1565c0", "#e53935", "#0288d1"

    import math
    # Canvas dimensions
    CW, CH = 1400, 900
    # Horizon line at ~55% height
    HL = CH * 0.52
    # Vanishing points
    angle_rad = math.radians(persp_angle)
    vp_dist = CW * 1.8
    VPL_X = CW / 2 - vp_dist * math.cos(angle_rad)
    VPR_X = CW / 2 + vp_dist * math.cos(angle_rad)
    VP_Y = HL
    
    # Building corner (front vertical edge) — center of canvas
    CORNER_X = CW / 2
    SCALE = 30  # px per meter
    TOTAL_H = bld_height * num_floors * SCALE
    CORNER_TOP = HL - TOTAL_H
    CORNER_BOT = HL

    # Perspective projection helper
    def persp_point(corner_x, corner_y, vp_x, vp_y, t_ratio):
        """Interpolate between corner and vanishing point."""
        return (corner_x + (vp_x - corner_x) * t_ratio,
                corner_y + (vp_y - corner_y) * t_ratio)

    # Compute facade widths in perspective (foreshortening)
    front_t = (bld_width / (bld_width + bld_depth)) * 0.55
    side_t = (bld_depth / (bld_width + bld_depth)) * 0.55

    # Front facade corners (top and bottom)
    FR_TOP = persp_point(CORNER_X, CORNER_TOP, VPR_X, VP_Y, front_t)
    FR_BOT = persp_point(CORNER_X, CORNER_BOT, VPR_X, VP_Y, front_t)
    FL_TOP = persp_point(CORNER_X, CORNER_TOP, VPL_X, VP_Y, side_t)
    FL_BOT = persp_point(CORNER_X, CORNER_BOT, VPL_X, VP_Y, side_t)

    svg = [f'<svg viewBox="0 0 {CW} {CH}" width="100%" height="auto" '
           f'xmlns="http://www.w3.org/2000/svg" '
           f'style="background:{p_bg}; border:2px solid {p_line}; border-radius:10px;">'
    ]
    
    svg.append('<defs>')
    svg.append(f'<pattern id="pGrid" width="50" height="50" patternUnits="userSpaceOnUse">'
               f'<path d="M 50 0 L 0 0 0 50" fill="none" stroke="{p_line}" stroke-opacity="0.04" stroke-width="1"/>'
               f'</pattern>')
    svg.append('</defs>')
    svg.append(f'<rect width="{CW}" height="{CH}" fill="{p_bg}"/>')
    svg.append(f'<rect width="{CW}" height="{CH}" fill="url(#pGrid)"/>')

    # ── Horizon Line ──
    svg.append(f'<line x1="0" y1="{HL}" x2="{CW}" y2="{HL}" stroke="{p_dim}" stroke-width="1" stroke-dasharray="20 8" opacity="0.5"/>')
    svg.append(f'<text x="20" y="{HL-8}" font-family="monospace" font-size="12" fill="{p_dim}" opacity="0.7">Horizon Line (خط الأفق)</text>')

    # ── Vanishing Points ──
    for vpx, lbl in [(VPL_X, "VP Left"), (VPR_X, "VP Right")]:
        svg.append(f'<circle cx="{vpx}" cy="{VP_Y}" r="8" fill="{p_vp}" fill-opacity="0.8"/>')
        svg.append(f'<circle cx="{vpx}" cy="{VP_Y}" r="18" fill="none" stroke="{p_vp}" stroke-width="1.5" stroke-dasharray="4 3" opacity="0.5"/>')
        anchor = "start" if "Right" in lbl else "end"
        svg.append(f'<text x="{vpx + (15 if "Right" in lbl else -15)}" y="{VP_Y - 12}" font-family="monospace" font-size="11" fill="{p_vp}" text-anchor="{anchor}">{lbl}</text>')

    # ── Construction Lines to Vanishing Points ──
    for (cx, cy) in [(CORNER_X, CORNER_TOP), (CORNER_X, CORNER_BOT)]:
        for vpx in [VPL_X, VPR_X]:
            svg.append(f'<line x1="{cx}" y1="{cy}" x2="{vpx}" y2="{VP_Y}" stroke="{p_vp}" stroke-width="0.7" stroke-dasharray="6 4" opacity="0.3"/>')

    # ── Draw Building Faces ──
    # Front face (right side, going to VPR)
    front_face = f"{CORNER_X},{CORNER_TOP} {FR_TOP[0]},{FR_TOP[1]} {FR_BOT[0]},{FR_BOT[1]} {CORNER_X},{CORNER_BOT}"
    svg.append(f'<polygon points="{front_face}" fill="{p_line}" fill-opacity="0.07" stroke="{p_line}" stroke-width="2.5"/>')
    
    # Side face (left side, going to VPL)
    side_face = f"{CORNER_X},{CORNER_TOP} {FL_TOP[0]},{FL_TOP[1]} {FL_BOT[0]},{FL_BOT[1]} {CORNER_X},{CORNER_BOT}"
    svg.append(f'<polygon points="{side_face}" fill="{p_line}" fill-opacity="0.03" stroke="{p_line}" stroke-width="2"/>')

    # Roof face
    roof_pts = f"{CORNER_X},{CORNER_TOP} {FR_TOP[0]},{FR_TOP[1]} {FR_TOP[0] + FL_TOP[0] - CORNER_X},{(FR_TOP[1] + FL_TOP[1]) / 2} {FL_TOP[0]},{FL_TOP[1]}"
    svg.append(f'<polygon points="{roof_pts}" fill="{p_line}" fill-opacity="0.12" stroke="{p_line}" stroke-width="2"/>')

    # ── Front Face Window/Door Elements ──
    total_front_w = FR_BOT[0] - CORNER_X
    per_floor_h_top = (CORNER_TOP - FR_TOP[1] if CORNER_X < FR_TOP[0] else 0)
    floor_h_px = TOTAL_H / num_floors
    win_w_px = min(total_front_w / max(win_front + 1, 2) * 0.6, 60)
    
    for fl in range(num_floors):
        floor_bot = CORNER_BOT - fl * floor_h_px
        floor_top_c = floor_bot - floor_h_px
        # Floor line (construction)
        fl_t = fl * floor_h_px / TOTAL_H * front_t
        floor_bot_r = persp_point(CORNER_X, floor_bot, VPR_X, VP_Y, front_t * 0.95)
        if fl > 0:
            svg.append(f'<line x1="{CORNER_X}" y1="{floor_bot}" x2="{FR_BOT[0]}" y2="{FR_BOT[1]}" '
                       f'stroke="{p_line}" stroke-width="0.8" opacity="0.4" stroke-dasharray="6 3"/>')

        if fl > 0 and has_balcony:  # Balcony on upper floors
            bal_h = 30
            bal_w = total_front_w * 0.4
            bx = CORNER_X + total_front_w * 0.3
            by = floor_bot - 40
            svg.append(f'<rect x="{bx}" y="{by}" width="{bal_w}" height="8" fill="{p_line}" fill-opacity="0.6"/>')
            for bi in range(int(bal_w / 14)):
                bpx = bx + bi * 14
                svg.append(f'<line x1="{bpx}" y1="{by}" x2="{bpx}" y2="{by + bal_h}" stroke="{p_line}" stroke-width="1.2" opacity="0.5"/>')

        # Windows on front face
        for wi in range(win_front):
            wx = CORNER_X + total_front_w * (wi + 0.7) / (win_front + 1.0)
            wy_mid = (floor_bot + floor_top_c) / 2
            win_h = floor_h_px * 0.40
            svg.append(f'<rect x="{wx - win_w_px/2}" y="{wy_mid - win_h/2}" width="{win_w_px}" height="{win_h}" '
                       f'fill="{p_win}" fill-opacity="0.25" stroke="{p_win}" stroke-width="1.8"/>')
            # Cross bar
            svg.append(f'<line x1="{wx - win_w_px/2}" y1="{wy_mid}" x2="{wx + win_w_px/2}" y2="{wy_mid}" stroke="{p_win}" stroke-width="1"/>')
            svg.append(f'<line x1="{wx}" y1="{wy_mid - win_h/2}" x2="{wx}" y2="{wy_mid + win_h/2}" stroke="{p_win}" stroke-width="1"/>')

    # Ground floor entrance door
    if has_entrance:
        door_w = total_front_w * 0.18
        door_x = CORNER_X + total_front_w * 0.15
        door_y_top = CORNER_BOT - floor_h_px * 0.7
        svg.append(f'<rect x="{door_x}" y="{door_y_top}" width="{door_w}" height="{CORNER_BOT - door_y_top}" '
                   f'fill="{p_line}" fill-opacity="0.5" stroke="{p_line}" stroke-width="2"/>')
        # Arch
        arch_cx = door_x + door_w / 2
        arch_rx = door_w / 2
        arch_ry = arch_rx * 0.55
        svg.append(f'<ellipse cx="{arch_cx}" cy="{door_y_top}" rx="{arch_rx}" ry="{arch_ry}" '
                   f'fill="{p_line}" fill-opacity="0.6" stroke="{p_line}" stroke-width="2"/>')

    # ── Side Face Windows ──
    total_side_w = CORNER_X - FL_BOT[0]
    side_win_w = min(total_side_w / max(win_side + 1, 2) * 0.5, 40)
    for fl in range(num_floors):
        floor_bot = CORNER_BOT - fl * floor_h_px
        floor_top_c = floor_bot - floor_h_px
        wy_mid = (floor_bot + floor_top_c) / 2
        win_h = floor_h_px * 0.40
        for wi in range(win_side):
            wx = CORNER_X - total_side_w * (wi + 0.6) / (win_side + 1.0)
            svg.append(f'<rect x="{wx - side_win_w/2}" y="{wy_mid - win_h/2}" width="{side_win_w}" height="{win_h}" '
                       f'fill="{p_win}" fill-opacity="0.15" stroke="{p_win}" stroke-width="1.5"/>')

    # ── Front Vertical Edge (Main) ──
    svg.append(f'<line x1="{CORNER_X}" y1="{CORNER_TOP}" x2="{CORNER_X}" y2="{CORNER_BOT}" stroke="{p_line}" stroke-width="4"/>')

    # ── Ground Line ──
    svg.append(f'<line x1="{FL_BOT[0] - 100}" y1="{CORNER_BOT}" x2="{FR_BOT[0] + 100}" y2="{CORNER_BOT}" stroke="{p_line}" stroke-width="2" opacity="0.7"/>')
    
    # ── Dimension annotations ──
    svg.append(f'<text x="{CORNER_X + total_front_w / 2}" y="{CORNER_BOT + 30}" font-family="Arial" font-size="14" fill="{p_dim}" text-anchor="middle">↔ {bld_width:.0f} م</text>')
    svg.append(f'<text x="{CORNER_X - 20}" y="{(CORNER_TOP + CORNER_BOT) / 2}" font-family="Arial" font-size="14" fill="{p_dim}" text-anchor="end" transform="rotate(-90 {CORNER_X - 20} {(CORNER_TOP + CORNER_BOT) / 2})">↕ {bld_height * num_floors:.1f} م</text>')

    # ── Title Block ──
    svg.append(f'<rect x="10" y="{CH-50}" width="350" height="40" fill="{p_bg}" fill-opacity="0.9" stroke="{p_line}" stroke-width="1.5" rx="5"/>')
    svg.append(f'<text x="20" y="{CH-28}" font-family="Arial Black" font-size="12" fill="{p_dim}" font-weight="900">EngiCost AI ● منظور هندسي ثنائي نقطة التلاشي</text>')
    svg.append(f'<text x="20" y="{CH-12}" font-family="monospace" font-size="10" fill="{p_line}" opacity="0.6">Scale: Approximate ● Floors: {num_floors} ● VP Angle: {persp_angle}°</text>')

    svg.append('</svg>')

    import streamlit.components.v1 as components
    components.html('\n'.join(svg), height=650, scrolling=False)

    # Export button
    svg_str = '\n'.join(svg)
    st.download_button(t("📥 تحميل المنظور (SVG)", "Download Perspective (SVG)"),
                       data=svg_str, file_name="perspective_drawing.svg", mime="image/svg+xml")


# ══════════════════════════════════════════════════════════════════
# TAB 4: ARCHITECTURAL ELEVATION VIEWS
# ══════════════════════════════════════════════════════════════════
def _render_elevation_tab(t, zoom_level, theme, rooms_data, floor_count):
    st.markdown(f"#### 🧱 {t('الواجهات المعمارية (Elevation Views)', 'Architectural Elevation Views')}")
    st.caption(t("يولد واجهات شمال/جنوب/شرق/غرب تلقائياً من بيانات المخطط.",
                 "Automatically generates North/South/East/West elevations from floor plan data."))
    
    ec1, ec2, ec3 = st.columns(3)
    with ec1: elev_floor_h = st.number_input(t("ارتفاع الطابق (م)", "Floor Height (m)"), 2.5, 5.0, 3.2, 0.1)
    with ec2: elev_floors = st.number_input(t("عدد الأدوار", "Floors"), 1, 8, max(floor_count, 1))
    with ec3: elev_style = st.selectbox(t("نوع الواجهة", "Elevation Style"), [t("مودرن", "Modern"), t("كلاسيك", "Classic"), t("خليجي", "Gulf")])

    if theme == "AutoCAD Dark":
        e_bg, e_line, e_dim, e_win, e_sky = "#0d0d0d", "#cccccc", "#00d4ff", "#4dd0e1", "#0d1a2e"
    elif theme == "Blueprint":
        e_bg, e_line, e_dim, e_win, e_sky = "#0a2744", "#dce8f5", "#ffdd57", "#29b6f6", "#071a30"
    else:
        e_bg, e_line, e_dim, e_win, e_sky = "#f0f4f8", "#1a1a2e", "#1565c0", "#0288d1", "#dbeafe"

    # Extract building dimensions from rooms_data
    bld_w_m, bld_d_m = 12.0, 10.0
    win_count_front, win_count_side = 3, 2
    if rooms_data and rooms_data.get('walls'):
        walls = rooms_data['walls']
        xs = [w.get('x', 0) for w in walls] + [w.get('x', 0) + w.get('w', 0) for w in walls]
        ys = [w.get('y', 0) for w in walls] + [w.get('y', 0) + w.get('h', 0) for w in walls]
        if xs and ys:
            bld_w_m = max(round((max(xs) - min(xs)) / 100, 1), 4.0)
            bld_d_m = max(round((max(ys) - min(ys)) / 100, 1), 4.0)
        # Count windows
        openings = rooms_data.get('openings', [])
        win_count_front = max(1, len([o for o in openings if 'window' in str(o.get('type', '')).lower()]))

    SCALE = 28  # px per meter
    EW = int(bld_w_m * SCALE) + 200   # building width in px (front)
    EW_S = int(bld_d_m * SCALE) + 200  # side elevation width px
    EH_bld = int(elev_floor_h * elev_floors * SCALE)
    C_H = EH_bld + 160  # canvas height
    GROUND = C_H - 60  # y position of ground line

    # ─── Helper: draw one elevation ───────────────────────────────
    def draw_elevation(ew_px, direction_label, win_n, add_door=True):
        svg = [f'<svg viewBox="0 0 {ew_px + 80} {C_H + 20}" width="100%" height="auto" '
               f'xmlns="http://www.w3.org/2000/svg" '
               f'style="background:{e_bg}; border:2px solid {e_line}; border-radius:8px;">'
        ]
        svg.append(f'<rect width="{ew_px + 80}" height="{C_H + 20}" fill="{e_bg}"/>')
        # Sky gradient simulation
        svg.append(f'<rect x="0" y="0" width="{ew_px + 80}" height="{GROUND - EH_bld}" fill="{e_sky}" fill-opacity="0.4"/>')
        # Ground fill
        svg.append(f'<rect x="0" y="{GROUND}" width="{ew_px + 80}" height="{C_H + 20 - GROUND}" fill="{e_line}" fill-opacity="0.12"/>')
        # Ground line
        svg.append(f'<line x1="0" y1="{GROUND}" x2="{ew_px + 80}" y2="{GROUND}" stroke="{e_line}" stroke-width="2.5"/>')

        bx = 40  # building starts at x=40
        # Building outline
        svg.append(f'<rect x="{bx}" y="{GROUND - EH_bld}" width="{ew_px}" height="{EH_bld}" '
                   f'fill="{e_line}" fill-opacity="0.05" stroke="{e_line}" stroke-width="3"/>')

        # Floor lines
        fh_px = EH_bld / elev_floors
        for fi in range(1, elev_floors):
            fy = GROUND - fi * fh_px
            svg.append(f'<line x1="{bx}" y1="{fy}" x2="{bx + ew_px}" y2="{fy}" stroke="{e_line}" stroke-width="1" stroke-dasharray="8 4" opacity="0.5"/>')

        # Roof style parapet/cornice
        parapet_h = 25
        if "Classic" in elev_style or "كلاسيك" in elev_style:
            # Classic cornice
            svg.append(f'<rect x="{bx - 8}" y="{GROUND - EH_bld - parapet_h}" width="{ew_px + 16}" height="{parapet_h}" '
                       f'fill="{e_line}" fill-opacity="0.25" stroke="{e_line}" stroke-width="2"/>')
            svg.append(f'<rect x="{bx - 4}" y="{GROUND - EH_bld - parapet_h*2}" width="{ew_px + 8}" height="{parapet_h}" '
                       f'fill="{e_line}" fill-opacity="0.1" stroke="{e_line}" stroke-width="1.5"/>')
        elif "Gulf" in elev_style or "خليجي" in elev_style:
            # Gulf parapet with battlements
            svg.append(f'<rect x="{bx}" y="{GROUND - EH_bld - parapet_h}" width="{ew_px}" height="{parapet_h}" '
                       f'fill="{e_line}" fill-opacity="0.2" stroke="{e_line}" stroke-width="2"/>')
            battlement_w = 30
            for bi in range(int(ew_px / (battlement_w * 2))):
                batt_x = bx + bi * battlement_w * 2
                svg.append(f'<rect x="{batt_x}" y="{GROUND - EH_bld - parapet_h * 1.8}" width="{battlement_w}" height="{parapet_h * 0.8}" '
                           f'fill="{e_line}" fill-opacity="0.3" stroke="{e_line}" stroke-width="1.5"/>')
        else:  # Modern flat parapet
            svg.append(f'<rect x="{bx - 4}" y="{GROUND - EH_bld - parapet_h}" width="{ew_px + 8}" height="{parapet_h}" '
                       f'fill="{e_line}" fill-opacity="0.2" stroke="{e_line}" stroke-width="2"/>')

        # Windows on each floor
        win_spacing = ew_px / max(win_n + 1, 2)
        win_w = win_spacing * 0.55
        for fi in range(elev_floors):
            fl_bot = GROUND - fi * fh_px
            fl_mid = fl_bot - fh_px / 2
            win_ht = fh_px * 0.42
            for wi in range(win_n):
                wx = bx + win_spacing * (wi + 0.5) + win_spacing * 0.2
                wy = fl_mid - win_ht / 2
                # Window frame
                svg.append(f'<rect x="{wx}" y="{wy}" width="{win_w}" height="{win_ht}" '
                           f'fill="{e_win}" fill-opacity="0.2" stroke="{e_win}" stroke-width="2" rx="2"/>')
                # Window dividers
                svg.append(f'<line x1="{wx + win_w/2}" y1="{wy}" x2="{wx + win_w/2}" y2="{wy + win_ht}" stroke="{e_win}" stroke-width="1"/>')
                svg.append(f'<line x1="{wx}" y1="{wy + win_ht*0.5}" x2="{wx + win_w}" y2="{wy + win_ht*0.5}" stroke="{e_win}" stroke-width="1"/>')
                # Window sill
                svg.append(f'<line x1="{wx - 5}" y1="{wy + win_ht}" x2="{wx + win_w + 5}" y2="{wy + win_ht}" stroke="{e_line}" stroke-width="2.5"/>')
                # Lintel
                svg.append(f'<line x1="{wx - 5}" y1="{wy}" x2="{wx + win_w + 5}" y2="{wy}" stroke="{e_line}" stroke-width="2"/>')

        # Main Entrance Door (ground floor only, on front)
        if add_door:
            d_w = ew_px * 0.12
            d_h = fh_px * 0.72
            d_x = bx + ew_px * 0.42
            d_y = GROUND - d_h
            svg.append(f'<rect x="{d_x}" y="{d_y}" width="{d_w}" height="{d_h}" '
                       f'fill="{e_line}" fill-opacity="0.45" stroke="{e_line}" stroke-width="2.5" rx="3"/>')
            if "Classic" in elev_style or "كلاسيك" in elev_style:
                # Arch above door
                arch_cy = d_y
                arch_rx = d_w / 2
                arch_ry = arch_rx * 0.6
                svg.append(f'<ellipse cx="{d_x + d_w / 2}" cy="{arch_cy}" rx="{arch_rx}" ry="{arch_ry}" '
                           f'fill="{e_line}" fill-opacity="0.3" stroke="{e_line}" stroke-width="2"/>')

        # Dimension lines
        dm_y = GROUND + 30
        svg.append(f'<line x1="{bx}" y1="{dm_y}" x2="{bx + ew_px}" y2="{dm_y}" stroke="{e_dim}" stroke-width="1.5" marker-start="url(#arrS)" marker-end="url(#arrE)"/>')
        svg.append(f'<text x="{bx + ew_px/2}" y="{dm_y + 16}" font-family="monospace" font-size="12" fill="{e_dim}" text-anchor="middle">{ew_px / SCALE:.1f} م</text>')
        # Height dim
        hd_x = bx - 35
        svg.append(f'<line x1="{hd_x}" y1="{GROUND - EH_bld}" x2="{hd_x}" y2="{GROUND}" stroke="{e_dim}" stroke-width="1.5"/>')
        svg.append(f'<text x="{hd_x - 4}" y="{GROUND - EH_bld/2}" font-family="monospace" font-size="12" fill="{e_dim}" text-anchor="middle" transform="rotate(-90 {hd_x - 4} {GROUND - EH_bld/2})">{elev_floor_h * elev_floors:.1f} م</text>')

        # Direction label
        svg.append(f'<text x="{(ew_px + 80)/2}" y="{C_H + 15}" font-family="Arial Black" font-size="15" fill="{e_dim}" text-anchor="middle" font-weight="900">{direction_label}</text>')

        svg.append('</svg>')
        return '\n'.join(svg)

    # Draw 4 elevations
    col_n, col_s = st.columns(2)
    with col_n:
        st.markdown(f"**{t('الواجهة الشمالية', 'North Elevation')}**")
        north_svg = draw_elevation(EW, t('⬆ شمال — North', '⬆ North'), win_count_front, add_door=False)
        import streamlit.components.v1 as components
        components.html(north_svg, height=C_H + 40)
    with col_s:
        st.markdown(f"**{t('الواجهة الجنوبية', 'South Elevation')}**")
        south_svg = draw_elevation(EW, t('⬇ جنوب — South', '⬇ South'), win_count_front, add_door=True)
        components.html(south_svg, height=C_H + 40)

    col_e, col_w = st.columns(2)
    with col_e:
        st.markdown(f"**{t('الواجهة الشرقية', 'East Elevation')}**")
        east_svg = draw_elevation(EW_S, t('➡ شرق — East', '➡ East'), win_count_side, add_door=False)
        components.html(east_svg, height=C_H + 40)
    with col_w:
        st.markdown(f"**{t('الواجهة الغربية', 'West Elevation')}**")
        west_svg = draw_elevation(EW_S, t('⬅ غرب — West', '⬅ West'), win_count_side, add_door=False)
        components.html(west_svg, height=C_H + 40)

    # Download all as combined SVG
    combined_w, combined_h = (EW + EW_S + 120) * 2, (C_H + 60) * 2
    all_svgs = f"""<svg viewBox="0 0 {combined_w} {combined_h}" width="{combined_w}" height="{combined_h}" xmlns="http://www.w3.org/2000/svg" style="background:{e_bg}">
    <text x="{combined_w/2}" y="30" font-family='Arial Black' font-size='20' fill='{e_dim}' text-anchor='middle' font-weight='900'>EngiCost AI - الواجهات المعمارية</text>
    </svg>"""
    st.download_button(t("📥 تحميل الواجهة الجنوبية (SVG)", "Download South Elevation (SVG)"),
                       data=south_svg, file_name="elevation_south.svg", mime="image/svg+xml")


# ══════════════════════════════════════════════════════════════════
# TAB 5: AI PLAN SCANNER
# ══════════════════════════════════════════════════════════════════
def _render_ai_scanner_tab(t):
    st.markdown(f"#### 📷 {t('ماسح المخططات بالذكاء الاصطناعي (AI Plan Scanner)', 'AI Architectural Plan Scanner')}")
    st.caption(t(
        "ارفع صورة مخطط معماري (JPG/PNG) وسيقوم الذكاء الاصطناعي (Gemini Vision) بتحليله وتحويله لرسمة رقمية عالية الدقة داخل المنصة.",
        "Upload a floor plan image (JPG/PNG) and Gemini Vision AI will analyze it and convert it into a high-fidelity digital drawing."
    ))

    st.info(t(
        "💡 مثال: ارفع أي صورة مخطط من هاتفك أو من ملف AutoCAD وسيتم تحليلها واستخراج غرفها ونقلها لأداة الرسم.",
        "💡 Example: Upload any floor plan image from your phone or a CAD file scan and the AI will extract all rooms."
    ))

    uploaded = st.file_uploader(
        t("📎 ارفع صورة المخطط (JPG, PNG, WEBP)", "📎 Upload Plan Image (JPG, PNG, WEBP)"),
        type=["jpg", "jpeg", "png", "webp"],
        key="plan_upload"
    )

    if uploaded:
        col_img, col_info = st.columns([2, 1])
        with col_img:
            st.image(uploaded, caption=t("المخطط المُرفوع", "Uploaded Plan"), use_container_width=True)
        with col_info:
            st.markdown(f"**{t('معلومات الملف', 'File Info')}**")
            st.write(f"📄 {uploaded.name}")
            st.write(f"📏 {round(uploaded.size / 1024, 1)} KB")
            st.write(f"🖼️ {uploaded.type}")

        st.markdown("---")
        if st.button("🤖 " + t("تحليل المخطط باستخدام Gemini Vision AI الآن", "Analyze Plan with Gemini Vision AI Now"),
                     type="primary", use_container_width=True, key="scan_btn"):
            with st.spinner(t("يتم تحليل المخطط وتحديد الغرف والأبعاد... (قد يستغرق 30-60 ثانية)",
                              "Analyzing plan, detecting rooms and dimensions... (may take 30-60 seconds)")):
                try:
                    image_bytes = uploaded.read()
                    ext = uploaded.name.split('.')[-1].lower()
                    
                    from ai_engine.drawing_brain import analyze_plan_image
                    result = analyze_plan_image(image_bytes, ext)

                    if result and (result.get('walls') or result.get('rooms')):
                        # Add project info if missing
                        if not result.get('project_info'):
                            result['project_info'] = {'title': uploaded.name, 'style': 'Extracted'}
                        st.session_state.current_rooms = result
                        st.session_state.analysis_items = []
                        n_rooms = len(result.get('rooms', []))
                        n_walls = len(result.get('walls', []))
                        st.success(t(
                            f"✅ تم تحليل المخطط بنجاح! تم استخراج {n_rooms} غرفة و {n_walls} حائط. يمكنك الآن عرض المخطط في تبويب 'لوحة الرسم'.",
                            f"✅ Plan analyzed successfully! Extracted {n_rooms} rooms and {n_walls} walls. Go to 'AI Drafting Board' tab to view."
                        ))
                        # Immediately show preview
                        st.markdown(f"**{t('معاينة سريعة للبيانات المستخرجة:', 'Quick Preview of Extracted Data:')}**")
                        proj_info = result.get('project_info', {})
                        m1, m2, m3 = st.columns(3)
                        m1.metric(t("الغرف", "Rooms"), n_rooms)
                        m2.metric(t("الحوائط", "Walls"), n_walls)
                        m3.metric(t("المساحة المقدرة", "Est. Area"), f"{proj_info.get('total_area', '—')} م²")
                        
                        if result.get('rooms'):
                            import pandas as pd
                            rooms_tbl = [{
                                t("اسم الغرفة", "Room Name"): r.get('name', ''),
                                t("النوع", "Type"): r.get('type', ''),
                                t("العرض (م)", "Width (m)"): r.get('width_m', ''),
                                t("العمق (م)", "Depth (m)"): r.get('height_m', ''),
                            } for r in result.get('rooms', [])]
                            st.dataframe(pd.DataFrame(rooms_tbl), use_container_width=True)
                    else:
                        st.warning(t(
                            "⚠️ لم يتمكن الذكاء الاصطناعي من استخراج بيانات كافية. تأكد من وضوح المخطط وأنه مخطط معماري فعلي.",
                            "⚠️ AI could not extract sufficient data. Make sure the image is a clear architectural floor plan."
                        ))
                except Exception as e:
                    st.error(t(f"خطأ في التحليل: {e}", f"Analysis Error: {e}"))
                    st.info(t(
                        "ملاحظة: هذه الميزة تتطلب مفتاح Gemini API. تأكد من ضبط GEMINI_API_KEY في الإعدادات.",
                        "Note: This feature requires a Gemini API key. Please set GEMINI_API_KEY in settings."
                    ))
    else:
        st.markdown(f"""<div style='border:2px dashed #aaa; border-radius:12px; padding:40px; text-align:center; opacity:0.7'>
        <div style='font-size:3em'>📐</div>
        <div style='font-size:1.1em; margin-top:10px'>{t('اسحب وأفلت صورة المخطط هنا، أو اضغط لاختيار ملف', 'Drag and drop a plan image here, or click to browse')}</div>
        <div style='font-size:0.85em; margin-top:8px; opacity:0.6'>{t('يدعم: JPG, PNG, WEBP حتى 10 ميجابايت', 'Supports: JPG, PNG, WEBP up to 10MB')}</div>
        </div>""", unsafe_allow_html=True)


def render_drawing_engine():
    try:
        _render_drawing_engine_internal()
    except Exception as e:
        import traceback
        st.error("⚠️ Error rendering Drawing Engine:")
        st.code(traceback.format_exc(), language="python")
