# -*- coding: utf-8 -*-
import psycopg2
from psycopg2.extras import execute_values
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Configuration de la base de données
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost/afor_emploi')

def fix_encoding():
    """Corriger les caractères mal encodés dans la table contrat"""
    
    try:
        # Connexion à la base de données
        conn = psycopg2.connect(DATABASE_URL)
        conn.set_client_encoding('UTF8')
        cursor = conn.cursor()
        
        print("Connexion à la base de données réussie")
        
        # Récupérer tous les type_contrat avec des caractères mal encodés
        cursor.execute("""
            SELECT DISTINCT type_contrat 
            FROM contrat 
            WHERE type_contrat IS NOT NULL
            ORDER BY type_contrat
        """)
        
        types_contrat = cursor.fetchall()
        print(f"\nTypes de contrat trouvés: {len(types_contrat)}")
        
        for (type_contrat,) in types_contrat:
            print(f"  - {type_contrat}")
        
        # Corriger les caractères mal encodés
        # "ImprÃ©cis" -> "Imprécis"
        corrections = [
            ("CDI Terme ImprÃ©cis", "CDI Terme Imprécis"),
            ("CDD Terme ImprÃ©cis", "CDD Terme Imprécis"),
        ]
        
        for old_value, new_value in corrections:
            cursor.execute("""
                UPDATE contrat 
                SET type_contrat = %s 
                WHERE type_contrat = %s
            """, (new_value, old_value))
            
            rows_updated = cursor.rowcount
            if rows_updated > 0:
                print(f"\n✓ Corrigé: '{old_value}' -> '{new_value}' ({rows_updated} lignes)")
            else:
                print(f"\n✗ Aucune ligne trouvée pour: '{old_value}'")
        
        # Vérifier les corrections
        cursor.execute("""
            SELECT DISTINCT type_contrat 
            FROM contrat 
            WHERE type_contrat IS NOT NULL
            ORDER BY type_contrat
        """)
        
        types_contrat_after = cursor.fetchall()
        print(f"\n\nTypes de contrat après correction: {len(types_contrat_after)}")
        
        for (type_contrat,) in types_contrat_after:
            print(f"  - {type_contrat}")
        
        # Commit les changements
        conn.commit()
        print("\n✓ Changements sauvegardés avec succès")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"✗ Erreur: {e}")
        if conn:
            conn.rollback()
            conn.close()

if __name__ == "__main__":
    fix_encoding()
