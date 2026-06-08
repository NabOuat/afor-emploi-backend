-- Script de normalisation UTF-8 pour PostgreSQL (Supabase)
-- Exécutez ce script dans Supabase SQL Editor

-- Fonction pour corriger l'encodage UTF-8 mal interprété
CREATE OR REPLACE FUNCTION fix_utf8_encoding(text_input TEXT) RETURNS TEXT AS $$
BEGIN
  IF text_input IS NULL THEN
    RETURN NULL;
  END IF;
  -- Remplacer les séquences de caractères mal encodées
  RETURN REPLACE(
    REPLACE(
      REPLACE(
        REPLACE(
          REPLACE(
            REPLACE(
              REPLACE(
                REPLACE(
                  REPLACE(
                    REPLACE(text_input, '├â┬®', 'é'),
                    '├â┬Ç', 'ç'),
                    '├â┬Ö', 'è'),
                    '├â┬ê', 'ê'),
                    '├ô┬ê', 'ô'),
                    '├ô┬ç', 'ù'),
                    '├â┬ô', 'à'),
                    '├â┬ô', 'î'),
                    '├â┬ü', 'ü'),
                    '├â┬ö', 'ö'
              );
END;
$$ LANGUAGE plpgsql;

-- 1. Normaliser la table fic_personne
UPDATE fic_personne 
SET 
  nom = fix_utf8_encoding(nom),
  prenom = fix_utf8_encoding(prenom),
  contact = fix_utf8_encoding(contact)
WHERE nom LIKE '%├%' OR prenom LIKE '%├%' OR contact LIKE '%├%';

-- 2. Normaliser la table contrat
UPDATE contrat 
SET 
  poste_nom = fix_utf8_encoding(poste_nom),
  categorie_poste = fix_utf8_encoding(categorie_poste),
  type_personne = fix_utf8_encoding(type_personne),
  poste = fix_utf8_encoding(poste),
  diplome = fix_utf8_encoding(diplome),
  ecole = fix_utf8_encoding(ecole)
WHERE poste_nom LIKE '%├%' OR categorie_poste LIKE '%├%' OR type_personne LIKE '%├%' 
  OR poste LIKE '%├%' OR diplome LIKE '%├%' OR ecole LIKE '%├%';

-- 3. Normaliser la table tregion
UPDATE tregion 
SET nom = fix_utf8_encoding(nom)
WHERE nom LIKE '%├%';

-- 4. Normaliser la table tdepartement
UPDATE tdepartement 
SET nom = fix_utf8_encoding(nom)
WHERE nom LIKE '%├%';

-- 5. Normaliser la table tsousprefecture
UPDATE tsousprefecture 
SET nom = fix_utf8_encoding(nom)
WHERE nom LIKE '%├%';

-- 6. Normaliser la table projet
UPDATE projet 
SET 
  nom = fix_utf8_encoding(nom),
  nom_complet = fix_utf8_encoding(nom_complet)
WHERE nom LIKE '%├%' OR nom_complet LIKE '%├%';

-- 7. Normaliser la table acteur
UPDATE acteur 
SET 
  nom = fix_utf8_encoding(nom),
  contact_1 = fix_utf8_encoding(contact_1),
  contact_2 = fix_utf8_encoding(contact_2),
  adresse_1 = fix_utf8_encoding(adresse_1),
  adresse_2 = fix_utf8_encoding(adresse_2),
  email_1 = fix_utf8_encoding(email_1),
  email_2 = fix_utf8_encoding(email_2)
WHERE nom LIKE '%├%' OR contact_1 LIKE '%├%' OR contact_2 LIKE '%├%' 
  OR adresse_1 LIKE '%├%' OR adresse_2 LIKE '%├%' OR email_1 LIKE '%├%' OR email_2 LIKE '%├%';

-- Vérifier les résultats
SELECT COUNT(*) as total_records_with_bad_encoding
FROM (
  SELECT 1 FROM fic_personne WHERE nom LIKE '%├%' OR prenom LIKE '%├%'
  UNION ALL
  SELECT 1 FROM contrat WHERE poste_nom LIKE '%├%' OR categorie_poste LIKE '%├%'
  UNION ALL
  SELECT 1 FROM tregion WHERE nom LIKE '%├%'
  UNION ALL
  SELECT 1 FROM tdepartement WHERE nom LIKE '%├%'
  UNION ALL
  SELECT 1 FROM tsousprefecture WHERE nom LIKE '%├%'
  UNION ALL
  SELECT 1 FROM projet WHERE nom LIKE '%├%'
  UNION ALL
  SELECT 1 FROM acteur WHERE nom LIKE '%├%'
) as bad_records;

-- Nettoyer la fonction
DROP FUNCTION IF EXISTS fix_utf8_encoding(TEXT);
