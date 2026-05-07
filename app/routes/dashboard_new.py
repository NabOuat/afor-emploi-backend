from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from datetime import datetime, date, timedelta
from app.database import get_db
from app.models import FicPersonne, Contrat, Acteur, Users, ZoneDIntervention, UserAction, FicPersonneLocalisation, Projet, FicPersonneProjet
from app.security import get_current_user

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/operator/contract-types/{acteur_id}")
async def get_contract_types(acteur_id: str, filter_type: str = "all", db: Session = Depends(get_db)):
    """Répartition par type de contrat (categorie_poste)"""
    
    try:
        today = date.today()
        query = db.query(
            Contrat.categorie_poste,
            func.count(FicPersonne.id).label("count")
        ).join(
            FicPersonne, FicPersonne.id == Contrat.fic_personne_id
        ).join(
            FicPersonneProjet, FicPersonneProjet.fic_personne_id == FicPersonne.id
        ).filter(
            FicPersonneProjet.acteur_id == acteur_id
        )
        
        if filter_type == "active":
            query = query.filter(
                Contrat.date_debut <= today,
                or_(Contrat.date_fin >= today, Contrat.date_fin.is_(None))
            )
        
        types = query.group_by(Contrat.categorie_poste).all()
        
        result = []
        total = 0
        for cat_poste, count in types:
            result.append({
                "type": cat_poste or "Non spécifié",
                "count": count
            })
            total += count
        
        for item in result:
            item["percentage"] = round((item["count"] / total * 100)) if total > 0 else 0
        
        return sorted(result, key=lambda x: x["count"], reverse=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/operator/education-level/{acteur_id}")
async def get_education_level(acteur_id: str, filter_type: str = "all", db: Session = Depends(get_db)):
    """Répartition par niveau d'éducation (diplôme)"""
    
    try:
        today = date.today()
        query = db.query(
            Contrat.diplome,
            func.count(FicPersonne.id).label("count")
        ).join(
            FicPersonne, FicPersonne.id == Contrat.fic_personne_id
        ).join(
            FicPersonneProjet, FicPersonneProjet.fic_personne_id == FicPersonne.id
        ).filter(
            FicPersonneProjet.acteur_id == acteur_id
        )
        
        if filter_type == "active":
            query = query.filter(
                Contrat.date_debut <= today,
                or_(Contrat.date_fin >= today, Contrat.date_fin.is_(None))
            )
        
        education = query.group_by(Contrat.diplome).all()
        
        result = []
        total = 0
        for diplome, count in education:
            result.append({
                "level": diplome or "Non spécifié",
                "count": count
            })
            total += count
        
        for item in result:
            item["percentage"] = round((item["count"] / total * 100)) if total > 0 else 0
        
        return sorted(result, key=lambda x: x["count"], reverse=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/operator/contract-renewal-rate/{acteur_id}")
async def get_contract_renewal_rate(acteur_id: str, db: Session = Depends(get_db)):
    """Taux de renouvellement des contrats (contrats expirés vs actifs)"""
    
    try:
        today = date.today()
        
        # Contrats actifs
        active = db.query(func.count(Contrat.id)).join(
            FicPersonne, FicPersonne.id == Contrat.fic_personne_id
        ).join(
            FicPersonneProjet, FicPersonneProjet.fic_personne_id == FicPersonne.id
        ).filter(
            FicPersonneProjet.acteur_id == acteur_id,
            Contrat.date_debut <= today,
            or_(Contrat.date_fin >= today, Contrat.date_fin.is_(None))
        ).scalar() or 0
        
        # Contrats expirés
        expired = db.query(func.count(Contrat.id)).join(
            FicPersonne, FicPersonne.id == Contrat.fic_personne_id
        ).join(
            FicPersonneProjet, FicPersonneProjet.fic_personne_id == FicPersonne.id
        ).filter(
            FicPersonneProjet.acteur_id == acteur_id,
            Contrat.date_fin < today
        ).scalar() or 0
        
        total = active + expired
        renewal_rate = round((active / total * 100)) if total > 0 else 0
        
        return {
            "active": active,
            "expired": expired,
            "total": total,
            "renewal_rate": renewal_rate
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/operator/top-schools/{acteur_id}")
async def get_top_schools(acteur_id: str, filter_type: str = "all", db: Session = Depends(get_db)):
    """Top 5 écoles/formations"""
    
    try:
        today = date.today()
        query = db.query(
            Contrat.ecole,
            func.count(FicPersonne.id).label("count")
        ).join(
            FicPersonne, FicPersonne.id == Contrat.fic_personne_id
        ).join(
            FicPersonneProjet, FicPersonneProjet.fic_personne_id == FicPersonne.id
        ).filter(
            FicPersonneProjet.acteur_id == acteur_id,
            Contrat.ecole.isnot(None)
        )
        
        if filter_type == "active":
            query = query.filter(
                Contrat.date_debut <= today,
                or_(Contrat.date_fin >= today, Contrat.date_fin.is_(None))
            )
        
        schools = query.group_by(Contrat.ecole).order_by(
            func.count(FicPersonne.id).desc()
        ).limit(5).all()
        
        result = []
        for school, count in schools:
            result.append({
                "school": school or "Non spécifié",
                "count": count
            })
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/operator/monthly-hires/{acteur_id}")
async def get_monthly_hires(acteur_id: str, months: int = 12, db: Session = Depends(get_db)):
    """Embauches par mois (derniers N mois)"""
    
    try:
        today = date.today()
        start_date = today - timedelta(days=30 * months)
        
        # Grouper par mois
        hires = db.query(
            func.date_trunc('month', Contrat.date_debut).label('month'),
            func.count(Contrat.id).label('count')
        ).join(
            FicPersonne, FicPersonne.id == Contrat.fic_personne_id
        ).join(
            FicPersonneProjet, FicPersonneProjet.fic_personne_id == FicPersonne.id
        ).filter(
            FicPersonneProjet.acteur_id == acteur_id,
            Contrat.date_debut >= start_date
        ).group_by(
            func.date_trunc('month', Contrat.date_debut)
        ).order_by(
            func.date_trunc('month', Contrat.date_debut)
        ).all()
        
        result = []
        for month, count in hires:
            if month:
                result.append({
                    "month": month.strftime("%Y-%m"),
                    "count": count
                })
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
