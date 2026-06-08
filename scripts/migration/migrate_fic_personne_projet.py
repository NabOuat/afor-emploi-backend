# -*- coding: utf-8 -*-
"""
Script de migration pour:
1. Peupler la table fic_personne_projet avec les données existantes
2. Restructurer la relation acteur -> fic_personne -> projet en acteur -> fic_personne et fic_personne -> projet (many-to-many)
3. Supprimer la colonne projet_id de fic_personne (optionnel)
"""

import psycopg2
from psycopg2.extras import execute_values
import os
from dotenv import load_dotenv
import uuid

# Charger les variables d'environnement
load_dotenv()

# Configuration de la base de données
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost/afor_emploi')

def migrate_data():
    """Migrer les données et restructurer les relations"""
    
    conn = None
    try:
        # Connexion à la base de données
        conn = psycopg2.connect(DATABASE_URL)
        conn.set_client_encoding('UTF8')
        cursor = conn.cursor()
        
        print("=" * 80)
        print("MIGRATION: Restructuration des relations acteur -> fic_personne -> projet")
        print("=" * 80 + "\n")
        
        # Étape 1: Vérifier si la table fic_personne_projet existe
        print("Étape 1: Vérification de la table fic_personne_projet...")
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_name = 'fic_personne_projet'
            )
        """)
        table_exists = cursor.fetchone()[0]
        
        if not table_exists:
            print("✗ La table fic_personne_projet n'existe pas!")
            print("  Exécutez d'abord le script SQL: scripts/migration/add_fic_personne_projet_table.sql")
            return False
        
        print("✓ Table fic_personne_projet trouvée\n")
        
        # Étape 2: Récupérer tous les employés avec leur projet
        print("Étape 2: Récupération des employés et leurs projets...")
        cursor.execute("""
            SELECT fp.id, fp.projet_id, fp.acteur_id
            FROM fic_personne fp
            WHERE fp.projet_id IS NOT NULL
            ORDER BY fp.id
        """)
        
        employees = cursor.fetchall()
        print(f"✓ {len(employees)} employés trouvés avec un projet\n")
        
        # Étape 3: Peupler la table fic_personne_projet
        print("Étape 3: Peuplement de la table fic_personne_projet...")
        
        inserted_count = 0
        skipped_count = 0
        
        for fic_personne_id, projet_id, acteur_id in employees:
            try:
                # Vérifier si l'entrée existe déjà
                cursor.execute("""
                    SELECT id FROM fic_personne_projet
                    WHERE fic_personne_id = %s AND projet_id = %s
                """, (fic_personne_id, projet_id))
                
                if cursor.fetchone():
                    skipped_count += 1
                    continue
                
                # Insérer la nouvelle entrée
                new_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO fic_personne_projet (id, fic_personne_id, projet_id, date_debut, date_fin)
                    VALUES (%s, %s, %s, NULL, NULL)
                """, (new_id, fic_personne_id, projet_id))
                
                inserted_count += 1
                
            except Exception as e:
                print(f"  ✗ Erreur pour employé {fic_personne_id}: {e}")
                continue
        
        print(f"✓ {inserted_count} entrées insérées")
        print(f"✓ {skipped_count} entrées déjà existantes\n")
        
        # Étape 4: Vérifier les employés sans projet
        print("Étape 4: Vérification des employés sans projet...")
        cursor.execute("""
            SELECT COUNT(*) FROM fic_personne
            WHERE projet_id IS NULL
        """)
        
        no_project_count = cursor.fetchone()[0]
        print(f"⚠ {no_project_count} employés sans projet (projet_id = NULL)\n")
        
        # Étape 5: Afficher les statistiques
        print("Étape 5: Statistiques finales...")
        cursor.execute("""
            SELECT COUNT(*) FROM fic_personne_projet
        """)
        total_relations = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(DISTINCT fic_personne_id) FROM fic_personne_projet
        """)
        employees_with_projects = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(DISTINCT projet_id) FROM fic_personne_projet
        """)
        projects_with_employees = cursor.fetchone()[0]
        
        print(f"✓ Total de relations fic_personne -> projet: {total_relations}")
        print(f"✓ Employés avec au moins un projet: {employees_with_projects}")
        print(f"✓ Projets avec au moins un employé: {projects_with_employees}\n")
        
        # Étape 6: Afficher les relations par acteur
        print("Étape 6: Relations par acteur...")
        cursor.execute("""
            SELECT 
                a.id,
                a.nom,
                COUNT(DISTINCT fpp.fic_personne_id) as nb_employees,
                COUNT(DISTINCT fpp.projet_id) as nb_projects
            FROM acteur a
            LEFT JOIN fic_personne fp ON fp.acteur_id = a.id
            LEFT JOIN fic_personne_projet fpp ON fpp.fic_personne_id = fp.id
            GROUP BY a.id, a.nom
            ORDER BY nb_employees DESC
        """)
        
        acteurs = cursor.fetchall()
        for acteur_id, acteur_nom, nb_emp, nb_proj in acteurs:
            print(f"  {acteur_nom}: {nb_emp} employés, {nb_proj} projets")
        
        print("\n" + "=" * 80)
        print("MIGRATION RÉUSSIE!")
        print("=" * 80)
        
        # Commit les changements
        conn.commit()
        
        # Étape 7: Recommandations
        print("\nRECOMMANDATIONS:")
        print("1. ✓ La table fic_personne_projet est maintenant peuplée")
        print("2. ✓ Les relations acteur -> fic_personne sont conservées")
        print("3. ✓ Les relations fic_personne -> projet sont maintenant many-to-many")
        print("\nOPTIONNEL (si vous voulez nettoyer):")
        print("4. Vous pouvez supprimer la colonne projet_id de fic_personne:")
        print("   ALTER TABLE fic_personne DROP COLUMN projet_id;")
        print("\n")
        
        cursor.close()
        return True
        
    except Exception as e:
        print(f"\n✗ ERREUR: {e}")
        if conn:
            conn.rollback()
        return False
        
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    success = migrate_data()
    exit(0 if success else 1)
