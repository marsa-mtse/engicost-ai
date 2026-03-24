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
        t("🏗️ قطاعات إنشائية (أوفلاين)", "🏗️ Structural Sections (Offline)")
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
                st.markdown(f"#### 📸 " + t("ريندر وتخيل بصري 8K (Nano-Render)", "8K Photorealistic AI Render (Nano-Render)"))
                
                render_prompt_custom = st.text_input(
                    t("تخصيص اللقطة (إضاءة، تفاصيل، ليلية/نهارية...)", "Customize Shot (Lighting, Details, Day/Night...)"), 
                    placeholder=t("مثال: لقطة ليلية مع إضاءة دافئة وعدسة سينمائية...", "e.g., Night shot with warm lighting and cinematic lens...")
                )
                
                if st.button("✨ " + t("توليد الريندر الآن", "Generate Render Now"), use_container_width=True, type="secondary"):
                    with st.spinner(t("جاري بناء المشهد ورندرة الإضاءة والخامات بجودة فائقة...", "Rendering scene lighting and materials in ultra-high quality...")):
                        import urllib.parse
                        import time
                        
                        # Build the image generation prompt based on project context
                        base_prompt = f"8k hyper realistic architectural render, {style_3d} {specialty}. "
                        if st.session_state.get('finishings_concept'):
                            fc = str(st.session_state.get('finishings_concept', ''))[:150]
                            base_prompt += f"Interior/Exterior vibe: {fc}. "
                        if render_prompt_custom:
                            base_prompt += f"{render_prompt_custom}. "
                        base_prompt += "Octane render, Unreal Engine 5 aesthetic, masterpiece, highly detailed, architectural photography, volumetric lighting, photorealistic."
                        
                        encoded_prompt = urllib.parse.quote(base_prompt)
                        timestamp = int(time.time()) # Bypass cache
                        img_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1920&height=1080&nologo=true&seed={timestamp}"
                        
                        st.session_state.last_render_url = img_url
                        
                if "last_render_url" in st.session_state:
                    st.image(st.session_state.last_render_url, use_container_width=True)
                    col_dl, col_blank = st.columns([1, 2])
                    with col_dl:
                        st.markdown(f"<a href='{st.session_state.last_render_url}' download='EngiCost_Render.jpg' target='_blank' style='display: block; text-align: center; background-color: #0ea5e9; color: white; padding: 10px; border-radius: 8px; text-decoration: none; font-weight: bold;'>📥 {t('تحميل بجودة 8K', 'Download 8K Resolution')}</a>", unsafe_allow_html=True)

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

def render_drawing_engine():
    try:
        _render_drawing_engine_internal()
    except Exception as e:
        import traceback
        st.error("⚠️ Error rendering Drawing Engine:")
        st.code(traceback.format_exc(), language="python")
