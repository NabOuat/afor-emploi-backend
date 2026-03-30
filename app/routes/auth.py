from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
from app.database import get_db
from app.models import Users, Acteur
from app.schemas import LoginRequest, TokenResponse
from app.security import verify_password, create_access_token, hash_password, require_admin
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

@router.post("/change-password")
async def change_password(
    data: dict,
    db: Session = Depends(get_db)
):
    username    = data.get("username")
    old_password = data.get("old_password")
    new_password = data.get("new_password")

    if not username or not old_password or not new_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Champs manquants")

    user = db.query(Users).filter(Users.username == username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur introuvable")

    if not verify_password(old_password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Ancien mot de passe incorrect")

    if len(new_password) < 8:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Le mot de passe doit contenir au moins 8 caractères")

    user.password = hash_password(new_password)
    db.commit()
    return {"message": "Mot de passe mis à jour avec succès"}


@router.put("/update-profile")
async def update_profile(
    data: dict,
    db: Session = Depends(get_db)
):
    username = data.get("username")
    if not username:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username requis")

    user = db.query(Users).filter(Users.username == username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur introuvable")

    if "nom" in data:
        user.nom = data["nom"]
    if "prenom" in data:
        user.prenom = data["prenom"]
    if "email" in data:
        user.email = data["email"] or None

    db.commit()
    db.refresh(user)
    return {
        "username": user.username,
        "nom": user.nom,
        "prenom": user.prenom,
        "email": user.email,
        "acteur_id": user.acteur_id,
    }


@router.get("/me/{username}")
async def get_me(username: str, db: Session = Depends(get_db)):
    user = db.query(Users).filter(Users.username == username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur introuvable")
    return {
        "username": user.username,
        "nom": user.nom,
        "prenom": user.prenom,
        "email": user.email,
        "acteur_id": user.acteur_id,
    }


@router.post("/send-test-report")
async def send_test_report(data: dict, db: Session = Depends(get_db)):
    """Envoie immédiatement le rapport à un responsable (test ou envoi manuel)."""
    username = data.get("username")
    if not username:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username requis")

    user = db.query(Users).filter(Users.username == username).first()
    if not user or not user.email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Utilisateur sans email configuré")

    from app.email_service import compute_weekly_stats, build_email_html, send_email
    from datetime import datetime

    stats   = compute_weekly_stats(db)
    name    = f"{user.prenom or ''} {user.nom or ''}".strip() or user.username
    week    = datetime.now().isocalendar()[1]
    year    = datetime.now().year
    subject = f"[AFOR Emploi] Rapport hebdomadaire — Semaine {week} / {year}"
    html    = build_email_html(name, stats)
    ok      = send_email(user.email, name, subject, html)

    if not ok:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Échec de l'envoi — vérifiez la configuration SMTP dans .env")
    return {"message": f"Rapport envoyé à {user.email}"}


@router.get("/users")
async def list_users(db: Session = Depends(get_db), _: Users = Depends(require_admin)):
    """Liste tous les utilisateurs avec leurs infos acteur."""
    users = db.query(Users).all()
    result = []
    for u in users:
        acteur = db.query(Acteur).filter(Acteur.id == u.acteur_id).first()
        result.append({
            "id": u.id,
            "username": u.username,
            "nom": u.nom,
            "prenom": u.prenom,
            "email": u.email,
            "acteur_id": u.acteur_id,
            "acteur_nom": acteur.nom if acteur else None,
            "type_acteur": acteur.type_acteur if acteur else None,
        })
    return result


@router.delete("/users/{user_id}")
async def delete_user(user_id: str, db: Session = Depends(get_db), _: Users = Depends(require_admin)):
    """Supprime un utilisateur."""
    user = db.query(Users).filter(Users.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur introuvable")
    db.delete(user)
    db.commit()
    return {"message": "Utilisateur supprimé"}


@router.post("/users")
async def create_user(data: dict, db: Session = Depends(get_db), _: Users = Depends(require_admin)):
    """Crée un utilisateur depuis l'interface admin."""
    username   = data.get("username")
    password   = data.get("password")
    acteur_id  = data.get("acteur_id")
    nom        = data.get("nom")
    prenom     = data.get("prenom")
    email      = data.get("email")

    if not username or not password or not acteur_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="username, password et acteur_id sont requis")

    if db.query(Users).filter(Users.username == username).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ce nom d'utilisateur existe déjà")

    acteur = db.query(Acteur).filter(Acteur.id == acteur_id).first()
    if not acteur:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Acteur introuvable")

    new_user = Users(
        id=str(uuid.uuid4()),
        username=username,
        password=hash_password(password),
        nom=nom,
        prenom=prenom,
        email=email,
        acteur_id=acteur_id,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {
        "id": new_user.id,
        "username": new_user.username,
        "nom": new_user.nom,
        "prenom": new_user.prenom,
        "email": new_user.email,
        "acteur_id": new_user.acteur_id,
        "acteur_nom": acteur.nom,
        "type_acteur": acteur.type_acteur,
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
