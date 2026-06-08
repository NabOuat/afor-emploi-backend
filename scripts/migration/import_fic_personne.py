import os
import csv
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv
from datetime import datetime

# Charger les variables d'environnement
load_dotenv()

# Configuration de la base de données
DB_HOST = 'localhost'
DB_PORT = '5432'
DB_NAME = 'emploi'
DB_USER = 'postgres'
DB_PASSWORD = 'Nabaga'

def parse_date(date_str):
    """Convertir une chaîne de date au format DATE SQL"""
    if not date_str or date_str.strip() == '':
        return None
    try:
        return datetime.strptime(date_str.strip(), '%Y-%m-%d').date()
    except ValueError:
        return None

def import_fic_personne(csv_file_path):
    """
    Importer les données du CSV fic_personne vers la table PostgreSQL
    
    Structure du CSV (ancienne):
    id, nom, prenom, contact, date_naissance, genre, type_contrat, 
    acteur_id, ?, ?, qualification, ?, numero_dossier, date_creation
    
    Structure cible (nouvelle):
    id, acteur_id, projet_id, nom, prenom, date_naissance, genre, contact
    """
    
    try:
        # Connexion à la base de données
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cursor = conn.cursor()
        
        # Compteurs
        inserted = 0
        skipped = 0
        errors = 0
        
        print(f"Lecture du fichier: {csv_file_path}")
        
        with open(csv_file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            
            for row_num, row in enumerate(reader, 1):
                try:
                    # Vérifier que la ligne a au moins les colonnes nécessaires
                    if len(row) < 14:
                        print(f"⚠️  Ligne {row_num}: Nombre de colonnes insuffisant ({len(row)})")
                        skipped += 1
                        continue
                    
                    # Mapping des colonnes du CSV
                    # Index: 0=id, 1=nom, 2=prenom, 3=contact, 4=date_naissance, 
                    #        5=genre, 6=type_contrat, 7=acteur_id, 8-10=vides, 
                    #        11=qualification, 12=numero_dossier, 13=date_creation
                    
                    fic_id = row[0].strip()
                    nom = row[1].strip()
                    prenom = row[2].strip()
                    contact = row[3].strip() if row[3].strip() else None
                    date_naissance = parse_date(row[4])
                    genre = row[5].strip() if row[5].strip() else None
                    # type_contrat = row[6].strip()  # Non utilisé dans la nouvelle structure
                    acteur_id = row[7].strip() if row[7].strip() else None
                    # Les colonnes 8, 9, 10 semblent vides
                    # qualification = row[11].strip()  # Non utilisé dans la nouvelle structure
                    # numero_dossier = row[12].strip()  # Non utilisé dans la nouvelle structure
                    # date_creation = row[13].strip()  # Non utilisé dans la nouvelle structure
                    
                    # Vérifier les champs obligatoires
                    if not fic_id or not nom or not prenom:
                        print(f"⚠️  Ligne {row_num}: Champs obligatoires manquants (id, nom, prenom)")
                        skipped += 1
                        continue
                    
                    # Déterminer le projet_id basé sur l'acteur_id
                    # Pour cette migration, on utilise une logique simple
                    # Vous pouvez adapter selon votre besoin
                    projet_id = None
                    
                    if acteur_id:
                        # Chercher le projet associé à cet acteur
                        cursor.execute(
                            "SELECT projet_id FROM zone_d_intervention WHERE acteur_id = %s LIMIT 1",
                            (acteur_id,)
                        )
                        result = cursor.fetchone()
                        if result:
                            projet_id = result[0]
                    
                    # Si pas de projet trouvé, utiliser un projet par défaut ou ignorer
                    if not projet_id:
                        # Chercher un projet par défaut
                        cursor.execute("SELECT id FROM projet LIMIT 1")
                        result = cursor.fetchone()
                        if result:
                            projet_id = result[0]
                        else:
                            print(f"⚠️  Ligne {row_num}: Aucun projet trouvé pour l'acteur {acteur_id}")
                            skipped += 1
                            continue
                    
                    # Insérer dans la table fic_personne
                    insert_query = sql.SQL("""
                        INSERT INTO fic_personne 
                        (id, acteur_id, projet_id, nom, prenom, date_naissance, genre, contact)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO NOTHING
                    """)
                    
                    cursor.execute(insert_query, (
                        fic_id,
                        acteur_id,
                        projet_id,
                        nom,
                        prenom,
                        date_naissance,
                        genre,
                        contact
                    ))
                    
                    inserted += 1
                    
                    # Afficher la progression tous les 100 enregistrements
                    if inserted % 100 == 0:
                        print(f"✓ {inserted} enregistrements insérés...")
                    
                except Exception as e:
                    print(f"❌ Erreur ligne {row_num}: {str(e)}")
                    errors += 1
                    continue
        
        # Valider les changements
        conn.commit()
        
        # Afficher le résumé
        print("\n" + "="*60)
        print("RÉSUMÉ DE L'IMPORT")
        print("="*60)
        print(f"✓ Enregistrements insérés: {inserted}")
        print(f"⚠️  Enregistrements ignorés: {skipped}")
        print(f"❌ Erreurs: {errors}")
        print("="*60)
        
        cursor.close()
        conn.close()
        
        return inserted, skipped, errors
        
    except psycopg2.Error as e:
        print(f"❌ Erreur de connexion à la base de données: {str(e)}")
        return 0, 0, 1
    except FileNotFoundError:
        print(f"❌ Fichier non trouvé: {csv_file_path}")
        return 0, 0, 1
    except Exception as e:
        print(f"❌ Erreur générale: {str(e)}")
        return 0, 0, 1

if __name__ == "__main__":
    # Chemin du fichier CSV
    csv_file = r"c:\Users\OUATTARA AFOR\Desktop\The Box\Web\Emploi\images\fic_personne.txt"
    
    print("Démarrage de l'import des données fic_personne...")
    print(f"Fichier source: {csv_file}")
    print()
    
    import_fic_personne(csv_file)
