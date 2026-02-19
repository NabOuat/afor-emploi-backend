from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Projet
from app.schemas import Projet as ProjetSchema, ProjetCreate
import uuid

router = APIRouter(prefix="/api/projets", tags=["projets"])

@router.get("", response_model=List[ProjetSchema])
async def get_projets(db: Session = Depends(get_db)):
    return db.query(Projet).all()

@router.get("/{projet_id}", response_model=ProjetSchema)
async def get_projet(projet_id: str, db: Session = Depends(get_db)):
    projet = db.query(Projet).filter(Projet.id == projet_id).first()
    if not projet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Projet not found")
    return projet

@router.post("", response_model=ProjetSchema)
async def create_projet(projet: ProjetCreate, db: Session = Depends(get_db)):
    db_projet = Projet(
        id=str(uuid.uuid4()),
        nom=projet.nom,
        nom_complet=projet.nom_complet
    )
    db.add(db_projet)
    db.commit()
    db.refresh(db_projet)
    return db_projet

@router.put("/{projet_id}", response_model=ProjetSchema)
async def update_projet(projet_id: str, projet: ProjetCreate, db: Session = Depends(get_db)):
    db_projet = db.query(Projet).filter(Projet.id == projet_id).first()
    if not db_projet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Projet not found")
    
    db_projet.nom = projet.nom
    db_projet.nom_complet = projet.nom_complet
    
    db.commit()
    db.refresh(db_projet)
    return db_projet

@router.delete("/{projet_id}")
async def delete_projet(projet_id: str, db: Session = Depends(get_db)):
    db_projet = db.query(Projet).filter(Projet.id == projet_id).first()
    if not db_projet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Projet not found")
    db.delete(db_projet)
    db.commit()
    return {"message": "Projet deleted"}
