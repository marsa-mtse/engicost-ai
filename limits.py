from database import SessionLocal, User
from config import PLANS

def check_limit_reached(username, feature):
    """
    Checks if a user has reached their plan limits for a specific feature.
    feature can be 'blueprints' or 'boqs'
    Returns True if limit reached, False otherwise.
    """
    db = SessionLocal()
    user = db.query(User).filter(User.username == username).first()
    
    if not user:
        db.close()
        return True # Default to blocked if not found
        
    if user.role == 'Admin':
        db.close()
        return False
        
    plan = user.plan
    plan_limits = PLANS.get(plan, PLANS["Free"])
    
    is_limited = False
    
    if feature == 'blueprints':
        max_b = plan_limits["max_blueprints"]
        if max_b != -1 and user.blueprints_analyzed >= max_b:
            is_limited = True
            
    elif feature == 'boqs':
        max_boq = plan_limits["max_boq"]
        if max_boq != -1 and user.boqs_generated >= max_boq:
            is_limited = True
            
    db.close()
    return is_limited

def increment_usage(username, feature):
    """Increments the usage counter for a given feature."""
    db = SessionLocal()
    user = db.query(User).filter(User.username == username).first()
    if user:
        if feature == 'blueprints':
            user.blueprints_analyzed += 1
        elif feature == 'boqs':
            user.boqs_generated += 1
        db.commit()
    db.close()
