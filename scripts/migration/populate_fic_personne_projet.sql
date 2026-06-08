-- Migration: Peupler la table fic_personne_projet avec les données existantes
-- Cette migration peuple la table de jonction à partir des colonnes existantes

-- ÉTAPE 1: Vérifier si la table fic_personne_projet existe
SELECT EXISTS (
    SELECT 1 FROM information_schema.tables 
    WHERE table_name = 'fic_personne_projet'
) as table_exists;

-- ÉTAPE 2: Vérifier si la colonne acteur_id existe dans fic_personne
SELECT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'fic_personne' AND column_name = 'acteur_id'
) as acteur_id_exists;

-- ÉTAPE 3: Vérifier si la colonne projet_id existe dans fic_personne
SELECT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'fic_personne' AND column_name = 'projet_id'
) as projet_id_exists;

-- ÉTAPE 4: Supprimer les entrées existantes (optionnel, pour nettoyer)
-- TRUNCATE TABLE fic_personne_projet;

-- ÉTAPE 5: Peupler fic_personne_projet avec les données existantes
-- Insérer les relations depuis fic_personne vers fic_personne_projet
INSERT INTO fic_personne_projet (id, fic_personne_id, projet_id, acteur_id, date_debut, date_fin)
SELECT 
    gen_random_uuid()::text,
    fp.id,
    fp.projet_id,
    fp.acteur_id,
    NULL,
    NULL
FROM fic_personne fp
WHERE fp.projet_id IS NOT NULL
AND fp.acteur_id IS NOT NULL
ON CONFLICT (fic_personne_id, projet_id) DO NOTHING;

-- ÉTAPE 6: Vérifier le nombre de relations insérées
SELECT COUNT(*) as total_relations FROM fic_personne_projet;

-- ÉTAPE 7: Afficher les statistiques par acteur
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

-- ÉTAPE 8: Afficher les employés sans projet
SELECT 
    fp.id,
    fp.nom,
    fp.prenom,
    a.nom as acteur_nom,
    COUNT(fpp.id) as nb_projets
FROM fic_personne fp
LEFT JOIN acteur a ON a.id = fp.acteur_id
LEFT JOIN fic_personne_projet fpp ON fpp.fic_personne_id = fp.id
WHERE fp.projet_id IS NOT NULL
GROUP BY fp.id, fp.nom, fp.prenom, a.id, a.nom
HAVING COUNT(fpp.id) = 0
LIMIT 10;
