-- ====================================================================
-- AFOR Emploi — Export de structure de base de données
-- ====================================================================
-- Environnement : Production (Supabase)
-- Hôte          : aws-1-eu-west-1.pooler.supabase.com:6543
-- Base          : postgres
-- Utilisateur   : postgres.pypmgdxmsbgxrwvbpfuo
-- SSL           : Oui
-- Date export   : 2026-05-28 10:18:13
-- ====================================================================

SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;


-- ──────────────────────────────────────────────────────────────────────
-- EXTENSIONS
-- ──────────────────────────────────────────────────────────────────────

CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";  -- v1.11
CREATE EXTENSION IF NOT EXISTS "pgcrypto";  -- v1.3
CREATE EXTENSION IF NOT EXISTS "supabase_vault";  -- v0.3.1
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";  -- v1.1


-- ──────────────────────────────────────────────────────────────────────
-- TABLES
-- ──────────────────────────────────────────────────────────────────────

-- Table: acteur
CREATE TABLE IF NOT EXISTS public."acteur" (
    "id" VARCHAR NOT NULL,
    "nom" VARCHAR NOT NULL,
    "type_acteur" VARCHAR NOT NULL,
    "contact_1" VARCHAR,
    "contact_2" VARCHAR,
    "adresse_1" VARCHAR,
    "adresse_2" VARCHAR,
    "email_1" VARCHAR,
    "email_2" VARCHAR,
    "date_creation" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "acteur_pkey" PRIMARY KEY (id)
);

-- Table: administrateur
CREATE TABLE IF NOT EXISTS public."administrateur" (
    "id" VARCHAR NOT NULL,
    "user_id" VARCHAR NOT NULL,
    "nom" VARCHAR NOT NULL,
    "prenom" VARCHAR NOT NULL,
    "email" VARCHAR,
    "contact" VARCHAR,
    "role" VARCHAR,
    "date_creation" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "administrateur_pkey" PRIMARY KEY (id),
    CONSTRAINT "administrateur_user_id_key" UNIQUE (user_id)
);

-- Table: contrat
CREATE TABLE IF NOT EXISTS public."contrat" (
    "id" VARCHAR NOT NULL,
    "fic_personne_id" VARCHAR NOT NULL,
    "poste_nom" VARCHAR NOT NULL,
    "categorie_poste" VARCHAR,
    "type_contrat" VARCHAR,
    "type_personne" VARCHAR,
    "poste" VARCHAR,
    "date_debut" DATE NOT NULL,
    "date_fin" DATE,
    "diplome" TEXT,
    "ecole" VARCHAR,
    "autre" TEXT,
    "projet_id" VARCHAR,
    "engagement_id" VARCHAR,
    CONSTRAINT "contrat_pkey" PRIMARY KEY (id)
);

-- Table: engagement
CREATE TABLE IF NOT EXISTS public."engagement" (
    "id" VARCHAR NOT NULL,
    "nom" VARCHAR NOT NULL,
    "description" TEXT,
    "date_creation" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "engagement_pkey" PRIMARY KEY (id),
    CONSTRAINT "engagement_nom_key" UNIQUE (nom)
);

-- Table: fic_personne
-- acteur_id : un employé appartient à un et un seul acteur (porté par la personne).
CREATE TABLE IF NOT EXISTS public."fic_personne" (
    "id" VARCHAR NOT NULL,
    "nom" VARCHAR NOT NULL,
    "prenom" VARCHAR NOT NULL,
    "date_naissance" DATE,
    "genre" VARCHAR,
    "contact" VARCHAR,
    "matricule" VARCHAR,
    "acteur_id" VARCHAR,
    "created_by" VARCHAR,
    CONSTRAINT "fic_personne_pkey" PRIMARY KEY (id)
);

-- Table: fic_personne_localisation
CREATE TABLE IF NOT EXISTS public."fic_personne_localisation" (
    "id" VARCHAR NOT NULL,
    "contrat_id" VARCHAR NOT NULL,
    "region_id" VARCHAR,
    "departement_id" VARCHAR,
    "sous_prefecture_id" VARCHAR,
    "date_debut" DATE,
    CONSTRAINT "fic_personne_localisation_pkey" PRIMARY KEY (id)
);


