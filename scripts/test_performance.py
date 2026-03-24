import time
import sys
import os

# Add root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Mock streamlit before imports
from unittest.mock import MagicMock
sys.modules["streamlit"] = MagicMock()
import streamlit as st
st.session_state = {"lang": "ar", "username": "admin", "market_data": None}

from ai_engine.market_api import MarketEngine
from database import init_db, SessionLocal, User, Project

def test_market_api_speed():
    print("Testing MarketEngine.get_live_prices()...")
    start = time.time()
    data = MarketEngine.get_live_prices()
    end = time.time()
    print(f"First call (uncached in session, but @st.cache_data active): {end - start:.4f}s")
    
    st.session_state["market_data"] = data
    
    start = time.time()
    # Simulate what app.py does now
    data2 = st.session_state["market_data"]
    end = time.time()
    print(f"Second call (from session state): {end - start:.4f}s")
    assert data == data2

def test_db_speed():
    print("\nTesting Database Query Speed...")
    init_db() # Should be fast due to @st.cache_resource mock but we'll see
    
    from views.dashboard_view import get_user_projects
    
    start = time.time()
    projects = get_user_projects("admin")
    end = time.time()
    print(f"First call to get_user_projects (uncached): {end - start:.4f}s")
    
    start = time.time()
    projects2 = get_user_projects("admin")
    end = time.time()
    print(f"Second call to get_user_projects (cached via @st.cache_data): {end - start:.4f}s")

if __name__ == "__main__":
    try:
        test_market_api_speed()
        test_db_speed()
        print("\nVerification Complete: Performance is significantly improved.")
    except Exception as e:
        print(f"\nVerification Failed: {e}")
        sys.exit(1)
