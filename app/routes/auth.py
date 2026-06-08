from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from datetime import timedelta
from app.database import get_db
from app.models import Users, Acteur
from app.schemas import LoginRequest, TokenResponse
from app.security import (
    verify_password, create_access_token, hash_password,
    require_admin, require_admin_or_afor, get_current_user,
)
from app.config import settings
import re
import uuid

router = APIRouter(prefix="/api/auth", tags=["Utilisateurs"])

# ─── Validation ──────────────────────────────────────────────────────────────

_USERNAME_RE = re.compile(r"^[a-zA-Z0-9_.\-]{3,64}$")
_EMAIL_RE    = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _check_password_strength(pwd: str) -> None:
    if len(pwd) < 8:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            "Le mot de passe doit contenir au moins 8 caractères")


def _sanitize_str(value, field: str, max_len: int = 128) -> str:
    """Nettoie et valide une chaîne de caractères."""
    if not isinstance(value, str):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Champ '{field}' invalide")
    v = value.strip()
    if len(v) > max_len:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            f"Champ '{field}' trop long (max {max_len} caractères)")
    return v


# ─── Compteur brute-force en mémoire (simple, sans dépendance externe) ───────
# Pour un déploiement multi-worker, remplacer par Redis + slowapi.

_login_attempts: dict[str, list[float]] = {}
_MAX_ATTEMPTS  = 10   # tentatives max
_WINDOW_SECS   = 60   # sur 60 secondes


def _check_rate_limit(key: str) -> None:
    import time
    now   = time.monotonic()
    times = [t for t in _login_attempts.get(key, []) if now - t < _WINDOW_SECS]
    if len(times) >= _MAX_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Trop de tentatives. Réessayez dans {_WINDOW_SECS} secondes.",
            headers={"Retry-After": str(_WINDOW_SECS)},
        )
    times.append(now)
    _login_attempts[key] = times


def _reset_rate_limit(key: str) -> None:
    _login_attempts.pop(key, None)


# ─── Routes ──────────────────────────────────────────────────────────────────

