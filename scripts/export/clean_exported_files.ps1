# Script PowerShell pour nettoyer les fichiers exportés PostgreSQL
# Supprime les commandes spécifiques à PostgreSQL qui ne sont pas compatibles avec Supabase

$exportDir = Join-Path $PSScriptRoot "exports_complete"

Write-Host "Nettoyage des fichiers exportés dans: $exportDir" -ForegroundColor Cyan

# Fonction pour nettoyer un fichier SQL
function Clean-SqlFile {
    param (
        [string]$FilePath
    )
    
    if (-not (Test-Path $FilePath)) {
        Write-Host "Fichier non trouvé: $FilePath" -ForegroundColor Yellow
        return
    }
    
    Write-Host "Nettoyage de: $(Split-Path $FilePath -Leaf)" -ForegroundColor Green
    
    # Lire le contenu du fichier
    $content = Get-Content $FilePath -Raw -Encoding utf8
    
    # Supprimer les lignes problématiques
    $cleanedContent = $content -replace '\\restrict\s+[A-Za-z0-9]+\s*', '' `
                                 -replace 'SET statement_timeout = \d+;', '' `
                                 -replace 'SET lock_timeout = \d+;', '' `
                                 -replace 'SET idle_in_transaction_session_timeout = \d+;', '' `
                                 -replace 'SET client_encoding = .+;', '' `
                                 -replace 'SET standard_conforming_strings = .+;', '' `
                                 -replace 'SET check_function_bodies = false;', '' `
                                 -replace 'SET xmloption = content;', '' `
                                 -replace 'SET client_min_messages = warning;', '' `
                                 -replace 'SET row_security = off;', '' `
                                 -replace 'SET default_table_access_method = heap;', '' `
                                 -replace 'SET default_tablespace = .+;', '' `
                                 -replace 'SET default_toast_compression = .+;', '' `
                                 -replace '-- Dumped from database version \d+\.\d+', '' `
                                 -replace '-- Dumped by pg_dump version \d+\.\d+', '' `
                                 -replace '-- PostgreSQL database dump', '' `
                                 -replace '--\s*\n\s*\n', '--' `
                                 -replace '\n\s*\n\s*\n', "\n"
    
    # Écrire le contenu nettoyé
    $cleanedContent | Out-File -FilePath $FilePath -Encoding utf8 -Force
}

# Nettoyer tous les fichiers SQL dans le dossier d'export
$sqlFiles = Get-ChildItem -Path $exportDir -Filter "*.sql" -File

foreach ($file in $sqlFiles) {
    Clean-SqlFile -FilePath $file.FullName
}

# Créer un fichier combiné nettoyé
$combinedFile = Join-Path $exportDir "all_data_clean.sql"

Write-Host "Création du fichier combiné nettoyé..." -ForegroundColor Cyan

# Supprimer le fichier combiné s'il existe
if (Test-Path $combinedFile) {
    Remove-Item $combinedFile
}

# Ajouter un en-tête propre
@"
-- Fichier d'export combiné pour Supabase (nettoyé)
-- Date: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
-- Base de données source: emploi
-- Compatible: Supabase PostgreSQL

"@ | Out-File -FilePath $combinedFile -Encoding utf8

# Ajouter chaque fichier de table dans l'ordre
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

Write-Host "Nettoyage terminé !" -ForegroundColor Green
Write-Host "Fichier combiné nettoyé: $combinedFile" -ForegroundColor Cyan
Write-Host "Les fichiers originaux ont été nettoyés sur place" -ForegroundColor Cyan

Write-Host @"

=================================================================
INSTRUCTIONS POUR IMPORTER LES DONNÉES NETTOYÉES
=================================================================

1. Connectez-vous à votre projet Supabase: https://app.supabase.io
2. Allez dans "SQL Editor"
3. Exécutez d'abord le script 'drop_all_tables.sql' pour nettoyer
4. Exécutez ensuite le script 'supabase_schema_final.sql' pour créer les tables
5. Enfin, copiez-collez le contenu du fichier 'exports_complete/all_data_clean.sql'
6. Exécutez ce script pour importer toutes les données

Le fichier 'all_data_clean.sql' est maintenant compatible avec Supabase !

=================================================================
"@ -ForegroundColor Yellow
