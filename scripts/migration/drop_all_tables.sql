-- Script pour supprimer toutes les tables existantes sur Supabase
-- Exécutez ce script AVANT de créer le nouveau schéma

-- Supprimer les tables dans le bon ordre (inverse des dépendances)
DROP TABLE IF EXISTS user_actions CASCADE;
DROP TABLE IF EXISTS fic_personne_localisation CASCADE;
DROP TABLE IF EXISTS contrat CASCADE;
DROP TABLE IF EXISTS supervision CASCADE;
DROP TABLE IF EXISTS fic_personne_projet CASCADE;
DROP TABLE IF EXISTS administrateur CASCADE;
DROP TABLE IF EXISTS login CASCADE;
DROP TABLE IF EXISTS zone_d_intervention CASCADE;
DROP TABLE IF EXISTS projet_engagement CASCADE;
DROP TABLE IF EXISTS engagement CASCADE;
DROP TABLE IF EXISTS projet CASCADE;
DROP TABLE IF EXISTS fic_personne CASCADE;
DROP TABLE IF EXISTS acteur CASCADE;
DROP TABLE IF EXISTS tsousprefecture CASCADE;
DROP TABLE IF EXISTS tdepartement CASCADE;
DROP TABLE IF EXISTS tregion CASCADE;

-- Message de confirmation
SELECT 'Toutes les tables ont été supprimées avec succès' as status;
