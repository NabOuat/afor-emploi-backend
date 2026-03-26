# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from datetime import date, timedelta
import time
import threading
from typing import Any, Dict, Optional, Tuple
from app.database import get_db
from app.models import FicPersonne, Contrat, Acteur, Login, ZoneDIntervention, UserAction, FicPersonneLocalisation, Projet, FicPersonneProjet, TRegion, TDepartement
from app.security import get_current_user

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

# ── Cache mémoire backend (TTL 5 min) ──────────────────────────────────────
# Évite de retaper Supabase pour chaque visite du dashboard.
_CACHE_TTL = 300  # secondes
_cache: Dict[str, Tuple[Any, float]] = {}
_cache_lock = threading.Lock()

def _cache_get(key: str) -> Optional[Any]:
    with _cache_lock:
        entry = _cache.get(key)
    if entry and time.time() - entry[1] < _CACHE_TTL:
        return entry[0]
    return None

def _cache_set(key: str, value: Any) -> None:
    with _cache_lock:
        _cache[key] = (value, time.time())

def _cache_invalidate(acteur_id: str) -> None:
    """Vide le cache pour un acteur donné (après import de données)."""
    prefix = f"op_all_{acteur_id}_"
    with _cache_lock:
        for k in [k for k in _cache if k.startswith(prefix)]:
            del _cache[k]

