from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List
from app.database import get_db
from app.models import UserAction, Login
from app.schemas import UserActionCreate, UserActionResponse
from app.security import get_current_user
import uuid

router = APIRouter(prefix="/api/user-actions", tags=["user-actions"])

@router.post("/log", response_model=dict)
async def log_user_action(
    action: UserActionCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """Enregistrer une action utilisateur"""
    try:
        user_action = UserAction(
            id=str(uuid.uuid4()),
            login_id=action.login_id,
            username=action.username,
            acteur_id=action.acteur_id,
            action_type=action.action_type,
            action_description=action.action_description,
            resource_type=action.resource_type,
            resource_id=action.resource_id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            status="success"
        )
        db.add(user_action)
        db.commit()
        db.refresh(user_action)
        return {"id": user_action.id, "status": "logged"}
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": str(e)}

@router.get("/user/{login_id}", response_model=List[UserActionResponse])
async def get_user_actions(
    login_id: str,
    days: int = 7,
    db: Session = Depends(get_db)
):
    """Récupérer les actions d'un utilisateur des N derniers jours"""
    start_date = datetime.utcnow() - timedelta(days=days)
    
    actions = db.query(UserAction).filter(
        UserAction.login_id == login_id,
        UserAction.created_at >= start_date
    ).order_by(UserAction.created_at.desc()).all()
    
    return actions

@router.get("/acteur/{acteur_id}", response_model=List[UserActionResponse])
async def get_acteur_actions(
    acteur_id: str,
    days: int = 7,
    db: Session = Depends(get_db)
):
    """Récupérer toutes les actions d'un acteur des N derniers jours"""
    start_date = datetime.utcnow() - timedelta(days=days)
    
    actions = db.query(UserAction).filter(
        UserAction.acteur_id == acteur_id,
        UserAction.created_at >= start_date
    ).order_by(UserAction.created_at.desc()).all()
    
    return actions

@router.get("/all", response_model=List[UserActionResponse])
async def get_all_actions(
    days: int = 7,
    action_type: str = None,
    db: Session = Depends(get_db)
):
    """Récupérer toutes les actions des N derniers jours"""
    start_date = datetime.utcnow() - timedelta(days=days)
    
    query = db.query(UserAction).filter(
        UserAction.created_at >= start_date
    )
    
    if action_type:
        query = query.filter(UserAction.action_type == action_type)
    
    actions = query.order_by(UserAction.created_at.desc()).all()
    
    return actions

@router.get("/stats/{acteur_id}")
async def get_acteur_stats(
    acteur_id: str,
    db: Session = Depends(get_db)
):
    """Récupérer les statistiques d'activité d'un acteur"""
    today = datetime.utcnow().date()
    
    total_actions = db.query(UserAction).filter(
        UserAction.acteur_id == acteur_id
    ).count()
    
    today_actions = db.query(UserAction).filter(
        UserAction.acteur_id == acteur_id,
        UserAction.created_at >= datetime.combine(today, datetime.min.time())
    ).count()
    
    action_types = db.query(UserAction.action_type, db.func.count(UserAction.id)).filter(
        UserAction.acteur_id == acteur_id
    ).group_by(UserAction.action_type).all()
    
    last_login = db.query(UserAction).filter(
        UserAction.acteur_id == acteur_id,
        UserAction.action_type == "LOGIN"
    ).order_by(UserAction.created_at.desc()).first()
    
    return {
        "total_actions": total_actions,
        "today_actions": today_actions,
        "action_types": {action_type: count for action_type, count in action_types},
        "last_login": last_login.created_at if last_login else None
    }
