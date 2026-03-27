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


-- ============================================
-- 4. Créer un administrateur complet (acteur + user + administrateur)
--    ⚠️ Le mot de passe est hashé en bcrypt — généré via Python :
--       from passlib.context import CryptContext
--       CryptContext(schemes=["bcrypt"]).hash("Admin@2026")
--    Remplacer <BCRYPT_HASH> par le hash généré.
-- ============================================

-- 4a. Récupérer l'acteur AFOR existant pour copier ses infos
--     SELECT id, nom FROM acteur WHERE type_acteur = 'AF';

-- 4b. Créer l'acteur administrateur
INSERT INTO acteur (id, nom, type_acteur, date_creation)
VALUES (
    gen_random_uuid()::text,
    'Administration AFOR',
    'AD',
    NOW()
)
ON CONFLICT DO NOTHING;

-- 4c. Créer le user admin (lié à l'acteur AD)
--     ⚠️ Remplacer <BCRYPT_HASH> par le vrai hash bcrypt du mot de passe
INSERT INTO users (id, username, password, nom, prenom, acteur_id)
VALUES (
    gen_random_uuid()::text,
    'admin_afor',
    '<BCRYPT_HASH>',
    'OUATTARA',
    'Admin',
    (SELECT id FROM acteur WHERE type_acteur = 'AD' LIMIT 1)
)
ON CONFLICT (username) DO NOTHING;

-- 4d. Créer l'entrée dans la table administrateur
INSERT INTO administrateur (id, user_id, nom, prenom, email, role, date_creation)
VALUES (
    gen_random_uuid()::text,
    (SELECT id FROM users WHERE username = 'admin_afor' LIMIT 1),
    'OUATTARA',
    'Admin',
    'admin@afor.bf',
    'super_admin',
    NOW()
)
ON CONFLICT DO NOTHING;

-- ============================================
-- VERIFICATION ADMIN
-- ============================================
-- SELECT u.username, u.nom, u.prenom, a.type_acteur, adm.role
-- FROM users u
-- JOIN acteur a ON u.acteur_id = a.id
-- LEFT JOIN administrateur adm ON adm.user_id = u.id
-- WHERE u.username = 'admin_afor';
