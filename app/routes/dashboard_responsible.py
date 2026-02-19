# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, text
from datetime import datetime, date, timedelta
from app.database import get_db
from app.models import FicPersonne, Contrat, Acteur, Login, ZoneDIntervention, UserAction, FicPersonneLocalisation, Projet, FicPersonneProjet
from app.security import get_current_user

router = APIRouter(prefix="/api/dashboard/responsible", tags=["dashboard_responsible"])

@router.get("/statistics/{acteur_id}")
async def get_responsible_statistics(acteur_id: str, filter_type: str = "tous", db: Session = Depends(get_db)):
    """Récupérer les statistiques complètes du dashboard responsable
    
    filter_type: 'tous', 'actifs', 'inactifs'
    """
    
    try:
        today = date.today()
        
        # Récupérer les employés avec filtrage
        query = db.query(FicPersonne).join(
            FicPersonneProjet, FicPersonne.id == FicPersonneProjet.fic_personne_id
        ).join(
            Contrat, FicPersonne.id == Contrat.fic_personne_id
        ).filter(
            FicPersonneProjet.acteur_id == acteur_id
        )
        
        if filter_type == "actifs":
            query = query.filter(
                Contrat.date_debut <= today,
                or_(Contrat.date_fin >= today, Contrat.date_fin.is_(None))
            )
        elif filter_type == "inactifs":
            query = query.filter(
                Contrat.date_fin < today
            )
        
        employees = query.distinct().all()
        
        # Calculer les statistiques
        total_employees = len(employees)
        
        # Par type de contrat
        cdi_count = sum(1 for e in employees if e.type_personne == 'CDI')
        cdd_count = sum(1 for e in employees if e.type_personne == 'CDD')
        consultant_count = sum(1 for e in employees if e.type_personne == 'Consultant')
        
        # Par genre
        male_count = sum(1 for e in employees if e.genre == 'M')
        female_count = sum(1 for e in employees if e.genre == 'F')
        
        # Âges
        ages = [e.age for e in employees if e.age]
        age_min = min(ages) if ages else 0
        age_max = max(ages) if ages else 0
        age_avg = sum(ages) // len(ages) if ages else 0
        
        # Contrats actifs/expirés
        active_contracts = sum(1 for e in employees if any(
            c.date_debut <= today and (c.date_fin is None or c.date_fin >= today)
            for c in db.query(Contrat).filter(Contrat.fic_personne_id == e.id).all()
        ))
        expired_contracts = total_employees - active_contracts
        
        # Ratio permanent/temporaire
        permanent = cdi_count
        temporary = cdd_count + consultant_count
        
        # Durée moyenne des contrats
        durations = []
        for e in employees:
            contracts = db.query(Contrat).filter(Contrat.fic_personne_id == e.id).all()
            for c in contracts:
                if c.date_debut and c.date_fin:
                    duration = (c.date_fin - c.date_debut).days
                    durations.append(duration // 30)  # Convertir en mois
        
        avg_duration = sum(durations) // len(durations) if durations else 0
        
        return {
            "totalEmployes": total_employees,
            "cdi": cdi_count,
            "cdd": cdd_count,
            "consultant": consultant_count,
            "hommes": male_count,
            "femmes": female_count,
            "tauxFeminisation": (female_count * 100) // total_employees if total_employees > 0 else 0,
            "ageMin": age_min,
            "ageMax": age_max,
            "ageMoyen": age_avg,
            "contratsActifs": active_contracts,
            "contratsExpires": expired_contracts,
            "tauxRenouvellement": (expired_contracts * 100) // total_employees if total_employees > 0 else 0,
            "ratioPermanentTemporaire": f"{permanent}/{temporary}",
            "dureemoyenneContrats": avg_duration
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/contrats-echeance/{acteur_id}")
async def get_contracts_expiring(acteur_id: str, db: Session = Depends(get_db)):
    """Récupérer les contrats arrivant à échéance (3, 6, 12 mois)"""
    
    try:
        today = date.today()
        in_3_months = today + timedelta(days=90)
        in_6_months = today + timedelta(days=180)
        in_12_months = today + timedelta(days=365)
        
        # Contrats dans 3 mois
        contracts_3m = db.query(func.count(Contrat.id)).join(
            FicPersonne, Contrat.fic_personne_id == FicPersonne.id
        ).join(
            FicPersonneProjet, FicPersonne.id == FicPersonneProjet.fic_personne_id
        ).filter(
            FicPersonneProjet.acteur_id == acteur_id,
            Contrat.date_fin > today,
            Contrat.date_fin <= in_3_months,
            Contrat.date_debut <= today
        ).scalar() or 0
        
        # Contrats dans 6 mois
        contracts_6m = db.query(func.count(Contrat.id)).join(
            FicPersonne, Contrat.fic_personne_id == FicPersonne.id
        ).join(
            FicPersonneProjet, FicPersonne.id == FicPersonneProjet.fic_personne_id
        ).filter(
            FicPersonneProjet.acteur_id == acteur_id,
            Contrat.date_fin > in_3_months,
            Contrat.date_fin <= in_6_months,
            Contrat.date_debut <= today
        ).scalar() or 0
        
        # Contrats dans 12 mois
        contracts_12m = db.query(func.count(Contrat.id)).join(
            FicPersonne, Contrat.fic_personne_id == FicPersonne.id
        ).join(
            FicPersonneProjet, FicPersonne.id == FicPersonneProjet.fic_personne_id
        ).filter(
            FicPersonneProjet.acteur_id == acteur_id,
            Contrat.date_fin > in_6_months,
            Contrat.date_fin <= in_12_months,
            Contrat.date_debut <= today
        ).scalar() or 0
        
        return {
            "dans3mois": contracts_3m,
            "dans6mois": contracts_6m,
            "dans12mois": contracts_12m
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/effectif-par-region/{acteur_id}")
async def get_employees_by_region(acteur_id: str, filter_type: str = "tous", db: Session = Depends(get_db)):
    """Récupérer l'effectif déployé par région"""
    
    try:
        today = date.today()
        
        query = db.query(
            FicPersonneLocalisation.region,
            func.count(FicPersonne.id).label('effectif')
        ).join(
            Contrat, FicPersonneLocalisation.contrat_id == Contrat.id
        ).join(
            FicPersonne, Contrat.fic_personne_id == FicPersonne.id
        ).join(
            FicPersonneProjet, FicPersonne.id == FicPersonneProjet.fic_personne_id
        ).filter(
            FicPersonneProjet.acteur_id == acteur_id
        )
        
        if filter_type == "actifs":
            query = query.filter(
                Contrat.date_debut <= today,
                or_(Contrat.date_fin >= today, Contrat.date_fin.is_(None))
            )
        elif filter_type == "inactifs":
            query = query.filter(Contrat.date_fin < today)
        
        results = query.group_by(FicPersonneLocalisation.region).all()
        
        total = sum(r[1] for r in results)
        
        return [
            {
                "region": r[0] or "Non spécifiée",
                "effectif": r[1],
                "pourcentage": (r[1] * 100) // total if total > 0 else 0
            }
            for r in sorted(results, key=lambda x: x[1], reverse=True)
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/taux-occupation-projets/{acteur_id}")
async def get_projects_occupation_rate(acteur_id: str, filter_type: str = "tous", db: Session = Depends(get_db)):
    """Récupérer le taux d'occupation par projet"""
    
    try:
        today = date.today()
        
        query = db.query(
            Projet.nom,
            func.count(FicPersonne.id).label('count')
        ).join(
            FicPersonneProjet, Projet.id == FicPersonneProjet.projet_id
        ).join(
            FicPersonne, FicPersonneProjet.fic_personne_id == FicPersonne.id
        ).join(
            Contrat, FicPersonne.id == Contrat.fic_personne_id
        ).filter(
            FicPersonneProjet.acteur_id == acteur_id
        )
        
        if filter_type == "actifs":
            query = query.filter(
                Contrat.date_debut <= today,
                or_(Contrat.date_fin >= today, Contrat.date_fin.is_(None))
            )
        elif filter_type == "inactifs":
            query = query.filter(Contrat.date_fin < today)
        
        results = query.group_by(Projet.nom).all()
        
        return [
            {
                "nomProjet": r[0],
                "nombrePersonnes": r[1],
                "capaciteMax": int(r[1] * 1.2),
                "tauxOccupation": int((r[1] / (r[1] * 1.2)) * 100) if r[1] > 0 else 0
            }
            for r in sorted(results, key=lambda x: x[1], reverse=True)
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/employes-par-poste/{acteur_id}")
async def get_employees_by_position(acteur_id: str, filter_type: str = "tous", db: Session = Depends(get_db)):
    """Récupérer les employés par poste"""
    
    try:
        today = date.today()
        
        query = db.query(
            FicPersonneLocalisation.poste,
            func.count(FicPersonne.id).label('count')
        ).join(
            Contrat, FicPersonneLocalisation.contrat_id == Contrat.id
        ).join(
            FicPersonne, Contrat.fic_personne_id == FicPersonne.id
        ).join(
            FicPersonneProjet, FicPersonne.id == FicPersonneProjet.fic_personne_id
        ).filter(
            FicPersonneProjet.acteur_id == acteur_id
        )
        
        if filter_type == "actifs":
            query = query.filter(
                Contrat.date_debut <= today,
                or_(Contrat.date_fin >= today, Contrat.date_fin.is_(None))
            )
        elif filter_type == "inactifs":
            query = query.filter(Contrat.date_fin < today)
        
        results = query.group_by(FicPersonneLocalisation.poste).all()
        
        total = sum(r[1] for r in results)
        
        return [
            {
                "poste": r[0] or "Non spécifié",
                "nombre": r[1],
                "pourcentage": (r[1] * 100) // total if total > 0 else 0
            }
            for r in sorted(results, key=lambda x: x[1], reverse=True)
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/niveau-education/{acteur_id}")
async def get_education_levels(acteur_id: str, filter_type: str = "tous", db: Session = Depends(get_db)):
    """Récupérer la répartition par niveau d'éducation"""
    
    try:
        today = date.today()
        
        query = db.query(
            FicPersonne.diplome,
            func.count(FicPersonne.id).label('count')
        ).join(
            FicPersonneProjet, FicPersonne.id == FicPersonneProjet.fic_personne_id
        ).join(
            Contrat, FicPersonne.id == Contrat.fic_personne_id
        ).filter(
            FicPersonneProjet.acteur_id == acteur_id,
            FicPersonne.diplome.isnot(None)
        )
        
        if filter_type == "actifs":
            query = query.filter(
                Contrat.date_debut <= today,
                or_(Contrat.date_fin >= today, Contrat.date_fin.is_(None))
            )
        elif filter_type == "inactifs":
            query = query.filter(Contrat.date_fin < today)
        
        results = query.group_by(FicPersonne.diplome).all()
        
        total = sum(r[1] for r in results)
        
        return [
            {
                "niveau": r[0] or "Non spécifié",
                "nombre": r[1],
                "pourcentage": (r[1] * 100) // total if total > 0 else 0
            }
            for r in sorted(results, key=lambda x: x[1], reverse=True)
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/groupes-age/{acteur_id}")
async def get_age_groups(acteur_id: str, filter_type: str = "tous", db: Session = Depends(get_db)):
    """Récupérer la distribution par groupes d'âge"""
    
    try:
        today = date.today()
        
        query = db.query(FicPersonne).join(
            FicPersonneProjet, FicPersonne.id == FicPersonneProjet.fic_personne_id
        ).join(
            Contrat, FicPersonne.id == Contrat.fic_personne_id
        ).filter(
            FicPersonneProjet.acteur_id == acteur_id,
            FicPersonne.age.isnot(None)
        )
        
        if filter_type == "actifs":
            query = query.filter(
                Contrat.date_debut <= today,
                or_(Contrat.date_fin >= today, Contrat.date_fin.is_(None))
            )
        elif filter_type == "inactifs":
            query = query.filter(Contrat.date_fin < today)
        
        employees = query.distinct().all()
        
        groups = {
            "< 25 ans": 0,
            "25-35 ans": 0,
            "35-45 ans": 0,
            "45-55 ans": 0,
            "> 55 ans": 0
        }
        
        for e in employees:
            if e.age < 25:
                groups["< 25 ans"] += 1
            elif e.age < 35:
                groups["25-35 ans"] += 1
            elif e.age < 45:
                groups["35-45 ans"] += 1
            elif e.age < 55:
                groups["45-55 ans"] += 1
            else:
                groups["> 55 ans"] += 1
        
        total = sum(groups.values())
        
        return [
            {
                "tranche": k,
                "nombre": v,
                "pourcentage": (v * 100) // total if total > 0 else 0
            }
            for k, v in groups.items()
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
