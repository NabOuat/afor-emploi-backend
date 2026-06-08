#!/usr/bin/env python3
"""
Script de migration directe des données vers Supabase
"""
import os
import sys
import psycopg2
import argparse
from datetime import datetime

# Paramètres de connexion directs
SOURCE_DB = {
    'host': os.getenv('SOURCE_DB_HOST', 'localhost'),
    'port': int(os.getenv('SOURCE_DB_PORT', '5432')),
    'database': os.getenv('SOURCE_DB_NAME', 'emploi'),
    'user': os.getenv('SOURCE_DB_USER', 'postgres'),
    'password': os.getenv('SOURCE_DB_PASSWORD', '')
}

SUPABASE_DB = {
    'host': os.getenv('SUPABASE_DB_HOST', ''),
    'port': int(os.getenv('SUPABASE_DB_PORT', '5432')),
    'database': os.getenv('SUPABASE_DB_NAME', 'postgres'),
    'user': os.getenv('SUPABASE_DB_USER', 'postgres'),
    'password': os.getenv('SUPABASE_DB_PASSWORD', '')
}

def connect_to_db(params):
    """Établit une connexion à la base de données"""
    try:
        print(f"Tentative de connexion à {params['host']}:{params['port']}/{params['database']} avec l'utilisateur {params['user']}")
        conn = psycopg2.connect(
            host=params['host'],
            port=params['port'],
            database=params['database'],
            user=params['user'],
            password=params['password']
        )
        return conn
    except Exception as e:
        print(f"Erreur de connexion: {e}")
        return None

def get_tables(conn):
    """Récupère la liste des tables dans la base de données"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name
    """)
    tables = [row[0] for row in cursor.fetchall()]
    cursor.close()
    return tables

def get_table_data(conn, table_name):
    """Récupère les données d'une table"""
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name}")
    columns = [desc[0] for desc in cursor.description]
    data = cursor.fetchall()
    cursor.close()
    return columns, data

def insert_data(conn, table_name, columns, data):
    """Insère les données dans la table de destination"""
    cursor = conn.cursor()
    
    # Vérifier si la table existe
    cursor.execute(f"""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = '{table_name}'
        )
    """)
    table_exists = cursor.fetchone()[0]
    
    if not table_exists:
        print(f"La table {table_name} n'existe pas dans la base de données de destination")
        return 0
    
    # Construire la requête d'insertion
    placeholders = ', '.join(['%s'] * len(columns))
    columns_str = ', '.join(columns)
    query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders}) ON CONFLICT DO NOTHING"
    
    # Insérer les données par lots
    batch_size = 100
    inserted = 0
    
    try:
        for i in range(0, len(data), batch_size):
            batch = data[i:i+batch_size]
            cursor.executemany(query, batch)
            conn.commit()
            inserted += cursor.rowcount
            print(f"  - Inséré {inserted}/{len(data)} lignes dans {table_name}")
    except Exception as e:
        conn.rollback()
        print(f"Erreur lors de l'insertion dans {table_name}: {e}")
    
    cursor.close()
    return inserted

def migrate_data(source_conn, dest_conn, tables=None):
    """Migre les données de la source vers la destination"""
    if not tables:
        tables = get_tables(source_conn)
    
    # Ordre de migration pour respecter les contraintes de clé étrangère
    migration_order = [
        'tregion', 'tdepartement', 'tsousprefecture',  # Tables géographiques
        'acteurs', 'projets', 'engagement',            # Tables de base
        'projet_engagement', 'zone_d_intervention',    # Relations
        'fic_personne',                                # Personnes
        'fic_personne_acteur', 'fic_personne_projet',  # Relations personnes
        'supervision', 'contrats',                     # Contrats
        'fic_personne_localisation',                   # Localisation
        'utilisateurs', 'user_actions'                 # Utilisateurs et actions
    ]
    
    # Filtrer et ordonner les tables selon migration_order
    ordered_tables = [t for t in migration_order if t in tables]
    remaining_tables = [t for t in tables if t not in migration_order]
    ordered_tables.extend(remaining_tables)  # Ajouter les tables restantes à la fin
    
    print(f"Migration des données de {len(ordered_tables)} tables...")
    
    total_rows = 0
    for table in ordered_tables:
        print(f"Migration de la table: {table}")
        columns, data = get_table_data(source_conn, table)
        rows = insert_data(dest_conn, table, columns, data)
        total_rows += rows
        print(f"  - {rows} lignes migrées dans {table}")
    
    print(f"Migration terminée. {total_rows} lignes migrées au total.")

def main():
    # Établir les connexions
    print("Connexion à la base de données source...")
    source_conn = connect_to_db(SOURCE_DB)
    if not source_conn:
        print("Impossible de se connecter à la base de données source. Vérifiez vos paramètres.")
        sys.exit(1)
    
    print("Connexion à la base de données Supabase...")
    dest_conn = connect_to_db(SUPABASE_DB)
    if not dest_conn:
        print("Impossible de se connecter à la base de données Supabase. Vérifiez vos paramètres.")
        source_conn.close()
        sys.exit(1)
    
    # Lister les tables disponibles
    print("Tables disponibles dans la base de données source:")
    tables = get_tables(source_conn)
    for i, table in enumerate(tables):
        print(f"  {i+1}. {table}")
    
    # Demander confirmation
    try:
        input_text = input("Appuyez sur Entrée pour continuer la migration ou Ctrl+C pour annuler...")
    except KeyboardInterrupt:
        print("\nMigration annulée.")
        source_conn.close()
        dest_conn.close()
        sys.exit(0)
    
    # Migrer les données
    try:
        migrate_data(source_conn, dest_conn)
    finally:
        source_conn.close()
        dest_conn.close()

if __name__ == "__main__":
    main()
