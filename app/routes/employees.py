# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import date
from app.database import get_db
from app.models import FicPersonne, Contrat, FicPersonneLocalisation, FicPersonneProjet, Projet, TRegion, TDepartement, TSousPrefecture, ZoneDIntervention
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/employees", tags=["employees"])

class EmployeeDetail:
    def __init__(self, fic_personne, contrat, localisation):
        self.id = fic_personne.id
        self.nom = fic_personne.nom
        self.prenom = fic_personne.prenom
        self.date_naissance = fic_personne.date_naissance
        self.genre = fic_personne.genre
        self.contact = fic_personne.contact
        self.poste_nom = contrat.poste_nom if contrat else None
        self.categorie_poste = contrat.categorie_poste if contrat else None
        self.type_personne = contrat.type_personne if contrat else None
        self.diplome = contrat.diplome if contrat else None
        self.ecole = contrat.ecole if contrat else None
        self.date_debut = contrat.date_debut if contrat else None
        self.date_fin = contrat.date_fin if contrat else None
        self.region_id = localisation.region_id if localisation else None
        self.departement_id = localisation.departement_id if localisation else None
        self.sous_prefecture_id = localisation.sous_prefecture_id if localisation else None

@router.get("/list/{acteur_id}")
async def get_employees_list(acteur_id: str, db: Session = Depends(get_db)):
    """Récupérer la liste complète des employés avec leurs contrats et localisations"""
    
    try:
        logger.info(f"Récupération des employés pour acteur_id: {acteur_id}")
        
        # Récupérer tous les employés de l'acteur via fic_personne_projet
        # Structure: acteur (1) -> (N) fic_personne_projet (N) <- (1) fic_personne
        fic_personne_projets = db.query(FicPersonneProjet).filter(
            FicPersonneProjet.acteur_id == acteur_id
        ).all()
        
        # Récupérer les IDs uniques des employés
        employee_ids = set(fpp.fic_personne_id for fpp in fic_personne_projets)
        
        # Récupérer les employés
        personnes = db.query(FicPersonne).filter(
            FicPersonne.id.in_(list(employee_ids))
        ).all() if employee_ids else []
        
        logger.info(f"Nombre d'employés trouvés: {len(personnes)}")
        
        employees = []
        
        for personne in personnes:
            try:
                # Récupérer le contrat le plus récent (le dernier créé)
                contrat = db.query(Contrat).filter(
                    Contrat.fic_personne_id == personne.id
                ).order_by(Contrat.date_debut.desc()).first()
                
                # Récupérer la localisation associée
                localisation = None
                if contrat:
                    localisation = db.query(FicPersonneLocalisation).filter(
                        FicPersonneLocalisation.contrat_id == contrat.id
                    ).first()
                
                # Calculer l'âge
                age = 0
                if personne.date_naissance:
                    today = date.today()
                    age = today.year - personne.date_naissance.year
                    if (today.month, today.day) < (personne.date_naissance.month, personne.date_naissance.day):
                        age -= 1
                
                # Déterminer si le contrat est actif
                today = date.today()
                is_active = False
                if contrat:
                    is_active = (contrat.date_debut <= today and 
                               (contrat.date_fin is None or contrat.date_fin >= today))
                
                # Récupérer les noms de région, département, sous-préfecture
                region_name = "-"
                departement_name = "-"
                sous_prefecture_name = "-"
                
                if localisation:
                    if localisation.region_id:
                        try:
                            region = db.query(TRegion).filter(TRegion.id == localisation.region_id).first()
                            if region:
                                region_name = region.nom
                        except Exception as e:
                            logger.warning(f"Erreur lors de la récupération de la région: {e}")
                    
                    if localisation.departement_id:
                        try:
                            departement = db.query(TDepartement).filter(TDepartement.id == localisation.departement_id).first()
                            if departement:
                                departement_name = departement.nom
                        except Exception as e:
                            logger.warning(f"Erreur lors de la récupération du département: {e}")
                    
                    if localisation.sous_prefecture_id:
                        try:
                            sous_pref = db.query(TSousPrefecture).filter(TSousPrefecture.id == localisation.sous_prefecture_id).first()
                            if sous_pref:
                                sous_prefecture_name = sous_pref.nom
                        except Exception as e:
                            logger.warning(f"Erreur lors de la récupération de la sous-préfecture: {e}")
                
                # Récupérer tous les projets de l'employé
                projets_list = []
                try:
                    fic_personne_projets = db.query(FicPersonneProjet).filter(
                        FicPersonneProjet.fic_personne_id == personne.id
                    ).all()
                    
                    for fp_proj in fic_personne_projets:
                        projet = db.query(Projet).filter(Projet.id == fp_proj.projet_id).first()
                        if projet:
                            projets_list.append({
                                "id": projet.id,
                                "nom": projet.nom,
                                "nom_complet": projet.nom_complet
                            })
                except Exception as e:
                    logger.warning(f"Erreur lors de la récupération des projets pour {personne.id}: {e}")
                
                employee = {
                    "id": personne.id,
                    "nom": personne.nom,
                    "prenom": personne.prenom,
                    "matricule": personne.matricule or "-",
                    "date_naissance": personne.date_naissance.isoformat() if personne.date_naissance else None,
                    "genre": personne.genre or "M",
                    "contact": personne.contact or "-",
                    "age": age,
                    "poste": contrat.poste_nom if contrat else "Non spécifié",
                    "categorie_poste": contrat.categorie_poste if contrat else "-",
                    "qualification": contrat.poste if contrat else "-",
                    "type_personne": contrat.type_personne if contrat else "-",
                    "statut": contrat.type_personne if contrat else "-",
                    "diplome": contrat.diplome if contrat else "-",
                    "ecole": contrat.ecole if contrat and contrat.ecole else "-",
                    "type_contrat": contrat.type_contrat if contrat else "-",
                    "date_debut": contrat.date_debut.isoformat() if contrat and contrat.date_debut else None,
                    "date_fin": contrat.date_fin.isoformat() if contrat and contrat.date_fin else None,
                    "validiteContrat": f"{contrat.date_debut.isoformat()} - {contrat.date_fin.isoformat() if contrat.date_fin else 'Indéterminée'}" if contrat and contrat.date_debut else "-",
                    "qualiteContrat": contrat.categorie_poste if contrat else "-",
                    "is_active": is_active,
                    "region": region_name,
                    "departement": departement_name,
                    "sousPrefecture": sous_prefecture_name,
                    "projets": projets_list,
                    "contrat_id": contrat.id if contrat else None,
                }
                
                employees.append(employee)
            except Exception as e:
                logger.error(f"Erreur lors du traitement de l'employé {personne.id}: {e}")
                continue
        
        logger.info(f"Nombre d'employés retournés: {len(employees)}")
        return employees
        
    except Exception as e:
        logger.error(f"Erreur dans get_employees_list: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/projects")
async def get_projects(acteur_id: str, db: Session = Depends(get_db)):
    """Récupérer les projets disponibles pour un acteur via zone_intervention"""
    
    try:
        logger.info(f"Récupération des projets pour acteur_id: {acteur_id}")
        
        # Utiliser une requête SQL directe pour éviter les colonnes manquantes
        from sqlalchemy import text
        
        result = db.execute(text("""
            SELECT DISTINCT projet_id 
            FROM zone_d_intervention 
            WHERE acteur_id = :acteur_id
        """), {"acteur_id": acteur_id})
        
        projet_ids = [row[0] for row in result]
        logger.info(f"Nombre de projets trouvés: {len(projet_ids)}")
        
        projets = []
        for projet_id in projet_ids:
            projet = db.query(Projet).filter(Projet.id == projet_id).first()
            if projet:
                projets.append({
                    "id": projet.id,
                    "nom": projet.nom,
                    "nom_complet": projet.nom_complet,
                })
        
        logger.info(f"Nombre de projets retournés: {len(projets)}")
        return projets
        
    except Exception as e:
        logger.error(f"Erreur dans get_projects: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
