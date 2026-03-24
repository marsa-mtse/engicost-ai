import streamlit as st
import pandas as pd
from utils import t, render_section_header

def render_mep_systems():
    render_section_header(t("الأنظمة الميكانيكية والكهربائية (MEP)", "Mechanical & Electrical Systems (MEP)"), "⚙️")
    
    st.markdown(f"""
    <div class="glass-card animate-up">
        <p style="color:var(--text-muted);">
            {t("وحدة شاملة لحساب وتقدير تكاليف مشاريع الكهروميكانيك ومحطات المياه والصرف الصحي والحماية المدنية.", 
               "Comprehensive module for calculating and estimating costs for electromechanical projects, water/sewage stations, and fire protection.")}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    tabs = st.tabs([
        t("💧 محطات المياه والصرف", "💧 Water & Sewage Stations"),
        t("🔥 الحماية المدنية والإطفاء", "🔥 Fire Protection"),
        t("❄️ التكييف والتهوية (HVAC)", "❄️ HVAC Systems"),
        t("⚡ الأنظمة الكهربائية", "⚡ Electrical Systems"),
        t("🚰 أعمال السباكة", "🚰 Plumbing Works")
    ])
    
    # helper for AI generation placeholder
    def generate_ai_boq_ui(system_name):
        st.markdown(f"### {t('تسعير ذكي وتوليد بنود — ', 'Smart BOQ Generation — ')}{system_name}")
        area = st.number_input(t("مساحة المشروع (م٢)", "Project Area (m2)"), min_value=10, value=500, step=50, key=f"area_{system_name}")
        desc = st.text_area(t("وصف المشروع والمتطلبات (اختياري)", "Project Description & Requirements (Optional)"), key=f"desc_{system_name}")
        
        if st.button("🤖 " + t("توليد وتسعير البنود آلياً", "Auto-generate & Price Items"), key=f"btn_{system_name}", type="primary"):
            st.info(t("⏳ يتم الآن استدعاء الذكاء الاصطناعي لتحليل المتطلبات وتوليد جداول الكميات (BOQ) بالأسعار الحية...", "⏳ Calling AI to analyze requirements and generate priced BOQ with live rates..."))
            st.success(t("✅ تم التوليد بنجاح! راجع الجدول أدناه.", "✅ Generated successfully! Review the table below."))
            # Mock data based on system
            df = pd.DataFrame([
                {"البند": f"توريد وتركيب معدات {system_name} رئيسية", "الوحدة": "مقطوعية", "الكمية": 1, "سعر الوحدة (ج.م)": 150000, "الإجمالي": 150000},
                {"البند": "شبكات مواسير وكابلات التغذية", "الوحدة": "م.ط", "الكمية": area * 1.5, "سعر الوحدة (ج.م)": 450, "الإجمالي": area * 1.5 * 450},
                {"البند": "لوحات التحكم (MCC/PLC)", "الوحدة": "عدد", "الكمية": 2, "سعر الوحدة (ج.م)": 85000, "الإجمالي": 170000},
                {"البند": "أعمال الاختبار والتسليم (Testing & Commissioning)", "الوحدة": "مقطوعية", "الكمية": 1, "سعر الوحدة (ج.م)": 35000, "الإجمالي": 35000},
            ])
            st.dataframe(df, use_container_width=True)
            total = df["الإجمالي"].sum()
            st.markdown(f"#### {t('الإجمالي التقديري:', 'Estimated Total:')} <span style='color:var(--success);'>{total:,.2f} ج.م</span>", unsafe_allow_html=True)

    # ─── Tab 1: Water & Sewage ──────────────────────────────────────────
    with tabs[0]:
        st.markdown(f"#### {t('معدات وبنود محطات المياه والصرف الصحي', 'Water & Sewage Station Equipment')}")
        col1, col2 = st.columns(2)
        with col1:
             st.markdown("##### " + t("المضخات (Pumps)", "Pumps"))
             st.checkbox(t("مضخات غاطسة (Submersible)", "Submersible Pumps"))
             st.checkbox(t("مضخات طرد مركزي (Centrifugal)", "Centrifugal Pumps"))
             st.checkbox(t("طلمبات جرعات طرد (Dosing Pumps)", "Dosing Pumps"))
        with col2:
             st.markdown("##### " + t("الشبكات والمعالجة (Networks & Treatment)", "Networks & Treatment"))
             st.checkbox(t("مواسير سحب وطرد (uPVC / GRP / Ductile)", "Suction/Discharge Pipes"))
             st.checkbox(t("محابس (Gate, Check, Butterfly Valves)", "Valves"))
             st.checkbox(t("أنظمة معالجة وتهوية (Blowers & Diffusers)", "Aeration Systems"))
        
        st.markdown("---")
        generate_ai_boq_ui("محطات المياه والصرف")

    # ─── Tab 2: Fire Protection ────────────────────────────────────────
    with tabs[1]:
        st.markdown(f"#### {t('أنظمة الحماية المدنية ومكافحة الحريق', 'Fire Protection & Civil Defense')}")
        col1, col2 = st.columns(2)
        with col1:
             st.markdown("##### " + t("مكافحة الحريق المائية (Water Firefighting)", "Water Firefighting"))
             st.checkbox(t("شبكة مرشات تلقائية (Sprinkler System)", "Sprinkler System"))
             st.checkbox(t("صناديق حريق وحنفيات (Fire Hose Cabinets/Hydrants)", "Fire Hose Cabinets/Hydrants"))
             st.checkbox(t("طلمبات حريق (Fire Pump Rooms - Electric/Diesel/Jockey)", "Fire Pumps Set"))
        with col2:
             st.markdown("##### " + t("الإنذار والإطفاء الغازي (Alarm & Gas)", "Alarm & Gas Firefighting"))
             st.checkbox(t("لوحة إنذار حريق (Fire Alarm Panels - Addressable/Conv.)", "Fire Alarm Panels"))
             st.checkbox(t("حساسات دخان وحرارة (Smoke/Heat Detectors)", "Detectors"))
             st.checkbox(t("إطفاء بالغاز (FM200 / CO2 / NOVEC)", "Gas Extinguishing"))
        
        st.markdown("---")
        generate_ai_boq_ui("الحماية المدنية والحريق")

    # ─── Tab 3: HVAC ──────────────────────────────────────────────────
    with tabs[2]:
        st.markdown(f"#### {t('أنظمة التكييف والتهوية (HVAC)', 'HVAC Systems')}")
        col1, col2 = st.columns(2)
        with col1:
             st.markdown("##### " + t("معدات التكييف (AC Equipment)", "AC Equipment"))
             st.checkbox(t("وحدات مجمعة (Package Units)", "Package Units"))
             st.checkbox(t("أنظمة التدفق المتغير (VRF/VRV Systems)", "VRF/VRV Systems"))
             st.checkbox(t("مبردات مياه (Chillers & Cooling Towers)", "Chillers & Cooling Towers"))
        with col2:
             st.markdown("##### " + t("التهوية ومجاري الهواء (Ventilation & Ducts)", "Ventilation & Ducts"))
             st.checkbox(t("مجاري هواء صاج (Galvanized Steel Ducts)", "Galvanized Steel Ducts"))
             st.checkbox(t("مراوح سحب وطرد (Exhaust & Fresh Air Fans)", "Exhaust & Fresh Air Fans"))
             st.checkbox(t("مخارج هواء (Grilles / Diffusers / Louvers)", "Air Outlets"))
             
        st.markdown("---")
        generate_ai_boq_ui("أنظمة التكييف والتهوية")

    # ─── Tab 4: Electrical ────────────────────────────────────────────
    with tabs[3]:
        st.markdown(f"#### {t('الأنظمة الكهربائية والتيار الخفيف', 'Electrical & Low Current Systems')}")
        col1, col2 = st.columns(2)
        with col1:
             st.markdown("##### " + t("القوى والإنارة (Power & Lighting)", "Power & Lighting"))
             st.checkbox(t("لوحات توزيع رئيسية وفرعية (MDB / SMDB / DB)", "Distribution Boards"))
             st.checkbox(t("كابلات نحاس وألومنيوم (Cables & Wires)", "Cables & Wires"))
             st.checkbox(t("وحدات إنارة (Led Luminaires)", "Lighting Fixtures"))
        with col2:
             st.markdown("##### " + t("التيار الخفيف والتحكم (Low Current & Control)", "Low Current & Control"))
             st.checkbox(t("كاميرات مراقبة (CCTV Systems)", "CCTV Systems"))
             st.checkbox(t("شبكات داتا وتليفون (Data & Telephone Networks)", "Data & Telephone Networks"))
             st.checkbox(t("أنظمة تحكم ذكية (BMS / KNX / Smart Home)", "BMS / Smart Home"))
             
        st.markdown("---")
        generate_ai_boq_ui("الأنظمة الكهربائية")

    # ─── Tab 5: Plumbing ──────────────────────────────────────────────
    with tabs[4]:
        st.markdown(f"#### {t('أعمال السباكة والصرف الداخلي', 'Plumbing & Internal Drainage')}")
        col1, col2 = st.columns(2)
        with col1:
             st.markdown("##### " + t("تغذية المياه (Water Supply)", "Water Supply"))
             st.checkbox(t("مواسير تغذية (PPR / PEX / CPVC)", "Supply Pipes"))
             st.checkbox(t("مضخات رفع منزلية / معزز (Booster / Transfer Pumps)", "Booster / Transfer Pumps"))
             st.checkbox(t("خزانات مياه (Water Tanks - PE / GRP / Concrete)", "Water Tanks"))
        with col2:
             st.markdown("##### " + t("الصرف والأجهزة (Drainage & Fixtures)", "Drainage & Fixtures"))
             st.checkbox(t("مواسير صرف (uPVC / Cast Iron / HDPE)", "Drainage Pipes"))
             st.checkbox(t("أجهزة صحية (Sanitary Fixtures - WC, Basin, Sink)", "Sanitary Fixtures"))
             st.checkbox(t("غرف تفتيش ووصلات (Inspection Chambers & Fittings)", "Chambers & Fittings"))
             
        st.markdown("---")
        generate_ai_boq_ui("أعمال السباكة")
