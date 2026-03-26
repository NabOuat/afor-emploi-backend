# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import date
from app.database import get_db
from app.models import FicPersonne, Contrat, FicPersonneLocalisation, FicPersonneProjet, Projet, TRegion, TDepartement, TSousPrefecture, ZoneDIntervention
from typing import List, Optional
import logging
import unicodedata

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/employees", tags=["employees"])

def normalize_utf8(text):
    """Normalise les caractères UTF-8 mal encodés"""
    if not text or not isinstance(text, str):
        return text
    try:
        # Dictionnaire de remplacement pour les caractères mal encodés courants
        replacements = {
            '├â┬®': 'é',
            '├â┬Ç': 'ç',
            '├â┬Ö': 'è',
            '├â┬ê': 'ê',
            '├ô┬ê': 'ô',
            '├ô┬ç': 'ù',
            '├â┬ô': 'à',
            '├â┬ô': 'î',
            '├â┬ü': 'ü',
            '├â┬ö': 'ö',
            '├â┬ô': 'á',
            '├â┬ö': 'ó',
            '├â┬ü': 'ú',
            '├â┬ô': 'í',
            'N├ó┬Ç┬Ö': 'NGUESSAN',
            'n├ó┬Ç┬Ö': 'nguessan',
            '├é┬á': 'é',
        }
        
        result = text
        for bad, good in replacements.items():
            result = result.replace(bad, good)
        
        return result
    except:
        return text

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
        
        # Requête SQL optimisée pour charger tous les données en une seule requête
        from sqlalchemy import text
        
        result = db.execute(text("""
            SELECT DISTINCT
                fp.id,
                fp.nom,
                fp.prenom,
                fp.matricule,
                fp.date_naissance::date,
                fp.genre,
                fp.contact,
                c.id as contrat_id,
                c.poste_nom,
                c.categorie_poste,
                c.poste,
                c.type_personne,
                c.diplome,
                c.ecole,
                c.type_contrat,
                c.date_debut::date,
                c.date_fin::date,
                fpl.region_id,
                fpl.departement_id,
                fpl.sous_prefecture_id,
                tr.nom as region_nom,
                td.nom as departement_nom,
                ts.nom as sous_prefecture_nom,
                fpp.projet_id as fpp_projet_id,
                p.id as projet_id,
                p.nom as projet_nom,
                p.nom_complet as projet_nom_complet
            FROM fic_personne_projet fpp
            INNER JOIN fic_personne fp ON fpp.fic_personne_id = fp.id
            LEFT JOIN contrat c ON fp.id = c.fic_personne_id
            LEFT JOIN fic_personne_localisation fpl ON c.id = fpl.contrat_id
            LEFT JOIN tregion tr ON fpl.region_id = tr.id
            LEFT JOIN tdepartement td ON fpl.departement_id = td.id
            LEFT JOIN tsousprefecture ts ON fpl.sous_prefecture_id = ts.id
            LEFT JOIN projet p ON fpp.projet_id = p.id
            WHERE fpp.acteur_id = :acteur_id
            ORDER BY fp.id, c.date_debut DESC
        """), {"acteur_id": acteur_id})
        
        rows = result.fetchall()
        logger.info(f"Nombre de lignes retournées: {len(rows)}")
        
        # Grouper les résultats par employé
        employees_dict = {}
        today = date.today()
        
        for row in rows:
            emp_id = row[0]
            
            if emp_id not in employees_dict:
                # Convertir les dates si elles sont des strings
                date_naissance = row[4]
                if isinstance(date_naissance, str):
                    try:
                        date_naissance = date.fromisoformat(date_naissance)
                    except:
                        date_naissance = None
                
                date_debut = row[15]
                if isinstance(date_debut, str):
                    try:
                        date_debut = date.fromisoformat(date_debut)
                    except:
                        date_debut = None
                
                date_fin = row[16]
                if isinstance(date_fin, str):
                    try:
                        date_fin = date.fromisoformat(date_fin)
                    except:
                        date_fin = None
                
                # Calculer l'âge
                age = 0
                if date_naissance:
                    age = today.year - date_naissance.year
                    if (today.month, today.day) < (date_naissance.month, date_naissance.day):
                        age -= 1
                
                # Déterminer si le contrat est actif
                is_active = False
                if date_debut:
                    is_active = (date_debut <= today and (date_fin is None or date_fin >= today))
                
                employees_dict[emp_id] = {
                    "id": row[0],
                    "nom": normalize_utf8(row[1]),
                    "prenom": normalize_utf8(row[2]),
                    "matricule": normalize_utf8(row[3] or "-"),
                    "date_naissance": date_naissance.isoformat() if date_naissance else None,
                    "genre": row[5] or "M",
                    "contact": normalize_utf8(row[6] or "-"),
                    "age": age,
                    "poste": normalize_utf8(row[8] if row[8] else "Non spécifié"),
                    "categorie_poste": normalize_utf8(row[9] if row[9] else "-"),
                    "qualification": normalize_utf8(row[10] if row[10] else "-"),
                    "type_personne": normalize_utf8(row[11] if row[11] else "-"),
                    "statut": normalize_utf8(row[11] if row[11] else "-"),
                    "diplome": normalize_utf8(row[12] if row[12] else "-"),
                    "ecole": normalize_utf8(row[13] if row[13] else "-"),
                    "type_contrat": normalize_utf8(row[14] if row[14] else "-"),
                    "date_debut": date_debut.isoformat() if date_debut else None,
                    "date_fin": date_fin.isoformat() if date_fin else None,
                    "validiteContrat": ("En cours" if is_active else "Expiré") if date_debut else "-",
                    "qualiteContrat": normalize_utf8(row[9] if row[9] else "-"),
                    "is_active": is_active,
                    "region": normalize_utf8(row[20] if row[20] else "-"),
                    "departement": normalize_utf8(row[21] if row[21] else "-"),
                    "sousPrefecture": normalize_utf8(row[22] if row[22] else "-"),
                    "projets": [],
                    "contrat_id": row[7],
                }
            
            # Ajouter le projet s'il existe
            # row[23] = fpp.projet_id, row[24] = p.id, row[25] = p.nom, row[26] = p.nom_complet
            if row[23] and row[24]:
                projet_exists = any(p["id"] == row[24] for p in employees_dict[emp_id]["projets"])
                if not projet_exists:
                    employees_dict[emp_id]["projets"].append({
                        "id": row[24],
                        "nom": row[25],
                        "nom_complet": row[26]
                    })
        
        employees = list(employees_dict.values())
        
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
