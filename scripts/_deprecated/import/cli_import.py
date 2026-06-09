#!/usr/bin/env python
"""
Script CLI pour importer les données fic_personne depuis un CSV
Utilisation: python cli_import.py <chemin_du_fichier_csv>
"""

import sys
import os
from dotenv import load_dotenv
from import_service import FicPersonneImporter

load_dotenv()

def main():
    """Fonction principale"""
    
    if len(sys.argv) < 2:
        print("❌ Utilisation: python cli_import.py <chemin_du_fichier_csv>")
        print("\nExemple:")
        print("  python cli_import.py c:\\Users\\OUATTARA AFOR\\Desktop\\The Box\\Web\\Emploi\\images\\fic_personne.txt")
        sys.exit(1)
    
    csv_file_path = sys.argv[1]
    
    # Vérifier que le fichier existe
    if not os.path.exists(csv_file_path):
        print(f"❌ Fichier non trouvé: {csv_file_path}")
        sys.exit(1)
    
    print("="*60)
    print("IMPORT DES DONNÉES FIC_PERSONNE")
    print("="*60)
    print(f"📂 Fichier source: {csv_file_path}")
    print(f"📊 Taille: {os.path.getsize(csv_file_path) / 1024 / 1024:.2f} MB")
    print()
    
    # Créer l'importeur
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL non définie dans .env")
        sys.exit(1)
    
    print(f"🔗 Connexion à: {database_url.split('@')[1] if '@' in database_url else 'base de données'}")
    print()
    
    importer = FicPersonneImporter(database_url)
    
    # Lancer l'import
    print("⏳ Démarrage de l'import...")
    print()
    
    success = importer.import_from_csv(csv_file_path)
    
    # Afficher le résumé
    summary = importer.print_summary()
    
    if success:
        print("\n✅ Import terminé avec succès!")
        sys.exit(0)
    else:
        print("\n❌ L'import a rencontré des erreurs")
        sys.exit(1)

if __name__ == '__main__':
    main()
