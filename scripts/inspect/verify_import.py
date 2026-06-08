#!/usr/bin/env python
"""
Script de vérification des données importées
Affiche des statistiques et des exemples de données
"""

import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'database'))
from db import Database

load_dotenv()

def print_section(title):
    """Afficher un titre de section"""
    print("\n" + "="*60)
    print(title)
    print("="*60)

def verify_database():
    """Vérifier la base de données et afficher les statistiques"""
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL non définie dans .env")
        return False
    
    db = Database(database_url)
    
    if not db.connect():
        print("❌ Impossible de se connecter à la base de données")
        return False
    
    print_section("VÉRIFICATION DE LA BASE DE DONNÉES")
    
    try:
        # 1. Vérifier les acteurs
        print("\n📊 ACTEURS")
        acteur_count = db.fetch_one("SELECT COUNT(*) FROM acteur")[0]
        print(f"   Total: {acteur_count}")
        
        acteurs_by_type = db.fetch_all("""
            SELECT type_acteur, COUNT(*) as count 
            FROM acteur 
            GROUP BY type_acteur
        """)
        for type_acteur, count in acteurs_by_type:
            print(f"   - {type_acteur}: {count}")
        
        # 2. Vérifier les projets
        print("\n📊 PROJETS")
        projet_count = db.fetch_one("SELECT COUNT(*) FROM projet")[0]
        print(f"   Total: {projet_count}")
        
        projets = db.fetch_all("SELECT id, nom FROM projet LIMIT 5")
        for projet_id, nom in projets:
            print(f"   - {projet_id}: {nom}")
        
        # 3. Vérifier les zones d'intervention
        print("\n📊 ZONES D'INTERVENTION")
        zone_count = db.fetch_one("SELECT COUNT(*) FROM zone_d_intervention")[0]
        print(f"   Total: {zone_count}")
        
        # 4. Vérifier fic_personne
        print("\n📊 FIC_PERSONNE")
        fic_count = db.fetch_one("SELECT COUNT(*) FROM fic_personne")[0]
        print(f"   Total: {fic_count}")
        
        # Statistiques par acteur
        fic_by_acteur = db.fetch_all("""
            SELECT acteur_id, COUNT(*) as count 
            FROM fic_personne 
            GROUP BY acteur_id 
            ORDER BY count DESC 
            LIMIT 10
        """)
        print("\n   Top 10 acteurs par nombre de personnes:")
        for acteur_id, count in fic_by_acteur:
            acteur = db.get_acteur(acteur_id)
            if acteur:
                print(f"   - {acteur[1]}: {count}")
            else:
                print(f"   - {acteur_id}: {count}")
        
        # Statistiques par projet
        fic_by_projet = db.fetch_all("""
            SELECT projet_id, COUNT(*) as count 
            FROM fic_personne 
            GROUP BY projet_id 
            ORDER BY count DESC
        """)
        print("\n   Personnes par projet:")
        for projet_id, count in fic_by_projet:
            projet = db.get_projet(projet_id)
            if projet:
                print(f"   - {projet[1]}: {count}")
            else:
                print(f"   - {projet_id}: {count}")
        
        # 5. Exemples de données
        print("\n📋 EXEMPLES DE DONNÉES (5 premiers enregistrements)")
        examples = db.fetch_all("""
            SELECT id, nom, prenom, genre, date_naissance, contact 
            FROM fic_personne 
            LIMIT 5
        """)
        for i, (fic_id, nom, prenom, genre, date_naissance, contact) in enumerate(examples, 1):
            print(f"\n   {i}. {nom} {prenom}")
            print(f"      ID: {fic_id}")
            print(f"      Genre: {genre}")
            print(f"      Date de naissance: {date_naissance}")
            print(f"      Contact: {contact}")
        
        # 6. Vérifier les valeurs NULL
        print("\n⚠️  VÉRIFICATION DES VALEURS NULL")
        null_checks = db.fetch_all("""
            SELECT 
                COUNT(CASE WHEN acteur_id IS NULL THEN 1 END) as null_acteur_id,
                COUNT(CASE WHEN projet_id IS NULL THEN 1 END) as null_projet_id,
                COUNT(CASE WHEN nom IS NULL THEN 1 END) as null_nom,
                COUNT(CASE WHEN prenom IS NULL THEN 1 END) as null_prenom
            FROM fic_personne
        """)[0]
        
        print(f"   Valeurs NULL acteur_id: {null_checks[0]}")
        print(f"   Valeurs NULL projet_id: {null_checks[1]}")
        print(f"   Valeurs NULL nom: {null_checks[2]}")
        print(f"   Valeurs NULL prenom: {null_checks[3]}")
        
        # 7. Vérifier les contraintes de clés étrangères
        print("\n🔗 VÉRIFICATION DES CLÉS ÉTRANGÈRES")
        
        # Acteurs orphelins
        orphan_acteurs = db.fetch_all("""
            SELECT DISTINCT fp.acteur_id 
            FROM fic_personne fp 
            LEFT JOIN acteur a ON fp.acteur_id = a.id 
            WHERE a.id IS NULL AND fp.acteur_id IS NOT NULL
        """)
        if orphan_acteurs:
            print(f"   ⚠️  Acteurs orphelins trouvés: {len(orphan_acteurs)}")
            for (acteur_id,) in orphan_acteurs[:5]:
                print(f"      - {acteur_id}")
        else:
            print("   ✓ Aucun acteur orphelin")
        
        # Projets orphelins
        orphan_projets = db.fetch_all("""
            SELECT DISTINCT fp.projet_id 
            FROM fic_personne fp 
            LEFT JOIN projet p ON fp.projet_id = p.id 
            WHERE p.id IS NULL AND fp.projet_id IS NOT NULL
        """)
        if orphan_projets:
            print(f"   ⚠️  Projets orphelins trouvés: {len(orphan_projets)}")
            for (projet_id,) in orphan_projets[:5]:
                print(f"      - {projet_id}")
        else:
            print("   ✓ Aucun projet orphelin")
        
        print_section("VÉRIFICATION TERMINÉE")
        print("✅ Toutes les vérifications sont terminées")
        
        db.disconnect()
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {str(e)}")
        db.disconnect()
        return False

if __name__ == '__main__':
    verify_database()
