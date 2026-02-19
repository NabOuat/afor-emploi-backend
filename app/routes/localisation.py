from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import FicPersonneLocalisation, Contrat
from app.schemas import FicPersonneLocalisation as FicPersonneLocalisationSchema, FicPersonneLocalisationCreate
import uuid

router = APIRouter(prefix="/api/localisations", tags=["localisations"])

@router.get("", response_model=List[FicPersonneLocalisationSchema])
async def get_localisations(contrat_id: str = None, db: Session = Depends(get_db)):
    query = db.query(FicPersonneLocalisation)
    if contrat_id:
        query = query.filter(FicPersonneLocalisation.contrat_id == contrat_id)
    return query.all()

@router.get("/{localisation_id}", response_model=FicPersonneLocalisationSchema)
async def get_localisation(localisation_id: str, db: Session = Depends(get_db)):
    localisation = db.query(FicPersonneLocalisation).filter(FicPersonneLocalisation.id == localisation_id).first()
    if not localisation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Localisation not found")
    return localisation

@router.post("", response_model=FicPersonneLocalisationSchema)
async def create_localisation(localisation: FicPersonneLocalisationCreate, db: Session = Depends(get_db)):
    contrat = db.query(Contrat).filter(Contrat.id == localisation.contrat_id).first()
    if not contrat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contrat not found")
    
    db_localisation = FicPersonneLocalisation(
        id=str(uuid.uuid4()),
        contrat_id=localisation.contrat_id,
        region_id=localisation.region_id,
        departement_id=localisation.departement_id,
        sous_prefecture_id=localisation.sous_prefecture_id,
        date_debut=localisation.date_debut
    )
    db.add(db_localisation)
    db.commit()
    db.refresh(db_localisation)
    return db_localisation

@router.put("/{localisation_id}", response_model=FicPersonneLocalisationSchema)
async def update_localisation(localisation_id: str, localisation: FicPersonneLocalisationCreate, db: Session = Depends(get_db)):
    db_localisation = db.query(FicPersonneLocalisation).filter(FicPersonneLocalisation.id == localisation_id).first()
    if not db_localisation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Localisation not found")
    
    contrat = db.query(Contrat).filter(Contrat.id == localisation.contrat_id).first()
    if not contrat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contrat not found")
    
    db_localisation.contrat_id = localisation.contrat_id
    db_localisation.region_id = localisation.region_id
    db_localisation.departement_id = localisation.departement_id
    db_localisation.sous_prefecture_id = localisation.sous_prefecture_id
    db_localisation.date_debut = localisation.date_debut
    
    db.commit()
    db.refresh(db_localisation)
    return db_localisation

@router.delete("/{localisation_id}")
async def delete_localisation(localisation_id: str, db: Session = Depends(get_db)):
    db_localisation = db.query(FicPersonneLocalisation).filter(FicPersonneLocalisation.id == localisation_id).first()
    if not db_localisation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Localisation not found")
    db.delete(db_localisation)
    db.commit()
    return {"message": "Localisation deleted"}

@router.post("/change/{employee_id}")
async def change_employee_location(employee_id: str, localisation: FicPersonneLocalisationCreate, db: Session = Depends(get_db)):
    """Changer la localisation d'un employé en créant une nouvelle entrée"""
    from app.models import FicPersonne
    
    # Vérifier que l'employé existe
    employee = db.query(FicPersonne).filter(FicPersonne.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employé non trouvé")
    
    # Vérifier que le contrat existe
    contrat = db.query(Contrat).filter(Contrat.id == localisation.contrat_id).first()
    if not contrat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contrat non trouvé")
    
    # Créer une nouvelle localisation
    db_localisation = FicPersonneLocalisation(
        id=str(uuid.uuid4()),
        contrat_id=localisation.contrat_id,
        region_id=localisation.region_id,
        departement_id=localisation.departement_id,
        sous_prefecture_id=localisation.sous_prefecture_id,
        date_debut=localisation.date_debut
    )
    db.add(db_localisation)
    db.commit()
    db.refresh(db_localisation)
    return db_localisation
