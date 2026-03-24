from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Float, Boolean, Text
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime
import os
from config import DATABASE_URL

# Database Configuration
LOCAL_DB_URL = "sqlite:///./engi_local.db"

def create_db_engine():
    try:
        # Try primary URL with short timeout to prevent hang
        connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {"connect_timeout": 5}
        _engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
        # Test connection (shallow check)
        with _engine.connect() as conn:
            pass
        return _engine
    except Exception:
        # Fallback to local SQLite immediately if cloud fails
        return create_engine(LOCAL_DB_URL, connect_args={"check_same_thread": False})

_engine = None

def get_engine():
    global _engine
    if _engine is None:
        _engine = create_db_engine()
    return _engine

def get_session_local():
    return sessionmaker(autocommit=False, autoflush=False, bind=get_engine())

def SessionLocal(*args, **kwargs):
    """Compatibility wrapper for legacy SessionLocal imports."""
    return get_session_local()(*args, **kwargs)

Base = declarative_base()

class Company(Base):
    __tablename__ = "companies"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True)
    logo_path = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Workspace(Base):
    __tablename__ = "workspaces"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    join_code = Column(String(20), unique=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    email = Column(String(100), unique=True, index=True)
    hashed_password = Column(String(200))
    plan = Column(String(50), default="Free") # Free, Pro, Enterprise
    role = Column(String(20), default="Engineer") # Admin, Engineer, Manager
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=True)
    workspace_role = Column(String(20), default="Owner") # Owner, Admin, Member
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Usage metrics
    blueprints_analyzed = Column(Integer, default=0)
    boqs_generated = Column(Integer, default=0)
    last_login = Column(DateTime)
    subscription_start = Column(DateTime)
    subscription_end = Column(DateTime)
    
    # Relationship to Project
    projects = relationship("Project", back_populates="owner")
    
    company = relationship("Company")

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=True)
    name = Column(String(100))
    project_type = Column(String(50)) # Blueprint or BOQ
    result_data = Column(String) # JSON string of result
    is_public = Column(Boolean, default=False)
    share_token = Column(String(100), unique=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    owner = relationship("User", foreign_keys=[owner_id])

class ProjectAccess(Base):
    __tablename__ = "project_access"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    can_edit = Column(Boolean, default=True)

class Inquiry(Base):
    __tablename__ = "inquiries"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100))
    subject = Column(String(200))
    message = Column(Text)
    status = Column(String(20), default="New") # New, Read, Replied
    created_at = Column(DateTime, default=datetime.utcnow)

class InventoryItem(Base):
    __tablename__ = "inventory_items"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    name = Column(String(100))
    unit = Column(String(20)) # Ton, m3, m2, etc.
    quantity = Column(Float, default=0.0)
    avg_price = Column(Float, default=0.0) # Average purchase price
    last_updated = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project")

class MaterialTransaction(Base):
    __tablename__ = "material_transactions"
    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("inventory_items.id"))
    type = Column(String(20)) # "IN" (Purchase), "OUT" (Consumption)
    quantity = Column(Float)
    unit_price = Column(Float, nullable=True)
    note = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    item = relationship("InventoryItem")

class Expense(Base):
    __tablename__ = "expenses"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    category = Column(String(50)) # Labor, Fuel, Equipment, etc.
    amount = Column(Float)
    description = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project")

class Staff(Base):
    __tablename__ = "staff"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    name = Column(String(100))
    role = Column(String(50)) # Foreman, Engineer, Laborer, etc.
    salary_rate = Column(Float) # Daily or monthly rate
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project")

class Attendance(Base):
    __tablename__ = "attendance"
    id = Column(Integer, primary_key=True, index=True)
    staff_id = Column(Integer, ForeignKey("staff.id"))
    date = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20)) # "Present", "Absent", "Leave"
    hours = Column(Float, default=8.0)
    notes = Column(String(200), nullable=True)

    staff = relationship("Staff")

class Equipment(Base):
    __tablename__ = "equipment"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    name = Column(String(100))
    type = Column(String(50)) # Excavator, Mixer, etc.
    ownership = Column(String(20)) # "Owned", "Rented"
    daily_rate = Column(Float, nullable=True) # If rented
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project")