-- Table: projet
CREATE TABLE IF NOT EXISTS public."projet" (
    "id" VARCHAR NOT NULL,
    "nom" VARCHAR NOT NULL,
    "nom_complet" VARCHAR,
    CONSTRAINT "projet_pkey" PRIMARY KEY (id)
);

-- Table: projet_engagement
CREATE TABLE IF NOT EXISTS public."projet_engagement" (
    "id" VARCHAR NOT NULL,
    "projet_id" VARCHAR NOT NULL,
    "engagement_id" VARCHAR NOT NULL,
    "date_creation" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "projet_engagement_pkey" PRIMARY KEY (id),
    CONSTRAINT "projet_engagement_projet_id_engagement_id_key" UNIQUE (projet_id, engagement_id)
);

-- Table: supervision
CREATE TABLE IF NOT EXISTS public."supervision" (
    "id" VARCHAR NOT NULL,
    "fic_personne_id" VARCHAR NOT NULL,
    "superviseur_id" VARCHAR,
    "date_debut" DATE,
    "date_fin" DATE,
    CONSTRAINT "supervision_pkey" PRIMARY KEY (id)
);

-- Table: tdepartement
CREATE TABLE IF NOT EXISTS public."tdepartement" (
    "id" VARCHAR NOT NULL,
    "nom" VARCHAR NOT NULL,
    "region_id" VARCHAR NOT NULL,
    CONSTRAINT "tdepartement_pkey" PRIMARY KEY (id)
);

-- Table: tregion
CREATE TABLE IF NOT EXISTS public."tregion" (
    "id" VARCHAR NOT NULL,
    "nom" VARCHAR NOT NULL,
    CONSTRAINT "tregion_pkey" PRIMARY KEY (id)
);

-- Table: tsousprefecture
CREATE TABLE IF NOT EXISTS public."tsousprefecture" (
    "id" VARCHAR NOT NULL,
    "nom" VARCHAR NOT NULL,
    "departement_id" VARCHAR NOT NULL,
    CONSTRAINT "tsousprefecture_pkey" PRIMARY KEY (id)
);

-- Table: user_actions
CREATE TABLE IF NOT EXISTS public."user_actions" (
    "id" VARCHAR NOT NULL,
    "user_id" VARCHAR(255) NOT NULL,
    "username" VARCHAR(255) NOT NULL,
    "acteur_id" VARCHAR(255) NOT NULL,
    "action_type" VARCHAR(100) NOT NULL,
    "action_description" TEXT,
    "resource_type" VARCHAR(100),
    "resource_id" VARCHAR(255),
    "ip_address" VARCHAR(45),
    "user_agent" TEXT,
    "status" VARCHAR(50) DEFAULT 'success'::character varying,
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "user_actions_pkey" PRIMARY KEY (id)
);

-- Table: users
CREATE TABLE IF NOT EXISTS public."users" (
    "id" VARCHAR NOT NULL,
    "username" VARCHAR NOT NULL,
    "password" VARCHAR NOT NULL,
    "acteur_id" VARCHAR NOT NULL,
    "nom" TEXT,
    "prenom" TEXT,
    "email" TEXT,
    CONSTRAINT "users_pkey" PRIMARY KEY (id),
    CONSTRAINT "users_username_key" UNIQUE (username)
);

-- Table: zone_d_intervention
CREATE TABLE IF NOT EXISTS public."zone_d_intervention" (
    "id" VARCHAR NOT NULL,
    "acteur_id" VARCHAR NOT NULL,
    "projet_id" VARCHAR NOT NULL,
    "region_id" VARCHAR,
    "departement_id" VARCHAR,
    "sous_prefecture_id" VARCHAR,
    CONSTRAINT "zone_d_intervention_pkey" PRIMARY KEY (id)
);



-- ──────────────────────────────────────────────────────────────────────
-- CLÉS ÉTRANGÈRES (FOREIGN KEYS)
-- ──────────────────────────────────────────────────────────────────────

ALTER TABLE public."administrateur"
    ADD CONSTRAINT "administrateur_user_id_fkey"
    FOREIGN KEY (user_id)
    REFERENCES public."users" (id) ON DELETE CASCADE;

