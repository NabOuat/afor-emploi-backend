# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import date
from typing import Optional
from app.database import get_db
from app.models import FicPersonne, FicPersonneProjet, Projet, Acteur, Contrat, FicPersonneLocalisation
from app.utils.logger import app_logger, log_employee_creation, log_db_operation, log_error
import uuid
router = APIRouter(prefix="/api/employees", tags=["employees"])

class ProjetSelection(BaseModel):
    projet_id: str
    engagement_id: Optional[str] = None

class CreateEmployeeRequest(BaseModel):
    nom: str
    prenom: str
    date_naissance: Optional[date] = None
    genre: str = "M"
    contact: Optional[str] = None
    matricule: Optional[str] = None
    diplome: Optional[str] = None
    type_personne: Optional[str] = None
    poste_nom: Optional[str] = None
    categorie_poste: Optional[str] = None
    type_contrat: Optional[str] = None
    poste: Optional[str] = None
    ecole: Optional[str] = None
    date_debut: Optional[date] = None
    date_fin: Optional[date] = None
    region_id: Optional[str] = None
    departement_id: Optional[str] = None
    sous_prefecture_id: Optional[str] = None
    projets: list[ProjetSelection] = []
    projet_id: Optional[str] = None
    engagement_id: Optional[str] = None
    created_by: Optional[str] = None

class CreateEmployeeResponse(BaseModel):
    id: str
    nom: str
    prenom: str
    message: str

