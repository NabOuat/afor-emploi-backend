"""
Script pour créer un administrateur et un responsable liés à l'acteur AFOR.

Usage:
    python create_users.py

Ce script :
1. Se connecte à la base de données via les variables d'environnement (.env)
2. Cherche l'acteur AFOR existant (type_acteur = 'AF')
3. Crée un acteur Admin (type_acteur = 'AD') et un acteur Responsable (type_acteur = 'RESPO')
4. Crée les logins correspondants avec mots de passe hashés en bcrypt
5. Crée l'entrée Administrateur pour le compte admin
"""

import uuid
import sys
import os

# Ajouter le répertoire parent au path pour importer les modules de l'app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models import Acteur, Login, Administrateur
from app.security import hash_password


def create_users():
    db = SessionLocal()
    try:
        # ── 1. Vérifier que l'acteur AFOR existe ──────────────────────────
        afor = db.query(Acteur).filter(Acteur.type_acteur == 'AF').first()
        if not afor:
            print("❌ Aucun acteur AFOR (type_acteur='AF') trouvé dans la base.")
            print("   Veuillez d'abord créer un acteur AFOR.")
            return

        print(f"✅ Acteur AFOR trouvé : {afor.nom} (ID: {afor.id})")

        # ── 2. Créer l'acteur Admin ───────────────────────────────────────
        admin_acteur_id = str(uuid.uuid4())
        existing_admin = db.query(Acteur).filter(Acteur.type_acteur == 'AD').first()
        if existing_admin:
            print(f"ℹ️  Acteur Admin existe déjà : {existing_admin.nom} (ID: {existing_admin.id})")
            admin_acteur_id = existing_admin.id
        else:
            admin_acteur = Acteur(
                id=admin_acteur_id,
                nom="Administration AFOR",
                type_acteur="AD",
                contact_1=afor.contact_1,
                email_1=afor.email_1,
                adresse_1=afor.adresse_1,
            )
            db.add(admin_acteur)
            db.flush()
            print(f"✅ Acteur Admin créé : Administration AFOR (ID: {admin_acteur_id})")

        # ── 3. Créer l'acteur Responsable ─────────────────────────────────
        respo_acteur_id = str(uuid.uuid4())
        existing_respo = db.query(Acteur).filter(Acteur.type_acteur == 'RESPO').first()
        if existing_respo:
            print(f"ℹ️  Acteur Responsable existe déjà : {existing_respo.nom} (ID: {existing_respo.id})")
            respo_acteur_id = existing_respo.id
        else:
            respo_acteur = Acteur(
                id=respo_acteur_id,
                nom="Responsable AFOR",
                type_acteur="RESPO",
                contact_1=afor.contact_1,
                email_1=afor.email_1,
                adresse_1=afor.adresse_1,
            )
            db.add(respo_acteur)
            db.flush()
            print(f"✅ Acteur Responsable créé : Responsable AFOR (ID: {respo_acteur_id})")

        # ── 4. Créer le login Admin ───────────────────────────────────────
        admin_username = "admin_afor"
        admin_password = "Admin@2026"

        existing_login = db.query(Login).filter(Login.username == admin_username).first()
        if existing_login:
            print(f"ℹ️  Login admin '{admin_username}' existe déjà.")
        else:
            admin_login = Login(
                id=str(uuid.uuid4()),
                username=admin_username,
                password=hash_password(admin_password),
                acteur_id=admin_acteur_id,
            )
            db.add(admin_login)
            db.flush()

            # Créer l'entrée Administrateur
            admin_entry = Administrateur(
                id=str(uuid.uuid4()),
                login_id=admin_login.id,
                nom="OUATTARA",
                prenom="Admin",
                email=afor.email_1 or "admin@afor.bf",
                role="super_admin",
            )
            db.add(admin_entry)
            print(f"✅ Login Admin créé : {admin_username} / {admin_password}")

        # ── 5. Créer le login Responsable ─────────────────────────────────
        respo_username = "respo_afor"
        respo_password = "Respo@2026"

        existing_login = db.query(Login).filter(Login.username == respo_username).first()
        if existing_login:
            print(f"ℹ️  Login responsable '{respo_username}' existe déjà.")
        else:
            respo_login = Login(
                id=str(uuid.uuid4()),
                username=respo_username,
                password=hash_password(respo_password),
                acteur_id=respo_acteur_id,
            )
            db.add(respo_login)
            print(f"✅ Login Responsable créé : {respo_username} / {respo_password}")

        # ── 6. Commit ─────────────────────────────────────────────────────
        db.commit()

        print("\n" + "=" * 60)
        print("  RÉCAPITULATIF DES COMPTES CRÉÉS")
        print("=" * 60)
        print(f"  🔐 Admin       : {admin_username} / {admin_password}")
        print(f"     → Redirigé vers : /admin/dashboard")
        print(f"  🔐 Responsable : {respo_username} / {respo_password}")
        print(f"     → Redirigé vers : /responsable/dashboard")
        print("=" * 60)
        print("\n⚠️  Changez les mots de passe après la première connexion !")

    except Exception as e:
        db.rollback()
        print(f"❌ Erreur : {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    create_users()
