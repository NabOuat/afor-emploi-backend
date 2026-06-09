#!/usr/bin/env python3
"""
Script pour créer un utilisateur de test dans la base de données.
"""
import sys
import uuid
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models import Base, Acteur, Users
from app.security import hash_password

def create_test_user():
    """Crée un utilisateur de test avec un acteur associé."""
    
    # Créer les tables si elles n'existent pas
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Vérifier si un acteur admin existe
        admin_acteur = db.query(Acteur).filter(Acteur.type_acteur == "AD").first()
        
        if not admin_acteur:
            # Créer un acteur admin
            admin_acteur = Acteur(
                id=str(uuid.uuid4()),
                nom="Administration",
                type_acteur="AD",
                contact="admin@afor.ci",
                email="admin@afor.ci"
            )
            db.add(admin_acteur)
            db.commit()
            print(f"✓ Acteur admin créé : {admin_acteur.id}")
        else:
            print(f"✓ Acteur admin existant : {admin_acteur.id}")
        
        # Vérifier si l'utilisateur test existe
        test_user = db.query(Users).filter(Users.username == "admin").first()
        
        if test_user:
            print(f"✓ Utilisateur 'admin' existe déjà")
            print(f"  ID: {test_user.id}")
            print(f"  Email: {test_user.email}")
        else:
            # Créer l'utilisateur test
            test_user = Users(
                id=str(uuid.uuid4()),
                username="admin",
                password=hash_password("admin123"),  # Mot de passe : admin123
                nom="Administrateur",
                prenom="Test",
                email="admin@afor.ci",
                acteur_id=admin_acteur.id
            )
            db.add(test_user)
            db.commit()
            print(f"✓ Utilisateur 'admin' créé avec succès")
            print(f"  ID: {test_user.id}")
            print(f"  Username: admin")
            print(f"  Password: admin123")
            print(f"  Email: {test_user.email}")
        
        print("\n✓ Utilisateur de test prêt !")
        print("\nIdentifiants de connexion :")
        print("  Username: admin")
        print("  Password: admin123")
        
    except Exception as e:
        print(f"✗ Erreur : {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    create_test_user()
