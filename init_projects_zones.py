#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script pour initialiser les projets et zones d'intervention
"""
import os
import sys
import uuid
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Projet, ZoneDIntervention, TRegion

load_dotenv()

def init_projects_zones():
    """Initialiser les projets et zones d'intervention"""
    
    db = SessionLocal()
    
    try:
        print("📝 Initialisation des projets et zones d'intervention...\n")
        
        # Créer les projets manquants
        print("1️⃣  Création des projets...")
        
        projets_data = [
            {"id": "HP", "nom": "HP", "nom_complet": "Haut Potentiel"},
            {"id": "PRESFOR", "nom": "PRESFOR", "nom_complet": "Programme d'Emploi et de Stabilisation de la Forêt"},
        ]
        
        for proj_data in projets_data:
            existing = db.query(Projet).filter(Projet.id == proj_data["id"]).first()
            if existing:
                print(f"   ⚠️  Projet '{proj_data['id']}' existe déjà")
            else:
                projet = Projet(
                    id=proj_data["id"],
                    nom=proj_data["nom"],
                    nom_complet=proj_data["nom_complet"],
                    date_creation=None
                )
                db.add(projet)
                db.commit()
                print(f"   ✅ Projet créé: {proj_data['id']}")
        
        # Récupérer les régions
        print("\n2️⃣  Récupération des régions...")
        regions = db.query(TRegion).all()
        print(f"   ✅ {len(regions)} régions trouvées")
        
        if not regions:
            print("   ⚠️  Aucune région trouvée. Créez d'abord les régions.")
            return
        
        # Créer des zones d'intervention pour l'acteur TEST
        print("\n3️⃣  Création des zones d'intervention pour TEST...")
        
        acteur_id = "TEST"
        zone_count = 0
        
        for projet_id in ["HP", "PRESFOR"]:
            for region in regions:
                # Vérifier si la zone existe
                existing_zone = db.query(ZoneDIntervention).filter(
                    ZoneDIntervention.acteur_id == acteur_id,
                    ZoneDIntervention.projet_id == projet_id,
                    ZoneDIntervention.region_id == region.id
                ).first()
                
                if not existing_zone:
                    zone = ZoneDIntervention(
                        id=str(uuid.uuid4()),
                        acteur_id=acteur_id,
                        projet_id=projet_id,
                        region_id=region.id,
                        departement_id=None,
                        sous_prefecture_id=None
                    )
                    db.add(zone)
                    zone_count += 1
        
        if zone_count > 0:
            db.commit()
            print(f"   ✅ {zone_count} zones créées pour TEST")
        else:
            print("   ⚠️  Aucune nouvelle zone créée")
        
        print("\n" + "="*60)
        print("✓ Initialisation terminée!")
        print("="*60)
        
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_projects_zones()
