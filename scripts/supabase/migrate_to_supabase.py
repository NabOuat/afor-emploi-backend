#!/usr/bin/env python3
"""
Script de migration des données vers Supabase
"""
import os
import sys
import psycopg2
import argparse
from dotenv import load_dotenv
from datetime import datetime

def connect_to_db(connection_string):
    """Établit une connexion à la base de données"""
    try:
        # Utiliser l'encodage latin1 pour éviter les problèmes avec les caractères spéciaux
        conn = psycopg2.connect(connection_string)
        return conn
    except Exception as e:
        print(f"Erreur de connexion: {e}")
        sys.exit(1)

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
    parser = argparse.ArgumentParser(description="Migrer les données vers Supabase")
    parser.add_argument("--source", help="Chaîne de connexion à la base source")
    parser.add_argument("--dest", help="Chaîne de connexion à la base Supabase")
    parser.add_argument("--tables", help="Liste des tables à migrer (séparées par des virgules)")
    args = parser.parse_args()
    
    # Charger les variables d'environnement depuis .env avec encoding spécifié
    load_dotenv(encoding='latin1')
    
    # Obtenir les chaînes de connexion
    source_conn_string = args.source or os.getenv("SOURCE_DATABASE_URL")
    dest_conn_string = args.dest or os.getenv("SUPABASE_DATABASE_URL")
    
    # Afficher les chaînes de connexion pour le débogage (masquer les mots de passe)
    if source_conn_string:
        debug_source = source_conn_string.replace(source_conn_string.split(':')[2].split('@')[0], '****')
        print(f"Source connection string: {debug_source}")
    if dest_conn_string:
        debug_dest = dest_conn_string.replace(dest_conn_string.split(':')[2].split('@')[0], '****')
        print(f"Destination connection string: {debug_dest}")
    
    if not source_conn_string or not dest_conn_string:
        print("Erreur: Les chaînes de connexion source et destination sont requises")
        print("Utilisez --source et --dest ou définissez SOURCE_DATABASE_URL et SUPABASE_DATABASE_URL dans .env")
        sys.exit(1)
    
    # Établir les connexions
    print("Connexion à la base de données source...")
    source_conn = connect_to_db(source_conn_string)
    
    print("Connexion à la base de données Supabase...")
    dest_conn = connect_to_db(dest_conn_string)
    
    # Préparer la liste des tables
    tables = None
    if args.tables:
        tables = [t.strip() for t in args.tables.split(',')]
    
    # Migrer les données
    try:
        migrate_data(source_conn, dest_conn, tables)
    finally:
        source_conn.close()
        dest_conn.close()

if __name__ == "__main__":
    main()
