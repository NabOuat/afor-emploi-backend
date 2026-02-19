# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Projet, Engagement, ProjetEngagement
import uuid
from datetime import datetime

router = APIRouter(prefix="/api/engagements", tags=["engagements-liaison"])


@router.post("/link-project")
async def link_engagement_to_project(projet_id: str, engagement_id: str, db: Session = Depends(get_db)):
    """Lier un engagement à un projet"""
    
    try:
        # Vérifier que le projet existe
        projet = db.query(Projet).filter(Projet.id == projet_id).first()
        if not projet:
            raise HTTPException(status_code=404, detail="Projet non trouvé")
        
        # Vérifier que l'engagement existe
        engagement = db.query(Engagement).filter(Engagement.id == engagement_id).first()
        if not engagement:
            raise HTTPException(status_code=404, detail="Engagement non trouvé")
        
        # Vérifier que la liaison n'existe pas déjà
        existing = db.query(ProjetEngagement).filter(
            ProjetEngagement.projet_id == projet_id,
            ProjetEngagement.engagement_id == engagement_id
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="Cette liaison existe déjà")
        
        # Créer la liaison
        liaison = ProjetEngagement(
            id=str(uuid.uuid4()),
            projet_id=projet_id,
            engagement_id=engagement_id
        )
        db.add(liaison)
        db.commit()
        db.refresh(liaison)
        
        return {
            "message": "Liaison créée avec succès",
            "projet_id": projet_id,
            "engagement_id": engagement_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/unlink-project")
async def unlink_engagement_from_project(projet_id: str, engagement_id: str, db: Session = Depends(get_db)):
    """Délier un engagement d'un projet"""
    
    try:
        # Trouver et supprimer la liaison
        liaison = db.query(ProjetEngagement).filter(
            ProjetEngagement.projet_id == projet_id,
            ProjetEngagement.engagement_id == engagement_id
        ).first()
        
        if not liaison:
            raise HTTPException(status_code=404, detail="Liaison non trouvée")
        
        db.delete(liaison)
        db.commit()
        
        return {"message": "Liaison supprimée avec succès"}
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/liaisons")
async def get_all_liaisons(db: Session = Depends(get_db)):
    """Récupérer toutes les liaisons engagement-projet"""
    
    try:
        liaisons = db.query(ProjetEngagement).all()
        
        result = []
        for liaison in liaisons:
            projet = db.query(Projet).filter(Projet.id == liaison.projet_id).first()
            engagement = db.query(Engagement).filter(Engagement.id == liaison.engagement_id).first()
            
            result.append({
                "id": liaison.id,
                "projet_id": liaison.projet_id,
                "projet_nom": projet.nom if projet else "",
                "engagement_id": liaison.engagement_id,
                "engagement_nom": engagement.nom if engagement else "",
                "date_creation": str(liaison.date_creation)
            })
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
