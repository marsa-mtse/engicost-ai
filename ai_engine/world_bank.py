# ==========================================================
# World Bank API Adapter — Free Official Data Source
# ==========================================================

import requests
from datetime import datetime, timedelta

class WorldBankAPI:
    """
    Fetches official construction-related indicators from the World Bank Open Data API.
    No API key required. Data is updated quarterly.
    """

    BASE_URL = "https://api.worldbank.org/v2"

    # Key indicators for construction cost intelligence
    INDICATORS = {
        "inflation_egypt": "FP.CPI.TOTL.ZG",      # Egypt CPI / Inflation rate
        "gdp_egypt": "NY.GDP.MKTP.CD",             # Egypt GDP (construction scale)
        "exchange_usd_egp": "PA.NUS.FCRF",         # Official exchange rate USD→EGP
        "steel_trade_index": "TX.VAL.MRCH.CD.WT",  # Merchandize trade value
    }

    @staticmethod
    def _fetch(indicator: str, country: str = "EG", years: int = 5):
        """Generic fetch from World Bank API."""
        try:
            url = f"{WorldBankAPI.BASE_URL}/country/{country}/indicator/{indicator}"
            params = {
                "format": "json",
                "per_page": years,
                "mrv": years,
            }
            resp = requests.get(url, params=params, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                if len(data) >= 2 and data[1]:
                    return [
                        {"year": d.get("date"), "value": d.get("value")}
                        for d in data[1] if d.get("value") is not None
                    ]
        except Exception:
            pass
        return []

    @staticmethod
    def get_egypt_inflation():
        """Returns Egypt CPI inflation rate data."""
        return WorldBankAPI._fetch(WorldBankAPI.INDICATORS["inflation_egypt"])

    @staticmethod
    def get_exchange_rate_history():
        """Returns historical USD/EGP exchange rate."""
        return WorldBankAPI._fetch(WorldBankAPI.INDICATORS["exchange_usd_egp"])

    @staticmethod
    def get_gdp_data():
        """Returns Egypt GDP time series."""
        return WorldBankAPI._fetch(WorldBankAPI.INDICATORS["gdp_egypt"])

    @staticmethod
    def get_summary():
        """
        Returns a compact summary of the most important World Bank indicators.
        Used to enrich AI context and forecasting views.
        """
        inflation_data = WorldBankAPI.get_egypt_inflation()
        exchange_data = WorldBankAPI.get_exchange_rate_history()

        latest_inflation = inflation_data[0]["value"] if inflation_data else None
        latest_exchange = exchange_data[0]["value"] if exchange_data else None

        return {
            "source": "World Bank Open Data",
            "updated_at": datetime.utcnow().strftime("%Y-%m-%d"),
            "inflation_rate_pct": latest_inflation,
            "official_usd_egp": latest_exchange,
            "inflation_series": inflation_data[:5],
            "exchange_series": exchange_data[:5],
        }
