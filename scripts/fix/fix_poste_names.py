# -*- coding: utf-8 -*-
import psycopg2
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Configuration de la base de données
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost/afor_emploi')

def fix_poste_names():
    """Corriger et normaliser les noms de postes dans la table contrat"""
    
    try:
        # Connexion à la base de données
        conn = psycopg2.connect(DATABASE_URL)
        conn.set_client_encoding('UTF8')
        cursor = conn.cursor()
        
        print("Connexion à la base de données réussie\n")
        
        # Récupérer tous les poste_nom avec leurs comptages
        cursor.execute("""
            SELECT poste_nom, COUNT(*) as count
            FROM contrat 
            WHERE poste_nom IS NOT NULL
            GROUP BY poste_nom
            ORDER BY count DESC
        """)
        
        postes = cursor.fetchall()
        print(f"Postes trouvés: {len(postes)}\n")
        
        for poste, count in postes:
            print(f"  {count:3d} - {poste}")
        
        # Définir les corrections à appliquer
        corrections = [
            ("Responsable Departemental", "REPRESENTANT DEPARTEMENTAL AFOR"),
            # Ajouter d'autres corrections si nécessaire
        ]
        
        print("\n" + "="*60)
        print("CORRECTIONS À APPLIQUER:")
        print("="*60 + "\n")
        
        for old_value, new_value in corrections:
            # Vérifier si l'ancien poste existe
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM contrat 
                WHERE poste_nom = %s
            """, (old_value,))
            
            count_old = cursor.fetchone()[0]
            
            if count_old > 0:
                # Appliquer la correction
                cursor.execute("""
                    UPDATE contrat 
                    SET poste_nom = %s 
                    WHERE poste_nom = %s
                """, (new_value, old_value))
                
                rows_updated = cursor.rowcount
                print(f"✓ Fusionné: '{old_value}' ({count_old}) -> '{new_value}'")
            else:
                print(f"✗ Aucune ligne trouvée pour: '{old_value}'")
        
        # Vérifier les corrections
        cursor.execute("""
            SELECT poste_nom, COUNT(*) as count
            FROM contrat 
            WHERE poste_nom IS NOT NULL
            GROUP BY poste_nom
            ORDER BY count DESC
        """)
        
        postes_after = cursor.fetchall()
        print(f"\n\nPostes après correction: {len(postes_after)}\n")
        
        for poste, count in postes_after:
            print(f"  {count:3d} - {poste}")
        
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
    fix_poste_names()
