# Guide de Migration Complète vers Supabase

Ce guide vous explique comment migrer votre base de données AFOR Emploi vers Supabase avec toutes les tables et colonnes correctes.

## 📋 Fichiers créés

### Scripts SQL
- `supabase_schema_complete.sql` - Schéma complet de la base de données pour Supabase
- `supabase_schema_corrected.sql` - Version précédente (obsolète)

### Scripts d'exportation
- `export_data_complete.ps1` - Script PowerShell pour exporter toutes les données
- `export_data_corrected.ps1` - Version précédente (obsolète)

## 🔧 Corrections apportées

### 1. Table `fic_personne`
- ✅ Ajout de la colonne `matricule` (VARCHAR, nullable)

### 2. Table `contrat`
- ✅ Ajout de la colonne `type_contrat` (VARCHAR, nullable)
- ✅ Ajout de la colonne `poste` (VARCHAR, nullable)

### 3. Table `user_actions`
- ✅ Correction complète avec toutes les colonnes :
  - `login_id` (VARCHAR(255))
  - `username` (VARCHAR(255))
  - `acteur_id` (VARCHAR(255))
  - `action_type` (VARCHAR(100))
  - `action_description` (TEXT)
  - `resource_type` (VARCHAR(100))
  - `resource_id` (VARCHAR(255))
  - `ip_address` (VARCHAR(45))
  - `user_agent` (TEXT)
  - `status` (VARCHAR(50))
  - `created_at` (TIMESTAMP)

## 🚀 Étapes de migration

### Étape 1: Exporter les données

Exécutez le script PowerShell pour exporter toutes les données :

```powershell
cd "C:\Users\OUATTARA AFOR\Desktop\The Box\Web\Emploi"
powershell -ExecutionPolicy Bypass -File .\scripts\export_data_complete.ps1
```

Cela créera un dossier `exports_complete` avec :
- Un fichier SQL par table
- Un fichier combiné `all_data.sql`

### Étape 2: Créer le schéma sur Supabase

1. Connectez-vous à votre projet Supabase : https://app.supabase.io
2. Allez dans "SQL Editor"
3. Créez un nouveau script
4. Copiez-collez le contenu du fichier `supabase_schema_complete.sql`
5. Exécutez le script pour créer toutes les tables

### Étape 3: Importer les données

1. Dans l'éditeur SQL de Supabase, créez un nouveau script
2. Copiez-collez le contenu du fichier `exports_complete/all_data.sql`
3. Exécutez ce script pour importer toutes les données

### Étape 4: Vérifier l'importation

Après l'importation, vérifiez que toutes les données ont été correctement importées :
- Allez dans "Table Editor"
- Vérifiez le nombre de lignes dans chaque table
- Comparez avec votre base de données locale

## 📊 Tables migrées

| Table | Colonnes | Lignes (approx.) |
|-------|----------|------------------|
| tregion | 2 | 33 |
| tdepartement | 3 | 111 |
| tsousprefecture | 3 | 510 |
| acteur | 10 | 17 |
| projet | 3 | 4 |
| engagement | 4 | 4 |
| projet_engagement | 4 | 4 |
| zone_d_intervention | 4 | 60 |
| fic_personne | 8 | 1317 |
| login | 4 | 10 |
| administrateur | 8 | 0 |
| fic_personne_projet | 4 | 1318 |
| supervision | 5 | 0 |
| contrat | 13 | 1381 |
| fic_personne_localisation | 6 | 1238 |
| user_actions | 12 | 0 |

## ⚙️ Configuration de l'application

Votre application est déjà configurée pour utiliser Supabase avec les informations suivantes :

```env
DATABASE_URL=postgresql://postgres:<password>@db.<project-ref>.supabase.co:5432/postgres
SECRET_KEY=<your-secret-key>
```

## 🚨 Dépannage

### Si l'exportation échoue
- Vérifiez que PostgreSQL est en cours d'exécution
- Vérifiez les identifiants de connexion dans le script
- Assurez-vous que la base de données `emploi` existe

### Si l'importation échoue sur Supabase
- Vérifiez que le schéma a été créé correctement
- Vérifiez les contraintes de clé étrangère
- Exécutez les tables dans le bon ordre

### Si des données manquent
- Comparez les structures de tables
- Vérifiez les types de données
- Consultez les logs d'importation

## 🔄 Pour une nouvelle migration

Si vous devez refaire la migration :

1. Supprimez toutes les tables sur Supabase
2. Recréez le schéma avec `supabase_schema_complete.sql`
3. Réimportez les données avec `exports_complete/all_data.sql`

## 📝 Notes importantes

- Le script `supabase_schema_complete.sql` est la version définitive
- Utilisez toujours `export_data_complete.ps1` pour les exportations futures
- Les anciennes versions des scripts sont conservées pour référence
- La migration préserve l'intégrité des données et des relations

## 🎯 Prochaines étapes

1. ✅ Exporter les données avec le script complet
2. ✅ Créer le schéma sur Supabase
3. ✅ Importer les données
4. 🔄 Tester l'application avec Supabase
5. 🔄 Déployer l'application en ligne

---

**Date de création :** 24 Février 2026  
**Version :** 1.0 (Complète et corrigée)
