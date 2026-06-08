@echo off
echo Exportation des donnees de la base locale vers des fichiers SQL...

REM Configuration
set PGUSER=postgres
set PGPASSWORD=Nabaga
set PGHOST=localhost
set PGDATABASE=emploi
set OUTPUT_DIR=%~dp0exports

REM Creer le repertoire de sortie s'il n'existe pas
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"

REM Liste des tables a exporter
set TABLES=acteurs projets engagement fic_personne utilisateurs tregion tdepartement tsousprefecture zone_d_intervention fic_personne_acteur fic_personne_projet supervision contrats fic_personne_localisation projet_engagement user_actions

REM Exporter chaque table
for %%t in (%TABLES%) do (
    echo Exportation de la table %%t...
    pg_dump -h %PGHOST% -U %PGUSER% -d %PGDATABASE% -t %%t --data-only --column-inserts > "%OUTPUT_DIR%\%%t.sql"
)

echo Exportation terminee. Les fichiers sont dans le dossier %OUTPUT_DIR%
pause
