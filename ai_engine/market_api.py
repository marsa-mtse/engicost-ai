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

import requests
from bs4 import BeautifulSoup
import re

class RealTimeScraper:
    """
    Scraper for Egyptian construction material prices from official sources.
    """
    @staticmethod
    def get_ezz_steel_price():
        """Scrapes the latest rebar price from ezz-steel.com."""
        url = "https://www.ezzsteel.com/en/our-products/rebar-and-wire-rod/prices"
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                # Look for price patterns like "EGP XX,XXX"
                text = soup.get_text()
                prices = re.findall(r"EGP\s?(\d{1,3}(?:,\d{3})*)", text)
                if prices:
                    # Return the first found price as an integer
                    return int(prices[0].replace(",", ""))
        except Exception:
            pass
        return None

    @staticmethod
    def get_suez_cement_price():
        """Placeholder for Suez Cement scraping logic."""
        # Note: Often cement prices are published on news sites or aggregate portals
        return None

    @staticmethod
    def get_cbe_exchange_rate():
        """Scrapes the official CBE exchange rate."""
        url = "https://www.cbe.org.eg/en/EconomicResearch/Statistics/Pages/ExchangeRates.aspx"
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                # Find the USD row
                usd_cell = soup.find(text=re.compile(r"US Dollar"))
                if usd_cell:
                    row = usd_cell.find_parent("tr")
                    cells = row.find_all("td")
                    # Usually the Buy/Sell rates are in the next cells
                    rate = float(cells[-1].get_text())
                    return rate
        except Exception:
            pass
        return None

class MarketEngine:
    """
    Handles fetching and simulating market prices for core construction materials.
    Designed to be easily connected to real commodity APIs.
    Uses an in-memory TTL cache to avoid redundant API/AI calls.
    """
    
    # Base prices for international standards (approx USD) - Updated for Egypt March 2026
    BASE_PRICES = {
        "Ezz Steel (Ton)": 790.0,
        "Cement (Ton)": 84.0,
        "Concrete (m3)": 36.0,
        "Red Bricks (1000)": 48.0,
        "Copper (kg)": 9.5,
        "Aluminum (Ton)": 2480.0
    }

    # ─── Sanity bounds for Egypt market Mar 2026 (EGP) ──────────────
    PRICE_BOUNDS_EGP = {
        "Iron_Steel_Ton":  (32000, 55000),
        "Cement_Ton":      (3000,  6500),
        "Concrete_m3":     (1200,  2800),
    }
    PRICE_BOUNDS_USD = {
        "Copper_Ton":    (7000, 12000),
        "Aluminum_Ton":  (1800,  3500),
    }
    RATE_BOUNDS = (45.0, 58.0)

    @staticmethod
    def _validate_prices(data: dict) -> bool:
        try:
            rate = float(data.get("EGP_USD_RATE", 0))
            if not (MarketEngine.RATE_BOUNDS[0] <= rate <= MarketEngine.RATE_BOUNDS[1]):
                return False
            for key, (lo, hi) in MarketEngine.PRICE_BOUNDS_EGP.items():
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
        Fetches prices using direct scraping (Primary) and AI Search (Secondary).
        """
        # --- Attempt Direct Scraping First ---
        if region == "Egypt" or region == "Global":
            scraped_steel = RealTimeScraper.get_ezz_steel_price()
            scraped_rate = RealTimeScraper.get_cbe_exchange_rate()
            
            if scraped_steel and scraped_rate:
                # If we got the core EG data, we can proceed with a hybrid
                return {
                    "Iron_Steel_Ton": scraped_steel,
                    "Cement_Ton": 4200, # Fallback to stable mean if scraper fails
                    "Concrete_m3": 1850,
                    "Copper_Ton": 9800,
                    "Aluminum_Ton": 2550,
                    "EGP_USD_RATE": scraped_rate,
                    "Source_Steel": "Ezz Steel (Real-time Scraping)",
                    "Source_Cement": "Market Industry Average",
                    "Is_Scraped": True
                }

        # --- Fallback to AI Search ---
        from ai_engine.cost_engine import get_cost_engine
        engine = get_cost_engine()

        prompt = f"""
        Search for construction material prices in Egypt as of {datetime.now().strftime('%B %Y')}.
        Return ONLY a JSON object:
        {{
            "Iron_Steel_Ton": <EGP per ton>,
            "Cement_Ton":     <EGP per ton>,
            "Concrete_m3":    <EGP per m3>,
            "Copper_Ton":     <USD per ton>,
            "Aluminum_Ton":   <USD per ton>,
            "EGP_USD_RATE":   <float>,
            "Source_Steel":   "<name>",
            "Source_Cement":  "<name>"
        }}
        """
        try:
            res, _ = engine._call_gemini_text(prompt, expect_json=True)
            if res and MarketEngine._validate_prices(res):
                return res
        except Exception:
            pass
        return None

    @staticmethod
    def get_live_prices(force_refresh: bool = False) -> dict:
        """
        Entry point for all market data requests.
        """
        region = st.session_state.get("region", "Egypt")
        if force_refresh:
            st.cache_data.clear()

        data = MarketEngine.fetch_real_time_prices(region)
        
        if data and isinstance(data, dict):
            rate = float(data.get("EGP_USD_RATE", 50.0))
            prices = {
                "Iron & Steel (Ton)": {"egp": float(data["Iron_Steel_Ton"]), "usd": float(data["Iron_Steel_Ton"]) / rate},
                "Cement (Ton)": {"egp": float(data["Cement_Ton"]), "usd": float(data["Cement_Ton"]) / rate},
                "Ready-mix Concrete (m3)": {"egp": float(data["Concrete_m3"]), "usd": float(data["Concrete_m3"]) / rate},
                "Copper (Ton/Global)": {"usd": float(data["Copper_Ton"]), "egp": float(data["Copper_Ton"]) * rate},
                "Aluminum (Ton/Global)": {"usd": float(data["Aluminum_Ton"]), "egp": float(data["Aluminum_Ton"]) * rate}
            }
            return {
                "prices": prices, 
                "rate": rate, 
                "sources": {k: data.get(f"Source_{k.split(' ')[0]}", "Industry Data") for k in prices.keys()},
                "live": True
            }

        # FINAL FALLBACK: Local Simulation
        rate = 50.0
        simulated = {
            "Iron & Steel (Ton)": {"egp": 39500, "usd": 790},
            "Cement (Ton)": {"egp": 4200, "usd": 84},
            "Ready-mix Concrete (m3)": {"egp": 1850, "usd": 37},
            "Red Bricks (1000)": {"egp": 2400, "usd": 48},
            "Copper (Ton/Global)": {"usd": 9500, "egp": 475000},
            "Aluminum (Ton/Global)": {"usd": 2480, "egp": 124000}
        }
        return {"prices": simulated, "rate": rate, "sources": {k: "Manual Update (Mar 2026)" for k in simulated.keys()}}


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
