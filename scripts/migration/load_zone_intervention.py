#!/usr/bin/env python3
"""
Script pour charger les données de zone_d_intervention depuis un fichier CSV
dans la base de données PostgreSQL.
"""

import csv
import psycopg2
from psycopg2.extras import execute_values
import os
from pathlib import Path

# Configuration de la base de données
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'emploi',
    'user': 'postgres',
    'password': 'postgres'  # À remplacer par le mot de passe réel
}

# Chemin du fichier CSV
CSV_FILE_PATH = Path(__file__).parent / "zoned'interv.csv"

def load_zone_intervention_data():
    """
    Charge les données du fichier CSV dans la table zone_d_intervention.
    """
    # Lire le fichier CSV avec gestion d'encodage
    data_rows = []
    encoding_used = None
    
    # Essayer différents encodages
    for encoding in ['latin-1', 'iso-8859-1', 'cp1252', 'utf-8']:
        try:
            with open(CSV_FILE_PATH, 'r', encoding=encoding) as csvfile:
                encoding_used = encoding
                print(f"✓ Fichier CSV lu avec l'encodage: {encoding}")
                csv_reader = csv.reader(csvfile)
                for row in csv_reader:
                    if len(row) >= 6:
                        # Extraire les colonnes
                        id_val = row[0].strip()
                        acteur_id = row[1].strip()
                        projet_id = row[2].strip()
                        region_id = row[3].strip() if row[3].strip() else None
                        departement_id = row[4].strip() if row[4].strip() else None
                        sous_prefecture_id = row[5].strip() if row[5].strip() else None
                        
                        data_rows.append((
                            id_val,
                            acteur_id,
                            projet_id,
                            region_id,
                            departement_id,
                            sous_prefecture_id
                        ))
            break
        except (UnicodeDecodeError, UnicodeError):
            continue
    
    if not encoding_used:
        print("✗ Erreur: Impossible de lire le fichier CSV avec les encodages disponibles")
        return False
    
    print(f"✓ {len(data_rows)} lignes lues depuis le fichier CSV")
    
    # Les données sont déjà en format correct (Latin-1 lues correctement)
    # PostgreSQL gérera l'encodage automatiquement
    cleaned_data_rows = data_rows
    
    try:
        # Connexion à la base de données
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print(f"✓ Connexion établie à la base de données '{DB_CONFIG['database']}'")
        
        
        # Insérer les données dans la table
        if cleaned_data_rows:
            insert_query = """
                INSERT INTO public.zone_d_intervention 
                (id, acteur_id, projet_id, region_id, departement_id, sous_prefecture_id)
                VALUES %s
                ON CONFLICT (id) DO UPDATE SET
                    acteur_id = EXCLUDED.acteur_id,
                    projet_id = EXCLUDED.projet_id,
                    region_id = EXCLUDED.region_id,
                    departement_id = EXCLUDED.departement_id,
                    sous_prefecture_id = EXCLUDED.sous_prefecture_id
            """
            
            execute_values(cursor, insert_query, cleaned_data_rows)
            conn.commit()
            
            print(f"✓ {cursor.rowcount} lignes insérées/mises à jour dans la table zone_d_intervention")
        
        cursor.close()
        conn.close()
        print("✓ Chargement terminé avec succès!")
        
    except FileNotFoundError:
        print(f"✗ Erreur: Fichier CSV non trouvé à {CSV_FILE_PATH}")
        return False
    except psycopg2.Error as e:
        print(f"✗ Erreur de base de données: {e}")
        return False
    except Exception as e:
        print(f"✗ Erreur: {e}")
        return False
    
    return True

def verify_data():
    """
    Vérifie que les données ont été correctement chargées.
    """
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Compter les lignes
        cursor.execute("SELECT COUNT(*) FROM public.zone_d_intervention")
        count = cursor.fetchone()[0]
        print(f"\n✓ Total de lignes dans zone_d_intervention: {count}")
        
        # Afficher quelques exemples
        cursor.execute("""
            SELECT id, acteur_id, projet_id, region_id, departement_id, sous_prefecture_id
            FROM public.zone_d_intervention
            LIMIT 5
        """)
        
        print("\nExemples de données:")
        print("-" * 100)
        for row in cursor.fetchall():
            print(f"ID: {row[0]}, Acteur: {row[1]}, Projet: {row[2]}, Région: {row[3]}, Département: {row[4]}, Sous-préf: {row[5]}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"✗ Erreur lors de la vérification: {e}")

if __name__ == "__main__":
    print("=" * 100)
    print("Chargement des données zone_d_intervention depuis CSV")
    print("=" * 100)
    
    success = load_zone_intervention_data()
    
    if success:
        verify_data()
    
    print("=" * 100)
