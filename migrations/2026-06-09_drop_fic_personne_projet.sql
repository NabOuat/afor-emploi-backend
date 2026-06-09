-- ============================================================================
--  Migration : suppression de fic_personne_projet
--  L'acteur d'un employé devient une colonne de fic_personne (1 acteur / employé).
--  Le projet reste porté par le contrat (contrat.projet_id).
--  Idempotente — rejouable sans risque.
-- ============================================================================

-- 1) Nouvelle colonne sur fic_personne
ALTER TABLE public."fic_personne" ADD COLUMN IF NOT EXISTS "acteur_id" VARCHAR;

-- 2) Recopier l'acteur depuis l'ancienne table (si elle existe encore et a des données).
--    On prend un acteur par personne (le premier).
UPDATE public."fic_personne" fp
SET acteur_id = sub.acteur_id
FROM (
    SELECT DISTINCT ON (fic_personne_id) fic_personne_id, acteur_id
    FROM public."fic_personne_projet"
    ORDER BY fic_personne_id
) sub
WHERE sub.fic_personne_id = fp.id AND fp.acteur_id IS NULL;

-- 3) Clé étrangère (créée seulement si absente)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fic_personne_acteur_id_fkey'
    ) THEN
        ALTER TABLE public."fic_personne"
            ADD CONSTRAINT "fic_personne_acteur_id_fkey"
            FOREIGN KEY (acteur_id) REFERENCES public."acteur" (id) ON DELETE CASCADE;
    END IF;
END$$;

-- 4) Index
CREATE INDEX IF NOT EXISTS idx_fic_personne_acteur_id
    ON public.fic_personne (acteur_id);

-- 5) Supprimer l'ancienne table (et la table morte fic_personne_acteur si présente)
DROP TABLE IF EXISTS public."fic_personne_projet" CASCADE;
DROP TABLE IF EXISTS public."fic_personne_acteur" CASCADE;