class EquipmentLog(Base):
    __tablename__ = "equipment_logs"
    id = Column(Integer, primary_key=True, index=True)
    equipment_id = Column(Integer, ForeignKey("equipment.id"))
    date = Column(DateTime, default=datetime.utcnow)
    hours_worked = Column(Float)
    fuel_cost = Column(Float, default=0.0)
    operator_name = Column(String(100), nullable=True)
    notes = Column(String(200), nullable=True)

    equipment = relationship("Equipment")

import streamlit as st

def run_migrations():
    """Core logic to initialize database and run manual migrations."""
    curr_engine = get_engine()
    Base.metadata.create_all(bind=curr_engine)
    
    from sqlalchemy import inspect, text
    
    dialect = "postgresql" if "postgresql" in str(curr_engine.url) else "sqlite"
    dt_type = "TIMESTAMP" if dialect == "postgresql" else "DATETIME"
    bool_type = "BOOLEAN" if dialect == "postgresql" else "BOOLEAN"
    
    try:
        with curr_engine.connect() as conn:
            inspector = inspect(curr_engine)
            existing_tables = inspector.get_table_names()

            # --- Force Create New Tables if missing ---
            new_tables = ["inventory_items", "material_transactions", "expenses", "inquiries", "staff", "attendance", "equipment", "equipment_logs", "workspaces"]
            for table_name in new_tables:
                if table_name not in existing_tables:
                    print(f"Table {table_name} missing, creating...")
            
            Base.metadata.create_all(bind=curr_engine)
            inspector = inspect(curr_engine) 
            
            # --- Users Table ---
            user_columns = [c['name'] for c in inspector.get_columns("users")]
            if "role" not in user_columns:
                conn.execute(text(f"ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'Engineer'"))
            if "company_id" not in user_columns:
                conn.execute(text(f"ALTER TABLE users ADD COLUMN company_id INTEGER"))
            if "last_login" not in user_columns:
                conn.execute(text(f"ALTER TABLE users ADD COLUMN last_login {dt_type}"))
            if "subscription_start" not in user_columns:
                conn.execute(text(f"ALTER TABLE users ADD COLUMN subscription_start {dt_type}"))
            if "subscription_end" not in user_columns:
                conn.execute(text(f"ALTER TABLE users ADD COLUMN subscription_end {dt_type}"))
            if "workspace_id" not in user_columns:
                conn.execute(text(f"ALTER TABLE users ADD COLUMN workspace_id INTEGER"))
            if "workspace_role" not in user_columns:
                conn.execute(text(f"ALTER TABLE users ADD COLUMN workspace_role VARCHAR(20) DEFAULT 'Owner'"))
            conn.commit()

            # --- Projects Table ---
            inspector = inspect(curr_engine)
            project_columns = [c['name'] for c in inspector.get_columns("projects")]
            if "owner_id" not in project_columns and "user_id" in project_columns:
                conn.execute(text(f"ALTER TABLE projects ADD COLUMN owner_id INTEGER"))
                conn.execute(text("UPDATE projects SET owner_id = user_id"))
            if "is_public" not in project_columns:
                conn.execute(text(f"ALTER TABLE projects ADD COLUMN is_public {bool_type} DEFAULT {'FALSE' if dialect=='postgresql' else '0'}"))
            if "share_token" not in project_columns:
                conn.execute(text("ALTER TABLE projects ADD COLUMN share_token VARCHAR(100)"))
            if "updated_at" not in project_columns:
                conn.execute(text(f"ALTER TABLE projects ADD COLUMN updated_at {dt_type}"))
            if "workspace_id" not in project_columns:
                conn.execute(text(f"ALTER TABLE projects ADD COLUMN workspace_id INTEGER"))
            conn.commit()
            
    except Exception as e:
        print(f"Database migration error: {e}")
    
    # Create default Admin
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        admin_exists = db.query(User).filter(User.username == "admin").first()
        if not admin_exists:
            from auth import create_user
            admin_user = create_user("admin", "admin@engicost.ai", "admin123")
            db_admin = db.query(User).filter(User.username == "admin").first()
            if db_admin:
                 db_admin.plan = "Enterprise"
                 db_admin.role = "Admin"
                 db.commit()
    except Exception:
        pass
    finally:
        db.close()

@st.cache_resource
def init_db():
    run_migrations()
    return True

def ensure_db_ready():
    """Lightweight check to ensure DB is initialized in session."""
    if "db_verified" not in st.session_state:
        init_db()
        st.session_state.db_verified = True

def get_db():
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
