from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Acteur
from app.schemas import Acteur as ActeurSchema, ActeurCreate
import uuid

router = APIRouter(prefix="/api/acteurs", tags=["acteurs"])

@router.get("", response_model=List[ActeurSchema])
async def get_acteurs(type_acteur: str = None, db: Session = Depends(get_db)):
    query = db.query(Acteur)
    if type_acteur:
        query = query.filter(Acteur.type_acteur == type_acteur)
    return query.all()

@router.get("/{acteur_id}", response_model=ActeurSchema)
async def get_acteur(acteur_id: str, db: Session = Depends(get_db)):
    acteur = db.query(Acteur).filter(Acteur.id == acteur_id).first()
    if not acteur:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Acteur not found")
    return acteur

@router.post("", response_model=ActeurSchema)
async def create_acteur(acteur: ActeurCreate, db: Session = Depends(get_db)):
    db_acteur = Acteur(
        id=str(uuid.uuid4()),
        nom=acteur.nom,
        type_acteur=acteur.type_acteur,
        contact_1=acteur.contact_1,
        contact_2=acteur.contact_2,
        adresse_1=acteur.adresse_1,
        adresse_2=acteur.adresse_2,
        email_1=acteur.email_1,
        email_2=acteur.email_2
    )
    db.add(db_acteur)
    db.commit()
    db.refresh(db_acteur)
    return db_acteur

@router.put("/{acteur_id}", response_model=ActeurSchema)
async def update_acteur(acteur_id: str, acteur: ActeurCreate, db: Session = Depends(get_db)):
    db_acteur = db.query(Acteur).filter(Acteur.id == acteur_id).first()
    if not db_acteur:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Acteur not found")
    
    db_acteur.nom = acteur.nom
    db_acteur.type_acteur = acteur.type_acteur
    db_acteur.contact_1 = acteur.contact_1
    db_acteur.contact_2 = acteur.contact_2
    db_acteur.adresse_1 = acteur.adresse_1
    db_acteur.adresse_2 = acteur.adresse_2
    db_acteur.email_1 = acteur.email_1
    db_acteur.email_2 = acteur.email_2
    
    db.commit()
    db.refresh(db_acteur)
    return db_acteur

@router.delete("/{acteur_id}")
async def delete_acteur(acteur_id: str, db: Session = Depends(get_db)):
    db_acteur = db.query(Acteur).filter(Acteur.id == acteur_id).first()
    if not db_acteur:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Acteur not found")
    db.delete(db_acteur)
    db.commit()
    return {"message": "Acteur deleted"}
