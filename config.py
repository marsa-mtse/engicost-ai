import os
import streamlit as st
from dotenv import load_dotenv

# Load local .env if exists
load_dotenv()

def get_secret(key, default=None):
    """Unified helper to get secrets from Streamlit or Environment."""
    try:
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return os.getenv(key, default)

# App Info
APP_NAME = "EngiCost AI"
APP_VERSION = "1.2.0"

# Secret Key for JWT/Sessions
SECRET_KEY = get_secret("SECRET_KEY", "prod-secret-key-39281726354")

# Database URI
DATABASE_URL = get_secret("DATABASE_URL", "sqlite:///engicost.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# ─── Subscription Plans (EGP Pricing) ───────────────────────────────────────
PLANS = {
    "Free":       {"price_egp": 0,    "price_usd": 0,   "max_blueprints": 1,   "max_boq": 1},
    "Pro":        {"price_egp": 299,  "price_usd": 6,   "max_blueprints": 50,  "max_boq": 100},
    "Enterprise": {"price_egp": 799,  "price_usd": 16,  "max_blueprints": -1,  "max_boq": -1},
}

# ─── Paymob Egypt Payment Gateway ───────────────────────────────────────────
PAYMOB_API_KEY          = get_secret("PAYMOB_API_KEY")
PAYMOB_HMAC_SECRET      = get_secret("PAYMOB_HMAC_SECRET")
PAYMOB_CARD_INTG_ID     = get_secret("PAYMOB_CARD_INTG_ID")
PAYMOB_FAWRY_INTG_ID    = get_secret("PAYMOB_FAWRY_INTG_ID")
PAYMOB_IFRAME_ID        = get_secret("PAYMOB_IFRAME_ID")
PAYMOB_BASE_URL         = "https://accept.paymob.com/api"

# ─── AI Settings ─────────────────────────────────────────────────────────────
OPENAI_API_KEY = get_secret("OPENAI_API_KEY")
GEMINI_API_KEY = get_secret("GEMINI_API_KEY")
GROQ_API_KEY   = get_secret("GROQ_API_KEY")
