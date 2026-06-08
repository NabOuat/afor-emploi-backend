#!/usr/bin/env python
# coding: utf-8
"""
Script simple pour récupérer la structure de la base de données
Utilise la configuration du projet existant
"""

import sys
import os
import json
from datetime import datetime
import psycopg2
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

def get_connection():
    """Créer une connexion à la base de données"""
    try:
        # Essayer d'abord avec DATABASE_URL
        database_url = os.getenv('DATABASE_URL')
        if database_url:
            return psycopg2.connect(database_url)
        
        # Sinon utiliser la config par défaut
        return psycopg2.connect(
            host='localhost',
            port=5432,
            database='afor_emploi',
            user='postgres',
            password='postgres',
            client_encoding='utf8'
        )
    except Exception as e:
        print(f"Erreur de connexion: {e}")
        raise

def get_all_tables(cursor):
    """Récupère la liste de toutes les tables"""
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_type = 'BASE TABLE'
        ORDER BY table_name;
    """)
    return [row[0] for row in cursor.fetchall()]

def get_table_columns(cursor, table_name):
    """Récupère les colonnes d'une table"""
    cursor.execute("""
        SELECT 
            column_name,
            data_type,
            character_maximum_length,
            is_nullable,
            column_default
        FROM information_schema.columns
        WHERE table_schema = 'public' 
        AND table_name = %s
        ORDER BY ordinal_position;
    """, (table_name,))
    
    columns = []
    for col in cursor.fetchall():
        columns.append({
            'name': col[0],
            'type': col[1],
            'max_length': col[2],
            'nullable': col[3] == 'YES',
            'default': col[4]
        })
    return columns

def get_table_count(cursor, table_name):
    """Compte le nombre de lignes dans une table"""
    try:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
        return cursor.fetchone()[0]
    except:
        return 0

def main():
    """Fonction principale"""
    print("🚀 Extraction de la structure de la base de données\n")
    
    conn = None
    try:
        # Connexion à la base de données
        print("📡 Connexion à la base de données...")
        conn = get_connection()
        cursor = conn.cursor()
        print("✅ Connecté!\n")
        
        # Récupérer toutes les tables
        print("📋 Récupération des tables...")
        tables = get_all_tables(cursor)
        print(f"✅ {len(tables)} tables trouvées\n")
        
        # Structure complète
        structure = {
            'database': 'afor_emploi',
            'timestamp': datetime.now().isoformat(),
            'tables': {}
        }
        
        # Pour chaque table
        for table_name in tables:
            print(f"🔍 {table_name}...", end=" ")
            
            columns = get_table_columns(cursor, table_name)
            row_count = get_table_count(cursor, table_name)
            
            structure['tables'][table_name] = {
                'columns': columns,
                'row_count': row_count
            }
            
            print(f"✅ {len(columns)} colonnes, {row_count} lignes")
        
        # Sauvegarder
        output_file = 'database_structure_simple.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(structure, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Structure sauvegardée dans: {output_file}")
        
        # Afficher un résumé
        print("\n" + "="*70)
        print("📊 RÉSUMÉ")
        print("="*70)
        print(f"{'Table':<35} {'Colonnes':<10} {'Lignes':<10}")
        print("-"*70)
        
        for table_name in sorted(structure['tables'].keys()):
            table_info = structure['tables'][table_name]
            print(f"{table_name:<35} {len(table_info['columns']):<10} {table_info['row_count']:<10}")
        
        print("="*70)
        print(f"\nTotal: {len(structure['tables'])} tables")
        
        # Afficher les détails des tables principales
        print("\n\n" + "="*70)
        print("📖 DÉTAILS DES TABLES PRINCIPALES")
        print("="*70)
        
        important_tables = [
            'fic_personne',
            'contrat', 
            'fic_personne_projet',
            'fic_personne_localisation',
            'projet',
            'acteur'
        ]
        
        for table_name in important_tables:
            if table_name in structure['tables']:
                table = structure['tables'][table_name]
                print(f"\n📋 {table_name.upper()} ({len(table['columns'])} colonnes, {table['row_count']} lignes)")
                print("-"*70)
                
                for col in table['columns']:
                    nullable = "NULL" if col['nullable'] else "NOT NULL"
                    type_info = col['type']
                    if col['max_length']:
                        type_info += f"({col['max_length']})"
                    
                    print(f"  • {col['name']:<30} {type_info:<20} {nullable}")
        
        print("\n✅ Terminé!")
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if conn:
            conn.close()
            print("\n🔌 Connexion fermée")

if __name__ == "__main__":
    main()
