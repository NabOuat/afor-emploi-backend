# Système d'Import de Données - Emploi DB

Application Flask pour importer les données `fic_personne` depuis un fichier CSV vers une base de données PostgreSQL avec la nouvelle structure.

## 📋 Table des matières

- [Installation](#installation)
- [Configuration](#configuration)
- [Utilisation](#utilisation)
- [API Endpoints](#api-endpoints)
- [Structure des données](#structure-des-données)
- [Dépannage](#dépannage)

## 🚀 Installation

### Prérequis

- Python 3.7+
- PostgreSQL 10+
- pip (gestionnaire de paquets Python)

### Étapes d'installation

1. **Cloner ou télécharger le projet**

```bash
cd "c:\Users\OUATTARA AFOR\Desktop\The Box\Web\Emploi"
```

2. **Créer un environnement virtuel (optionnel mais recommandé)**

```bash
python -m venv venv
venv\Scripts\activate
```

3. **Installer les dépendances**

```bash
pip install -r requirements.txt
```

## ⚙️ Configuration

### Fichier .env

Créer ou modifier le fichier `.env` à la racine du projet :

```env
FLASK_APP=run.py
FLASK_ENV=development
DATABASE_URL=postgresql://postgres:Nabaga@localhost:5432/emploidb?client_encoding=utf8
SECRET_KEY=your-secret-key-here
PORT=5000
```

**Variables importantes :**

- `FLASK_ENV`: `development` ou `production`
- `DATABASE_URL`: URL de connexion PostgreSQL
- `SECRET_KEY`: Clé secrète pour Flask (à changer en production)
- `PORT`: Port d'écoute (par défaut 5000)

## 📖 Utilisation

### Option 1 : Utiliser le script CLI (Recommandé)

```bash
python cli_import.py "c:\Users\OUATTARA AFOR\Desktop\The Box\Web\Emploi\images\fic_personne.txt"
```

**Exemple de sortie :**

```
============================================================
IMPORT DES DONNÉES FIC_PERSONNE
============================================================
📂 Fichier source: c:\Users\OUATTARA AFOR\Desktop\The Box\Web\Emploi\images\fic_personne.txt
📊 Taille: 2.45 MB

🔗 Connexion à: localhost:5432/emploidb

⏳ Démarrage de l'import...

✓ 100 enregistrements insérés...
✓ 200 enregistrements insérés...
✓ 300 enregistrements insérés...

============================================================
RÉSUMÉ DE L'IMPORT
============================================================
✓ Enregistrements insérés: 1280
⚠️  Enregistrements ignorés: 0
❌ Erreurs: 0
============================================================

✅ Import terminé avec succès!
```

### Option 2 : Utiliser l'API Flask

1. **Démarrer le serveur Flask**

```bash
python run.py
```

Le serveur démarre sur `http://localhost:5000`

2. **Appeler l'endpoint d'import**

```bash
curl -X POST http://localhost:5000/api/import/fic-personne \
  -H "Content-Type: application/json" \
  -d "{\"csv_file_path\": \"c:\\Users\\OUATTARA AFOR\\Desktop\\The Box\\Web\\Emploi\\images\\fic_personne.txt\"}"
```

## 🔌 API Endpoints

### 1. Health Check

```
GET /health
```

Vérifier la santé de l'application et la connexion à la base de données.

**Réponse (200) :**
```json
{
  "status": "healthy",
  "message": "Application et base de données sont opérationnelles"
}
```

### 2. Import fic_personne

```
POST /api/import/fic-personne
```

Importer les données depuis un fichier CSV.

**Body :**
```json
{
  "csv_file_path": "c:\\Users\\OUATTARA AFOR\\Desktop\\The Box\\Web\\Emploi\\images\\fic_personne.txt"
}
```

**Réponse (200) :**
```json
{
  "status": "success",
  "message": "Import terminé avec succès",
  "summary": {
    "inserted": 1280,
    "skipped": 0,
    "errors": 0
  }
}
```

### 3. Statistiques fic_personne

```
GET /api/stats/fic-personne
```

Récupérer le nombre total d'enregistrements dans la table `fic_personne`.

**Réponse (200) :**
```json
{
  "status": "success",
  "table": "fic_personne",
  "total_records": 1280
}
```

### 4. Vérifier les acteurs

```
GET /api/verify/acteurs
```

Récupérer les 20 premiers acteurs disponibles.

**Réponse (200) :**
```json
{
  "status": "success",
  "acteurs": [
    {
      "id": "7bde678e-ac7a-4ba6-bee4-b3afa0215c2b",
      "nom": "GROUPEMENT GEOART / SETOM / CGEKA",
      "type": "operateur"
    }
  ]
}
```

### 5. Vérifier les projets

```
GET /api/verify/projets
```

Récupérer les 20 premiers projets disponibles.

**Réponse (200) :**
```json
{
  "status": "success",
  "projets": [
    {
      "id": "PASFOR-2025-1",
      "nom": "Projet PASFOR 2025"
    }
  ]
}
```

## 📊 Structure des données

### Fichier CSV source (fic_personne.txt)

**Colonnes :**
```
0:  id (UUID)
1:  nom (VARCHAR)
2:  prenom (VARCHAR)
3:  contact (VARCHAR)
4:  date_naissance (DATE: YYYY-MM-DD)
5:  genre (VARCHAR: M/F)
6:  type_contrat (VARCHAR)
7:  acteur_id (UUID)
8:  (vide)
9:  (vide)
10: (vide)
11: qualification (VARCHAR)
12: numero_dossier (VARCHAR)
13: date_creation (DATE: YYYY-MM-DD)
```

### Table cible (fic_personne)

**Colonnes :**
```
id                  CHARACTER VARYING PRIMARY KEY
acteur_id           CHARACTER VARYING NOT NULL (FK -> acteur.id)
projet_id           CHARACTER VARYING NOT NULL (FK -> projet.id)
nom                 CHARACTER VARYING NOT NULL
prenom              CHARACTER VARYING NOT NULL
date_naissance      DATE
genre               CHARACTER VARYING
contact             CHARACTER VARYING
```

## 🔍 Dépannage

### Erreur : "Fichier non trouvé"

```
❌ Fichier non trouvé: c:\Users\OUATTARA AFOR\Desktop\The Box\Web\Emploi\images\fic_personne.txt
```

**Solution :** Vérifier que le chemin du fichier est correct et que le fichier existe.

### Erreur : "DATABASE_URL non définie"

```
❌ DATABASE_URL non définie dans .env
```

**Solution :** Créer ou modifier le fichier `.env` avec la variable `DATABASE_URL`.

### Erreur : "Impossible de se connecter à la base de données"

```
❌ Erreur de connexion: could not connect to server
```

**Solutions :**
1. Vérifier que PostgreSQL est en cours d'exécution
2. Vérifier les identifiants dans `DATABASE_URL`
3. Vérifier que la base de données `emploidb` existe
4. Vérifier la connectivité réseau

### Erreur : "Acteur non trouvé"

```
⚠️  Ligne 5: Acteur 0dc52f9d-779e-4c26-90e3-9396b6878ef1 non trouvé
```

**Solution :** S'assurer que tous les acteurs sont insérés dans la table `acteur` avant d'importer les données `fic_personne`.

### Erreur : "Aucun projet disponible"

```
⚠️  Ligne 10: Aucun projet disponible
```

**Solution :** S'assurer qu'au moins un projet existe dans la table `projet`.

## 📝 Fichiers du projet

```
.
├── .env                      # Variables d'environnement
├── requirements.txt          # Dépendances Python
├── config.py                 # Configuration Flask
├── db.py                     # Classe Database pour connexion PostgreSQL
├── import_service.py         # Service d'import FicPersonneImporter
├── app.py                    # Application Flask avec routes
├── run.py                    # Point d'entrée Flask
├── cli_import.py             # Script CLI pour import
├── verify_import.py          # Script de vérification
└── README.md                 # Ce fichier
```

## 🧪 Vérification après import

Après l'import, vérifier les données :

```bash
python verify_import.py
```

Ou utiliser l'endpoint API :

```bash
curl http://localhost:5000/api/stats/fic-personne
```

## 📞 Support

Pour toute question ou problème, consulter les logs de l'application ou vérifier les erreurs dans la console.

## 📄 Licence

Propriétaire : AFOR