@router.post("/create", response_model=CreateEmployeeResponse)
async def create_employee(request: CreateEmployeeRequest, acteur_id: str, db: Session = Depends(get_db)):
    """Créer un nouvel employé avec sélection de projets et informations de contrat"""
    
    try:
        # LOG: Données reçues
        employee_data_dict = request.dict()
        app_logger.info(f"🔍 DONNÉES REÇUES PAR LE BACKEND:")
        app_logger.info(f"  - poste_nom: {request.poste_nom}")
        app_logger.info(f"  - categorie_poste: {request.categorie_poste}")
        app_logger.info(f"  - poste (qualification): {request.poste}")
        app_logger.info(f"  - ecole: {request.ecole}")
        log_employee_creation(employee_data_dict, acteur_id)
        
        # Vérifier que l'acteur existe
        acteur = db.query(Acteur).filter(Acteur.id == acteur_id).first()
        if not acteur:
            raise HTTPException(status_code=404, detail="Acteur non trouvé")
        
        # Vérifier qu'au moins un projet est sélectionné
        if not request.projets or len(request.projets) == 0:
            raise HTTPException(status_code=400, detail="Au moins un projet doit être sélectionné")
        
        # Créer le nouvel employé dans fic_personne (SEULEMENT les colonnes qui existent)
        employee_id = str(uuid.uuid4())
        new_employee = FicPersonne(
            id=employee_id,
            nom=request.nom,
            prenom=request.prenom,
            date_naissance=request.date_naissance,
            genre=request.genre,
            contact=request.contact,
            matricule=request.matricule,
            created_by=request.created_by
        )
        
        log_db_operation("INSERT", "fic_personne", {
            "id": employee_id,
            "nom": request.nom,
            "prenom": request.prenom,
            "matricule": request.matricule
        })
        
        db.add(new_employee)
        db.flush()
        
        # Créer le contrat associé si des informations sont fournies
        contrat_id = None
        effective_poste_nom = request.poste_nom or request.poste
        if effective_poste_nom and request.date_debut:
            contrat_id = str(uuid.uuid4())
            new_contrat = Contrat(
                id=contrat_id,
                fic_personne_id=employee_id,
                projet_id=request.projet_id,
                engagement_id=request.engagement_id,
                poste_nom=effective_poste_nom,
                categorie_poste=request.categorie_poste,
                type_contrat=request.type_contrat,
                type_personne=request.type_personne,
                poste=request.poste,
                date_debut=request.date_debut,
                date_fin=request.date_fin,
                diplome=request.diplome,
                ecole=request.ecole
            )
            
            log_db_operation("INSERT", "contrat", {
                "id": contrat_id,
                "fic_personne_id": employee_id,
                "poste_nom": request.poste_nom,
                "type_contrat": request.type_contrat,
                "ecole": request.ecole
            })
            
            app_logger.info(f"🔍 AVANT INSERTION DANS LA BD:")
            app_logger.info(f"  - new_contrat.poste_nom: {new_contrat.poste_nom}")
            app_logger.info(f"  - new_contrat.categorie_poste: {new_contrat.categorie_poste}")
            app_logger.info(f"  - new_contrat.poste: {new_contrat.poste}")
            app_logger.info(f"  - new_contrat.ecole: {new_contrat.ecole}")
            
            db.add(new_contrat)
            db.flush()
            
            app_logger.info(f"🔍 APRÈS FLUSH (ce qui sera dans la BD):")
            app_logger.info(f"  - new_contrat.poste_nom: {new_contrat.poste_nom}")
            app_logger.info(f"  - new_contrat.categorie_poste: {new_contrat.categorie_poste}")
            app_logger.info(f"  - new_contrat.poste: {new_contrat.poste}")
            app_logger.info(f"  - new_contrat.ecole: {new_contrat.ecole}")
        
        # Créer la localisation si le contrat existe et des infos de localisation sont fournies
        if contrat_id and (request.region_id or request.departement_id or request.sous_prefecture_id):
            localisation_id = str(uuid.uuid4())
            new_localisation = FicPersonneLocalisation(
                id=localisation_id,
                contrat_id=contrat_id,
                region_id=request.region_id,
                departement_id=request.departement_id,
                sous_prefecture_id=request.sous_prefecture_id,
                date_debut=request.date_debut
            )
            
            log_db_operation("INSERT", "fic_personne_localisation", {
                "id": localisation_id,
                "contrat_id": contrat_id,
                "region_id": request.region_id,
                "departement_id": request.departement_id,
                "sous_prefecture_id": request.sous_prefecture_id
            })
            
            db.add(new_localisation)
        
        # Ajouter les projets sélectionnés via fic_personne_projet
        for projet_sel in request.projets:
            # Vérifier que le projet existe
            projet = db.query(Projet).filter(Projet.id == projet_sel.projet_id).first()
            if not projet:
                app_logger.warning(f"Projet {projet_sel.projet_id} non trouvé")
                continue
            
            # Créer la relation fic_personne_projet
            relation_id = str(uuid.uuid4())
            relation = FicPersonneProjet(
                id=relation_id,
                fic_personne_id=employee_id,
                projet_id=projet_sel.projet_id,
                acteur_id=acteur_id
            )
            
            log_db_operation("INSERT", "fic_personne_projet", {
                "id": relation_id,
                "fic_personne_id": employee_id,
                "projet_id": projet_sel.projet_id,
                "acteur_id": acteur_id
            })
            
            db.add(relation)
        
        db.commit()
        
        app_logger.info(f"✅ Employé {request.nom} {request.prenom} créé avec succès (ID: {employee_id})")
        
        return CreateEmployeeResponse(
            id=employee_id,
            nom=request.nom,
            prenom=request.prenom,
            message=f"Employé {request.nom} {request.prenom} créé avec succès"
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        log_error("CREATION_EMPLOYEE", str(e), {"acteur_id": acteur_id, "nom": request.nom})
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/projects")
async def get_projects(acteur_id: str, db: Session = Depends(get_db)):
    """Récupérer la liste des projets disponibles pour un acteur"""
    
    try:
        # Récupérer les projets associés à cet acteur
        projets = db.query(Projet).join(
            FicPersonneProjet, Projet.id == FicPersonneProjet.projet_id
        ).filter(
            FicPersonneProjet.acteur_id == acteur_id
        ).distinct().all()
        
        result = []
        for projet in projets:
            result.append({
                "id": projet.id,
                "nom": projet.nom,
                "nom_complet": projet.nom_complet
            })
        
        return result
    except Exception as e:
        app_logger.error(f"Erreur lors de la récupération des projets: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/update/{employee_id}")
async def update_employee(employee_id: str, request: CreateEmployeeRequest, db: Session = Depends(get_db)):
    """Mettre à jour un employé existant"""
    
    try:
        # Vérifier que l'employé existe
        employee = db.query(FicPersonne).filter(FicPersonne.id == employee_id).first()
        if not employee:
            raise HTTPException(status_code=404, detail="Employé non trouvé")
        
        # Mettre à jour les informations de base dans fic_personne
        employee.nom = request.nom
        employee.prenom = request.prenom
        employee.date_naissance = request.date_naissance
        employee.genre = request.genre
        employee.contact = request.contact
        employee.matricule = request.matricule
        
        # Mettre à jour le contrat
        contrat = db.query(Contrat).filter(Contrat.fic_personne_id == employee_id).first()
        effective_poste_nom = request.poste_nom or request.poste
        if contrat:
            contrat.poste_nom = effective_poste_nom or contrat.poste_nom
            contrat.categorie_poste = request.categorie_poste
            contrat.type_contrat = request.type_contrat
            contrat.type_personne = request.type_personne
            contrat.poste = request.poste
            contrat.date_debut = request.date_debut or contrat.date_debut
            contrat.date_fin = request.date_fin
            contrat.diplome = request.diplome
            contrat.ecole = [request.ecole] if request.ecole else None
        else:
            # Créer un nouveau contrat si aucun n'existe
            if effective_poste_nom and request.date_debut:
                contrat_id = str(uuid.uuid4())
                new_contrat = Contrat(
                    id=contrat_id,
                    fic_personne_id=employee_id,
                    poste_nom=effective_poste_nom,
                    categorie_poste=request.categorie_poste,
                    type_contrat=request.type_contrat,
                    type_personne=request.type_personne,
                    poste=request.poste,
                    date_debut=request.date_debut,
                    date_fin=request.date_fin,
                    diplome=request.diplome,
                    ecole=request.ecole
                )
                db.add(new_contrat)
                db.flush()
                contrat = new_contrat
        
        # Mettre à jour la localisation si elle existe
        if contrat and (request.region_id or request.departement_id or request.sous_prefecture_id):
            localisation = db.query(FicPersonneLocalisation).filter(
                FicPersonneLocalisation.contrat_id == contrat.id
            ).first()
            
            if localisation:
                localisation.region_id = request.region_id
                localisation.departement_id = request.departement_id
                localisation.sous_prefecture_id = request.sous_prefecture_id
                localisation.date_debut = request.date_debut
            else:
                # Créer une nouvelle localisation
                localisation_id = str(uuid.uuid4())
                new_localisation = FicPersonneLocalisation(
                    id=localisation_id,
                    contrat_id=contrat.id,
                    region_id=request.region_id,
                    departement_id=request.departement_id,
                    sous_prefecture_id=request.sous_prefecture_id,
                    date_debut=request.date_debut
                )
                db.add(new_localisation)
        
        db.commit()
        db.refresh(employee)
        
        app_logger.info(f"Employé mis à jour: {employee.nom} {employee.prenom}")
        
        return {
            "id": employee_id,
            "nom": request.nom,
            "prenom": request.prenom,
            "message": "Employé mis à jour avec succès"
        }
        
    except Exception as e:
        db.rollback()
        app_logger.error(f"Erreur lors de la mise à jour de l'employé: {e}")
        raise HTTPException(status_code=500, detail=str(e))
