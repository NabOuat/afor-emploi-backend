-- Script SQL pour créer un compte utilisateur de type RESPO et son login
-- Base de données: AFOR Emploi
-- Date: 12 Février 2026

-- ========================================
-- 1. Création de l'acteur de type RESPO
-- ========================================

-- Vérifier si l'acteur existe déjà
SELECT * FROM acteurs WHERE nom = 'RESPONSABLE_TEST' OR code = 'RESPO_TEST';

-- Créer l'acteur de type RESPO
INSERT INTO acteurs (
    id,
    nom,
    code,
    type_acteur,
    description,
    date_creation,
    statut
) VALUES (
    gen_random_uuid(),  -- UUID généré automatiquement
    'RESPONSABLE TEST',
    'RESPO_TEST',
    'RESPO',
    'Acteur responsable pour tests du système',
    CURRENT_TIMESTAMP,
    'ACTIF'
) ON CONFLICT (code) DO NOTHING;

-- Récupérer l'ID de l'acteur RESPO créé
DO $$
DECLARE
    resp_actor_id UUID;
BEGIN
    SELECT id INTO resp_actor_id FROM acteurs WHERE code = 'RESPO_TEST';
    
    -- ========================================
    -- 2. Création de la personne (utilisateur)
    -- ========================================
    
    -- Vérifier si la personne existe déjà
    SELECT * FROM fic_personne WHERE nom = 'RESPONSABLE' AND prenom = 'TEST';
    
    -- Créer la personne responsable
    INSERT INTO fic_personne (
        id,
        nom,
        prenom,
        date_naissance,
        genre,
        contact,
        matricule,
        date_creation
    ) VALUES (
        gen_random_uuid(),  -- UUID généré automatiquement
        'RESPONSABLE',
        'TEST',
        '1990-01-15',  -- Date de naissance (35 ans)
        'M',
        '+2250700000000',  -- Contact téléphonique
        'RESPO001',  -- Matricule
        CURRENT_TIMESTAMP
    ) ON CONFLICT (matricule) DO NOTHING;
    
    -- Récupérer l'ID de la personne créée
    DECLARE
        resp_personne_id UUID;
    SELECT id INTO resp_personne_id FROM fic_personne WHERE matricule = 'RESPO001';
    
    -- ========================================
    -- 3. Association personne-acteur
    -- ========================================
    
    -- Associer la personne à l'acteur RESPO
    INSERT INTO fic_personne_acteur (
        id,
        fic_personne_id,
        acteur_id,
        date_debut,
        statut
    ) VALUES (
        gen_random_uuid(),
        resp_personne_id,
        resp_actor_id,
        CURRENT_TIMESTAMP,
        'ACTIF'
    ) ON CONFLICT (fic_personne_id, acteur_id) DO NOTHING;
    
    -- ========================================
    -- 4. Création du compte utilisateur (login)
    -- ========================================
    
    -- Vérifier si le login existe déjà
    SELECT * FROM utilisateurs WHERE username = 'responsable_test';
    
    -- Créer le compte utilisateur
    INSERT INTO utilisateurs (
        id,
        username,
        password_hash,
        email,
        role,
        statut,
        date_creation,
        dernier_connexion,
        fic_personne_id,
        acteur_id
    ) VALUES (
        gen_random_uuid(),
        'responsable_test',
        '$2b$12$LQv3c1yqBWVHxkd0LHAkO7/3E9Hn5QKcCZqZjC7bX8vE9UfW7gKcCZqZjC7bX8vE9UfW7gKcCZqZjC7bX8vE9UfW7g',  -- Mot de passe: "test123" (hashé avec bcrypt)
        'responsable.test@afor.ci',
        'RESPONSABLE',
        'ACTIF',
        CURRENT_TIMESTAMP,
        NULL,  -- Pas encore de connexion
        resp_personne_id,
        resp_actor_id
    ) ON CONFLICT (username) DO NOTHING;
    
    -- ========================================
    -- 5. Attribution d'un projet par défaut (si nécessaire)
    -- ========================================
    
    -- Vérifier s'il y a des projets existants
    DECLARE
        project_exists BOOLEAN;
    SELECT EXISTS(SELECT 1 FROM projets LIMIT 1) INTO project_exists;
    
    IF project_exists THEN
        -- Prendre le premier projet existant
        DECLARE
            first_project_id UUID;
        SELECT id INTO first_project_id FROM projets LIMIT 1;
        
        -- Associer l'employé au projet
        INSERT INTO fic_personne_projet (
            id,
            fic_personne_id,
            projet_id,
            date_debut,
            statut
        ) VALUES (
            gen_random_uuid(),
            resp_personne_id,
            first_project_id,
            CURRENT_TIMESTAMP,
            'ACTIF'
        ) ON CONFLICT (fic_personne_id, projet_id) DO NOTHING;
    END IF;
    
    -- ========================================
    -- 6. Création d'un contrat par défaut
    -- ========================================
    
    -- Créer un contrat pour l'employé responsable
    INSERT INTO contrats (
        id,
        fic_personne_id,
        poste_nom,
        categorie_poste,
        type_contrat,
        type_personne,
        poste,
        date_debut,
        date_fin,
        diplome,
        ecole,
        projet_id,
        engagement_id,
        date_creation
    ) VALUES (
        gen_random_uuid(),
        resp_personne_id,
        'Responsable',
        'Cadre',
        'CDI',
        'Contractuel',
        'Responsable',
        CURRENT_TIMESTAMP,
        NULL,  -- Pas de date de fin pour CDI
        'Master',
        'Université Félix Houphouët-Boigny',
        (SELECT id FROM projets LIMIT 1),  -- Premier projet si disponible
        NULL,  -- Pas d'engagement pour le moment
        CURRENT_TIMESTAMP
    );
    
    -- ========================================
    -- 7. Confirmation et affichage des informations
    -- ========================================
    
    RAISE NOTICE 'Compte RESPO créé avec succès!';
    
    -- Afficher les informations de connexion
    SELECT 
        'INFORMATIONS DE CONNEXION' as information,
        'Username: responsable_test' as username,
        'Password: test123' as password,
        'Role: RESPONSABLE' as role,
        'Dashboard: /responsable/dashboard' as dashboard;
    
    -- Afficher les détails du compte créé
    SELECT 
        u.username,
        u.email,
        u.role,
        a.nom as acteur_nom,
        a.type_acteur,
        p.nom as personne_nom,
        p.prenom as personne_prenom,
        p.matricule
    FROM utilisateurs u
    JOIN acteurs a ON u.acteur_id = a.id
    JOIN fic_personne p ON u.fic_personne_id = p.id
    WHERE u.username = 'responsable_test';
    
