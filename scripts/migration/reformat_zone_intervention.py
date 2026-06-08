#!/usr/bin/env python3
"""
Script pour reformater le fichier CSV zone_d_intervention
Colonnes attendues: id, projet_id, region_id, acteur_id
Fusion de operateur_id, ecole_id, agence_id dans acteur_id
"""

import csv
from pathlib import Path

# Chemins des fichiers
INPUT_CSV = Path(__file__).parent / "zoned'interv.csv"
OUTPUT_CSV = Path(__file__).parent / "zone_d_intervention_formatted.csv"

def reformat_csv():
    """
    Reformate le fichier CSV avec les colonnes correctes.
    """
    try:
        # Lire le fichier CSV avec gestion d'encodage
        data_rows = []
        encoding_used = None
        
        # Essayer différents encodages
        for encoding in ['latin-1', 'iso-8859-1', 'cp1252', 'utf-8']:
            try:
                with open(INPUT_CSV, 'r', encoding=encoding) as csvfile:
                    encoding_used = encoding
                    print(f"✓ Fichier CSV lu avec l'encodage: {encoding}")
                    csv_reader = csv.reader(csvfile)
                    for row in csv_reader:
                        if len(row) >= 6:
                            # Extraire les colonnes du fichier original
                            id_val = row[0].strip()
                            projet_id = row[1].strip()
                            region_id = row[2].strip()
                            operateur_id = row[3].strip() if row[3].strip() else None
                            ecole_id = row[4].strip() if row[4].strip() else None
                            agence_id = row[5].strip() if row[5].strip() else None
                            
                            # Fusionner les IDs d'acteur (prendre le premier non-vide)
                            acteur_id = operateur_id or ecole_id or agence_id or None
                            
                            data_rows.append((
                                id_val,
                                projet_id,
                                region_id,
                                acteur_id
                            ))
                break
            except (UnicodeDecodeError, UnicodeError):
                continue
        
        if not encoding_used:
            print("✗ Erreur: Impossible de lire le fichier CSV avec les encodages disponibles")
            return False
        
        print(f"✓ {len(data_rows)} lignes lues depuis le fichier CSV")
        
        # Écrire le fichier CSV reformaté
        with open(OUTPUT_CSV, 'w', encoding='utf-8', newline='') as csvfile:
            csv_writer = csv.writer(csvfile)
            # Écrire l'en-tête
            csv_writer.writerow(['id', 'projet_id', 'region_id', 'acteur_id'])
            # Écrire les données
            csv_writer.writerows(data_rows)
        
        print(f"✓ Fichier CSV reformaté écrit: {OUTPUT_CSV}")
        print(f"✓ {len(data_rows)} lignes écrites")
        
        # Afficher quelques exemples
        print("\nExemples de données reformatées:")
        print("-" * 100)
        for i, row in enumerate(data_rows[:5]):
            print(f"ID: {row[0]}, Projet: {row[1]}, Région: {row[2]}, Acteur: {row[3]}")
        
        return True
        
    except Exception as e:
        print(f"✗ Erreur: {e}")
        return False

if __name__ == "__main__":
    print("=" * 100)
    print("Reformatage du fichier CSV zone_d_intervention")
    print("=" * 100)
    
    success = reformat_csv()
    
    if success:
        print("\n✓ Reformatage terminé avec succès!")
        print(f"✓ Fichier de sortie: {OUTPUT_CSV}")
    else:
        print("\n✗ Erreur lors du reformatage")
    
    print("=" * 100)
