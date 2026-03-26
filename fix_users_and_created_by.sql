-- ============================================
-- 1. Retirer la contrainte UNIQUE sur acteur_id dans users
-- ============================================
-- Trouver le nom exact de la contrainte
-- SELECT constraint_name FROM information_schema.table_constraints 
-- WHERE table_name = 'users' AND constraint_type = 'UNIQUE';

ALTER TABLE users DROP CONSTRAINT IF EXISTS login_acteur_id_key;
ALTER TABLE users DROP CONSTRAINT IF EXISTS users_acteur_id_key;

-- ============================================
-- 2. Ajouter la colonne created_by dans fic_personne
--    (FK vers users.id, nullable car les anciens enregistrements n'ont pas cette info)
-- ============================================
ALTER TABLE fic_personne 
ADD COLUMN IF NOT EXISTS created_by VARCHAR REFERENCES users(id) ON DELETE SET NULL;

-- ============================================
-- 3. Créer un index pour accélérer les requêtes par créateur
-- ============================================
CREATE INDEX IF NOT EXISTS idx_fic_personne_created_by ON fic_personne(created_by);

-- ============================================
-- VERIFICATION
-- ============================================
-- SELECT column_name, data_type, is_nullable 
-- FROM information_schema.columns 
-- WHERE table_name = 'fic_personne' AND column_name = 'created_by';
