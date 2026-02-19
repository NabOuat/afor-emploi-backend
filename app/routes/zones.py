from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import ZoneDIntervention, TRegion, TDepartement, TSousPrefecture
from pydantic import BaseModel

router = APIRouter(prefix="/api/zones", tags=["zones"])

class ZoneResponse(BaseModel):
    region_id: str
    region_nom: str
    departement_id: str
    departement_nom: str
    sous_prefecture_id: str
    sous_prefecture_nom: str
    
    class Config:
        from_attributes = True

@router.get("/intervention/projects")
async def get_zones_by_projects(projet_ids: str, acteur_id: str, db: Session = Depends(get_db)):
    """
    Récupérer les zones d'intervention pour une liste de projets d'un acteur
    projet_ids: IDs des projets séparés par des virgules (ex: "HP,PASFOR")
    acteur_id: ID de l'acteur connecté
    """
    try:
        # Séparer les IDs des projets
        projet_list = [p.strip() for p in projet_ids.split(',') if p.strip()]
        
        if not projet_list:
            return {
                "regions": [],
                "departements": [],
                "sous_prefectures": []
            }
        
        # Récupérer toutes les zones d'intervention pour ces projets ET cet acteur
        zones = db.query(ZoneDIntervention).filter(
            ZoneDIntervention.projet_id.in_(projet_list),
            ZoneDIntervention.acteur_id == acteur_id
        ).all()
        
        # Extraire les IDs uniques des régions
        region_ids = set()
        for zone in zones:
            if zone.region_id:
                region_ids.add(zone.region_id)
        
        # Récupérer les détails des régions
        regions = []
        if region_ids:
            regions_data = db.query(TRegion).filter(TRegion.id.in_(region_ids)).all()
            regions = [{"id": r.id, "nom": r.nom} for r in regions_data]
        
        # Récupérer tous les départements de ces régions
        departements = []
        if region_ids:
            dept_data = db.query(TDepartement).filter(TDepartement.region_id.in_(region_ids)).all()
            departements = [{"id": d.id, "nom": d.nom, "region_id": d.region_id} for d in dept_data]
        
        # Récupérer toutes les sous-préfectures de ces départements
        sous_prefectures = []
        if departements:
            dept_ids = [d["id"] for d in departements]
            sp_data = db.query(TSousPrefecture).filter(TSousPrefecture.departement_id.in_(dept_ids)).all()
            sous_prefectures = [{"id": sp.id, "nom": sp.nom, "departement_id": sp.departement_id} for sp in sp_data]
        
        return {
            "regions": sorted(regions, key=lambda x: x["nom"]),
            "departements": sorted(departements, key=lambda x: x["nom"]),
            "sous_prefectures": sorted(sous_prefectures, key=lambda x: x["nom"])
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
