import os
import psycopg2
from dotenv import load_dotenv
import re
import uuid

# Charger les variables d'environnement
load_dotenv()

# Configuration de la base de données
DATABASE_URL = os.getenv('DATABASE_URL')

# Liste des organisations
ORGANIZATIONS = [
    "GROUPEMENT AVICENNE CONSULT/ GROUPE DE GEOMATIQUE AZIMUT TERRABO INGENIEUR CONSEIL / CABINET DE GEOMETRE EXPERT /AKMEL YEDAGNE (GE-2ATY)",
    "Institut National Polytechnique HOUPHOUET BOIGNY",
    "Institut National de Formation Professionnelle Agricole",
    "Université Alassane Ouattara",
    "CABINET DE GEOMETRE EXPERT DIALLO SEKOU (CGEDS)",
    "GROUPEMENT GEOART / SETOM / CGEKA",
    "user",
    "GROUPEMENT ETAFAT-CGEA 2TF",
    "CABINET TOPO BENHIBA",
    "AGENCE FONCIERE RURALE - RH",
    "AGENCE FONCIERE RURALE   -   RH",
    "AGENCE FONCIERE RURALE . RH",
    "GROUPEMENT D'EXPERTS FONCIERS (GEF)",
    "GROUPEMENT  CGEDS - ETAFAT -TERRABO",
    "GROUPEMENT TERRA VITAL - CGE SOTTI",
    "GROUPEMENT ALLIANCE IVOIRIENNE CITRAT/CGE SAKO/CDGE C. DOHOULOU/CGET/IVOIRE GEO AGRO",
    "GROUPEMENT CAG"
]

def generate_username(org_name):
    """
    Générer un nom d'utilisateur à partir du nom de l'organisation
    Format: prendre les premières lettres de chaque mot, en minuscules
    """
    # Nettoyer le nom
    org_name = org_name.strip()
    
    # Extraire les premières lettres de chaque mot
    words = re.findall(r'\b\w+', org_name)
    username = ''.join([word[0].lower() for word in words if word])
    
    # Si le username est trop court, utiliser une version simplifiée
    if len(username) < 3:
        username = org_name[:10].lower().replace(' ', '_').replace('/', '_')
    
    return username[:20]  # Limiter à 20 caractères

def create_user_access():
    """
    Créer des accès utilisateurs pour chaque organisation
    Insère dans la table login avec les acteurs correspondants
    """
    
    try:
        # Connexion à la base de données
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        print("🔄 Création des accès utilisateurs...")
        print("📧 Domaine email: @afor_emploi.ci")
        print("="*70)
        
        created_count = 0
        skipped_count = 0
        
        for org_name in ORGANIZATIONS:
            try:
                # Générer les identifiants
                username = generate_username(org_name)
                email = f"{username}@afor_emploi.ci"
                login_id = str(uuid.uuid4())
                
                print(f"\n📝 Organisation: {org_name}")
                print(f"   👤 Utilisateur: {username}")
                print(f"   📧 Email: {email}")
                
                # Chercher l'acteur correspondant par nom
                cursor.execute(
                    "SELECT id FROM acteur WHERE nom = %s LIMIT 1",
                    (org_name,)
                )
                
                acteur_result = cursor.fetchone()
                
                if not acteur_result:
                    print(f"   ⚠️  Acteur non trouvé pour cette organisation")
                    skipped_count += 1
                    continue
                
                acteur_id = acteur_result[0]
                
                # Vérifier si le login existe déjà pour cet acteur
                cursor.execute(
                    "SELECT id FROM login WHERE acteur_id = %s",
                    (acteur_id,)
                )
                
                if cursor.fetchone():
                    print(f"   ⚠️  Login déjà existant pour cet acteur")
                    skipped_count += 1
                else:
                    # Générer un mot de passe simple (à remplacer par un vrai mot de passe)
                    password = f"pass_{username}_{str(uuid.uuid4())[:8]}"
                    
                    # Créer le login
                    cursor.execute("""
                        INSERT INTO login (id, username, password, acteur_id)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (id) DO NOTHING
                    """, (login_id, username, password, acteur_id))
                    
                    conn.commit()
                    print(f"   ✅ Login créé")
                    print(f"      ID: {login_id}")
                    print(f"      Acteur ID: {acteur_id}")
                    created_count += 1
                    
            except psycopg2.Error as e:
                print(f"   ❌ Erreur: {str(e)}")
                conn.rollback()
                continue
        
        print("\n" + "="*70)
        print(f"✓ Création terminée!")
        print(f"  - Logins créés: {created_count}")
        print(f"  - Logins ignorés: {skipped_count}")
        print(f"  - Total organisations: {len(ORGANIZATIONS)}")
        print("="*70)
        
        cursor.close()
        conn.close()
        
        return True
        
    except psycopg2.Error as e:
        print(f"❌ Erreur de base de données: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Erreur générale: {str(e)}")
        return False

if __name__ == "__main__":
    print("\n⚠️  IMPORTANT: Vérifiez que votre table 'users' existe avec les colonnes appropriées")
    print("   Colonnes attendues: id, username, email, organization, created_at")
    print("   Adaptez le script si votre structure est différente\n")
    
    create_user_access()
