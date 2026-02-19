from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import FicPersonne, Acteur, Projet
from app.schemas import FicPersonne as FicPersonneSchema, FicPersonneCreate
import uuid

router = APIRouter(prefix="/api/personnes", tags=["personnes"])

@router.get("", response_model=List[FicPersonneSchema])
async def get_personnes(db: Session = Depends(get_db)):
    return db.query(FicPersonne).all()

@router.get("/{personne_id}", response_model=FicPersonneSchema)
async def get_personne(personne_id: str, db: Session = Depends(get_db)):
    personne = db.query(FicPersonne).filter(FicPersonne.id == personne_id).first()
    if not personne:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Personne not found")
    return personne

@router.post("", response_model=FicPersonneSchema)
async def create_personne(personne: FicPersonneCreate, db: Session = Depends(get_db)):
    db_personne = FicPersonne(
        id=str(uuid.uuid4()),
        nom=personne.nom,
        prenom=personne.prenom,
        date_naissance=personne.date_naissance,
        genre=personne.genre,
        contact=personne.contact
    )
    db.add(db_personne)
    db.commit()
    db.refresh(db_personne)
    return db_personne

@router.put("/{personne_id}", response_model=FicPersonneSchema)
async def update_personne(personne_id: str, personne: FicPersonneCreate, db: Session = Depends(get_db)):
    db_personne = db.query(FicPersonne).filter(FicPersonne.id == personne_id).first()
    if not db_personne:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Personne not found")
    
    db_personne.nom = personne.nom
    db_personne.prenom = personne.prenom
    db_personne.date_naissance = personne.date_naissance
    db_personne.genre = personne.genre
    db_personne.contact = personne.contact
    
    db.commit()
    db.refresh(db_personne)
    return db_personne

@router.delete("/{personne_id}")
async def delete_personne(personne_id: str, db: Session = Depends(get_db)):
    db_personne = db.query(FicPersonne).filter(FicPersonne.id == personne_id).first()
    if not db_personne:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Personne not found")
    db.delete(db_personne)
    db.commit()
    return {"message": "Personne deleted"}
