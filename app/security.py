from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.config import settings
from app.models import Users, Acteur
from app.database import get_db

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    import hashlib
    if not hashed_password:
        return False
    # Vérifier si c'est un hash bcrypt
    if hashed_password.startswith('$2'):
        return pwd_context.verify(plain_password, hashed_password)
    # Vérifier si c'est un hash SHA256 (64 caractères hex)
    elif len(hashed_password) == 64:
        return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password
    # Sinon, comparaison directe (pour les tests)
    else:
        return plain_password == hashed_password

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    credential_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credential_exception
    except JWTError:
        raise credential_exception
    
    user = db.query(Users).filter(Users.username == username).first()
    if user is None:
        raise credential_exception
    return user


async def require_admin(current_user: Users = Depends(get_current_user), db: Session = Depends(get_db)):
    """Vérifie que l'utilisateur connecté est de type AD (Administrateur)."""
    acteur = db.query(Acteur).filter(Acteur.id == current_user.acteur_id).first()
    if not acteur or acteur.type_acteur != "AD":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès réservé aux administrateurs",
        )
    return current_user
