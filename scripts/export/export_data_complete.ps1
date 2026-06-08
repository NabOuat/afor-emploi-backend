# Script PowerShell pour exporter les données vers Supabase (version complète)
# Configuration de la base de données source
$sourceConfig = @{
    Host = if ($env:SOURCE_DB_HOST) { $env:SOURCE_DB_HOST } else { "localhost" }
    Port = if ($env:SOURCE_DB_PORT) { [int]$env:SOURCE_DB_PORT } else { 5432 }
    Database = if ($env:SOURCE_DB_NAME) { $env:SOURCE_DB_NAME } else { "emploi" }
    User = if ($env:SOURCE_DB_USER) { $env:SOURCE_DB_USER } else { "postgres" }
    Password = if ($env:SOURCE_DB_PASSWORD) { $env:SOURCE_DB_PASSWORD } else { "" }
}

# Configuration de la base de données Supabase
$supabaseConfig = @{
    Host = if ($env:SUPABASE_DB_HOST) { $env:SUPABASE_DB_HOST } else { "" }
    Port = if ($env:SUPABASE_DB_PORT) { [int]$env:SUPABASE_DB_PORT } else { 5432 }
    Database = if ($env:SUPABASE_DB_NAME) { $env:SUPABASE_DB_NAME } else { "postgres" }
    User = if ($env:SUPABASE_DB_USER) { $env:SUPABASE_DB_USER } else { "postgres" }
    Password = if ($env:SUPABASE_DB_PASSWORD) { $env:SUPABASE_DB_PASSWORD } else { "" }
}

# Créer le dossier d'export s'il n'existe pas
$exportDir = Join-Path $PSScriptRoot "exports_complete"
if (-not (Test-Path $exportDir)) {
    New-Item -ItemType Directory -Path $exportDir | Out-Null
    Write-Host "Dossier d'export créé: $exportDir"
}

# Liste des tables à exporter (dans l'ordre pour respecter les dépendances)
# Basé sur la structure complète de votre base de données
$tables = @(
    "tregion",
    "tdepartement", 
    "tsousprefecture",
    "acteur", 
    "projet", 
    "engagement",
    "projet_engagement", 
    "zone_d_intervention",
    "fic_personne",
    "login",
    "administrateur",
    "fic_personne_projet",
    "supervision", 
    "contrat",
    "fic_personne_localisation",
    "user_actions"
)

# Fonction pour exporter une table
function Export-Table {
    param (
        [string]$TableName
    )
    
    $outputFile = Join-Path $exportDir "$TableName.sql"
    
    Write-Host "Exportation de la table $TableName..."
    
    # Commande pg_dump pour exporter uniquement les données (pas la structure)
    $pgDumpCmd = "pg_dump -h $($sourceConfig.Host) -p $($sourceConfig.Port) -U $($sourceConfig.User) " +
                 "-d $($sourceConfig.Database) -t $TableName --data-only --column-inserts > `"$outputFile`""
    
    # Définir la variable d'environnement PGPASSWORD pour l'authentification
    $env:PGPASSWORD = $sourceConfig.Password
    
    # Exécuter la commande
    Invoke-Expression "cmd /c $pgDumpCmd"
    
    if (Test-Path $outputFile) {
        $fileSize = (Get-Item $outputFile).Length
        if ($fileSize -gt 0) {
            Write-Host "Table $TableName exportée avec succès ($fileSize octets)" -ForegroundColor Green
            return $true
        } else {
            Write-Host "La table $TableName a été exportée mais le fichier est vide" -ForegroundColor Yellow
            return $false
        }
    } else {
        Write-Host "Échec de l'exportation de la table $TableName" -ForegroundColor Red
        return $false
    }
}

# Fonction pour créer un fichier SQL combiné
function Create-CombinedSqlFile {
    $combinedFile = Join-Path $exportDir "all_data.sql"
    
    Write-Host "Création du fichier SQL combiné..."
    
    # Supprimer le fichier s'il existe déjà
    if (Test-Path $combinedFile) {
        Remove-Item $combinedFile
    }
    
    # Ajouter un en-tête
    @"
-- Fichier d'export combiné pour Supabase
-- Date: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
-- Base de données source: $($sourceConfig.Database)
-- Script de schéma utilisé: supabase_schema_complete.sql

"@ | Out-File -FilePath $combinedFile -Encoding utf8
    
    # Ajouter chaque fichier de table dans l'ordre
    foreach ($table in $tables) {
        $tableFile = Join-Path $exportDir "$table.sql"
        if (Test-Path $tableFile) {
            @"
-- ========================================
-- Données pour la table $table
-- ========================================

"@ | Out-File -FilePath $combinedFile -Append -Encoding utf8
            
            Get-Content $tableFile -Encoding utf8 | Out-File -FilePath $combinedFile -Append -Encoding utf8
            
            @"

"@ | Out-File -FilePath $combinedFile -Append -Encoding utf8
        }
    }
    
    Write-Host "Fichier SQL combiné créé: $combinedFile" -ForegroundColor Green
}

# Exporter toutes les tables
Write-Host "Début de l'exportation des données..." -ForegroundColor Cyan
$successCount = 0

foreach ($table in $tables) {
    if (Export-Table -TableName $table) {
        $successCount++
    }
}

# Créer le fichier SQL combiné
Create-CombinedSqlFile

Write-Host "Exportation terminée: $successCount / $($tables.Count) tables exportées avec succès" -ForegroundColor Cyan
Write-Host "Les fichiers SQL sont disponibles dans: $exportDir" -ForegroundColor Cyan

# Instructions pour l'importation dans Supabase
Write-Host @"

=================================================================
INSTRUCTIONS POUR IMPORTER LES DONNÉES DANS SUPABASE
=================================================================

1. Connectez-vous à votre projet Supabase: https://app.supabase.io
2. Allez dans "SQL Editor"
3. Créez un nouveau script
4. Copiez-collez d'abord le contenu du fichier 'supabase_schema_complete.sql' 
   pour créer la structure de la base de données complète
5. Exécutez ce script
6. Créez un nouveau script
7. Copiez-collez le contenu du fichier 'exports_complete/all_data.sql'
8. Exécutez ce script pour importer toutes les données

=================================================================
RÉCAPITULATIF DES CORRECTIONS:
- Ajout de la colonne 'matricule' dans la table fic_personne
- Correction complète de la table user_actions avec toutes les colonnes
- Ajout des colonnes 'type_contrat' et 'poste' dans la table contrat
- Maintien de la compatibilité avec votre structure de données existante

=================================================================
"@ -ForegroundColor Yellow

Write-Host "Appuyez sur une touche pour quitter..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
