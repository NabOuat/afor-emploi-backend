# -*- coding: utf-8 -*-
"""
Système de logging centralisé pour l'application AFOR Emploi
Enregistre toutes les activités backend dans backend.log
"""

import logging
from logging.handlers import RotatingFileHandler
import os
from datetime import datetime
import json

# Créer le dossier logs s'il n'existe pas
LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
os.makedirs(LOGS_DIR, exist_ok=True)

# Chemin du fichier de log
BACKEND_LOG_FILE = os.path.join(LOGS_DIR, 'backend.log')

# Configuration du logger
def setup_logger(name='afor_emploi'):
    """Configure et retourne un logger avec rotation de fichiers"""
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Éviter les doublons de handlers
    if logger.handlers:
        return logger
    
    # Format détaillé pour les logs
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler pour fichier avec rotation (max 10MB, 5 fichiers)
    file_handler = RotatingFileHandler(
        BACKEND_LOG_FILE,
        maxBytes=10*1024*1024,  # 10 MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    # Handler pour console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# Logger principal
app_logger = setup_logger()

def log_api_request(endpoint: str, method: str, params: dict = None, body: dict = None):
    """Log une requête API entrante"""
    app_logger.info(f"{'='*80}")
    app_logger.info(f"📥 REQUÊTE API: {method} {endpoint}")
    if params:
        app_logger.info(f"   Paramètres: {json.dumps(params, ensure_ascii=False, default=str)}")
    if body:
        app_logger.info(f"   Body: {json.dumps(body, ensure_ascii=False, default=str)}")
    app_logger.info(f"{'='*80}")

def log_api_response(endpoint: str, status_code: int, response_data: dict = None):
    """Log une réponse API sortante"""
    app_logger.info(f"📤 RÉPONSE API: {endpoint} - Status {status_code}")
    if response_data:
        app_logger.debug(f"   Data: {json.dumps(response_data, ensure_ascii=False, default=str)}")

def log_db_operation(operation: str, table: str, data: dict = None, result: str = None):
    """Log une opération sur la base de données"""
    app_logger.info(f"💾 OPÉRATION BD: {operation} sur {table}")
    if data:
        app_logger.debug(f"   Données: {json.dumps(data, ensure_ascii=False, default=str)}")
    if result:
        app_logger.info(f"   Résultat: {result}")

def log_employee_creation(employee_data: dict, acteur_id: str):
    """Log spécifique pour la création d'employé"""
    app_logger.info(f"{'='*80}")
    app_logger.info(f"👤 CRÉATION D'EMPLOYÉ")
    app_logger.info(f"{'='*80}")
    app_logger.info(f"Acteur ID: {acteur_id}")
    app_logger.info(f"\n🔵 INFORMATIONS PERSONNELLES (→ fic_personne):")
    app_logger.info(f"  - nom: {employee_data.get('nom')}")
    app_logger.info(f"  - prenom: {employee_data.get('prenom')}")
    app_logger.info(f"  - date_naissance: {employee_data.get('date_naissance')}")
    app_logger.info(f"  - genre: {employee_data.get('genre')}")
    app_logger.info(f"  - contact: {employee_data.get('contact')}")
    app_logger.info(f"  - matricule: {employee_data.get('matricule')}")
    app_logger.info(f"\n🟢 INFORMATIONS DE CONTRAT (→ contrat):")
    app_logger.info(f"  - type_personne: {employee_data.get('type_personne')}")
    app_logger.info(f"  - diplome: {employee_data.get('diplome')}")
    app_logger.info(f"  - ecole: {employee_data.get('ecole')}")
    app_logger.info(f"  - date_debut: {employee_data.get('date_debut')}")
    app_logger.info(f"  - date_fin: {employee_data.get('date_fin')}")
    app_logger.info(f"  - poste_nom: {employee_data.get('poste_nom')}")
    app_logger.info(f"  - categorie_poste: {employee_data.get('categorie_poste')}")
    app_logger.info(f"  - poste (qualification): {employee_data.get('poste')}")
    app_logger.info(f"  - type_contrat: {employee_data.get('type_contrat')}")
    app_logger.info(f"\n🟡 LOCALISATION (→ fic_personne_localisation):")
    app_logger.info(f"  - region_id: {employee_data.get('region_id')}")
    app_logger.info(f"  - departement_id: {employee_data.get('departement_id')}")
    app_logger.info(f"  - sous_prefecture_id: {employee_data.get('sous_prefecture_id')}")
    app_logger.info(f"\n🔴 PROJETS (→ fic_personne_projet):")
    projets = employee_data.get('projets', [])
    app_logger.info(f"  - Nombre de projets: {len(projets)}")
    for i, p in enumerate(projets):
        app_logger.info(f"  - Projet {i+1}: {p.get('projet_id')}")
    app_logger.info(f"{'='*80}")

def log_error(error_type: str, error_message: str, context: dict = None):
    """Log une erreur"""
    app_logger.error(f"❌ ERREUR: {error_type}")
    app_logger.error(f"   Message: {error_message}")
    if context:
        app_logger.error(f"   Contexte: {json.dumps(context, ensure_ascii=False, default=str)}")
