#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour corriger les erreurs d'encodage UTF-8 dans la base de données
Les caractères accentués sont mal encodés (ex: Ã© au lieu de é)
"""

import psycopg2
from dotenv import load_dotenv
import os
import sys

# Charger les variables d'environnement
load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:Nabaga@localhost:5432/emploi?client_encoding=utf8')

def fix_encoding():
    """Corriger les erreurs d'encodage dans la BD"""
    
    try:
        # Connexion à la BD
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        print("🔧 Correction des erreurs d'encodage...")
        print("=" * 60)
        
        # Récupérer tous les postes avec erreurs d'encodage
        cur.execute("""
            SELECT id, poste_nom FROM contrat 
            WHERE poste_nom LIKE '%Ã%' OR poste_nom LIKE '%Â%'
            ORDER BY poste_nom
        """)
        
        rows = cur.fetchall()
        print(f"\n📋 {len(rows)} postes avec erreurs d'encodage trouvés:")
        
        corrections = {}
        for row_id, poste_nom in rows:
            # Décoder correctement le texte mal encodé
            try:
                # UTF-8 mal interprété comme Latin-1
                fixed_name = poste_nom.encode('latin-1').decode('utf-8')
                corrections[poste_nom] = fixed_name
                print(f"  ❌ {poste_nom}")
                print(f"  ✅ {fixed_name}")
            except Exception as e:
                print(f"  ⚠️  Impossible de corriger: {poste_nom} - {str(e)}")
        
        # Appliquer les corrections
        if corrections:
            print(f"\n💾 Application des {len(corrections)} corrections...")
            for old_name, new_name in corrections.items():
                cur.execute("""
                    UPDATE contrat SET poste_nom = %s 
                    WHERE poste_nom = %s
                """, (new_name, old_name))
            
            conn.commit()
            print("✅ Corrections appliquées avec succès!")
        else:
            print("\n✅ Aucune correction nécessaire")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    fix_encoding()
