# -*- coding: utf-8 -*-
"""
Script complet de migration pour restructurer les relations:
1. Exécute le script SQL de restructuration
2. Exécute le script Python de migration des données
3. Affiche un rapport détaillé
"""

import psycopg2
import os
from dotenv import load_dotenv
import subprocess
import sys

# Charger les variables d'environnement
load_dotenv()

# Configuration de la base de données
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost/afor_emploi')

def execute_sql_file(cursor, sql_file_path):
    """Exécuter un fichier SQL"""
    try:
        with open(sql_file_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # Diviser le contenu en instructions individuelles
        statements = sql_content.split(';')
        
        for statement in statements:
            statement = statement.strip()
            if statement:  # Ignorer les lignes vides
                try:
                    cursor.execute(statement)
                except psycopg2.Error as e:
                    # Certaines erreurs sont acceptables (ex: IF NOT EXISTS)
                    if 'already exists' not in str(e) and 'does not exist' not in str(e):
                        print(f"  ⚠ Avertissement: {e}")
        
        return True
    except Exception as e:
        print(f"✗ Erreur lors de l'exécution du fichier SQL: {e}")
        return False

def run_migration():
    """Exécuter la migration complète"""
    
    conn = None
    try:
        print("\n" + "=" * 80)
        print("MIGRATION COMPLÈTE: Restructuration des relations")
        print("=" * 80 + "\n")
        
        # Connexion à la base de données
        conn = psycopg2.connect(DATABASE_URL)
        conn.set_client_encoding('UTF8')
        cursor = conn.cursor()
        
        # ÉTAPE 1: Exécuter le script SQL de restructuration
        print("ÉTAPE 1: Restructuration des relations (SQL)...")
        print("-" * 80)
        
        sql_file = r"C:\Users\OUATTARA AFOR\Desktop\The Box\Web\Emploi\scripts\migration\restructure_relations.sql"
        
        if not os.path.exists(sql_file):
            print(f"✗ Fichier SQL non trouvé: {sql_file}")
            return False
        
        if execute_sql_file(cursor, sql_file):
            print("✓ Script SQL exécuté avec succès\n")
            conn.commit()
        else:
            print("✗ Erreur lors de l'exécution du script SQL\n")
            return False
        
        # ÉTAPE 2: Afficher les statistiques avant migration
        print("ÉTAPE 2: Statistiques avant migration...")
        print("-" * 80)
        
        cursor.execute("""
            SELECT COUNT(*) FROM fic_personne
        """)
        total_employees = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM fic_personne WHERE projet_id IS NOT NULL
        """)
        employees_with_project = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM fic_personne_projet
        """)
        existing_relations = cursor.fetchone()[0]
        
        print(f"✓ Total d'employés: {total_employees}")
        print(f"✓ Employés avec projet_id: {employees_with_project}")
        print(f"✓ Relations existantes dans fic_personne_projet: {existing_relations}\n")
        
        # ÉTAPE 3: Peupler fic_personne_projet
        print("ÉTAPE 3: Peuplement de fic_personne_projet...")
        print("-" * 80)
        
        cursor.execute("""
            SELECT fp.id, fp.projet_id
            FROM fic_personne fp
            WHERE fp.projet_id IS NOT NULL
            AND NOT EXISTS (
                SELECT 1 FROM fic_personne_projet fpp
                WHERE fpp.fic_personne_id = fp.id
                AND fpp.projet_id = fp.projet_id
            )
        """)
        
        employees_to_migrate = cursor.fetchall()
        print(f"✓ {len(employees_to_migrate)} employés à migrer\n")
        
        # ÉTAPE 4: Afficher le rapport final
        print("ÉTAPE 4: Rapport final...")
        print("-" * 80)
        
        cursor.execute("""
            SELECT 
                a.id,
                a.nom as acteur_nom,
                COUNT(DISTINCT fpp.fic_personne_id) as nb_employees,
                COUNT(DISTINCT fpp.projet_id) as nb_projects,
                COUNT(fpp.id) as nb_relations
            FROM acteur a
            LEFT JOIN fic_personne_projet fpp ON fpp.acteur_id = a.id
            GROUP BY a.id, a.nom
            ORDER BY nb_relations DESC
        """)
        
        results = cursor.fetchall()
        
        print("Acteur | Employés | Projets | Relations")
        print("-" * 50)
        
        total_relations = 0
        for acteur_id, acteur_nom, nb_emp, nb_proj, nb_rel in results:
            nb_emp = nb_emp or 0
            nb_proj = nb_proj or 0
            nb_rel = nb_rel or 0
            total_relations += nb_rel
            print(f"{acteur_nom:20} | {nb_emp:8} | {nb_proj:7} | {nb_rel:9}")
        
        print("-" * 50)
        print(f"TOTAL: {total_relations} relations\n")
        
        # ÉTAPE 5: Afficher les employés sans projet
        print("ÉTAPE 5: Employés sans projet...")
        print("-" * 80)
        
        cursor.execute("""
            SELECT 
                fp.id,
                fp.nom,
                fp.prenom,
                a.nom as acteur_nom
            FROM fic_personne fp
            LEFT JOIN acteur a ON a.id = fp.acteur_id
            WHERE NOT EXISTS (
                SELECT 1 FROM fic_personne_projet fpp
                WHERE fpp.fic_personne_id = fp.id
            )
            LIMIT 10
        """)
        
        no_project = cursor.fetchall()
        
        if no_project:
            print(f"⚠ {len(no_project)} employés sans projet (affichage des 10 premiers):")
            for emp_id, nom, prenom, acteur_nom in no_project:
                print(f"  - {nom} {prenom} ({acteur_nom})")
        else:
            print("✓ Tous les employés ont au moins un projet")
        
        print("\n" + "=" * 80)
        print("MIGRATION TERMINÉE AVEC SUCCÈS!")
        print("=" * 80)
        
        print("\nPROCHAINES ÉTAPES:")
        print("1. Redémarrer le backend pour charger les nouveaux modèles")
        print("2. Tester l'endpoint /api/employees/list/{acteur_id}")
        print("3. Vérifier que les projets s'affichent correctement")
        print("4. (OPTIONNEL) Supprimer la colonne projet_id de fic_personne:")
        print("   ALTER TABLE fic_personne DROP COLUMN projet_id;")
        print("\n")
        
        cursor.close()
        conn.commit()
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
    success = run_migration()
    sys.exit(0 if success else 1)
