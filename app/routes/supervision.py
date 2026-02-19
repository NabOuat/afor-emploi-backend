from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Supervision, FicPersonne
from app.schemas import Supervision as SupervisionSchema, SupervisionCreate
import uuid

router = APIRouter(prefix="/api/supervisions", tags=["supervisions"])

@router.get("", response_model=List[SupervisionSchema])
async def get_supervisions(fic_personne_id: str = None, db: Session = Depends(get_db)):
    query = db.query(Supervision)
    if fic_personne_id:
        query = query.filter(Supervision.fic_personne_id == fic_personne_id)
    return query.all()

@router.get("/{supervision_id}", response_model=SupervisionSchema)
async def get_supervision(supervision_id: str, db: Session = Depends(get_db)):
    supervision = db.query(Supervision).filter(Supervision.id == supervision_id).first()
    if not supervision:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supervision not found")
    return supervision

@router.post("", response_model=SupervisionSchema)
async def create_supervision(supervision: SupervisionCreate, db: Session = Depends(get_db)):
    personne = db.query(FicPersonne).filter(FicPersonne.id == supervision.fic_personne_id).first()
    if not personne:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Personne not found")
    
    db_supervision = Supervision(
        id=str(uuid.uuid4()),
        fic_personne_id=supervision.fic_personne_id,
        superviseur_id=supervision.superviseur_id,
        date_debut=supervision.date_debut,
        date_fin=supervision.date_fin
    )
    db.add(db_supervision)
    db.commit()
    db.refresh(db_supervision)
    return db_supervision

@router.put("/{supervision_id}", response_model=SupervisionSchema)
async def update_supervision(supervision_id: str, supervision: SupervisionCreate, db: Session = Depends(get_db)):
    db_supervision = db.query(Supervision).filter(Supervision.id == supervision_id).first()
    if not db_supervision:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supervision not found")
    
    personne = db.query(FicPersonne).filter(FicPersonne.id == supervision.fic_personne_id).first()
    if not personne:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Personne not found")
    
    db_supervision.fic_personne_id = supervision.fic_personne_id
    db_supervision.superviseur_id = supervision.superviseur_id
    db_supervision.date_debut = supervision.date_debut
    db_supervision.date_fin = supervision.date_fin
    
    db.commit()
    db.refresh(db_supervision)
    return db_supervision

@router.delete("/{supervision_id}")
async def delete_supervision(supervision_id: str, db: Session = Depends(get_db)):
    db_supervision = db.query(Supervision).filter(Supervision.id == supervision_id).first()
    if not db_supervision:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supervision not found")
    db.delete(db_supervision)
    db.commit()
    return {"message": "Supervision deleted"}
