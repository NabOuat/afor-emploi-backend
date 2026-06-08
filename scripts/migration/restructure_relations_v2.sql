-- Migration V2: Restructurer les relations
-- Structure finale: acteur (1) -> (N) fic_personne_projet (N) <- (1) projet
-- fic_personne n'a AUCUNE relation directe avec acteur

-- ÉTAPE 1: Supprimer la contrainte de clé étrangère acteur_id de fic_personne (si elle existe)
ALTER TABLE fic_personne 
DROP CONSTRAINT IF EXISTS fic_personne_acteur_id_fkey;

-- ÉTAPE 2: Supprimer la colonne acteur_id de fic_personne
ALTER TABLE fic_personne 
DROP COLUMN IF EXISTS acteur_id;

-- ÉTAPE 3: Ajouter la colonne acteur_id à fic_personne_projet (si elle n'existe pas)
ALTER TABLE fic_personne_projet 
ADD COLUMN IF NOT EXISTS acteur_id VARCHAR(36);

-- ÉTAPE 4: Peupler acteur_id dans fic_personne_projet à partir des données existantes
-- Récupérer l'acteur_id depuis la table fic_personne avant suppression (via une requête temporaire)
-- Si la colonne acteur_id existe encore dans fic_personne, utiliser cette requête:
UPDATE fic_personne_projet fpp
SET acteur_id = (
    SELECT DISTINCT fp.acteur_id
    FROM fic_personne fp
    WHERE fp.id = fpp.fic_personne_id
    LIMIT 1
)
WHERE fpp.acteur_id IS NULL
AND EXISTS (
    SELECT 1 FROM fic_personne fp
    WHERE fp.id = fpp.fic_personne_id
    AND fp.acteur_id IS NOT NULL
);

-- ÉTAPE 5: Ajouter la contrainte NOT NULL et la clé étrangère
ALTER TABLE fic_personne_projet
ALTER COLUMN acteur_id SET NOT NULL;

ALTER TABLE fic_personne_projet
ADD CONSTRAINT IF NOT EXISTS fk_fic_personne_projet_acteur 
FOREIGN KEY (acteur_id) REFERENCES acteur(id) ON DELETE CASCADE;

-- ÉTAPE 6: Ajouter les index pour les requêtes
CREATE INDEX IF NOT EXISTS idx_fic_personne_projet_acteur_id 
ON fic_personne_projet(acteur_id);

CREATE INDEX IF NOT EXISTS idx_fic_personne_projet_fic_personne_id 
ON fic_personne_projet(fic_personne_id);

CREATE INDEX IF NOT EXISTS idx_fic_personne_projet_projet_id 
ON fic_personne_projet(projet_id);

-- ÉTAPE 7: Vérifier l'intégrité des données
-- Afficher les employés sans projet
SELECT 
    fp.id,
    fp.nom,
    fp.prenom,
    COUNT(fpp.id) as nb_projets
FROM fic_personne fp
LEFT JOIN fic_personne_projet fpp ON fpp.fic_personne_id = fp.id
GROUP BY fp.id, fp.nom, fp.prenom
HAVING COUNT(fpp.id) = 0;

-- ÉTAPE 8: Afficher les statistiques finales
SELECT 
    a.id,
    a.nom as acteur_nom,
    COUNT(DISTINCT fpp.fic_personne_id) as nb_employees,
    COUNT(DISTINCT fpp.projet_id) as nb_projects,
    COUNT(fpp.id) as nb_relations
FROM acteur a
LEFT JOIN fic_personne_projet fpp ON fpp.acteur_id = a.id
GROUP BY a.id, a.nom
ORDER BY nb_relations DESC;

-- ÉTAPE 9: Vérifier la structure finale
-- Afficher les relations par acteur et projet
SELECT 
    a.nom as acteur_nom,
    p.nom as projet_nom,
    COUNT(fpp.fic_personne_id) as nb_employees
FROM acteur a
LEFT JOIN fic_personne_projet fpp ON fpp.acteur_id = a.id
LEFT JOIN projet p ON p.id = fpp.projet_id
GROUP BY a.id, a.nom, p.id, p.nom
ORDER BY a.nom, p.nom;
