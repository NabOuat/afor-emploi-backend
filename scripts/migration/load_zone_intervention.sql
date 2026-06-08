-- Script SQL pour charger les données zone_d_intervention depuis le fichier CSV
-- Exécuter ce script dans pgAdmin ou psql

-- Créer la table temporaire pour importer les données
CREATE TEMP TABLE zone_d_intervention_temp (
    id VARCHAR(255),
    acteur_id VARCHAR(255),
    projet_id VARCHAR(255),
    region_id VARCHAR(255),
    departement_id VARCHAR(255),
    sous_prefecture_id VARCHAR(255)
);

-- Importer les données depuis le fichier CSV
\COPY zone_d_intervention_temp FROM 'C:/Users/OUATTARA AFOR/Desktop/The Box/Web/Emploi/scripts/migration/zoned''interv.csv' WITH (FORMAT csv, DELIMITER ',', QUOTE '"', ESCAPE '''');

-- Insérer les données dans la table zone_d_intervention
INSERT INTO public.zone_d_intervention (id, acteur_id, projet_id, region_id, departement_id, sous_prefecture_id)
SELECT 
    id,
    acteur_id,
    projet_id,
    NULLIF(region_id, '')::UUID,
    NULLIF(departement_id, '')::INTEGER,
    NULLIF(sous_prefecture_id, '')
FROM zone_d_intervention_temp
ON CONFLICT (id) DO UPDATE SET
    acteur_id = EXCLUDED.acteur_id,
    projet_id = EXCLUDED.projet_id,
    region_id = EXCLUDED.region_id,
    departement_id = EXCLUDED.departement_id,
    sous_prefecture_id = EXCLUDED.sous_prefecture_id;

-- Afficher le nombre de lignes insérées
SELECT COUNT(*) as total_inserted FROM public.zone_d_intervention;

-- Afficher quelques exemples
SELECT id, acteur_id, projet_id, region_id, departement_id, sous_prefecture_id
FROM public.zone_d_intervention
LIMIT 10;
