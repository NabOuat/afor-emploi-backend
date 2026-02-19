from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Contrat, FicPersonne
from app.schemas import Contrat as ContratSchema, ContratCreate
import uuid

router = APIRouter(prefix="/api/contrats", tags=["contrats"])

@router.get("", response_model=List[ContratSchema])
async def get_contrats(fic_personne_id: str = None, db: Session = Depends(get_db)):
    query = db.query(Contrat)
    if fic_personne_id:
        query = query.filter(Contrat.fic_personne_id == fic_personne_id)
    return query.all()

@router.get("/{contrat_id}", response_model=ContratSchema)
async def get_contrat(contrat_id: str, db: Session = Depends(get_db)):
    contrat = db.query(Contrat).filter(Contrat.id == contrat_id).first()
    if not contrat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contrat not found")
    return contrat

@router.post("", response_model=ContratSchema)
async def create_contrat(contrat: ContratCreate, db: Session = Depends(get_db)):
    personne = db.query(FicPersonne).filter(FicPersonne.id == contrat.fic_personne_id).first()
    if not personne:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Personne not found")
    
    db_contrat = Contrat(
        id=str(uuid.uuid4()),
        fic_personne_id=contrat.fic_personne_id,
        poste_nom=contrat.poste_nom,
        categorie_poste=contrat.categorie_poste,
        type_contrat=contrat.type_contrat,
        type_personne=contrat.type_personne,
        poste=contrat.poste,
        date_debut=contrat.date_debut,
        date_fin=contrat.date_fin,
        diplome=contrat.diplome,
        ecole=contrat.ecole
    )
    db.add(db_contrat)
    db.commit()
    db.refresh(db_contrat)
    return db_contrat

@router.put("/{contrat_id}", response_model=ContratSchema)
async def update_contrat(contrat_id: str, contrat: ContratCreate, projet_id: str = None, engagement_id: str = None, db: Session = Depends(get_db)):
    db_contrat = db.query(Contrat).filter(Contrat.id == contrat_id).first()
    if not db_contrat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contrat not found")
    
    personne = db.query(FicPersonne).filter(FicPersonne.id == contrat.fic_personne_id).first()
    if not personne:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Personne not found")
    
    db_contrat.fic_personne_id = contrat.fic_personne_id
    db_contrat.poste_nom = contrat.poste_nom
    db_contrat.categorie_poste = contrat.categorie_poste
    db_contrat.type_contrat = contrat.type_contrat
    db_contrat.type_personne = contrat.type_personne
    db_contrat.poste = contrat.poste
    db_contrat.date_debut = contrat.date_debut
    db_contrat.date_fin = contrat.date_fin
    db_contrat.diplome = contrat.diplome
    db_contrat.ecole = contrat.ecole
    db_contrat.projet_id = projet_id
    db_contrat.engagement_id = engagement_id
    
    db.commit()
    db.refresh(db_contrat)
    return db_contrat

@router.delete("/{contrat_id}")
async def delete_contrat(contrat_id: str, db: Session = Depends(get_db)):
    db_contrat = db.query(Contrat).filter(Contrat.id == contrat_id).first()
    if not db_contrat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contrat not found")
    db.delete(db_contrat)
    db.commit()
    return {"message": "Contrat deleted"}

@router.post("/renew/{employee_id}")
async def renew_contract(employee_id: str, contrat: ContratCreate, projet_id: str = None, engagement_id: str = None, db: Session = Depends(get_db)):
    """Reconduire le contrat d'un employé en créant un nouveau contrat"""
    
    print(f"DEBUG: Données reçues - contrat: {contrat}")
    print(f"DEBUG: projet_id: {projet_id}, engagement_id: {engagement_id}")
    
    # Vérifier que l'employé existe
    personne = db.query(FicPersonne).filter(FicPersonne.id == employee_id).first()
    if not personne:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employé non trouvé")
    
    # Créer toujours un nouveau contrat lors de la reconduction
    db_contrat = Contrat(
        id=str(uuid.uuid4()),
        fic_personne_id=employee_id,
        poste_nom=contrat.poste_nom,
        categorie_poste=contrat.categorie_poste,
        type_contrat=contrat.type_contrat,
        type_personne=contrat.type_personne,
        poste=contrat.poste,
        date_debut=contrat.date_debut,
        date_fin=contrat.date_fin,
        diplome=contrat.diplome,
        ecole=contrat.ecole,
        projet_id=projet_id,
        engagement_id=engagement_id
    )
    db.add(db_contrat)
    db.commit()
    db.refresh(db_contrat)
    return db_contrat
