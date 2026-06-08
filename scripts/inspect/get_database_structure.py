#!/usr/bin/env python
# coding: utf-8
"""
Script pour récupérer la structure complète de la base de données
Génère un fichier JSON avec toutes les tables, colonnes, types et relations
"""

import psycopg2
import json
from datetime import datetime
import os
import sys

# Ajouter le chemin parent pour importer la config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def get_database_structure():
    """Récupère la structure complète de la base de données"""
    
    # Configuration de la connexion
    DB_CONFIG = {
        'host': 'localhost',
        'port': 5432,
        'database': 'afor_emploi',
        'user': 'postgres',
        'password': 'postgres',
        'client_encoding': 'utf8'
    }
    
    try:
        # Connexion à la base de données
        print("📡 Connexion à la base de données...")
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        structure = {
            'database': DB_CONFIG['database'],
            'timestamp': datetime.now().isoformat(),
            'tables': {}
        }
        
        # Récupérer toutes les tables (hors tables système)
        print("📋 Récupération de la liste des tables...")
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """)
        
        tables = [row[0] for row in cursor.fetchall()]
        print(f"✅ {len(tables)} tables trouvées: {', '.join(tables)}\n")
        
        # Pour chaque table, récupérer sa structure
        for table_name in tables:
            print(f"🔍 Analyse de la table: {table_name}")
            
            # Récupérer les colonnes
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
                column_info = {
                    'name': col[0],
                    'type': col[1],
                    'max_length': col[2],
                    'nullable': col[3] == 'YES',
                    'default': col[4]
                }
                columns.append(column_info)
            
            # Récupérer les clés primaires
            cursor.execute("""
                SELECT a.attname
                FROM pg_index i
                JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
                WHERE i.indrelid = %s::regclass
                AND i.indisprimary;
            """, (table_name,))
            
            primary_keys = [row[0] for row in cursor.fetchall()]
            
            # Récupérer les clés étrangères
            cursor.execute("""
                SELECT
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name,
                    rc.delete_rule
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                    AND ccu.table_schema = tc.table_schema
                JOIN information_schema.referential_constraints AS rc
                    ON rc.constraint_name = tc.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_name = %s;
            """, (table_name,))
            
            foreign_keys = []
            for fk in cursor.fetchall():
                foreign_keys.append({
                    'column': fk[0],
                    'references_table': fk[1],
                    'references_column': fk[2],
                    'on_delete': fk[3]
                })
            
            # Récupérer les index
            cursor.execute("""
                SELECT
                    i.relname AS index_name,
                    a.attname AS column_name,
                    ix.indisunique AS is_unique
                FROM pg_class t
                JOIN pg_index ix ON t.oid = ix.indrelid
                JOIN pg_class i ON i.oid = ix.indexrelid
                JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(ix.indkey)
                WHERE t.relname = %s
                AND t.relkind = 'r'
                AND i.relname NOT LIKE '%_pkey';
            """, (table_name,))
            
            indexes = []
            for idx in cursor.fetchall():
                indexes.append({
                    'name': idx[0],
                    'column': idx[1],
                    'unique': idx[2]
                })
            
            # Compter le nombre de lignes
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            row_count = cursor.fetchone()[0]
            
            # Stocker les informations de la table
            structure['tables'][table_name] = {
                'columns': columns,
                'primary_keys': primary_keys,
                'foreign_keys': foreign_keys,
                'indexes': indexes,
                'row_count': row_count
            }
            
            print(f"  ✅ {len(columns)} colonnes, {len(foreign_keys)} FK, {row_count} lignes\n")
        
        # Fermer la connexion
        cursor.close()
        conn.close()
        
        # Sauvegarder dans un fichier JSON
        output_file = 'database_structure.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(structure, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Structure de la base de données sauvegardée dans: {output_file}")
        
        # Afficher un résumé
        print("\n" + "="*60)
        print("📊 RÉSUMÉ DE LA STRUCTURE")
        print("="*60)
        print(f"Base de données: {structure['database']}")
        print(f"Nombre de tables: {len(structure['tables'])}")
        print(f"Date d'extraction: {structure['timestamp']}")
        print("\nTables et nombre de colonnes:")
        for table_name, table_info in sorted(structure['tables'].items()):
            print(f"  • {table_name:30} {len(table_info['columns']):2} colonnes, {table_info['row_count']:6} lignes")
        print("="*60)
        
        return structure
        
    except psycopg2.Error as e:
        print(f"❌ Erreur de connexion à la base de données: {e}")
        return None
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return None


def print_table_details(structure, table_name):
    """Affiche les détails d'une table spécifique"""
    
    if table_name not in structure['tables']:
        print(f"❌ Table '{table_name}' non trouvée")
        return
    
    table = structure['tables'][table_name]
    
    print(f"\n{'='*80}")
    print(f"TABLE: {table_name}")
    print(f"{'='*80}")
    
    print(f"\n📋 COLONNES ({len(table['columns'])}):")
    print(f"{'Nom':<30} {'Type':<20} {'Nullable':<10} {'Default':<20}")
    print("-" * 80)
    for col in table['columns']:
        nullable = "✓" if col['nullable'] else "✗"
        default = str(col['default'])[:20] if col['default'] else "-"
        print(f"{col['name']:<30} {col['type']:<20} {nullable:<10} {default:<20}")
    
    if table['primary_keys']:
        print(f"\n🔑 CLÉS PRIMAIRES:")
        for pk in table['primary_keys']:
            print(f"  • {pk}")
    
    if table['foreign_keys']:
        print(f"\n🔗 CLÉS ÉTRANGÈRES ({len(table['foreign_keys'])}):")
        for fk in table['foreign_keys']:
            print(f"  • {fk['column']} → {fk['references_table']}.{fk['references_column']} (ON DELETE {fk['on_delete']})")
    
    if table['indexes']:
        print(f"\n📇 INDEX ({len(table['indexes'])}):")
        for idx in table['indexes']:
            unique = "UNIQUE" if idx['unique'] else ""
            print(f"  • {idx['name']} sur {idx['column']} {unique}")
    
    print(f"\n📊 STATISTIQUES:")
    print(f"  • Nombre de lignes: {table['row_count']}")
    print("="*80)


if __name__ == "__main__":
    print("🚀 Extraction de la structure de la base de données\n")
    
    structure = get_database_structure()
    
    if structure:
        # Afficher les détails de quelques tables importantes
        important_tables = ['fic_personne', 'contrat', 'fic_personne_projet', 'fic_personne_localisation']
        
        print("\n\n📖 DÉTAILS DES TABLES PRINCIPALES:")
        for table in important_tables:
            if table in structure['tables']:
                print_table_details(structure, table)
        
        print("\n✅ Script terminé avec succès!")
    else:
        print("\n❌ Échec de l'extraction de la structure")
