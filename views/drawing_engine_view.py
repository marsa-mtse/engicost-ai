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
                # --- 2D Professional SVG (AutoCAD Style) ---
                st.markdown(f"### 🖼️ " + t("مخطط أوتوكاد الشامل (V1.7.5 Pro)", "World-Class AutoCAD Plan (V1.7.5 Pro)"))
                
                bg_color = "#000000" if theme == "AutoCAD Dark" else "#0a3a66" if theme == "Blueprint" else "#f8f9fa"
                line_color = "#ffffff" if theme != "Modern Light" else "#333333"
                wall_fill = "url(#wallHatch)" if theme != "Modern Light" else "#e2e8f0"
                wall_stroke = "#00ff00" if theme == "AutoCAD Dark" else "#ffffff" if theme == "Blueprint" else "#1e293b"
                
                # Element boundaries
                w_list = r_data.get('walls', []) if isinstance(r_data.get('walls'), list) else []
                o_list = r_data.get('openings', []) if isinstance(r_data.get('openings'), list) else []
                f_list = r_data.get('furniture', []) if isinstance(r_data.get('furniture'), list) else []
                all_w = w_list + o_list + f_list
                
                min_x = min([w.get('x',0) for w in all_w] + [0]) - 500
                max_x = max([w.get('x',0)+w.get('w',0) for w in all_w] + [1200]) + 500
                min_y = min([w.get('y',0) for w in all_w] + [0]) - 500
                max_y = max([w.get('y',0)+w.get('h',0) for w in all_w] + [1200]) + 500
                
                # Responsive Viewbox
                vb_w, vb_h = (max_x - min_x) / zoom_level, (max_y - min_y) / zoom_level
                
                svg = [f'<svg viewBox="{min_x} {min_y} {vb_w} {vb_h}" width="100%" height="auto" style="background:{bg_color}; border:2px solid {line_color}; border-radius:8px; display:block;" xmlns="http://www.w3.org/2000/svg">']
                
                # Defs (Hatch, Grid)
                svg.append('<defs>')
                svg.append(f'<pattern id="grid" width="50" height="50" patternUnits="userSpaceOnUse"><path d="M 50 0 L 0 0 0 50" fill="none" stroke="{line_color}" stroke-opacity="0.1" stroke-width="1"/></pattern>')
                svg.append(f'<pattern id="wallHatch" width="10" height="10" patternTransform="rotate(45 0 0)" patternUnits="userSpaceOnUse"><line x1="0" y1="0" x2="0" y2="10" stroke="{wall_stroke}" stroke-opacity="0.5" stroke-width="1" /></pattern>')
                svg.append('</defs>')
                svg.append(f'<rect x="{min_x}" y="{min_y}" width="{max_x-min_x}" height="{max_y-min_y}" fill="url(#grid)" />')
                
                # External Dimension Lines
                svg.append(f'<g fill="none" stroke="{line_color}" stroke-width="1" stroke-opacity="0.6">')
                # Top
                svg.append(f'<line x1="{min_x+100}" y1="{min_y+50}" x2="{max_x-100}" y2="{min_y+50}" />')
                svg.append(f'<line x1="{min_x+100}" y1="{min_y+40}" x2="{min_x+100}" y2="{min_y+60}" />')
                svg.append(f'<line x1="{max_x-100}" y1="{min_y+40}" x2="{max_x-100}" y2="{min_y+60}" />')
                svg.append(f'<circle cx="{min_x+100}" cy="{min_y+50}" r="2" fill="{line_color}"/>')
                svg.append(f'<circle cx="{max_x-100}" cy="{min_y+50}" r="2" fill="{line_color}"/>')
                svg.append(f'<text x="{(min_x+max_x)/2}" y="{min_y+40}" font-family="monospace" font-size="{20/zoom_level}" fill="{line_color}" stroke="none" text-anchor="middle">{max_x-min_x-200} cm</text>')
                # Left
                svg.append(f'<line x1="{min_x+50}" y1="{min_y+100}" x2="{min_x+50}" y2="{max_y-100}" />')
                svg.append(f'<line x1="{min_x+40}" y1="{min_y+100}" x2="{min_x+60}" y2="{min_y+100}" />')
                svg.append(f'<line x1="{min_x+40}" y1="{max_y-100}" x2="{min_x+60}" y2="{max_y-100}" />')
                svg.append(f'<text x="{min_x+40}" y="{(min_y+max_y)/2}" font-family="monospace" font-size="{20/zoom_level}" fill="{line_color}" stroke="none" transform="rotate(-90 {min_x+40} {(min_y+max_y)/2})" text-anchor="middle">{max_y-min_y-200} cm</text>')
                svg.append('</g>')

                # Furniture/Greenery
                for f in r_data.get('furniture', []):
                    fx, fy, fw, fh = f.get('x',0), f.get('y',0), f.get('w',50), f.get('h',50)
                    fname = f.get('name', '')
                    ftype = str(f.get('type', '')).lower()
                    if 'pool' in ftype or 'water' in ftype:
                        svg.append(f'<rect x="{fx}" y="{fy}" width="{fw}" height="{fh}" fill="#2196f3" fill-opacity="0.3" stroke="#2196f3" stroke-width="2" rx="10"/>')
                    elif 'tree' in ftype or 'green' in ftype or 'land' in ftype:
                        cx, cy, r = fx+fw/2, fy+fh/2, min(fw,fh)/2
                        svg.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#4caf50" fill-opacity="0.3" stroke="#4caf50" stroke-width="2" stroke-dasharray="4 2"/>')
                    else:
                        svg.append(f'<rect x="{fx}" y="{fy}" width="{fw}" height="{fh}" fill="{line_color}" fill-opacity="0.05" stroke="{line_color}" stroke-opacity="0.4" stroke-width="1.5" rx="4"/>')
                    svg.append(f'<text x="{fx+fw/2}" y="{fy+fh/2}" font-family="sans-serif" font-size="{12/zoom_level}" fill="{line_color}" fill-opacity="0.7" text-anchor="middle" dominant-baseline="middle">{fname}</text>')
                
                # Walls (rendered with hatch and stroke)
                for w in r_data.get('walls', []):
                    wx, wy, ww, wh = w.get('x',0), w.get('y',0), max(w.get('w',10),10), max(w.get('h',10),10)
                    is_ext = w.get('is_exterior', False)
                    stroke_w = "3.5" if is_ext else "2"
                    svg.append(f'<rect x="{wx}" y="{wy}" width="{ww}" height="{wh}" fill="{wall_fill}" stroke="{wall_stroke}" stroke-width="{stroke_w}" />')

                # Openings — Professional door arcs + window panes
                for o in r_data.get('openings', []):
                    ox, oy, ow, oh = o.get('x',0), o.get('y',0), max(o.get('w',20),10), max(o.get('h',20),10)
                    otype = str(o.get('type','')).lower()
                    if 'door' in otype:
                        # Clear wall gap
                        svg.append(f'<rect x="{ox}" y="{oy}" width="{ow}" height="{oh}" fill="{bg_color}" stroke="none" />')
                        # Door leaf (thin line)
                        if ow >= oh:  # Horizontal wall
                            svg.append(f'<line x1="{ox}" y1="{oy+oh/2}" x2="{ox+ow}" y2="{oy+oh/2}" stroke="#ffeb3b" stroke-width="2"/>')
                            svg.append(f'<path d="M {ox} {oy+oh/2} A {ow} {ow} 0 0 1 {ox+ow} {oy+oh/2+ow}" fill="none" stroke="#ffeb3b" stroke-width="1.5" stroke-dasharray="6,3"/>')
                        else:  # Vertical wall
                            svg.append(f'<line x1="{ox+ow/2}" y1="{oy}" x2="{ox+ow/2}" y2="{oy+oh}" stroke="#ffeb3b" stroke-width="2"/>')
                            svg.append(f'<path d="M {ox+ow/2} {oy} A {oh} {oh} 0 0 1 {ox+ow/2+oh} {oy+oh}" fill="none" stroke="#ffeb3b" stroke-width="1.5" stroke-dasharray="6,3"/>')
                    else:
                        # Window: clear gap + double parallel lines + crosses
                        svg.append(f'<rect x="{ox}" y="{oy}" width="{ow}" height="{oh}" fill="{bg_color}" stroke="none" />')
                        svg.append(f'<rect x="{ox}" y="{oy}" width="{ow}" height="{oh}" fill="none" stroke="#00bcd4" stroke-width="2" />')
                        if ow >= oh:
                            mid = oy + oh/2
                            svg.append(f'<line x1="{ox}" y1="{mid-3}" x2="{ox+ow}" y2="{mid-3}" stroke="#00bcd4" stroke-width="1.5"/>')
                            svg.append(f'<line x1="{ox}" y1="{mid+3}" x2="{ox+ow}" y2="{mid+3}" stroke="#00bcd4" stroke-width="1.5"/>')
                        else:
                            mid = ox + ow/2
                            svg.append(f'<line x1="{mid-3}" y1="{oy}" x2="{mid-3}" y2="{oy+oh}" stroke="#00bcd4" stroke-width="1.5"/>')
                            svg.append(f'<line x1="{mid+3}" y1="{oy}" x2="{mid+3}" y2="{oy+oh}" stroke="#00bcd4" stroke-width="1.5"/>')

                # Room Labels with area (m²)
                for lbl in r_data.get('labels', []):
                    lx, ly, txt = lbl.get('x',0), lbl.get('y',0), lbl.get('text', '')
                    area = lbl.get('area_m2', '')
                    svg.append(f'<text x="{lx}" y="{ly - 10}" font-family="sans-serif" font-weight="bold" font-size="{22/zoom_level}" fill="{wall_stroke}" text-anchor="middle">{txt}</text>')
                    if area:
                        svg.append(f'<text x="{lx}" y="{ly + 14}" font-family="monospace" font-size="{16/zoom_level}" fill="{wall_stroke}" fill-opacity="0.65" text-anchor="middle">{area} m²</text>')

                # Professional Title Block
                tb_w, tb_h = 300, 120
                tb_x, tb_y = max_x - tb_w - 20, max_y - tb_h - 20
                svg.append(f'<g transform="translate({tb_x}, {tb_y})">')
                svg.append(f'<rect x="0" y="0" width="{tb_w}" height="{tb_h}" fill="{bg_color}" fill-opacity="0.9" stroke="{line_color}" stroke-width="3"/>')
                svg.append(f'<line x1="0" y1="40" x2="{tb_w}" y2="40" stroke="{line_color}" stroke-width="1.5"/>')
                svg.append(f'<line x1="0" y1="80" x2="{tb_w}" y2="80" stroke="{line_color}" stroke-width="1.5"/>')
                svg.append(f'<line x1="{tb_w/2}" y1="40" x2="{tb_w/2}" y2="120" stroke="{line_color}" stroke-width="1.5"/>')
                svg.append(f'<text x="15" y="26" font-family="sans-serif" font-size="{18/zoom_level}" fill="{line_color}" font-weight="900" letter-spacing="2">ENGICOST AI V1.7.5 PRO</text>')
                svg.append(f'<text x="15" y="66" font-family="sans-serif" font-size="{14/zoom_level}" fill="{line_color}">Style: {style_3d[:15]}</text>')
                svg.append(f'<text x="{tb_w/2 + 15}" y="66" font-family="sans-serif" font-size="{14/zoom_level}" fill="{line_color}">Floors: {floor_count}</text>')
                svg.append(f'<text x="15" y="106" font-family="sans-serif" font-size="{14/zoom_level}" fill="{line_color}">Rooms: {bed_count}B/{bath_count}H</text>')
                svg.append(f'<text x="{tb_w/2 + 15}" y="106" font-family="sans-serif" font-size="{14/zoom_level}" fill="{line_color}">V: Ultra Pro</text>')
                svg.append(f'</g>')
                
                svg.append('</svg>')
                final_svg = "\n".join(svg)
                st.session_state.last_svg = final_svg
                
                # Use HTML component for better rendering of raw SVG
                import streamlit.components.v1 as components
                components.html(final_svg, height=max(600, int(vb_h * zoom_level * 0.8)), scrolling=True)
                
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
        st.markdown(f"#### {t('توليد قطاع تسليح آلي (محلي)', 'Automated Offline Drafting')}")
        sc1, sc2, sc3 = st.columns(3)
        with sc1:
            m_type = st.selectbox(t("نوع العنصر", "Member Type"), [t("عمود", "Column"), t("كمرة", "Beam")], key="sc_mtype_v2")
            w_val = st.number_input(t("العرض (mm)", "Width (mm)"), value=300, step=50, key="sc_w")
        with sc2:
            d_val = st.number_input(t("العمق (mm)", "Depth (mm)"), value=600, step=50, key="sc_d")
            b_cnt = st.number_input(t("عدد الأسياخ", "Bars Count"), value=6, min_value=2, key="sc_bc")
        with sc3:
            b_dia = st.number_input(t("قطر السيخ (mm)", "Bar Diameter (mm)"), value=16, step=2, key="sc_dia")
            c_val = st.number_input(t("الغطاء الخرساني (mm)", "Concrete Cover (mm)"), value=25, key="sc_cov")

        if st.button(t("🖋️ رسم القطاع الآن", "🖋️ Draw Section Now"), key="sc_draw_btn", use_container_width=True):
            fig = go.Figure()
            fig.add_shape(type="rect", x0=0, y0=0, x1=w_val, y1=d_val, line=dict(color="#00ff00", width=4))
            fig.add_shape(type="rect", x0=c_val, y0=c_val, x1=w_val-c_val, y1=d_val-c_val, line=dict(color="#00ffff", width=2, dash="dash"))
            fig.update_layout(paper_bgcolor="black", plot_bgcolor="rgba(0,0,0,0)", font_color="white", height=500,
                              xaxis=dict(showgrid=False, zeroline=False), yaxis=dict(showgrid=False, zeroline=False, scaleanchor="x", scaleratio=1))
            st.plotly_chart(fig, use_container_width=True)

    # ─── Export Section ───
    st.markdown("---")
    if "last_svg" in st.session_state and st.session_state.last_svg:
        st.download_button("📤 " + t("تحميل التصميم (SVG/CAD)", "Download Design (SVG/CAD)"), 
                           st.session_state.last_svg, "engi_draft.svg", "image/svg+xml", use_container_width=True)

def render_drawing_engine():
    try:
        _render_drawing_engine_internal()
    except Exception as e:
        import traceback
        st.error("⚠️ Error rendering Drawing Engine:")
        st.code(traceback.format_exc(), language="python")