@router.get("/operator/stats/{acteur_id}")
async def get_operator_stats(acteur_id: str, filter_type: str = "all", db: Session = Depends(get_db)):
    """Récupérer les statistiques du dashboard opérateur
    
    filter_type: 'all' pour tous les employés, 'active' pour employés actifs uniquement
    acteur_id: ID de l'opérateur ou 'global' pour les données agrégées
    """
    
    try:
        today = date.today()
        
        # Construire le filtre acteur_id
        if acteur_id == "global":
            acteur_filter = None  # Pas de filtre, récupérer tous
        else:
            acteur_filter = acteur_id
        
        # Déterminer le filtre à appliquer
        # Récupérer les employés via fic_personne_projet (nouvelle structure many-to-many)
        if filter_type == "active":
            # Filtrer seulement les employés avec contrats actifs
            query = db.query(FicPersonne.id).join(
                FicPersonneProjet, FicPersonne.id == FicPersonneProjet.fic_personne_id
            ).join(
                Contrat, FicPersonne.id == Contrat.fic_personne_id
            ).filter(
                Contrat.date_debut <= today,
                or_(Contrat.date_fin >= today, Contrat.date_fin.is_(None))
            )
            if acteur_filter:
                query = query.filter(FicPersonneProjet.acteur_id == acteur_filter)
            employee_ids = query.distinct().all()
            employee_ids = [e[0] for e in employee_ids]
        else:
            # Tous les employés
            query = db.query(FicPersonne.id).join(
                FicPersonneProjet, FicPersonne.id == FicPersonneProjet.fic_personne_id
            )
            if acteur_filter:
                query = query.filter(FicPersonneProjet.acteur_id == acteur_filter)
            employee_ids = query.distinct().all()
            employee_ids = [e[0] for e in employee_ids]
        
        # 1. Nombre total d'employés
        total_employees = len(employee_ids)
        
        # 2. Nombre d'employés avec contrat actif
        query = db.query(func.count(FicPersonne.id)).join(
            FicPersonneProjet, FicPersonne.id == FicPersonneProjet.fic_personne_id
        ).join(
            Contrat, FicPersonne.id == Contrat.fic_personne_id
        ).filter(
            Contrat.date_debut <= today,
            or_(Contrat.date_fin >= today, Contrat.date_fin.is_(None))
        )
        if acteur_filter:
            query = query.filter(FicPersonneProjet.acteur_id == acteur_filter)
        active_contracts = query.scalar() or 0
        
        # 3. Nombre d'employés de plus de 25 ans (via fic_personne_localisation)
        if filter_type == "active":
            # Employés actifs avec date de naissance
            query = db.query(FicPersonne).join(
                FicPersonneProjet, FicPersonne.id == FicPersonneProjet.fic_personne_id
            ).join(
                Contrat, FicPersonne.id == Contrat.fic_personne_id
            ).join(
                FicPersonneLocalisation, Contrat.id == FicPersonneLocalisation.contrat_id
            ).filter(
                FicPersonne.date_naissance.isnot(None),
                Contrat.date_debut <= today,
                or_(Contrat.date_fin >= today, Contrat.date_fin.is_(None))
            )
            if acteur_filter:
                query = query.filter(FicPersonneProjet.acteur_id == acteur_filter)
            employees_with_birth = query.distinct().all()
        else:
            # Tous les employés avec date de naissance
            query = db.query(FicPersonne).join(
                FicPersonneProjet, FicPersonne.id == FicPersonneProjet.fic_personne_id
            ).join(
                Contrat, FicPersonne.id == Contrat.fic_personne_id
            ).join(
                FicPersonneLocalisation, Contrat.id == FicPersonneLocalisation.contrat_id
            ).filter(
                FicPersonne.date_naissance.isnot(None)
            )
            if acteur_filter:
                query = query.filter(FicPersonneProjet.acteur_id == acteur_filter)
            employees_with_birth = query.distinct().all()
        
        young_count = 0
        for emp in employees_with_birth:
            if emp.date_naissance:
                age = (today - emp.date_naissance).days // 365
                if age > 25:
                    young_count += 1
        
        # 4. Dernière connexion
        query = db.query(UserAction).filter(
            UserAction.action_type == "LOGIN"
        )
        if acteur_filter:
            query = query.filter(UserAction.acteur_id == acteur_filter)
        last_login = query.order_by(UserAction.created_at.desc()).first()
        
        last_login_date = last_login.created_at if last_login else None
        
        return {
            "total_employees": total_employees,
            "active_contracts": active_contracts,
            "young_employees_over_25": young_count,
            "last_login": last_login_date
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/operator/employees-progression/{acteur_id}")
async def get_employees_progression(acteur_id: str, months: int = 6, db: Session = Depends(get_db)):
    """Progression des employés par mois"""
    
    try:
        progression = []
        today = date.today()
        
        for i in range(months, -1, -1):
            month_start = today.replace(day=1) - timedelta(days=30*i)
            month_end = month_start.replace(day=28) + timedelta(days=4)
            month_end = month_end.replace(day=1) - timedelta(days=1)
            
            count = db.query(func.count(FicPersonne.id)).join(
                FicPersonneProjet, FicPersonne.id == FicPersonneProjet.fic_personne_id
            ).filter(
                FicPersonneProjet.acteur_id == acteur_id
            ).scalar() or 0
            
            progression.append({
                "month": month_start.strftime("%B %Y"),
                "count": count,
                "date": month_start.isoformat()
            })
        
        return progression
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/operator/employees-by-zone/{acteur_id}")
async def get_employees_by_zone(acteur_id: str, filter_type: str = "all", db: Session = Depends(get_db)):
    """Nombre d'employés par zone d'intervention via fic_personne_localisation"""
    
    try:
        today = date.today()
        
        # Récupérer les zones avec le nombre d'employés
        query = db.query(
            FicPersonneLocalisation.region_id,
            FicPersonneLocalisation.departement_id,
            func.count(FicPersonne.id).label("count")
        ).join(
            Contrat, Contrat.id == FicPersonneLocalisation.contrat_id
        ).join(
            FicPersonne, FicPersonne.id == Contrat.fic_personne_id
        ).join(
            FicPersonneProjet, FicPersonne.id == FicPersonneProjet.fic_personne_id
        ).filter(
            FicPersonneProjet.acteur_id == acteur_id
        )
        
        if filter_type == "active":
            query = query.filter(
                Contrat.date_debut <= today,
                or_(Contrat.date_fin >= today, Contrat.date_fin.is_(None))
            )
        
        zones_data = query.group_by(
            FicPersonneLocalisation.region_id,
            FicPersonneLocalisation.departement_id
        ).all()
        
        result = []
        for region_id, dept_id, count in zones_data:
            if count > 0:
                region_name = "N/A"
                dept_name = "N/A"

                if region_id:
                    region_obj = db.query(TRegion).filter(TRegion.id == region_id).first()
                    if region_obj:
                        region_name = region_obj.nom

                if dept_id:
                    dept_obj = db.query(TDepartement).filter(TDepartement.id == dept_id).first()
                    if dept_obj:
                        dept_name = dept_obj.nom

                result.append({
                    "region": region_name,
                    "departement": dept_name,
                    "count": count
                })
        
        return sorted(result, key=lambda x: x["count"], reverse=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/operator/employees-by-position/{acteur_id}")
async def get_employees_by_position(acteur_id: str, filter_type: str = "all", db: Session = Depends(get_db)):
    """Nombre d'employés par poste"""
    
    try:
        today = date.today()
        query = db.query(
            Contrat.poste_nom,
            func.count(FicPersonne.id).label("count")
        ).join(
            FicPersonne, FicPersonne.id == Contrat.fic_personne_id
        ).join(
            FicPersonneProjet, FicPersonne.id == FicPersonneProjet.fic_personne_id
        ).filter(
            FicPersonneProjet.acteur_id == acteur_id
        )
        
        if filter_type == "active":
            query = query.filter(
                Contrat.date_debut <= today,
                or_(Contrat.date_fin >= today, Contrat.date_fin.is_(None))
            )
        
        positions = query.group_by(Contrat.poste_nom).all()
        
        result = []
        for poste_nom, count in positions:
            result.append({
                "position": poste_nom or "Non spécifié",
                "count": count
            })
        
        return sorted(result, key=lambda x: x["count"], reverse=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/operator/average-contract-duration/{acteur_id}")
async def get_average_contract_duration(acteur_id: str, filter_type: str = "all", db: Session = Depends(get_db)):
    """Durée moyenne des contrats"""
    
    try:
        today = date.today()
        query = db.query(Contrat).join(
            FicPersonne, FicPersonne.id == Contrat.fic_personne_id
        ).join(
            FicPersonneProjet, FicPersonne.id == FicPersonneProjet.fic_personne_id
        ).filter(
            FicPersonneProjet.acteur_id == acteur_id,
            Contrat.date_debut.isnot(None)
        )
        
        if filter_type == "active":
            query = query.filter(
                Contrat.date_debut <= today,
                or_(Contrat.date_fin >= today, Contrat.date_fin.is_(None))
            )
        
        contracts = query.all()
        
        if not contracts:
            return {"average_days": 0, "average_months": 0}
        
        total_days = 0
        count = 0
        
        for contract in contracts:
            if contract.date_fin:
                duration = (contract.date_fin - contract.date_debut).days
            else:
                duration = (date.today() - contract.date_debut).days
            
            total_days += duration
            count += 1
        
        average_days = total_days // count if count > 0 else 0
        average_months = average_days // 30
        
        return {
            "average_days": average_days,
            "average_months": average_months,
            "total_contracts": count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/operator/contract-status/{acteur_id}")
async def get_contract_status(acteur_id: str, filter_type: str = "all", db: Session = Depends(get_db)):
    """Statut des contrats (actifs, terminés, à venir)"""
    
    try:
        today = date.today()
        
        if filter_type == "active":
            # Pour le filtre actif, on compte seulement les contrats actifs
            active = db.query(func.count(FicPersonne.id)).join(
                Contrat, FicPersonne.id == Contrat.fic_personne_id
            ).join(
                FicPersonneProjet, FicPersonne.id == FicPersonneProjet.fic_personne_id
            ).filter(
                FicPersonneProjet.acteur_id == acteur_id,
                Contrat.date_debut <= today,
                or_(Contrat.date_fin >= today, Contrat.date_fin.is_(None))
            ).scalar() or 0
            completed = 0
            upcoming = 0
        else:
            # Pour tous les employés
            active = db.query(func.count(FicPersonne.id)).join(
                Contrat, FicPersonne.id == Contrat.fic_personne_id
            ).join(
                FicPersonneProjet, FicPersonne.id == FicPersonneProjet.fic_personne_id
            ).filter(
                FicPersonneProjet.acteur_id == acteur_id,
                Contrat.date_debut <= today,
                or_(Contrat.date_fin >= today, Contrat.date_fin.is_(None))
            ).scalar() or 0
            
            completed = db.query(func.count(FicPersonne.id)).join(
                Contrat, FicPersonne.id == Contrat.fic_personne_id
            ).join(
                FicPersonneProjet, FicPersonne.id == FicPersonneProjet.fic_personne_id
            ).filter(
                FicPersonneProjet.acteur_id == acteur_id,
                Contrat.date_fin < today
            ).scalar() or 0
            
            upcoming = db.query(func.count(FicPersonne.id)).join(
                Contrat, FicPersonne.id == Contrat.fic_personne_id
            ).join(
                FicPersonneProjet, FicPersonne.id == FicPersonneProjet.fic_personne_id
            ).filter(
                FicPersonneProjet.acteur_id == acteur_id,
                Contrat.date_debut > today
            ).scalar() or 0
        
        return {
            "active": active,
            "completed": completed,
            "upcoming": upcoming
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/operator/employees-by-project/{acteur_id}")
async def get_employees_by_project(acteur_id: str, filter_type: str = "all", db: Session = Depends(get_db)):
    """Nombre d'employés par projet"""
    
    try:
        today = date.today()
        query = db.query(
            Projet.id,
            Projet.nom,
            func.count(FicPersonne.id).label("count")
        ).join(
            FicPersonneProjet, Projet.id == FicPersonneProjet.projet_id
        ).join(
            FicPersonne, FicPersonne.id == FicPersonneProjet.fic_personne_id
        ).filter(
            FicPersonneProjet.acteur_id == acteur_id
        )
        
        if filter_type == "active":
            query = query.join(
                Contrat, FicPersonne.id == Contrat.fic_personne_id
            ).filter(
                Contrat.date_debut <= today,
                or_(Contrat.date_fin >= today, Contrat.date_fin.is_(None))
            )
        
        projects = query.group_by(Projet.id, Projet.nom).all()
        
        result = []
        for projet_id, projet_nom, count in projects:
            if count > 0:
                result.append({
                    "project_id": projet_id,
                    "project_name": projet_nom or "Non spécifié",
                    "count": count
                })
        
        return sorted(result, key=lambda x: x["count"], reverse=True)
    except Exception as e:
        print(f"Error in get_employees_by_project: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/operator/employees-by-gender/{acteur_id}")
async def get_employees_by_gender(acteur_id: str, filter_type: str = "all", db: Session = Depends(get_db)):
    """Répartition des employés par genre"""
    
    try:
        today = date.today()
        query = db.query(
            FicPersonne.genre,
            func.count(FicPersonne.id).label("count")
        ).join(
            FicPersonneProjet, FicPersonne.id == FicPersonneProjet.fic_personne_id
        ).filter(
            FicPersonneProjet.acteur_id == acteur_id
        )
        
        if filter_type == "active":
            query = query.join(
                Contrat, FicPersonne.id == Contrat.fic_personne_id
            ).filter(
                Contrat.date_debut <= today,
                or_(Contrat.date_fin >= today, Contrat.date_fin.is_(None))
            )
        
        genders = query.group_by(FicPersonne.genre).all()
        
        result = []
        total = 0
        for gender, count in genders:
            result.append({
                "gender": gender or "Non spécifié",
                "count": count
            })
            total += count
        
        # Ajouter les pourcentages
        for item in result:
            item["percentage"] = round((item["count"] / total * 100)) if total > 0 else 0
        
        return sorted(result, key=lambda x: x["count"], reverse=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/operator/age-statistics/{acteur_id}")
async def get_age_statistics(acteur_id: str, filter_type: str = "all", db: Session = Depends(get_db)):
    """Statistiques d'âge des employés"""
    
    try:
        today = date.today()
        query = db.query(FicPersonne).join(
            FicPersonneProjet, FicPersonne.id == FicPersonneProjet.fic_personne_id
        ).filter(
            FicPersonneProjet.acteur_id == acteur_id,
            FicPersonne.date_naissance.isnot(None)
        )
        
        if filter_type == "active":
            # Employés actifs avec date de naissance
            query = query.join(
                Contrat, FicPersonne.id == Contrat.fic_personne_id
            ).filter(
                Contrat.date_debut <= today,
                or_(Contrat.date_fin >= today, Contrat.date_fin.is_(None))
            ).distinct()
        
        employees = query.all()
        
        if not employees:
            return {
                "average_age": 0,
                "min_age": 0,
                "max_age": 0,
                "age_groups": {}
            }
        
        today = date.today()
        ages = []
        age_groups = {"18-25": 0, "26-35": 0, "36-45": 0, "46-55": 0, "56+": 0}
        
        for emp in employees:
            if emp.date_naissance:
                age = (today - emp.date_naissance).days // 365
                ages.append(age)
                
                if age <= 25:
                    age_groups["18-25"] += 1
                elif age <= 35:
                    age_groups["26-35"] += 1
                elif age <= 45:
                    age_groups["36-45"] += 1
                elif age <= 55:
                    age_groups["46-55"] += 1
                else:
                    age_groups["56+"] += 1
        
        return {
            "average_age": round(sum(ages) / len(ages)) if ages else 0,
            "min_age": min(ages) if ages else 0,
            "max_age": max(ages) if ages else 0,
            "age_groups": age_groups
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/operator/contract-types/{acteur_id}")
async def get_contract_types(acteur_id: str, filter_type: str = "all", db: Session = Depends(get_db)):
    """Répartition par type de contrat (type_contrat)"""
    
    try:
        today = date.today()
        
        # Construire le filtre acteur_id
        if acteur_id == "global":
            acteur_filter = None
        else:
            acteur_filter = acteur_id
        
        query = db.query(
            Contrat.type_contrat,
            func.count(FicPersonne.id).label("count")
        ).join(
            FicPersonne, FicPersonne.id == Contrat.fic_personne_id
        ).join(
            FicPersonneProjet, FicPersonne.id == FicPersonneProjet.fic_personne_id
        )
        
        if acteur_filter:
            query = query.filter(FicPersonneProjet.acteur_id == acteur_filter)
        
        if filter_type == "active":
            query = query.filter(
                Contrat.date_debut <= today,
                or_(Contrat.date_fin >= today, Contrat.date_fin.is_(None))
            )
        
        types = query.group_by(Contrat.type_contrat).all()
        
        result = []
        total = 0
        for type_contrat, count in types:
            # Normaliser l'encodage UTF-8
            type_str = str(type_contrat or "Non spécifié")
            if isinstance(type_str, bytes):
                type_str = type_str.decode('utf-8')
            
            result.append({
                "type": type_str,
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
            FicPersonneProjet, FicPersonne.id == FicPersonneProjet.fic_personne_id
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
        
        active = db.query(func.count(Contrat.id)).join(
            FicPersonne, FicPersonne.id == Contrat.fic_personne_id
        ).join(
            FicPersonneProjet, FicPersonne.id == FicPersonneProjet.fic_personne_id
        ).filter(
            FicPersonneProjet.acteur_id == acteur_id,
            Contrat.date_debut <= today,
            or_(Contrat.date_fin >= today, Contrat.date_fin.is_(None))
        ).scalar() or 0
        
        expired = db.query(func.count(Contrat.id)).join(
            FicPersonne, FicPersonne.id == Contrat.fic_personne_id
        ).join(
            FicPersonneProjet, FicPersonne.id == FicPersonneProjet.fic_personne_id
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
        
        # Construire le filtre acteur_id
        if acteur_id == "global":
            acteur_filter = None
        else:
            acteur_filter = acteur_id
        
        query = db.query(
            Contrat.ecole,
            func.count(FicPersonne.id).label("count")
        ).join(
            FicPersonne, FicPersonne.id == Contrat.fic_personne_id
        ).join(
            FicPersonneProjet, FicPersonne.id == FicPersonneProjet.fic_personne_id
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
            # Normaliser l'encodage UTF-8
            school_str = str(school or "Non spécifié")
            if isinstance(school_str, bytes):
                school_str = school_str.decode('utf-8')
            
            result.append({
                "school": school_str,
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

        hires = db.query(
            func.date_trunc('month', Contrat.date_debut).label('month'),
            func.count(Contrat.id).label('count')
        ).join(
            FicPersonne, FicPersonne.id == Contrat.fic_personne_id
        ).join(
            FicPersonneProjet, FicPersonne.id == FicPersonneProjet.fic_personne_id
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


@router.get("/operator/all/{acteur_id}")
async def get_operator_dashboard_all(acteur_id: str, filter_type: str = "all", db: Session = Depends(get_db)):
    """Toutes les données du dashboard en un seul appel API.
    Réduit 9 requêtes HTTP → 1, élimine le N+1 zones, et utilise un cache mémoire 5 min.
    """
    cache_key = f"op_all_{acteur_id}_{filter_type}"
    cached = _cache_get(cache_key)
    if cached is not None:
        print(f"[DASHBOARD] Cache HIT pour acteur_id={acteur_id} filter={filter_type}")
        return cached

    print(f"[DASHBOARD] → Requête reçue: acteur_id={acteur_id} filter_type={filter_type}")
    try:
        today = date.today()
        acteur_filter = None if acteur_id == "global" else acteur_id
        is_active = filter_type == "active"

        # ── 1. Nombre total d'employés ──────────────────────────────────────
        emp_q = db.query(FicPersonne.id).join(
            FicPersonneProjet, FicPersonne.id == FicPersonneProjet.fic_personne_id
        )
        if acteur_filter:
            emp_q = emp_q.filter(FicPersonneProjet.acteur_id == acteur_filter)
        if is_active:
            emp_q = emp_q.join(
                Contrat, FicPersonne.id == Contrat.fic_personne_id
            ).filter(
                Contrat.date_debut <= today,
                or_(Contrat.date_fin >= today, Contrat.date_fin.is_(None))
            )
        total_employees = emp_q.distinct().count()

        # ── 2. Contrats actifs ──────────────────────────────────────────────
        ac_q = db.query(func.count(func.distinct(FicPersonne.id))).join(
            FicPersonneProjet, FicPersonne.id == FicPersonneProjet.fic_personne_id
        ).join(
            Contrat, FicPersonne.id == Contrat.fic_personne_id
        ).filter(
            Contrat.date_debut <= today,
            or_(Contrat.date_fin >= today, Contrat.date_fin.is_(None))
        )
        if acteur_filter:
            ac_q = ac_q.filter(FicPersonneProjet.acteur_id == acteur_filter)
        active_contracts = ac_q.scalar() or 0

        # ── 3. Dates de naissance (réutilisées pour >25 ans ET tranches d'âge) ─
        bd_q = db.query(FicPersonne.date_naissance).join(
            FicPersonneProjet, FicPersonne.id == FicPersonneProjet.fic_personne_id
        ).filter(FicPersonne.date_naissance.isnot(None))
        if acteur_filter:
            bd_q = bd_q.filter(FicPersonneProjet.acteur_id == acteur_filter)
        if is_active:
            bd_q = bd_q.join(
                Contrat, FicPersonne.id == Contrat.fic_personne_id
            ).filter(
                Contrat.date_debut <= today,
                or_(Contrat.date_fin >= today, Contrat.date_fin.is_(None))
            )
        ages = [(today - row[0]).days // 365 for row in bd_q.distinct().all()]
        young_count = sum(1 for a in ages if a > 25)

        # ── 4. Dernière connexion ───────────────────────────────────────────
        ll_q = db.query(UserAction.created_at).filter(UserAction.action_type == "LOGIN")
        if acteur_filter:
            ll_q = ll_q.filter(UserAction.acteur_id == acteur_filter)
        ll_row = ll_q.order_by(UserAction.created_at.desc()).first()
        last_login_date = ll_row[0] if ll_row else None

        # ── 5. Postes ───────────────────────────────────────────────────────
        pos_q = db.query(
            Contrat.poste_nom,
            func.count(FicPersonne.id).label("count")
        ).join(FicPersonne, FicPersonne.id == Contrat.fic_personne_id
        ).join(FicPersonneProjet, FicPersonne.id == FicPersonneProjet.fic_personne_id)
        if acteur_filter:
            pos_q = pos_q.filter(FicPersonneProjet.acteur_id == acteur_filter)
        if is_active:
            pos_q = pos_q.filter(
                Contrat.date_debut <= today,
                or_(Contrat.date_fin >= today, Contrat.date_fin.is_(None))
            )
        positions = sorted([
            {"position": p or "Non spécifié", "count": c}
            for p, c in pos_q.group_by(Contrat.poste_nom).all()
        ], key=lambda x: x["count"], reverse=True)

        # ── 6. Zones géographiques (JOIN unique — élimine N+1) ──────────────
        zone_q = db.query(
            func.coalesce(TRegion.nom, 'N/A').label('region'),
            func.coalesce(TDepartement.nom, 'N/A').label('departement'),
            func.count(func.distinct(FicPersonne.id)).label("count")
        ).select_from(FicPersonneLocalisation
        ).join(Contrat, Contrat.id == FicPersonneLocalisation.contrat_id
        ).join(FicPersonne, FicPersonne.id == Contrat.fic_personne_id
        ).join(FicPersonneProjet, FicPersonne.id == FicPersonneProjet.fic_personne_id
        ).outerjoin(TRegion, TRegion.id == FicPersonneLocalisation.region_id
        ).outerjoin(TDepartement, TDepartement.id == FicPersonneLocalisation.departement_id)
        if acteur_filter:
            zone_q = zone_q.filter(FicPersonneProjet.acteur_id == acteur_filter)
        if is_active:
            zone_q = zone_q.filter(
                Contrat.date_debut <= today,
                or_(Contrat.date_fin >= today, Contrat.date_fin.is_(None))
            )
        zones = sorted([
            {"region": r, "departement": d, "count": c}
            for r, d, c in zone_q.group_by(TRegion.nom, TDepartement.nom).all() if c > 0
        ], key=lambda x: x["count"], reverse=True)

        # ── 7. Statut des contrats ──────────────────────────────────────────
        if is_active:
            cs_completed = 0
            cs_upcoming = 0
        else:
            def _contract_count(extra_filter):
                q = db.query(func.count(func.distinct(FicPersonne.id))).join(
                    Contrat, FicPersonne.id == Contrat.fic_personne_id
                ).join(FicPersonneProjet, FicPersonne.id == FicPersonneProjet.fic_personne_id)
                if acteur_filter:
                    q = q.filter(FicPersonneProjet.acteur_id == acteur_filter)
                return q.filter(extra_filter).scalar() or 0

            cs_completed = _contract_count(Contrat.date_fin < today)
            cs_upcoming  = _contract_count(Contrat.date_debut > today)

        # ── 8. Durée moyenne des contrats ───────────────────────────────────
        dur_q = db.query(Contrat.date_debut, Contrat.date_fin).join(
            FicPersonne, FicPersonne.id == Contrat.fic_personne_id
        ).join(FicPersonneProjet, FicPersonne.id == FicPersonneProjet.fic_personne_id
        ).filter(Contrat.date_debut.isnot(None))
        if acteur_filter:
            dur_q = dur_q.filter(FicPersonneProjet.acteur_id == acteur_filter)
        if is_active:
            dur_q = dur_q.filter(
                Contrat.date_debut <= today,
                or_(Contrat.date_fin >= today, Contrat.date_fin.is_(None))
            )
        contracts = dur_q.all()
        if contracts:
            total_days = sum(
                (row.date_fin - row.date_debut).days if row.date_fin else (today - row.date_debut).days
                for row in contracts
            )
            avg_days = total_days // len(contracts)
        else:
            avg_days = 0

        # ── 9. Projets ──────────────────────────────────────────────────────
        proj_q = db.query(
            Projet.id,
            Projet.nom,
            func.count(func.distinct(FicPersonne.id)).label("count")
        ).join(FicPersonneProjet, Projet.id == FicPersonneProjet.projet_id
        ).join(FicPersonne, FicPersonne.id == FicPersonneProjet.fic_personne_id)
        if acteur_filter:
            proj_q = proj_q.filter(FicPersonneProjet.acteur_id == acteur_filter)
        if is_active:
            proj_q = proj_q.join(
                Contrat, FicPersonne.id == Contrat.fic_personne_id
            ).filter(
                Contrat.date_debut <= today,
                or_(Contrat.date_fin >= today, Contrat.date_fin.is_(None))
            )
        projects = sorted([
            {"project_id": pid, "project_name": pname or "Non spécifié", "count": c}
            for pid, pname, c in proj_q.group_by(Projet.id, Projet.nom).all() if c > 0
        ], key=lambda x: x["count"], reverse=True)

        # ── 10. Genre ───────────────────────────────────────────────────────
        gen_q = db.query(
            FicPersonne.genre,
            func.count(FicPersonne.id).label("count")
        ).join(FicPersonneProjet, FicPersonne.id == FicPersonneProjet.fic_personne_id)
        if acteur_filter:
            gen_q = gen_q.filter(FicPersonneProjet.acteur_id == acteur_filter)
        if is_active:
            gen_q = gen_q.join(
                Contrat, FicPersonne.id == Contrat.fic_personne_id
            ).filter(
                Contrat.date_debut <= today,
                or_(Contrat.date_fin >= today, Contrat.date_fin.is_(None))
            )
        genders_raw = gen_q.group_by(FicPersonne.genre).all()
        total_g = sum(c for _, c in genders_raw)
        genders = sorted([
            {"gender": g or "Non spécifié", "count": c,
             "percentage": round(c / total_g * 100) if total_g else 0}
            for g, c in genders_raw
        ], key=lambda x: x["count"], reverse=True)

        # ── 11. Tranches d'âge (réutilise les âges calculés au §3) ─────────
        age_groups = {"18-25": 0, "26-35": 0, "36-45": 0, "46-55": 0, "56+": 0}
        for age in ages:
            if   age <= 25: age_groups["18-25"] += 1
            elif age <= 35: age_groups["26-35"] += 1
            elif age <= 45: age_groups["36-45"] += 1
            elif age <= 55: age_groups["46-55"] += 1
            else:           age_groups["56+"]   += 1
        age_stats = {
            "average_age": round(sum(ages) / len(ages)) if ages else 0,
            "min_age":     min(ages) if ages else 0,
            "max_age":     max(ages) if ages else 0,
            "age_groups":  age_groups,
        }

        # ── 12. Embauches mensuelles ────────────────────────────────────────
        start_date = today - timedelta(days=365)
        hires_q = db.query(
            func.date_trunc('month', Contrat.date_debut).label('month'),
            func.count(Contrat.id).label('count')
        ).join(FicPersonne, FicPersonne.id == Contrat.fic_personne_id
        ).join(FicPersonneProjet, FicPersonne.id == FicPersonneProjet.fic_personne_id
        ).filter(Contrat.date_debut >= start_date)
        if acteur_filter:
            hires_q = hires_q.filter(FicPersonneProjet.acteur_id == acteur_filter)
        hires_data = hires_q.group_by(
            func.date_trunc('month', Contrat.date_debut)
        ).order_by(func.date_trunc('month', Contrat.date_debut)).all()
        monthly_hires = [
            {"month": m.strftime("%Y-%m"), "count": c}
            for m, c in hires_data if m
        ]

        result = {
            "stats": {
                "total_employees":         total_employees,
                "active_contracts":        active_contracts,
                "young_employees_over_25": young_count,
                "last_login":              last_login_date.isoformat() if last_login_date else None,
            },
            "employees_by_position": positions,
            "employees_by_zone":     zones,
            "contract_status": {
                "active":    active_contracts,
                "completed": cs_completed,
                "upcoming":  cs_upcoming,
            },
            "average_contract_duration": {
                "average_days":    avg_days,
                "average_months":  avg_days // 30,
                "total_contracts": len(contracts),
            },
            "employees_by_project": projects,
            "employees_by_gender":  genders,
            "age_statistics":       age_stats,
            "monthly_hires":        monthly_hires,
        }
        _cache_set(cache_key, result)
        print(f"[DASHBOARD] ← Réponse envoyée: total_employees={result['stats']['total_employees']}, "
              f"active_contracts={result['stats']['active_contracts']}, "
              f"positions={len(result['employees_by_position'])}, "
              f"zones={len(result['employees_by_zone'])}, "
              f"gender={result['employees_by_gender']}, "
              f"contract_status={result['contract_status']}, "
              f"monthly_hires={len(result['monthly_hires'])}, "
              f"age_stats={result['age_statistics']}")
        return result
    except Exception as e:
        print(f"[DASHBOARD] ERREUR: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/operator/cache/{acteur_id}")
async def invalidate_operator_cache(acteur_id: str):
    """Vide le cache backend pour cet acteur (à appeler après un import)."""
    _cache_invalidate(acteur_id)
    return {"ok": True}
