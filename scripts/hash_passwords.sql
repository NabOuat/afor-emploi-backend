-- ============================================================================
--  Re-hachage des mots de passe stockés en clair  (base : EmploiNewDb)
-- ----------------------------------------------------------------------------
--  Contexte : 10 comptes sur 12 ont leur mot de passe en TEXTE CLAIR.
--  Le backend (app/security.py -> verify_password) rejette tout mot de passe
--  qui ne commence pas par "$2" => ces comptes renvoient toujours 401.
--
--  Ce script utilise l'extension pgcrypto de PostgreSQL pour générer des
--  hash bcrypt ("$2a$...") COMPATIBLES avec la lib Python `bcrypt` du backend.
--  Il CONSERVE le mot de passe actuel de chaque utilisateur, il ne fait que
--  le hacher. Les comptes déjà hachés (admin, larh) ne sont pas touchés.
--
--  ⚠️  Faites une sauvegarde avant : pg_dump -U postgres EmploiNewDb > backup.sql
-- ============================================================================

-- 1) Activer pgcrypto (fournit crypt() et gen_salt())
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- 2) Aperçu : quels comptes vont être modifiés (mdp NON haché)
SELECT username, password AS mot_de_passe_clair
FROM   users
WHERE  password NOT LIKE '$2%';

-- 3) Re-hacher en bcrypt (coût 12) tous les mots de passe en clair.
--    crypt() prend le mot de passe actuel et produit un hash "$2a$12$...".
UPDATE users
SET    password = crypt(password, gen_salt('bf', 12))
WHERE  password NOT LIKE '$2%';

-- 4) Vérification : tous les mots de passe doivent désormais commencer par "$2".
--    'cleartext_restants' doit valoir 0.
SELECT
    count(*) FILTER (WHERE password LIKE '$2%')     AS hash_bcrypt,
    count(*) FILTER (WHERE password NOT LIKE '$2%') AS cleartext_restants
FROM users;

-- ----------------------------------------------------------------------------
--  OPTIONNEL : forcer un mot de passe connu pour un compte précis.
--  (décommentez et adaptez la valeur ; le mot de passe doit faire >= 8 car.)
-- ----------------------------------------------------------------------------
-- UPDATE users
-- SET    password = crypt('Admin@2026', gen_salt('bf', 12))
-- WHERE  username = 'admin';
