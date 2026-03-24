"""
Audit Log helper — Records key user actions to the database.

Usage:
    from .audit_log import log_action
    log_action(username="ahmed", action="BOQ_SAVE", detail="Project: Villa A")
"""

from database import get_engine, SessionLocal, Base
from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id         = Column(Integer, primary_key=True, index=True)
    username   = Column(String(100), index=True)
    action     = Column(String(100))          # e.g. "LOGIN", "BOQ_SAVE", "PDF_EXPORT"
    detail     = Column(Text, nullable=True)  # Extra context
    created_at = Column(DateTime, default=datetime.utcnow)


def ensure_audit_table():
    """Creates the audit_logs table if it doesn't exist."""
    try:
        from database import get_engine
        engine = get_engine()
        Base.metadata.create_all(bind=engine, tables=[AuditLog.__table__])
    except Exception:
        pass


def log_action(username: str, action: str, detail: str = ""):
    """
    Records an action for the given user.
    Fails silently so it never blocks the main app flow.
    """
    try:
        ensure_audit_table()
        db = SessionLocal()
        entry = AuditLog(username=username, action=action, detail=detail)
        db.add(entry)
        db.commit()
        db.close()
    except Exception:
        pass


def get_recent_logs(username: str = None, limit: int = 50) -> list:
    """Retrieves recent audit log entries (all users or filtered by username)."""
    try:
        ensure_audit_table()
        db = SessionLocal()
        query = db.query(AuditLog).order_by(AuditLog.created_at.desc())
        if username:
            query = query.filter(AuditLog.username == username)
        results = query.limit(limit).all()
        db.close()
        return [
            {
                "time": r.created_at.strftime("%Y-%m-%d %H:%M") if r.created_at else "",
                "user": r.username,
                "action": r.action,
                "detail": r.detail or "",
            }
            for r in results
        ]
    except Exception:
        return []
