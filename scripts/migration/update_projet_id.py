import os
import psycopg2
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Configuration de la base de données
DATABASE_URL = os.getenv('DATABASE_URL')

def update_projet_id():
    """
    Remplacer tous les projet_id avec valeur 'projet' par 'PRESFOR'
    dans la table fic_personne
    """
    
    try:
        # Connexion à la base de données
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        print("🔄 Début de la mise à jour...")
        print("📊 Remplacement de projet_id: 'projet' → 'PRESFOR'")
        
        # Compter les enregistrements avant
        cursor.execute("SELECT COUNT(*) FROM fic_personne WHERE projet_id = %s", ('projet',))
        count_before = cursor.fetchone()[0]
        print(f"\n📈 Enregistrements à mettre à jour: {count_before}")
        
        # Effectuer la mise à jour
        cursor.execute(
            "UPDATE fic_personne SET projet_id = %s WHERE projet_id = %s",
            ('PRESFOR', 'projet')
        )
        
        # Valider les changements
        conn.commit()
        
        # Vérifier le résultat
        cursor.execute("SELECT COUNT(*) FROM fic_personne WHERE projet_id = %s", ('PRESFOR',))
        count_after = cursor.fetchone()[0]
        
        print(f"✅ Enregistrements mis à jour: {count_after}")
        print("\n" + "="*60)
        print("✓ Mise à jour terminée avec succès!")
        print("="*60)
        
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
    update_projet_id()
