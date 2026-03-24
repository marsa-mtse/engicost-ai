import bcrypt
import hashlib
import streamlit as st
import json
import os
from database import get_session_local, User
from sync_engine import check_connection

LOCAL_AUTH_FILE = ".local_auth.json"


def _prepare_password(password: str) -> bytes:
    """Pre-hash with SHA-256 to always stay under bcrypt's 72-byte limit."""
    return hashlib.sha256(password.encode('utf-8')).hexdigest().encode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(_prepare_password(plain_password), hashed_password.encode('utf-8'))
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    hashed = bcrypt.hashpw(_prepare_password(password), bcrypt.gensalt())
    return hashed.decode('utf-8')

def _save_local_auth(username, hashed_password, plan="Free"):
    """Save credentials and plan to a local file for offline access."""
    try:
        auth_data = {}
        if os.path.exists(LOCAL_AUTH_FILE):
            with open(LOCAL_AUTH_FILE, "r") as f:
                auth_data = json.load(f)
        
        auth_data[username] = {"hash": hashed_password, "plan": plan}
        with open(LOCAL_AUTH_FILE, "w") as f:
            json.dump(auth_data, f)
    except:
        pass

def _check_local_auth(username, password):
    """Verify credentials against local file."""
    try:
        if not os.path.exists(LOCAL_AUTH_FILE):
            return None
        with open(LOCAL_AUTH_FILE, "r") as f:
            auth_data = json.load(f)
        
        entry = auth_data.get(username)
        if not entry:
            return None
        
        # Support both old format (plain hash string) and new format (dict)
        if isinstance(entry, dict):
            hashed_pwd = entry.get("hash", "")
            saved_plan = entry.get("plan", "Free")
        else:
            hashed_pwd = entry  # Legacy format
            saved_plan = "Free"
        
        if hashed_pwd and verify_password(password, hashed_pwd):
            class MockUser:
                def __init__(self, username, plan):
                    self.username = username
                    self.plan = plan
                    self.role = "User"
            return MockUser(username, saved_plan)
    except:
        pass
    return None

import datetime

def authenticate_user(username, password):
    is_online = check_connection()
    
    if not is_online:
        return _check_local_auth(username, password)

    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            return False
        if not verify_password(password, user.hashed_password):
            return False
        
        # Success: Save to local for next offline session (with real plan)
        _save_local_auth(username, user.hashed_password, plan=user.plan or "Free")
        
        # Update last login
        user.last_login = datetime.datetime.utcnow()
        db.commit()
        db.refresh(user)
        return user
    except Exception:
        # Fallback if DB is online but query fails (e.g. timeout)
        return _check_local_auth(username, password)
    finally:
        db.close()


def create_user(username, email, password):
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        if db.query(User).filter((User.username == username) | (User.email == email)).first():
            return None

        hashed_pwd = get_password_hash(password)
        now = datetime.datetime.utcnow()
        new_user = User(
            username=username, 
            email=email, 
            hashed_password=hashed_pwd,
            subscription_start=now,
            last_login=now
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    finally:
        db.close()


def init_session():
    """Initialize session state variables."""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'plan' not in st.session_state:
        st.session_state.plan = "Free"
    if 'role' not in st.session_state:
        st.session_state.role = "User"
    if 'lang' not in st.session_state:
        st.session_state.lang = "ar"
    if 'region' not in st.session_state:
        st.session_state.region = "Global"
    if 'currency' not in st.session_state:
        st.session_state.currency = "USD"


def logout():
    st.session_state.authenticated = False
    st.session_state.username = None
    st.session_state.plan = "Free"
    st.rerun()
