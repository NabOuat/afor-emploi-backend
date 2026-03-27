from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import ZoneDIntervention, Acteur, Projet, TRegion
from app.schemas import ZoneDIntervention as ZoneDInterventionSchema, ZoneDInterventionCreate
import uuid

router = APIRouter(prefix="/api/zones-intervention", tags=["zones-intervention"])

@router.get("/full")
async def get_zones_full(acteur_id: str = None, projet_id: str = None, db: Session = Depends(get_db)):
    """Zones d'intervention avec noms des acteurs, projets et régions."""
    query = db.query(ZoneDIntervention)
    if acteur_id:
        query = query.filter(ZoneDIntervention.acteur_id == acteur_id)
    if projet_id:
        query = query.filter(ZoneDIntervention.projet_id == projet_id)
    result = []
    for z in query.all():
        acteur = db.query(Acteur).filter(Acteur.id == z.acteur_id).first()
        projet = db.query(Projet).filter(Projet.id == z.projet_id).first()
        region = db.query(TRegion).filter(TRegion.id == z.region_id).first() if z.region_id else None
        result.append({
            "id": z.id,
            "acteur_id": z.acteur_id,
            "acteur_nom": acteur.nom if acteur else None,
            "type_acteur": acteur.type_acteur if acteur else None,
            "projet_id": z.projet_id,
            "projet_nom": projet.nom if projet else None,
            "region_id": z.region_id,
            "region_nom": region.nom if region else None,
        })
    return result

@router.get("", response_model=List[ZoneDInterventionSchema])
async def get_zones(acteur_id: str = None, projet_id: str = None, db: Session = Depends(get_db)):
    query = db.query(ZoneDIntervention)
    if acteur_id:
        query = query.filter(ZoneDIntervention.acteur_id == acteur_id)
    if projet_id:
        query = query.filter(ZoneDIntervention.projet_id == projet_id)
    return query.all()

@router.get("/{zone_id}", response_model=ZoneDInterventionSchema)
async def get_zone(zone_id: str, db: Session = Depends(get_db)):
    zone = db.query(ZoneDIntervention).filter(ZoneDIntervention.id == zone_id).first()
    if not zone:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Zone not found")
    return zone

@router.post("", response_model=ZoneDInterventionSchema)
async def create_zone(zone: ZoneDInterventionCreate, db: Session = Depends(get_db)):
    acteur = db.query(Acteur).filter(Acteur.id == zone.acteur_id).first()
    if not acteur:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Acteur not found")
    
    projet = db.query(Projet).filter(Projet.id == zone.projet_id).first()
    if not projet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Projet not found")
    
    db_zone = ZoneDIntervention(
        id=str(uuid.uuid4()),
        acteur_id=zone.acteur_id,
        projet_id=zone.projet_id,
        region_id=zone.region_id
    )
    db.add(db_zone)
    db.commit()
    db.refresh(db_zone)
    return db_zone

@router.put("/{zone_id}", response_model=ZoneDInterventionSchema)
async def update_zone(zone_id: str, zone: ZoneDInterventionCreate, db: Session = Depends(get_db)):
    db_zone = db.query(ZoneDIntervention).filter(ZoneDIntervention.id == zone_id).first()
    if not db_zone:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Zone not found")
    
    acteur = db.query(Acteur).filter(Acteur.id == zone.acteur_id).first()
    if not acteur:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Acteur not found")
    
    projet = db.query(Projet).filter(Projet.id == zone.projet_id).first()
    if not projet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Projet not found")
    
    db_zone.acteur_id = zone.acteur_id
    db_zone.projet_id = zone.projet_id
    db_zone.region_id = zone.region_id
    
    db.commit()
    db.refresh(db_zone)
    return db_zone

@router.delete("/{zone_id}")
async def delete_zone(zone_id: str, db: Session = Depends(get_db)):
    db_zone = db.query(ZoneDIntervention).filter(ZoneDIntervention.id == zone_id).first()
    if not db_zone:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Zone not found")
    db.delete(db_zone)
    db.commit()
    return {"message": "Zone deleted"}
