-- ============================================
-- SCRIPT DE MIGRATION V1 -> V2
-- ============================================
-- Ce script migre les données des anciennes tables vers la nouvelle structure
-- À exécuter APRÈS la création des nouvelles tables

-- ============================================
-- 1. MIGRATION DES RÉGIONS (pas de changement)
-- ============================================
INSERT INTO tregion (id, nom)
SELECT id, nom FROM public.tregion_old
ON CONFLICT (id) DO NOTHING;

-- ============================================
-- 2. MIGRATION DES DÉPARTEMENTS (pas de changement)
-- ============================================
INSERT INTO tdepartement (id, nom, region_id)
SELECT id, nom, region_id FROM public.tdepartement_old
ON CONFLICT (id) DO NOTHING;

-- ============================================
-- 3. MIGRATION DES SOUS-PRÉFECTURES (pas de changement)
-- ============================================
INSERT INTO tsousprefecture (id, nom, departement_id)
SELECT id, nom, departement_id FROM public.tsousprefecture_old
ON CONFLICT (id) DO NOTHING;

-- ============================================
-- 4. CONSOLIDATION DES ACTEURS
-- Fusion de toperateur_foncier, tecole_partenaire, tagence_execution
-- ============================================

-- Insérer les opérateurs
INSERT INTO acteur (id, nom, type_acteur, contact_1, contact_2, adresse_1, adresse_2, email_1, email_2, date_creation)
SELECT 
    id,
    nom,
    'operateur' as type_acteur,
    contact_1,
    contact_2,
    adresse_1,
    adresse_2,
    email_1,
    email_2,
    CURRENT_TIMESTAMP
FROM public.toperateur_foncier_old
ON CONFLICT (id) DO NOTHING;

-- Insérer les écoles partenaires
INSERT INTO acteur (id, nom, type_acteur, date_creation)
SELECT 
    id,
    name as nom,
    'ecole' as type_acteur,
    CURRENT_TIMESTAMP
FROM public.tecole_partenaire_old
ON CONFLICT (id) DO NOTHING;

-- Insérer les agences d'exécution
INSERT INTO acteur (id, nom, type_acteur, date_creation)
SELECT 
    id,
    name as nom,
    'agence' as type_acteur,
    CURRENT_TIMESTAMP
FROM public.tagence_execution_old
ON CONFLICT (id) DO NOTHING;

-- ============================================
-- 5. MIGRATION DES LOGINS
-- ============================================
INSERT INTO login (id, username, password, acteur_id)
SELECT 
    id,
    username,
    password,
    COALESCE(operateur_id, ecole_partenaire_id, agence_execution_id) as acteur_id
FROM public.login_old
WHERE COALESCE(operateur_id, ecole_partenaire_id, agence_execution_id) IS NOT NULL
ON CONFLICT (id) DO NOTHING;

-- ============================================
-- 6. MIGRATION DES ADMINISTRATEURS
-- ============================================
INSERT INTO administrateur (id, login_id, nom, prenom, email, contact, role, date_creation)
SELECT 
    id,
    NULL as login_id,
    nom,
    prenom,
    email,
    contact,
    role,
    date_creation
FROM public.administrateur_old
ON CONFLICT (id) DO NOTHING;

-- ============================================
-- 7. MIGRATION DES PROJETS
-- ============================================
INSERT INTO projet (id, nom, nom_complet)
SELECT 
    id,
    nom,
    "nom complet" as nom_complet
FROM public.projet_old
ON CONFLICT (id) DO NOTHING;

-- ============================================
-- 8. MIGRATION DES ZONES D'INTERVENTION
-- ============================================
INSERT INTO zone_d_intervention (id, acteur_id, projet_id, region_id, departement_id, sous_prefecture_id)
SELECT 
    id,
    COALESCE(operateur_id, ecole_id, agence_id) as acteur_id,
    projet_id,
    region_id,
    NULL as departement_id,
    NULL as sous_prefecture_id
FROM public.zone_d_intervention_old
WHERE COALESCE(operateur_id, ecole_id, agence_id) IS NOT NULL
ON CONFLICT (id) DO NOTHING;

-- ============================================
-- 9. MIGRATION DES FICHES PERSONNE
-- ============================================
INSERT INTO fic_personne (id, acteur_id, projet_id, nom, prenom, date_naissance, genre, contact)
SELECT 
    id,
    COALESCE(operateur_id, ecole_id, agence_id) as acteur_id,
    NULL as projet_id,
    nom,
    prenom,
    date_naissance,
    genre,
    contact
FROM public.fic_personne_old
WHERE COALESCE(operateur_id, ecole_id, agence_id) IS NOT NULL
ON CONFLICT (id) DO NOTHING;

-- ============================================
-- 10. MIGRATION DES CONTRATS
-- ============================================
INSERT INTO contrat (id, fic_personne_id, poste_nom, categorie_poste, diplome, type_personne, date_debut, date_fin, autre)
SELECT 
    c.id,
    c.fic_personne_id,
    p.poste as poste_nom,
    c.categorie_poste,
    fp.diplome,
    fp.type_personne,
    c.date_debut,
    c.date_fin,
    c.autre
FROM public.contrat_old c
LEFT JOIN public.poste_old p ON c.poste_id = p.id
LEFT JOIN public.fic_personne_old fp ON c.fic_personne_id = fp.id
ON CONFLICT (id) DO NOTHING;

-- ============================================
-- 11. MIGRATION DES LOCALISATIONS
-- ============================================
INSERT INTO fic_personne_localisation (id, contrat_id, region_id, departement_id, sous_prefecture_id, date_debut)
SELECT 
    id,
    contrat_id,
    region_id,
    departement_id,
    sous_prefecture_id,
    date_debut
FROM public.fic_personne_localisation_old
ON CONFLICT (id) DO NOTHING;

-- ============================================
-- 12. MIGRATION DES SUPERVISIONS
-- ============================================
INSERT INTO supervision (id, fic_personne_id, superviseur_id, date_debut, date_fin)
SELECT 
    id,
    employee_id as fic_personne_id,
    supervisor_id as superviseur_id,
    date_debut,
    date_fin
FROM public.supervisor_employee_old
ON CONFLICT (id) DO NOTHING;

-- ============================================
-- VÉRIFICATION DES DONNÉES MIGRÉES
-- ============================================
SELECT 'Acteurs' as table_name, COUNT(*) as count FROM acteur
UNION ALL
SELECT 'Logins', COUNT(*) FROM login
UNION ALL
SELECT 'Administrateurs', COUNT(*) FROM administrateur
UNION ALL
SELECT 'Projets', COUNT(*) FROM projet
UNION ALL
SELECT 'Zones d''intervention', COUNT(*) FROM zone_d_intervention
UNION ALL
SELECT 'Fiches Personne', COUNT(*) FROM fic_personne
UNION ALL
SELECT 'Contrats', COUNT(*) FROM contrat
UNION ALL
SELECT 'Localisations', COUNT(*) FROM fic_personne_localisation
UNION ALL
SELECT 'Supervisions', COUNT(*) FROM supervision;
