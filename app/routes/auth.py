from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
from app.database import get_db
from app.models import Users, Acteur
from app.schemas import LoginRequest, TokenResponse
from app.security import verify_password, create_access_token, hash_password
from app.config import settings
import uuid

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(Users).filter(Users.username == request.username).first()
    
    if not user or not verify_password(request.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    acteur = db.query(Acteur).filter(Acteur.id == user.acteur_id).first()
    if not acteur:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Actor not found"
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "actor_type": acteur.type_acteur,
        "username": user.username,
        "nom": user.nom,
        "prenom": user.prenom,
        "acteur_id": user.acteur_id
    }

@router.post("/register")
async def register(username: str, password: str, acteur_id: str, db: Session = Depends(get_db)):
    existing_user = db.query(Users).filter(Users.username == username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    acteur = db.query(Acteur).filter(Acteur.id == acteur_id).first()
    if not acteur:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Acteur not found"
        )
    
    new_user = Users(
        id=str(uuid.uuid4()),
        username=username,
        password=hash_password(password),
        acteur_id=acteur_id
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {"id": new_user.id, "username": new_user.username, "nom": new_user.nom, "prenom": new_user.prenom}