END $$;

-- ========================================
-- 8. Vérification finale
-- ========================================

-- Vérifier que tout a été créé correctement
SELECT 
    'Acteurs RESPO créés' as type_info,
    COUNT(*) as total
FROM acteurs 
WHERE type_acteur = 'RESPO';

SELECT 
    'Utilisateurs RESPO créés' as type_info,
    COUNT(*) as total
FROM utilisateurs 
WHERE role = 'RESPONSABLE';

SELECT 
    'Personnes associées aux RESPO' as type_info,
    COUNT(*) as total
FROM fic_personne fp
JOIN fic_personne_acteur fpa ON fp.id = fpa.fic_personne_id
JOIN acteurs a ON fpa.acteur_id = a.id
WHERE a.type_acteur = 'RESPO';

-- ========================================
-- 9. Instructions pour la connexion
-- ========================================

/*
INSTRUCTIONS DE CONNEXION:
=========================

1. URL de connexion: http://localhost:3000/login
2. Username: responsable_test
3. Password: test123
4. Dashboard: /responsable/dashboard

NOTES:
=======
- Le mot de passe "test123" est hashé avec bcrypt
- L'utilisateur sera automatiquement redirigé vers /responsable/dashboard
- Le compte est associé à un projet existant s'il y en a un
- Un contrat CDI par défaut est créé pour l'employé
- Le statut du compte est "ACTIF"

Pour tester avec d'autres utilisateurs:
- Administrateur: admin / admin123 → /admin/dashboard
- Opérateur: operator / operator123 → /operator/dashboard
- AFOR: afor / afor123 → /afor/dashboard
*/
