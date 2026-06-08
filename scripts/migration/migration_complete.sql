-- ============================================
-- SCRIPT DE MIGRATION COMPLET V1 -> V2
-- De postgres (ancienne) vers emploidb (nouvelle)
-- ============================================

-- ============================================
-- ÉTAPE 1 : CRÉER LES TABLES TEMPORAIRES AVEC LES DONNÉES DE L'ANCIENNE BD
-- Exécuter d'abord cette partie dans la base 'postgres'
-- ============================================

-- Créer des sauvegardes des anciennes tables
CREATE TABLE IF NOT EXISTS tregion_backup AS SELECT * FROM tregion;
CREATE TABLE IF NOT EXISTS tdepartement_backup AS SELECT * FROM tdepartement;
CREATE TABLE IF NOT EXISTS tsousprefecture_backup AS SELECT * FROM tsousprefecture;
CREATE TABLE IF NOT EXISTS toperateur_foncier_backup AS SELECT * FROM toperateur_foncier;
CREATE TABLE IF NOT EXISTS tecole_partenaire_backup AS SELECT * FROM tecole_partenaire;
CREATE TABLE IF NOT EXISTS tagence_execution_backup AS SELECT * FROM tagence_execution;
CREATE TABLE IF NOT EXISTS login_backup AS SELECT * FROM login;
CREATE TABLE IF NOT EXISTS administrateur_backup AS SELECT * FROM administrateur;
CREATE TABLE IF NOT EXISTS projet_backup AS SELECT * FROM projet;
CREATE TABLE IF NOT EXISTS zone_d_intervention_backup AS SELECT * FROM zone_d_intervention;
CREATE TABLE IF NOT EXISTS fic_personne_backup AS SELECT * FROM fic_personne;
CREATE TABLE IF NOT EXISTS contrat_backup AS SELECT * FROM contrat;
CREATE TABLE IF NOT EXISTS poste_backup AS SELECT * FROM poste;
CREATE TABLE IF NOT EXISTS fic_personne_localisation_backup AS SELECT * FROM fic_personne_localisation;
CREATE TABLE IF NOT EXISTS superviseurs_backup AS SELECT * FROM superviseurs;
CREATE TABLE IF NOT EXISTS supervisor_employee_backup AS SELECT * FROM supervisor_employee;

-- ============================================
-- ÉTAPE 2 : EXPORTER LES DONNÉES EN CSV (OPTIONNEL)
-- À exécuter manuellement dans psql si nécessaire :
-- psql -d postgres -c "\COPY tregion_backup TO '/tmp/tregion.csv' WITH CSV HEADER;"
-- ============================================
-- Les commandes \COPY ne peuvent pas être exécutées dans un script SQL
-- Utilisez les commandes psql directement si vous avez besoin d'exporter en CSV

-- ============================================
-- ÉTAPE 3 : MIGRATION DANS LA NOUVELLE BD 'emploidb'
-- À exécuter dans la base 'emploidb' APRÈS avoir créé les tables
-- ============================================

-- ============================================
-- 1. MIGRATION DES RÉGIONS
-- ============================================
INSERT INTO tregion (id, nom)
SELECT id, nom FROM dblink(
    'dbname=postgres',
    'SELECT id, nom FROM tregion_backup'
) AS t(id CHARACTER VARYING, nom CHARACTER VARYING)
ON CONFLICT (id) DO NOTHING;

-- ============================================
-- 2. MIGRATION DES DÉPARTEMENTS
-- ============================================
INSERT INTO tdepartement (id, nom, region_id)
SELECT id, nom, region_id FROM dblink(
    'dbname=postgres',
    'SELECT id, nom, region_id FROM tdepartement_backup'
) AS t(id CHARACTER VARYING, nom CHARACTER VARYING, region_id CHARACTER VARYING)
ON CONFLICT (id) DO NOTHING;

-- ============================================
-- 3. MIGRATION DES SOUS-PRÉFECTURES
-- ============================================
INSERT INTO tsousprefecture (id, nom, departement_id)
SELECT id, nom, departement_id FROM dblink(
    'dbname=postgres',
    'SELECT id, nom, departement_id FROM tsousprefecture_backup'
) AS t(id CHARACTER VARYING, nom CHARACTER VARYING, departement_id CHARACTER VARYING)
ON CONFLICT (id) DO NOTHING;

-- ============================================
-- 4. CONSOLIDATION DES ACTEURS
-- ============================================

