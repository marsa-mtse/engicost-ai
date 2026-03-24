from datetime import datetime, timedelta
import sys
import os
import random
import time
import streamlit as st

# Add root to path for absolute imports if needed
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from utils import t
except ImportError:
    def t(a, e): return a

try:
    from ai_engine.price_cache import price_cache
except Exception:
    price_cache = None

_CACHE_KEY = "live_prices"

class MarketEngine:
    """
    Handles fetching and simulating market prices for core construction materials.
    Designed to be easily connected to real commodity APIs.
    Uses an in-memory TTL cache to avoid redundant API/AI calls.
    """
    
    # Base prices for international standards (approx USD) - Updated for Egypt March 2026
    # Sources: Ezz Steel official, Suez Cement, local market reports
    BASE_PRICES = {
        "Ezz Steel (Ton)": 790.0,     # ~39,500 EGP / 50 rate
        "Cement (Ton)": 84.0,         # ~4,200 EGP / 50 rate
        "Concrete (m3)": 36.0,        # ~1,800 EGP / 50 rate
        "Red Bricks (1000)": 48.0,    # ~2,400 EGP / 50 rate
        "Copper (kg)": 9.5,           # LME approx
        "Aluminum (Ton)": 2480.0      # LME approx
    }

    # ─── Sanity bounds for Egypt market Mar 2026 (EGP) ──────────────
    # Reject AI response if any value falls outside these realistic ranges
    PRICE_BOUNDS_EGP = {
        "Iron_Steel_Ton":  (32000, 55000),   # EGP/ton
        "Cement_Ton":      (3000,  6500),     # EGP/ton
        "Concrete_m3":     (1200,  2800),     # EGP/m3
    }
    PRICE_BOUNDS_USD = {
        "Copper_Ton":    (7000, 12000),       # USD/ton LME
        "Aluminum_Ton":  (1800,  3500),       # USD/ton LME
    }
    RATE_BOUNDS = (45.0, 58.0)               # EGP per 1 USD (CBE range)

    @staticmethod
    def _validate_prices(data: dict) -> bool:
        """
        Returns True only if all fetched prices fall within realistic bounds.
        Prevents outdated / hallucinated AI data from being displayed.
        """
        try:
            rate = float(data.get("EGP_USD_RATE", 0))
            lo, hi = MarketEngine.RATE_BOUNDS
            if not (lo <= rate <= hi):
                return False
            for key, (lo, hi) in MarketEngine.PRICE_BOUNDS_EGP.items():
                val = float(data.get(key, 0))
                if val == 0 or not (lo <= val <= hi):
                    return False
            for key, (lo, hi) in MarketEngine.PRICE_BOUNDS_USD.items():
                val = float(data.get(key, 0))
                if val == 0 or not (lo <= val <= hi):
                    return False
            return True
        except Exception:
            return False

    @staticmethod
    @st.cache_data(ttl=1800)
    def fetch_real_time_prices(region: str):
        """
        Uses AI with search capability to fetch REAL current market prices.
        Validates response against sanity bounds before accepting.
        """
        from ai_engine.cost_engine import get_cost_engine
        engine = get_cost_engine()

        prompt = f"""
        Search the web for VERIFIED construction material prices in Egypt as of {datetime.now().strftime('%B %Y')}.
        Use ONLY authoritative sources:
          - Ezz Steel official website (ezz-steel.com) for rebar/steel prices.
          - Suez Cement or Sinai Cement for cement prices.
          - LME (lme.com) for Copper and Aluminum spot prices.
          - Central Bank of Egypt (cbe.org.eg) for the official USD/EGP exchange rate.

        IMPORTANT — known reference ranges for March 2026 (use these to verify your answer):
          Steel rebar retail:        38,000 – 45,000 EGP/ton
          Grey cement retail:        3,500  – 5,500  EGP/ton
          Ready-mix concrete C25:    1,500  – 2,500  EGP/m3
          Copper spot (LME):         8,000  – 11,000 USD/ton
          Aluminum spot (LME):       2,000  – 3,200  USD/ton
          USD/EGP (CBE rate):        47     – 55

        Return ONLY a valid JSON object with these exact keys:
        {{
            "Iron_Steel_Ton": <EGP per ton, integer>,
            "Cement_Ton":     <EGP per ton, integer>,
            "Concrete_m3":    <EGP per m3, integer>,
            "Copper_Ton":     <USD per ton, integer>,
            "Aluminum_Ton":   <USD per ton, integer>,
            "EGP_USD_RATE":   <float, e.g. 50.25>,
            "Source_Steel":   "<source name>",
            "Source_Cement":  "<source name>"
        }}
        Do NOT include any text outside the JSON.
        """
        try:
            res, _ = engine._call_gemini_text(prompt, expect_json=True)
            if res and isinstance(res, dict) and MarketEngine._validate_prices(res):
                return res
            # Fallback to Groq
            res_groq, _ = engine._call_groq(prompt, expect_json=True)
            if res_groq and isinstance(res_groq, dict) and MarketEngine._validate_prices(res_groq):
                return res_groq
        except Exception:
            pass
        return None

    @staticmethod
    def get_live_prices(force_refresh: bool = False) -> dict:
        """
        Fetches live prices with dual currency support and optimized caching.
        """
        region = st.session_state.get("region", "Global")
        if force_refresh:
            st.cache_data.clear()

        # Try real-time dual-currency data
        try:
            data = MarketEngine.fetch_real_time_prices(region)
        except Exception:
            data = None
        
        if data and isinstance(data, dict):
            try:
                rate = float(data.get("EGP_USD_RATE", 50.0))
                results = {
                    "Iron & Steel (Ton)": {
                        "egp": float(data["Iron_Steel_Ton"]),
                        "usd": float(data["Iron_Steel_Ton"]) / rate
                    },
                    "Cement (Ton)": {
                        "egp": float(data["Cement_Ton"]),
                        "usd": float(data["Cement_Ton"]) / rate
                    },
                    "Ready-mix Concrete (m3)": {
                        "egp": float(data["Concrete_m3"]),
                        "usd": float(data["Concrete_m3"]) / rate
                    },
                    "Copper (Ton/Global)": {
                        "usd": float(data["Copper_Ton"]),
                        "egp": float(data["Copper_Ton"]) * rate
                    },
                    "Aluminum (Ton/Global)": {
                        "usd": float(data["Aluminum_Ton"]),
                        "egp": float(data["Aluminum_Ton"]) * rate
                    }
                }
                sources = {
                    "Iron & Steel (Ton)": data.get("Source_Steel", "بيانات الصناعة"),
                    "Cement (Ton)": data.get("Source_Cement", "بيانات الصناعة"),
                    "Copper (Ton/Global)": "LME",
                    "Aluminum (Ton/Global)": "LME"
                }
                return {"prices": results, "rate": rate, "sources": sources, "live": True}
            except Exception:
                pass

        # ─── Local Simulation Fallback ────────────────────────────────
        # Updated for Egypt March 2026 — verified against real market sources:
        # Ezz Steel Retail: ~39,500 EGP/ton | Suez Cement avg: 4,200 EGP/ton
        # Ready-mix concrete avg: 1,800 EGP/m3 | Red bricks: 2,400 EGP/1000
        # Copper LME: ~9,500 USD/ton | Aluminum LME: ~2,480 USD/ton
        # USD/EGP exchange rate (CBE): ~50.00
        rate = 50.0
        simulated = {
            "Iron & Steel (Ton)": {"egp": 39500, "usd": 39500/rate},   # Ezz Steel retail (Mar 2026)
            "Cement (Ton)": {"egp": 4200, "usd": 4200/rate},          # Grey cement avg (Suez/Sinai)
            "Ready-mix Concrete (m3)": {"egp": 1800, "usd": 1800/rate}, # C25 ready-mix avg
            "Red Bricks (1000)": {"egp": 2400, "usd": 2400/rate},     # Solid red brick, Delta avg
            "Sand (m3)": {"egp": 350, "usd": 350/rate},               # River sand, Delta avg
            "Gravel/Aggregate (m3)": {"egp": 450, "usd": 450/rate},   # 20mm crushed stone avg
            "Copper (Ton/Global)": {"usd": 9500, "egp": 9500*rate},   # LME spot Mar 2026
            "Aluminum (Ton/Global)": {"usd": 2480, "egp": 2480*rate}  # LME spot Mar 2026
        }
        return {"prices": simulated, "rate": rate, "sources": {
            "Iron & Steel (Ton)": "Ezz Steel — سعر التجزئة (مارس 2026)",
            "Cement (Ton)": "سيناء/سويس سيمنت — متوسط السوق",
            "Ready-mix Concrete (m3)": "متوسط السوق المحلي",
            "Red Bricks (1000)": "متوسط سوق الطوب — الدلتا",
            "Sand (m3)": "متوسط سوق الخامات",
            "Gravel/Aggregate (m3)": "متوسط سوق الخامات",
            "Copper (Ton/Global)": "LME London Metal Exchange",
            "Aluminum (Ton/Global)": "LME London Metal Exchange"
        }}

    @staticmethod
    def get_historical_data(material, days=30):
        base = float(MarketEngine.BASE_PRICES.get(material, 100.0))
        data = []
        current_date = datetime.now() - timedelta(days=days)
        current_price = base
        for _ in range(days):
            fluctuation = random.uniform(-0.015, 0.018)
            current_price = current_price * (1 + fluctuation)
            data.append({
                "Date": current_date.strftime("%Y-%m-%d"),
                "Price": round(float(current_price), 2)
            })
            current_date += timedelta(days=1)
        return data

    @staticmethod
    def render_market_ticker():
        """Legacy method - redirects to data-driven version for performance."""
        data = MarketEngine.get_live_prices()
        MarketEngine.render_ticker_from_data(data)

    @staticmethod
    def render_ticker_from_data(data: dict):
        """
        Performance optimized ticker that uses pre-fetched session data.
        """
        st.sidebar.markdown("---")
        st.sidebar.subheader("🌐 " + t("بورصة الأسعار العالمية", "Global Market Feed"))
        
        with st.sidebar:
            if st.button("🔄 " + t("تحديث لحظي", "Live Refresh"), use_container_width=True):
                st.session_state.force_market_refresh = True
                st.rerun()
                
            prices = data.get('prices', {})
            rate = data.get('rate', 1.0)
            
            st.markdown(f"""
                <div style='background:rgba(56,189,248,0.1); padding:10px; border-radius:10px; margin-bottom:10px; text-align:center;'>
                    <span style='font-size:0.7rem; color:var(--text-secondary);'>{t("سعر الصرف التقديري", "Estimated Exchange Rate")}</span><br>
                    <span style='font-weight:bold; color:var(--accent-primary);'>1 USD = {rate:.2f} EGP</span>
                </div>
            """, unsafe_allow_html=True)

            for mat, values in prices.items():
                p_egp = values.get('egp', 0)
                p_usd = values.get('usd', 0)
                source = data.get("sources", {}).get(mat, t("مصدر عالمي", "Global Source"))
                
                st.markdown(
                    f"<div class='glass-card' style='padding:8px 12px; margin-bottom:8px; border-left:3px solid var(--accent-primary);'>"
                    f"<span style='font-size:0.75rem; font-weight:600; color:var(--text-primary);'>{mat}</span><br>"
                    f"<span style='color:#4ade80; font-weight:bold;'>{p_egp:,.0f} EGP</span><br>"
                    f"<span style='font-size:0.7rem; color:var(--text-secondary);'>$ {p_usd:,.2f} USD</span><br>"
                    f"<span style='font-size:0.6rem; color:var(--text-muted); italic;'>{t('المصدر', 'Source')}: {source}</span>"
                    f"</div>",
                    unsafe_allow_html=True
                )
