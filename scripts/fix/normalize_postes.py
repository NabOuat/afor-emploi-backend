# -*- coding: utf-8 -*-
import psycopg2
import os
from dotenv import load_dotenv
import unicodedata

# Charger les variables d'environnement
load_dotenv()

# Configuration de la base de données
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost/afor_emploi')

def normalize_string(s):
    """Normaliser une chaîne pour la comparaison (minuscules, sans accents)"""
    if not s:
        return ""
    # Convertir en minuscules
    s = s.lower().strip()
    # Supprimer les accents
    s = ''.join(c for c in unicodedata.normalize('NFD', s)
                if unicodedata.category(c) != 'Mn')
    return s

def normalize_postes():
    """Normaliser et fusionner les postes similaires"""
    
    try:
        # Connexion à la base de données
        conn = psycopg2.connect(DATABASE_URL)
        conn.set_client_encoding('UTF8')
        cursor = conn.cursor()
        
        print("Connexion à la base de données réussie\n")
        
        # Récupérer tous les postes uniques
        cursor.execute("""
            SELECT DISTINCT poste_nom
            FROM contrat 
            WHERE poste_nom IS NOT NULL
            ORDER BY poste_nom
        """)
        
        postes = [row[0] for row in cursor.fetchall()]
        print(f"Postes uniques trouvés: {len(postes)}\n")
        
        # Grouper les postes similaires
        poste_groups = {}
        for poste in postes:
            normalized = normalize_string(poste)
            if normalized not in poste_groups:
                poste_groups[normalized] = []
            poste_groups[normalized].append(poste)
        
        # Trouver les groupes avec plusieurs variantes
        corrections = []
        for normalized, variants in poste_groups.items():
            if len(variants) > 1:
                # Utiliser la variante la plus longue comme référence
                canonical = max(variants, key=len)
                for variant in variants:
                    if variant != canonical:
                        corrections.append((variant, canonical))
        
        print(f"Groupes de postes similaires trouvés: {len([g for g in poste_groups.values() if len(g) > 1])}\n")
        print("="*80)
        print("CORRECTIONS À APPLIQUER:")
        print("="*80 + "\n")
        
        total_updated = 0
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
                total_updated += rows_updated
                print(f"✓ '{old_value}' ({count_old}) -> '{new_value}'")
        
        print(f"\nTotal de lignes mises à jour: {total_updated}")
        
        # Vérifier les corrections
        cursor.execute("""
            SELECT DISTINCT poste_nom
            FROM contrat 
            WHERE poste_nom IS NOT NULL
            ORDER BY poste_nom
        """)
        
        postes_after = [row[0] for row in cursor.fetchall()]
        print(f"\nPostes uniques après correction: {len(postes_after)}")
        print(f"Réduction: {len(postes) - len(postes_after)} postes fusionnés")
        
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
    normalize_postes()
