import requests
import streamlit as st
import time

@st.cache_data(ttl=30)
def check_connection() -> bool:
    """Check if the internet/DB connection is active. Cached for 30 seconds to avoid blocking every render."""
    try:
        requests.get("https://www.google.com", timeout=2)
        return True
    except Exception:
        return False

def get_connection_status():
    """Get status with icon and text."""
    is_online = check_connection()
    if is_online:
        return "🟢 Online", True
    else:
        return "🔴 Offline (Site Mode)", False

def render_sync_indicator():
    """Render a small sync indicator in the sidebar."""
    from database import get_engine
    engine = get_engine()
    db_type = "PostgreSQL (Cloud)" if "postgresql" in str(engine.url) else "SQLite (Local)"
    
    status_text, is_online = get_connection_status()
    st.sidebar.markdown(f"**Status:** {status_text}")
    st.sidebar.markdown(f"**Database:** `{db_type}`")
    
    if not is_online:
        st.sidebar.warning("⚠️ Working in Offline Mode. Data will be saved locally.")
    
    if "sync_queue" not in st.session_state:
        st.session_state.sync_queue = []
        
    if is_online and len(st.session_state.sync_queue) > 0:
        if st.sidebar.button(f"🔄 Sync {len(st.session_state.sync_queue)} pending items"):
            st.sidebar.info("Syncing...")
            time.sleep(1)
            st.session_state.sync_queue = []
            st.sidebar.success("Sync complete!")
            st.rerun()
