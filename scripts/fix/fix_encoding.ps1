# Script PowerShell pour corriger l'encodage des caractères dans les fichiers SQL
# Corrige les problèmes d'encodage UTF-8 comme "├®" → "é"

$exportDir = Join-Path $PSScriptRoot "exports_complete"

Write-Host "Correction de l'encodage des fichiers dans: $exportDir" -ForegroundColor Cyan

# Fonction pour corriger l'encodage d'un fichier
function Fix-Encoding {
    param (
        [string]$FilePath
    )
    
    if (-not (Test-Path $FilePath)) {
        Write-Host "Fichier non trouvé: $FilePath" -ForegroundColor Yellow
        return
    }
    
    Write-Host "Correction de l'encodage de: $(Split-Path $FilePath -Leaf)" -ForegroundColor Green
    
    # Lire le contenu du fichier
    $content = Get-Content $FilePath -Raw -Encoding utf8
    
    # Corrections d'encodage courantes
    $fixes = @{
        '├®' = 'é'
        '├¿' = 'è'
        '├â' = 'â'
        '┬®' = 'é'
        '┬¬' = 'ê'
        '┬ª' = 'ê'
        '┬º' = 'ç'
        '┬á' = 'à'
        '┬╗' = 'ù'
        '┬┤' = 'ô'
        '┬«' = 'î'
        '┬»' = 'û'
        '┬┬' = 'Â'
        '┬┐' = 'À'
        '┬┬' = 'Â'
        '┬┬' = 'Â'
        '┬┬' = 'Â'
    }
    
    # Appliquer les corrections
    foreach ($wrong in $fixes.Keys) {
        $correct = $fixes[$wrong]
        $content = $content -replace [regex]::Escape($wrong), $correct
    }
    
    # Écrire le contenu corrigé
    $content | Out-File -FilePath $FilePath -Encoding utf8 -Force
}

# Corriger tous les fichiers SQL dans le dossier d'export
$sqlFiles = Get-ChildItem -Path $exportDir -Filter "*.sql" -File

foreach ($file in $sqlFiles) {
    Fix-Encoding -FilePath $file.FullName
}

Write-Host "Correction de l'encodage terminée !" -ForegroundColor Green
