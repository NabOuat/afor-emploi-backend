-- Script de correction d'encodage UTF-8 pour Supabase
-- Exécutez ce script dans Supabase SQL Editor

-- Fonction pour corriger l'encodage UTF-8 mal interprété
CREATE OR REPLACE FUNCTION fix_utf8_encoding(text_input TEXT) RETURNS TEXT AS $$
DECLARE
  result TEXT;
BEGIN
  IF text_input IS NULL THEN
    RETURN NULL;
  END IF;
  
  result := text_input;
  result := REPLACE(result, '├â┬®', 'é');
  result := REPLACE(result, '├â┬Ç', 'ç');
  result := REPLACE(result, '├â┬Ö', 'è');
  result := REPLACE(result, '├â┬ê', 'ê');
  result := REPLACE(result, '├ô┬ê', 'ô');
  result := REPLACE(result, '├ô┬ç', 'ù');
  result := REPLACE(result, '├â┬ô', 'à');
  result := REPLACE(result, '├â┬ü', 'ü');
  result := REPLACE(result, '├â┬ö', 'ö');
  result := REPLACE(result, 'N├ó┬Ç┬Ö', 'NGUESSAN');
  result := REPLACE(result, 'n├ó┬Ç┬Ö', 'nguessan');
  result := REPLACE(result, '├é┬á', 'é');
  
  RETURN result;
END;
$$ LANGUAGE plpgsql;

-- 1. Corriger la table fic_personne
UPDATE fic_personne 
SET 
  nom = fix_utf8_encoding(nom),
  prenom = fix_utf8_encoding(prenom),
  contact = fix_utf8_encoding(contact)
WHERE nom LIKE '%├%' OR prenom LIKE '%├%' OR contact LIKE '%├%';

-- 2. Corriger la table contrat
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

-- 3. Corriger la table tregion
UPDATE tregion 
SET nom = fix_utf8_encoding(nom)
WHERE nom LIKE '%├%';

-- 4. Corriger la table tdepartement
UPDATE tdepartement 
SET nom = fix_utf8_encoding(nom)
WHERE nom LIKE '%├%';

-- 5. Corriger la table tsousprefecture
UPDATE tsousprefecture 
SET nom = fix_utf8_encoding(nom)
WHERE nom LIKE '%├%';

-- 6. Corriger la table projet
UPDATE projet 
SET 
  nom = fix_utf8_encoding(nom),
  nom_complet = fix_utf8_encoding(nom_complet)
WHERE nom LIKE '%├%' OR nom_complet LIKE '%├%';

-- 7. Corriger la table acteur
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