ALTER TABLE public."user_actions"
    ADD CONSTRAINT "user_actions_user_id_fkey"
    FOREIGN KEY (user_id)
    REFERENCES public."users" (id) ON DELETE CASCADE;

ALTER TABLE public."user_actions"
    ADD CONSTRAINT "user_actions_acteur_id_fkey"
    FOREIGN KEY (acteur_id)
    REFERENCES public."acteur" (id) ON DELETE CASCADE;

ALTER TABLE public."contrat"
    ADD CONSTRAINT "contrat_engagement_id_fkey"
    FOREIGN KEY (engagement_id)
    REFERENCES public."engagement" (id) ON DELETE SET NULL;

ALTER TABLE public."contrat"
    ADD CONSTRAINT "contrat_fic_personne_id_fkey"
    FOREIGN KEY (fic_personne_id)
    REFERENCES public."fic_personne" (id) ON DELETE CASCADE;

ALTER TABLE public."contrat"
    ADD CONSTRAINT "contrat_projet_id_fkey"
    FOREIGN KEY (projet_id)
    REFERENCES public."projet" (id) ON DELETE SET NULL;

ALTER TABLE public."fic_personne"
    ADD CONSTRAINT "fic_personne_created_by_fkey"
    FOREIGN KEY (created_by)
    REFERENCES public."users" (id) ON DELETE SET NULL;

ALTER TABLE public."fic_personne"
    ADD CONSTRAINT "fic_personne_acteur_id_fkey"
    FOREIGN KEY (acteur_id)
    REFERENCES public."acteur" (id) ON DELETE CASCADE;

ALTER TABLE public."fic_personne_localisation"
    ADD CONSTRAINT "fic_personne_localisation_contrat_id_fkey"
    FOREIGN KEY (contrat_id)
    REFERENCES public."contrat" (id) ON DELETE CASCADE;

ALTER TABLE public."fic_personne_localisation"
    ADD CONSTRAINT "fic_personne_localisation_departement_id_fkey"
    FOREIGN KEY (departement_id)
    REFERENCES public."tdepartement" (id) ON DELETE SET NULL;

ALTER TABLE public."fic_personne_localisation"
    ADD CONSTRAINT "fic_personne_localisation_region_id_fkey"
    FOREIGN KEY (region_id)
    REFERENCES public."tregion" (id) ON DELETE SET NULL;

ALTER TABLE public."fic_personne_localisation"
    ADD CONSTRAINT "fic_personne_localisation_sous_prefecture_id_fkey"
    FOREIGN KEY (sous_prefecture_id)
    REFERENCES public."tsousprefecture" (id) ON DELETE SET NULL;

ALTER TABLE public."projet_engagement"
    ADD CONSTRAINT "projet_engagement_engagement_id_fkey"
    FOREIGN KEY (engagement_id)
    REFERENCES public."engagement" (id);

ALTER TABLE public."projet_engagement"
    ADD CONSTRAINT "projet_engagement_projet_id_fkey"
    FOREIGN KEY (projet_id)
    REFERENCES public."projet" (id);

ALTER TABLE public."supervision"
    ADD CONSTRAINT "supervision_fic_personne_id_fkey"
    FOREIGN KEY (fic_personne_id)
    REFERENCES public."fic_personne" (id) ON DELETE CASCADE;

ALTER TABLE public."tdepartement"
    ADD CONSTRAINT "tdepartement_region_id_fkey"
    FOREIGN KEY (region_id)
    REFERENCES public."tregion" (id) ON DELETE CASCADE;

ALTER TABLE public."tsousprefecture"
    ADD CONSTRAINT "tsousprefecture_departement_id_fkey"
    FOREIGN KEY (departement_id)
    REFERENCES public."tdepartement" (id) ON DELETE CASCADE;

ALTER TABLE public."users"
    ADD CONSTRAINT "users_acteur_id_fkey"
    FOREIGN KEY (acteur_id)
    REFERENCES public."acteur" (id) ON DELETE CASCADE;

ALTER TABLE public."zone_d_intervention"
    ADD CONSTRAINT "zone_d_intervention_acteur_id_fkey"
    FOREIGN KEY (acteur_id)
    REFERENCES public."acteur" (id) ON DELETE CASCADE;

