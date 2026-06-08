# Guide de migration vers Supabase et déploiement en ligne

Ce guide vous explique comment migrer votre base de données vers Supabase et déployer votre application en ligne.

## 1. Configuration de Supabase

### 1.1 Créer un compte et un projet Supabase

1. Rendez-vous sur [Supabase](https://supabase.com/) et créez un compte
2. Créez un nouveau projet avec un nom (ex: "afor-emploi")
3. Choisissez une région proche de vos utilisateurs (ex: Europe)
4. Définissez un mot de passe pour la base de données
5. Notez les informations de connexion à la base de données (dans Project Settings > Database)

### 1.2 Créer le schéma de base de données

1. Dans le tableau de bord Supabase, allez dans "SQL Editor"
2. Créez un nouveau script
3. Copiez-collez le contenu du fichier `scripts/supabase_schema.sql`
4. Exécutez le script

## 2. Migration des données

### 2.1 Préparer l'environnement

1. Créez un fichier `.env` dans le dossier `scripts/` en vous basant sur `.env.example`
2. Remplissez les informations de connexion pour votre base de données source et Supabase

### 2.2 Installer les dépendances

```bash
pip install psycopg2-binary python-dotenv
```

### 2.3 Exécuter le script de migration

```bash
python scripts/migrate_to_supabase.py
```

Vous pouvez aussi spécifier les connexions en ligne de commande :

```bash
python scripts/migrate_to_supabase.py --source "postgresql://user:pass@host:port/db" --dest "postgresql://postgres:pass@db.supabase.co:5432/postgres"
```

Pour migrer seulement certaines tables :

```bash
python scripts/migrate_to_supabase.py --tables "acteurs,projets,fic_personne"
```

## 3. Mise à jour de l'application

### 3.1 Configuration du backend

1. Copiez le fichier `.env.supabase` vers `.env` dans le dossier `afor-emploi-backend/`
2. Modifiez les paramètres avec vos informations de connexion Supabase

```
DATABASE_URL=postgresql://postgres:votre_mot_de_passe@db.xxxxxxxxxxxx.supabase.co:5432/postgres
SECRET_KEY=votre_cle_secrete_pour_jwt
```

## 4. Déploiement en ligne

### 4.1 Déployer le backend

Vous pouvez déployer votre backend FastAPI sur plusieurs plateformes :

#### Option 1: Déploiement sur Render

1. Créez un compte sur [Render](https://render.com/)
2. Connectez votre dépôt GitHub
3. Créez un nouveau "Web Service"
4. Sélectionnez votre dépôt
5. Configurez le service :
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `cd afor-emploi-backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
6. Ajoutez les variables d'environnement (DATABASE_URL, SECRET_KEY, etc.)
7. Déployez

#### Option 2: Déploiement sur Railway

1. Créez un compte sur [Railway](https://railway.app/)
2. Créez un nouveau projet
3. Déployez depuis GitHub
4. Configurez les variables d'environnement
5. Déployez

### 4.2 Déployer le frontend

Pour déployer le frontend React :

1. Mettez à jour l'URL de l'API dans votre frontend pour pointer vers votre backend déployé
2. Déployez sur [Vercel](https://vercel.com/), [Netlify](https://www.netlify.com/) ou [GitHub Pages](https://pages.github.com/)

## 5. Vérification et tests

Après le déploiement :

1. Vérifiez que l'API fonctionne correctement
2. Testez les fonctionnalités principales de l'application
3. Vérifiez les journaux pour détecter d'éventuelles erreurs

## 6. Maintenance

- Sauvegardez régulièrement votre base de données Supabase
- Surveillez les performances et l'utilisation des ressources
- Mettez à jour les dépendances de sécurité