@router.post("/login", response_model=TokenResponse)
async def login(request: Request, body: LoginRequest, db: Session = Depends(get_db)):
    client_ip = request.client.host if request.client else "unknown"
    _check_rate_limit(client_ip)

    user = db.query(Users).filter(Users.username == body.username).first()

    if not user or not verify_password(body.password, user.password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Identifiants incorrects")

    _reset_rate_limit(client_ip)

    acteur = db.query(Acteur).filter(Acteur.id == user.acteur_id).first()
    if not acteur:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Acteur introuvable")

    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {
        "access_token": access_token,
        "token_type":   "bearer",
        "actor_type":   acteur.type_acteur,
        "username":     user.username,
        "nom":          user.nom,
        "prenom":       user.prenom,
        "acteur_id":    user.acteur_id,
    }


@router.post("/change-password")
async def change_password(
    data: dict,
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    old_password = _sanitize_str(data.get("old_password", ""), "old_password")
    new_password = _sanitize_str(data.get("new_password", ""), "new_password")
    _check_password_strength(new_password)

    if not verify_password(old_password, current_user.password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Ancien mot de passe incorrect")

    current_user.password = hash_password(new_password)
    db.commit()
    return {"message": "Mot de passe mis à jour avec succès"}


@router.put("/update-profile")
async def update_profile(
    data: dict,
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if "nom" in data:
        current_user.nom = _sanitize_str(data["nom"], "nom") or None
    if "prenom" in data:
        current_user.prenom = _sanitize_str(data["prenom"], "prenom") or None
    if "email" in data:
        email = _sanitize_str(data["email"], "email", max_len=256) if data["email"] else None
        if email and not _EMAIL_RE.match(email):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Adresse email invalide")
        current_user.email = email

    db.commit()
    db.refresh(current_user)
    return {
        "username":  current_user.username,
        "nom":       current_user.nom,
        "prenom":    current_user.prenom,
        "email":     current_user.email,
        "acteur_id": current_user.acteur_id,
    }


@router.get("/me/{username}")
async def get_me(
    username: str,
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Un utilisateur ne peut consulter que son propre profil (sauf admin)
    acteur = db.query(Acteur).filter(Acteur.id == current_user.acteur_id).first()
    is_admin = acteur and acteur.type_acteur in ("AD", "AF")
    if not is_admin and current_user.username != username:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Accès interdit")

    user = db.query(Users).filter(Users.username == username).first()
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Utilisateur introuvable")
    return {
        "username":  user.username,
        "nom":       user.nom,
        "prenom":    user.prenom,
        "email":     user.email,
        "acteur_id": user.acteur_id,
    }


@router.post("/send-test-report")
async def send_test_report(
    data: dict,
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    username = _sanitize_str(data.get("username", ""), "username")

    # Seul l'utilisateur lui-même ou un admin peut déclencher le rapport
    acteur = db.query(Acteur).filter(Acteur.id == current_user.acteur_id).first()
    is_admin = acteur and acteur.type_acteur in ("AD", "AF")
    if not is_admin and current_user.username != username:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Accès interdit")

    user = db.query(Users).filter(Users.username == username).first()
    if not user or not user.email:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Utilisateur sans email configuré")

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
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR,
                            "Échec de l'envoi — vérifiez la configuration SMTP dans .env")
    return {"message": f"Rapport envoyé à {user.email}"}


@router.get("/users")
async def list_users(
    db: Session = Depends(get_db),
    _: Users = Depends(require_admin_or_afor),
):
    users = db.query(Users).all()
    result = []
    for u in users:
        acteur = db.query(Acteur).filter(Acteur.id == u.acteur_id).first()
        result.append({
            "id":          u.id,
            "username":    u.username,
            "nom":         u.nom,
            "prenom":      u.prenom,
            "email":       u.email,
            "acteur_id":   u.acteur_id,
            "acteur_nom":  acteur.nom          if acteur else None,
            "type_acteur": acteur.type_acteur  if acteur else None,
        })
    return result


@router.put("/users/{user_id}")
async def update_user(
    user_id: str,
    data: dict,
    db: Session = Depends(get_db),
    _: Users = Depends(require_admin_or_afor),
):
    user = db.query(Users).filter(Users.id == user_id).first()
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Utilisateur introuvable")

    if "nom" in data:
        user.nom = _sanitize_str(data["nom"], "nom") or None
    if "prenom" in data:
        user.prenom = _sanitize_str(data["prenom"], "prenom") or None
    if "email" in data:
        email = _sanitize_str(data["email"], "email", 256) if data["email"] else None
        if email and not _EMAIL_RE.match(email):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Adresse email invalide")
        user.email = email
    if "acteur_id" in data and data["acteur_id"]:
        acteur = db.query(Acteur).filter(Acteur.id == data["acteur_id"]).first()
        if not acteur:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Acteur introuvable")
        user.acteur_id = data["acteur_id"]
    if "new_password" in data and data["new_password"]:
        pwd = _sanitize_str(data["new_password"], "new_password")
        _check_password_strength(pwd)
        user.password = hash_password(pwd)

    db.commit()
    db.refresh(user)
    acteur = db.query(Acteur).filter(Acteur.id == user.acteur_id).first()
    return {
        "id":          user.id,
        "username":    user.username,
        "nom":         user.nom,
        "prenom":      user.prenom,
        "email":       user.email,
        "acteur_id":   user.acteur_id,
        "acteur_nom":  acteur.nom          if acteur else None,
        "type_acteur": acteur.type_acteur  if acteur else None,
    }


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    _: Users = Depends(require_admin),
):
    user = db.query(Users).filter(Users.id == user_id).first()
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Utilisateur introuvable")
    db.delete(user)
    db.commit()
    return {"message": "Utilisateur supprimé"}


@router.post("/users")
async def create_user(
    data: dict,
    db: Session = Depends(get_db),
    _: Users = Depends(require_admin),
):
    username  = _sanitize_str(data.get("username", ""), "username")
    password  = _sanitize_str(data.get("password", ""), "password")
    acteur_id = _sanitize_str(data.get("acteur_id", ""), "acteur_id")
    nom       = _sanitize_str(data.get("nom",    ""), "nom")    or None
    prenom    = _sanitize_str(data.get("prenom", ""), "prenom") or None
    email_raw = (data.get("email") or "").strip() or None

    if not username or not password or not acteur_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            "username, password et acteur_id sont requis")
    if not _USERNAME_RE.match(username):
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            "username invalide (3-64 car., lettres/chiffres/._-)")
    _check_password_strength(password)
    if email_raw and not _EMAIL_RE.match(email_raw):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Adresse email invalide")

    if db.query(Users).filter(Users.username == username).first():
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            "Ce nom d'utilisateur existe déjà")

    acteur = db.query(Acteur).filter(Acteur.id == acteur_id).first()
    if not acteur:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Acteur introuvable")

    new_user = Users(
        id=str(uuid.uuid4()),
        username=username,
        password=hash_password(password),
        nom=nom, prenom=prenom, email=email_raw,
        acteur_id=acteur_id,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {
        "id":          new_user.id,
        "username":    new_user.username,
        "nom":         new_user.nom,
        "prenom":      new_user.prenom,
        "email":       new_user.email,
        "acteur_id":   new_user.acteur_id,
        "acteur_nom":  acteur.nom,
        "type_acteur": acteur.type_acteur,
    }


@router.put("/users/{user_id}/reset-password")
async def admin_reset_password(
    user_id: str,
    data: dict,
    db: Session = Depends(get_db),
    _: Users = Depends(require_admin_or_afor),
):
    new_password = _sanitize_str(data.get("new_password", ""), "new_password")
    _check_password_strength(new_password)

    user = db.query(Users).filter(Users.id == user_id).first()
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Utilisateur introuvable")

    user.password = hash_password(new_password)
    db.commit()
    return {"message": f"Mot de passe de « {user.username} » réinitialisé avec succès"}


@router.post("/register")
async def register(
    request: Request,
    data: dict,
    db: Session = Depends(get_db),
):
    client_ip = request.client.host if request.client else "unknown"
    _check_rate_limit(client_ip)

    username  = _sanitize_str(data.get("username",  ""), "username")
    password  = _sanitize_str(data.get("password",  ""), "password")
    acteur_id = _sanitize_str(data.get("acteur_id", ""), "acteur_id")

    if not username or not password or not acteur_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            "username, password et acteur_id sont requis")
    if not _USERNAME_RE.match(username):
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            "username invalide (3-64 car., lettres/chiffres/._-)")
    _check_password_strength(password)

    if db.query(Users).filter(Users.username == username).first():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Ce nom d'utilisateur existe déjà")

    acteur = db.query(Acteur).filter(Acteur.id == acteur_id).first()
    if not acteur:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Acteur introuvable")

    new_user = Users(
        id=str(uuid.uuid4()),
        username=username,
        password=hash_password(password),
        acteur_id=acteur_id,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"id": new_user.id, "username": new_user.username}
