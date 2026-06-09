-- Migration : index de performance
-- À exécuter une seule fois sur la base de données cible.
-- Tous les CREATE INDEX utilisent IF NOT EXISTS — sans risque si déjà présents.

-- ── fic_personne ───────────────────────────────────────────────────────────
-- L'acteur est désormais porté par la personne (colonne très filtrée :
-- dashboard, employees, responsible). Remplace l'ancien fic_personne_projet.
CREATE INDEX IF NOT EXISTS idx_fp_acteur_id
    ON fic_personne (acteur_id);

-- ── contrat ────────────────────────────────────────────────────────────────
-- Filtres fréquents : projet, statut actif (date_debut/date_fin) et jointure sur fic_personne
CREATE INDEX IF NOT EXISTS idx_contrat_fic_personne_id
    ON contrat (fic_personne_id);

CREATE INDEX IF NOT EXISTS idx_contrat_projet_id
    ON contrat (projet_id);

CREATE INDEX IF NOT EXISTS idx_contrat_dates
    ON contrat (date_debut, date_fin);

-- ── fic_personne_localisation ──────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_fpl_contrat_id
    ON fic_personne_localisation (contrat_id);

CREATE INDEX IF NOT EXISTS idx_fpl_region_id
    ON fic_personne_localisation (region_id);

-- ── fic_personne ───────────────────────────────────────────────────────────
-- Calculs d'âge et filtres démographiques
CREATE INDEX IF NOT EXISTS idx_fp_date_naissance
    ON fic_personne (date_naissance);

-- ── user_actions ───────────────────────────────────────────────────────────
-- Requêtes "dernière connexion" triées par created_at DESC
CREATE INDEX IF NOT EXISTS idx_user_actions_acteur_type_date
    ON user_actions (acteur_id, action_type, created_at DESC);

-- ── zone_d_intervention ────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_zone_acteur_id
    ON zone_d_intervention (acteur_id);

CREATE INDEX IF NOT EXISTS idx_zone_projet_id
    ON zone_d_intervention (projet_id);
