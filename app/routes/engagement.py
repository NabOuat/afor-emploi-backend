from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Engagement, ProjetEngagement, Projet

router = APIRouter(prefix="/api/engagements", tags=["engagements"])


@router.get("/project/{projet_id}")
async def get_engagements_by_projet(projet_id: str, db: Session = Depends(get_db)):
    """
    Récupère tous les engagements disponibles pour un projet donné
    """
    try:
        # Vérifier que le projet existe
        projet = db.query(Projet).filter(Projet.id == projet_id).first()
        if not projet:
            raise HTTPException(status_code=404, detail="Projet non trouvé")
        
        # Récupérer les engagements du projet
        projet_engagements = db.query(ProjetEngagement).filter(
            ProjetEngagement.projet_id == projet_id
        ).all()
        
        engagements = []
        for pe in projet_engagements:
            engagement = db.query(Engagement).filter(
                Engagement.id == pe.engagement_id
            ).first()
            if engagement:
                engagements.append({
                    "id": engagement.id,
                    "nom": engagement.nom,
                    "description": engagement.description
                })
        
        return {
            "projet_id": projet_id,
            "projet_nom": projet.nom,
            "engagements": engagements
        }
    
    except Exception as e:
        print(f"Erreur lors de la récupération des engagements: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def get_all_engagements(db: Session = Depends(get_db)):
    """
    Récupère tous les engagements disponibles
    """
    try:
        engagements = db.query(Engagement).all()
        return [
            {
                "id": e.id,
                "nom": e.nom,
                "description": e.description
            }
            for e in engagements
        ]
    except Exception as e:
        print(f"Erreur lors de la récupération des engagements: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/")
async def create_engagement(nom: str, description: str = None, db: Session = Depends(get_db)):
    """
    Crée un nouvel engagement
    """
    try:
        # Vérifier que l'engagement n'existe pas déjà
        existing = db.query(Engagement).filter(Engagement.nom == nom).first()
        if existing:
            raise HTTPException(status_code=400, detail="Cet engagement existe déjà")
        
        import uuid
        engagement = Engagement(
            id=str(uuid.uuid4()),
            nom=nom,
            description=description
        )
        db.add(engagement)
        db.commit()
        db.refresh(engagement)
        
        return {
            "id": engagement.id,
            "nom": engagement.nom,
            "description": engagement.description
        }
    except Exception as e:
        db.rollback()
        print(f"Erreur lors de la création de l'engagement: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
