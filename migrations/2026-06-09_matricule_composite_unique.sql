-- Migration : contrainte matricule unique par acteur (et non globale)
-- Deux opérateurs différents peuvent avoir des employés avec le même matricule.
-- Avant : UNIQUE(matricule)  →  Après : UNIQUE(acteur_id, matricule)

-- Supprimer l'ancienne contrainte unique globale (si elle existe)
ALTER TABLE fic_personne DROP CONSTRAINT IF EXISTS fic_personne_matricule_key;

-- Créer la contrainte composite
ALTER TABLE fic_personne
    ADD CONSTRAINT uq_fic_personne_acteur_matricule
    UNIQUE (acteur_id, matricule);