ALTER TABLE public."zone_d_intervention"
    ADD CONSTRAINT "zone_d_intervention_departement_id_fkey"
    FOREIGN KEY (departement_id)
    REFERENCES public."tdepartement" (id) ON DELETE SET NULL;

ALTER TABLE public."zone_d_intervention"
    ADD CONSTRAINT "zone_d_intervention_projet_id_fkey"
    FOREIGN KEY (projet_id)
    REFERENCES public."projet" (id) ON DELETE CASCADE;

ALTER TABLE public."zone_d_intervention"
    ADD CONSTRAINT "zone_d_intervention_region_id_fkey"
    FOREIGN KEY (region_id)
    REFERENCES public."tregion" (id) ON DELETE SET NULL;

ALTER TABLE public."zone_d_intervention"
    ADD CONSTRAINT "zone_d_intervention_sous_prefecture_id_fkey"
    FOREIGN KEY (sous_prefecture_id)
    REFERENCES public."tsousprefecture" (id) ON DELETE SET NULL;



-- ──────────────────────────────────────────────────────────────────────
-- INDEX
-- ──────────────────────────────────────────────────────────────────────

CREATE INDEX idx_administrateur_user_id ON public.administrateur USING btree (user_id);
CREATE INDEX idx_contrat_engagement_id ON public.contrat USING btree (engagement_id);
CREATE INDEX idx_contrat_fic_personne_id ON public.contrat USING btree (fic_personne_id);
CREATE INDEX idx_contrat_projet_id ON public.contrat USING btree (projet_id);
CREATE INDEX idx_fic_personne_created_by ON public.fic_personne USING btree (created_by);
CREATE INDEX idx_fic_personne_acteur_id ON public.fic_personne USING btree (acteur_id);
CREATE INDEX idx_fic_personne_localisation_contrat_id ON public.fic_personne_localisation USING btree (contrat_id);
CREATE INDEX idx_projet_engagement_engagement_id ON public.projet_engagement USING btree (engagement_id);
CREATE INDEX idx_projet_engagement_projet_id ON public.projet_engagement USING btree (projet_id);
CREATE INDEX idx_supervision_fic_personne_id ON public.supervision USING btree (fic_personne_id);
CREATE INDEX idx_tdepartement_region_id ON public.tdepartement USING btree (region_id);
CREATE INDEX idx_tsousprefecture_departement_id ON public.tsousprefecture USING btree (departement_id);
CREATE INDEX idx_user_actions_acteur_id ON public.user_actions USING btree (acteur_id);
CREATE INDEX idx_user_actions_user_id ON public.user_actions USING btree (user_id);
CREATE INDEX idx_user_actions_resource_id ON public.user_actions USING btree (resource_id);
CREATE INDEX idx_user_actions_username ON public.user_actions USING btree (username);
CREATE INDEX idx_users_acteur_id ON public.users USING btree (acteur_id);
CREATE INDEX idx_zone_intervention_acteur_id ON public.zone_d_intervention USING btree (acteur_id);
CREATE INDEX idx_zone_intervention_projet_id ON public.zone_d_intervention USING btree (projet_id);


-- ──────────────────────────────────────────────────────────────────────
-- STATISTIQUES (nombre de lignes par table)
-- ──────────────────────────────────────────────────────────────────────

-- Ces valeurs sont indicatives au moment de l'export.

-- acteur                                           19 ligne(s)
-- administrateur                                    1 ligne(s)
-- contrat                                        1391 ligne(s)
-- engagement                                        4 ligne(s)
-- fic_personne                                   1324 ligne(s)
-- fic_personne_acteur                               0 ligne(s)
-- fic_personne_localisation                      1239 ligne(s)
-- fic_personne_projet                            1325 ligne(s)
-- projet                                            3 ligne(s)
-- projet_engagement                                 4 ligne(s)
-- supervision                                       0 ligne(s)
-- tdepartement                                    111 ligne(s)
-- tregion                                          33 ligne(s)
-- tsousprefecture                                 510 ligne(s)
-- user_actions                                      0 ligne(s)
-- users                                            12 ligne(s)
-- zone_d_intervention                              60 ligne(s)
