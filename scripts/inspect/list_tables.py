#!/usr/bin/env python3
import psycopg2

# Paramètres de connexion
conn_params = {
    'host': 'localhost',
    'port': 5432,
    'database': 'emploi',
    'user': 'postgres',
    'password': 'Nabaga'
}

try:
    # Connexion à la base de données
    conn = psycopg2.connect(**conn_params)
    cursor = conn.cursor()
    
    # Requête pour lister toutes les tables
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name
    """)
    
    # Afficher les résultats
    print("Tables dans la base de données:")
    print("=" * 40)
    for i, (table,) in enumerate(cursor.fetchall()):
        print(f"{i+1}. {table}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Erreur: {e}")

input("\nAppuyez sur Entrée pour quitter...")