-- Insérer les opérateurs
INSERT INTO acteur (id, nom, type_acteur, contact_1, contact_2, adresse_1, adresse_2, email_1, email_2, date_creation)
SELECT 
    id, nom, 'operateur', contact_1, contact_2, adresse_1, adresse_2, email_1, email_2, CURRENT_TIMESTAMP
FROM dblink(
    'dbname=postgres',
    'SELECT id, nom, contact_1, contact_2, adresse_1, adresse_2, email_1, email_2 FROM toperateur_foncier_backup'
) AS t(id CHARACTER VARYING, nom CHARACTER VARYING, contact_1 CHARACTER VARYING, contact_2 CHARACTER VARYING, 
       adresse_1 CHARACTER VARYING, adresse_2 CHARACTER VARYING, email_1 CHARACTER VARYING, email_2 CHARACTER VARYING)
ON CONFLICT (id) DO NOTHING;

-- Insérer les écoles partenaires
INSERT INTO acteur (id, nom, type_acteur, date_creation)
SELECT id, name, 'ecole', CURRENT_TIMESTAMP
FROM dblink(
    'dbname=postgres',
    'SELECT id, name FROM tecole_partenaire_backup'
) AS t(id CHARACTER VARYING, name CHARACTER VARYING)
ON CONFLICT (id) DO NOTHING;

-- Insérer les agences d'exécution
INSERT INTO acteur (id, nom, type_acteur, date_creation)
SELECT id, name, 'agence', CURRENT_TIMESTAMP
FROM dblink(
    'dbname=postgres',
    'SELECT id, name FROM tagence_execution_backup'
) AS t(id CHARACTER VARYING, name CHARACTER VARYING)
ON CONFLICT (id) DO NOTHING;

-- ============================================
-- 5. MIGRATION DES LOGINS
-- ============================================
INSERT INTO login (id, username, password, acteur_id)
SELECT 
    id, username, password,
    COALESCE(operateur_id, ecole_partenaire_id, agence_execution_id)
FROM dblink(
    'dbname=postgres',
    'SELECT id, username, password, operateur_id, ecole_partenaire_id, agence_execution_id FROM login_backup'
) AS t(id CHARACTER VARYING, username CHARACTER VARYING, password CHARACTER VARYING, 
       operateur_id CHARACTER VARYING, ecole_partenaire_id CHARACTER VARYING, agence_execution_id CHARACTER VARYING)
WHERE COALESCE(operateur_id, ecole_partenaire_id, agence_execution_id) IS NOT NULL
ON CONFLICT (id) DO NOTHING;

-- ============================================
-- 6. MIGRATION DES ADMINISTRATEURS
-- ============================================
INSERT INTO administrateur (id, nom, prenom, email, contact, role, date_creation)
SELECT id, nom, prenom, email, contact, role, date_creation
FROM dblink(
    'dbname=postgres',
    'SELECT id, nom, prenom, email, contact, role, date_creation FROM administrateur_backup'
) AS t(id CHARACTER VARYING, nom CHARACTER VARYING, prenom CHARACTER VARYING, email CHARACTER VARYING, 
       contact CHARACTER VARYING, role CHARACTER VARYING, date_creation TIMESTAMP)
ON CONFLICT (id) DO NOTHING;

-- ============================================
-- 7. MIGRATION DES PROJETS
-- ============================================
INSERT INTO projet (id, nom, nom_complet)
SELECT id, nom, "nom complet"
FROM dblink(
    'dbname=postgres',
    'SELECT id, nom, "nom complet" FROM projet_backup'
) AS t(id CHARACTER VARYING, nom CHARACTER VARYING, "nom complet" CHARACTER VARYING)
ON CONFLICT (id) DO NOTHING;

-- ============================================
-- 8. MIGRATION DES ZONES D'INTERVENTION
-- ============================================
INSERT INTO zone_d_intervention (id, acteur_id, projet_id, region_id)
SELECT 
    id,
    COALESCE(operateur_id, ecole_id, agence_id),
    projet_id,
    region_id
FROM dblink(
    'dbname=postgres',
    'SELECT id, operateur_id, ecole_id, agence_id, projet_id, region_id FROM zone_d_intervention_backup'
) AS t(id CHARACTER VARYING, operateur_id CHARACTER VARYING, ecole_id CHARACTER VARYING, agence_id CHARACTER VARYING,
       projet_id CHARACTER VARYING, region_id CHARACTER VARYING)
