# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, text
from datetime import datetime, date, timedelta
from app.database import get_db
from app.models import FicPersonne, Contrat, Acteur, Users, ZoneDIntervention, UserAction, FicPersonneLocalisation, Projet, FicPersonneProjet, TRegion, TDepartement
from app.security import get_current_user

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

def get_employee_ids_for_acteur(db: Session, acteur_id: str, filter_type: str = "all"):
    """Récupérer les IDs des employés pour un acteur via fic_personne_projet"""
    today = date.today()
    
    if filter_type == "active":
        query = db.query(FicPersonne.id).join(
            FicPersonneProjet, FicPersonne.id == FicPersonneProjet.fic_personne_id
        ).join(
            Contrat, FicPersonne.id == Contrat.fic_personne_id
        ).filter(
            FicPersonneProjet.acteur_id == acteur_id,
            Contrat.date_debut <= today,
            or_(Contrat.date_fin >= today, Contrat.date_fin.is_(None))
        )
    else:
        query = db.query(FicPersonne.id).join(
            FicPersonneProjet, FicPersonne.id == FicPersonneProjet.fic_personne_id
        ).filter(
            FicPersonneProjet.acteur_id == acteur_id
        )
    
    return [e[0] for e in query.distinct().all()]

@router.get("/operator/stats/{acteur_id}")
async def get_operator_stats(acteur_id: str, filter_type: str = "all", db: Session = Depends(get_db)):
    """Récupérer les statistiques du dashboard opérateur"""
    
    try:
        today = date.today()
        
        if acteur_id == "global":
            acteur_filter = None
        else:
            acteur_filter = acteur_id
        
        # Récupérer les IDs des employés
        if acteur_filter:
            employee_ids = get_employee_ids_for_acteur(db, acteur_filter, filter_type)
        else:
            query = db.query(FicPersonne.id).join(
                FicPersonneProjet, FicPersonne.id == FicPersonneProjet.fic_personne_id
            )
            if filter_type == "active":
                query = query.join(
                    Contrat, FicPersonne.id == Contrat.fic_personne_id
                ).filter(
                    Contrat.date_debut <= today,
                    or_(Contrat.date_fin >= today, Contrat.date_fin.is_(None))
                )
            employee_ids = [e[0] for e in query.distinct().all()]
        
        total_employees = len(employee_ids)
        
        # Contrats actifs
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
        
        # Employés avec date de naissance
        query = db.query(FicPersonne).join(
            FicPersonneProjet, FicPersonne.id == FicPersonneProjet.fic_personne_id
        ).filter(
            FicPersonne.date_naissance.isnot(None)
        )
        if acteur_filter:
            query = query.filter(FicPersonneProjet.acteur_id == acteur_filter)
        
        if filter_type == "active":
            query = query.join(
                Contrat, FicPersonne.id == Contrat.fic_personne_id
            ).filter(
                Contrat.date_debut <= today,
                or_(Contrat.date_fin >= today, Contrat.date_fin.is_(None))
            )
        
        employees_with_birth = query.distinct().all()
        
        young_count = 0
        for emp in employees_with_birth:
            if emp.date_naissance:
                age = (today - emp.date_naissance).days // 365
                if age > 25:
                    young_count += 1
        
        # Dernière connexion
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

@router.get("/operator/employees-by-zone/{acteur_id}")
async def get_employees_by_zone(acteur_id: str, filter_type: str = "all", db: Session = Depends(get_db)):
    """Nombre d'employés par zone d'intervention"""
    
    try:
        today = date.today()
        
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
        
        for item in result:
            item["percentage"] = round((item["count"] / total * 100)) if total > 0 else 0
        
        return sorted(result, key=lambda x: x["count"], reverse=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/operator/contract-types/{acteur_id}")
async def get_contract_types(acteur_id: str, filter_type: str = "all", db: Session = Depends(get_db)):
    """Répartition par type de contrat"""
    
    try:
        today = date.today()
        
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

@router.get("/operator/top-schools/{acteur_id}")
async def get_top_schools(acteur_id: str, filter_type: str = "all", db: Session = Depends(get_db)):
    """Top 5 écoles/formations"""
    
    try:
        today = date.today()
        
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
            Contrat.ecole.isnot(None)
        )
        
        if acteur_filter:
            query = query.filter(FicPersonneProjet.acteur_id == acteur_filter)
        
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
    """Taux de renouvellement des contrats"""
    
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

@router.get("/operator/monthly-hires/{acteur_id}")
async def get_monthly_hires(acteur_id: str, months: int = 12, db: Session = Depends(get_db)):
    """Embauches par mois"""
    
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