WHERE COALESCE(operateur_id, ecole_id, agence_id) IS NOT NULL
ON CONFLICT (id) DO NOTHING;

-- ============================================
-- 9. MIGRATION DES FICHES PERSONNE
-- ============================================
INSERT INTO fic_personne (id, acteur_id, nom, prenom, date_naissance, genre, contact)
SELECT 
    id,
    COALESCE(operateur_id, ecole_id, agence_id),
    nom,
    prenom,
    date_naissance,
    genre,
    contact
FROM dblink(
    'dbname=postgres',
    'SELECT id, operateur_id, ecole_id, agence_id, nom, prenom, date_naissance, genre, contact FROM fic_personne_backup'
) AS t(id CHARACTER VARYING, operateur_id CHARACTER VARYING, ecole_id CHARACTER VARYING, agence_id CHARACTER VARYING,
       nom CHARACTER VARYING, prenom CHARACTER VARYING, date_naissance DATE, genre CHARACTER VARYING, contact CHARACTER VARYING)
WHERE COALESCE(operateur_id, ecole_id, agence_id) IS NOT NULL
ON CONFLICT (id) DO NOTHING;

-- ============================================
-- 10. MIGRATION DES CONTRATS
-- ============================================
INSERT INTO contrat (id, fic_personne_id, poste_nom, categorie_poste, date_debut, date_fin, autre)
SELECT 
    c.id,
    c.fic_personne_id,
    p.poste,
    c.categorie_poste,
    c.date_debut,
    c.date_fin,
    c.autre
FROM dblink(
    'dbname=postgres',
    'SELECT id, fic_personne_id, poste_id, categorie_poste, date_debut, date_fin, autre FROM contrat_backup'
) AS c(id CHARACTER VARYING, fic_personne_id CHARACTER VARYING, poste_id CHARACTER VARYING, categorie_poste CHARACTER VARYING,
       date_debut DATE, date_fin DATE, autre TEXT)
LEFT JOIN dblink(
    'dbname=postgres',
    'SELECT id, poste FROM poste_backup'
) AS p(id CHARACTER VARYING, poste CHARACTER VARYING) ON c.poste_id = p.id
ON CONFLICT (id) DO NOTHING;

-- ============================================
-- 11. MIGRATION DES LOCALISATIONS
-- ============================================
INSERT INTO fic_personne_localisation (id, contrat_id, region_id, departement_id, sous_prefecture_id, date_debut)
SELECT id, contrat_id, region_id, departement_id, sous_prefecture_id, date_debut
FROM dblink(
    'dbname=postgres',
    'SELECT id, contrat_id, region_id, departement_id, sous_prefecture_id, date_debut FROM fic_personne_localisation_backup'
) AS t(id CHARACTER VARYING, contrat_id CHARACTER VARYING, region_id CHARACTER VARYING, departement_id CHARACTER VARYING,
       sous_prefecture_id CHARACTER VARYING, date_debut DATE)
ON CONFLICT (id) DO NOTHING;

-- ============================================
-- 12. MIGRATION DES SUPERVISIONS
-- ============================================
INSERT INTO supervision (id, fic_personne_id, superviseur_id, date_debut, date_fin)
SELECT 
    id,
    employee_id,
    supervisor_id,
    date_debut,
    date_fin
FROM dblink(
    'dbname=postgres',
    'SELECT id, employee_id, supervisor_id, date_debut, date_fin FROM supervisor_employee_backup'
) AS t(id CHARACTER VARYING, employee_id CHARACTER VARYING, supervisor_id CHARACTER VARYING, date_debut DATE, date_fin DATE)
ON CONFLICT (id) DO NOTHING;

-- ============================================
-- VÉRIFICATION FINALE
-- ============================================
SELECT 'Acteurs' as table_name, COUNT(*) as count FROM acteur
UNION ALL
SELECT 'Logins', COUNT(*) FROM login
UNION ALL
SELECT 'Administrateurs', COUNT(*) FROM administrateur
UNION ALL
SELECT 'Projets', COUNT(*) FROM projet
UNION ALL
SELECT 'Zones d''intervention', COUNT(*) FROM zone_d_intervention
UNION ALL
SELECT 'Fiches Personne', COUNT(*) FROM fic_personne
UNION ALL
SELECT 'Contrats', COUNT(*) FROM contrat
UNION ALL
SELECT 'Localisations', COUNT(*) FROM fic_personne_localisation
UNION ALL
SELECT 'Supervisions', COUNT(*) FROM supervision;
