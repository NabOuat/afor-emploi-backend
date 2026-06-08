-- Script de création de schéma pour Supabase (version UUID)
-- Base de données: AFOR Emploi
-- Date: 24 Février 2026
-- Correction: Utilise UUID pour les ID comme dans les données exportées

-- ============================================
-- GEOGRAPHIC HIERARCHY TABLES
-- ============================================

CREATE TABLE tregion (
    id UUID PRIMARY KEY,
    nom VARCHAR NOT NULL
);

CREATE TABLE tdepartement (
    id UUID PRIMARY KEY,
    nom VARCHAR NOT NULL,
    region_id UUID NOT NULL,
    FOREIGN KEY (region_id) REFERENCES tregion(id) ON DELETE CASCADE
);

CREATE TABLE tsousprefecture (
    id UUID PRIMARY KEY,
    nom VARCHAR NOT NULL,
    departement_id UUID NOT NULL,
    FOREIGN KEY (departement_id) REFERENCES tdepartement(id) ON DELETE CASCADE
);

-- ============================================
-- ACTOR & AUTHENTICATION TABLES
-- ============================================

CREATE TABLE acteur (
    id UUID PRIMARY KEY,
    nom VARCHAR NOT NULL,
    type_acteur VARCHAR NOT NULL,
    contact_1 VARCHAR,
    contact_2 VARCHAR,
    adresse_1 VARCHAR,
    adresse_2 VARCHAR,
    email_1 VARCHAR,
    email_2 VARCHAR,
    date_creation TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE login (
    id UUID PRIMARY KEY,
    username VARCHAR NOT NULL UNIQUE,
    password VARCHAR NOT NULL,
    acteur_id UUID NOT NULL UNIQUE,
    FOREIGN KEY (acteur_id) REFERENCES acteur(id) ON DELETE CASCADE
);

CREATE TABLE administrateur (
    id UUID PRIMARY KEY,
    login_id UUID NOT NULL UNIQUE,
    nom VARCHAR NOT NULL,
    prenom VARCHAR NOT NULL,
    email VARCHAR,
    contact VARCHAR,
    role VARCHAR,
    date_creation TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (login_id) REFERENCES login(id) ON DELETE CASCADE
);

-- ============================================
-- PROJECT & ENGAGEMENT TABLES
-- ============================================

CREATE TABLE projet (
    id UUID PRIMARY KEY,
    nom VARCHAR NOT NULL,
    nom_complet VARCHAR
);

CREATE TABLE engagement (
    id UUID PRIMARY KEY,
    nom VARCHAR NOT NULL UNIQUE,
    description TEXT,
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE projet_engagement (
    id UUID PRIMARY KEY,
    projet_id UUID NOT NULL,
    engagement_id UUID NOT NULL,
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (projet_id) REFERENCES projet(id),
    FOREIGN KEY (engagement_id) REFERENCES engagement(id),
    UNIQUE(projet_id, engagement_id)
);

CREATE TABLE zone_d_intervention (
    id UUID PRIMARY KEY,
    acteur_id UUID NOT NULL,
    projet_id UUID NOT NULL,
    region_id UUID,
    departement_id UUID,
    sous_prefecture_id UUID,
    FOREIGN KEY (acteur_id) REFERENCES acteur(id) ON DELETE CASCADE,
    FOREIGN KEY (projet_id) REFERENCES projet(id) ON DELETE CASCADE,
    FOREIGN KEY (region_id) REFERENCES tregion(id) ON DELETE SET NULL,
    FOREIGN KEY (departement_id) REFERENCES tdepartement(id) ON DELETE SET NULL,
    FOREIGN KEY (sous_prefecture_id) REFERENCES tsousprefecture(id) ON DELETE SET NULL
);

-- ============================================
-- PERSON & CONTRACT TABLES
-- ============================================

CREATE TABLE fic_personne (
    id UUID PRIMARY KEY,
    nom VARCHAR NOT NULL,
    prenom VARCHAR NOT NULL,
    date_naissance DATE,
    genre VARCHAR,
    contact VARCHAR,
    matricule VARCHAR,
    projet_id UUID NOT NULL,
    FOREIGN KEY (projet_id) REFERENCES projet(id) ON DELETE CASCADE
);

CREATE TABLE fic_personne_projet (
    id UUID PRIMARY KEY,
    fic_personne_id UUID NOT NULL,
    projet_id UUID NOT NULL,
    acteur_id UUID NOT NULL,
    date_debut TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    statut VARCHAR DEFAULT 'ACTIF',
    FOREIGN KEY (fic_personne_id) REFERENCES fic_personne(id) ON DELETE CASCADE,
    FOREIGN KEY (projet_id) REFERENCES projet(id) ON DELETE CASCADE,
    FOREIGN KEY (acteur_id) REFERENCES acteur(id) ON DELETE CASCADE
);

CREATE TABLE supervision (
    id UUID PRIMARY KEY,
    fic_personne_id UUID NOT NULL,
    superviseur_id UUID,
    date_debut DATE,
    date_fin DATE,
    FOREIGN KEY (fic_personne_id) REFERENCES fic_personne(id) ON DELETE CASCADE
);

CREATE TABLE contrat (
    id UUID PRIMARY KEY,
    fic_personne_id UUID NOT NULL,
    poste_nom VARCHAR NOT NULL,
    categorie_poste VARCHAR,
    type_contrat VARCHAR,
    type_personne VARCHAR,
    poste VARCHAR,
    date_debut DATE NOT NULL,
    date_fin DATE,
    diplome TEXT,
    ecole VARCHAR,
    autre TEXT,
    projet_id UUID,
    engagement_id UUID,
    FOREIGN KEY (fic_personne_id) REFERENCES fic_personne(id) ON DELETE CASCADE,
    FOREIGN KEY (projet_id) REFERENCES projet(id) ON DELETE SET NULL,
    FOREIGN KEY (engagement_id) REFERENCES engagement(id) ON DELETE SET NULL
);

CREATE TABLE fic_personne_localisation (
    id UUID PRIMARY KEY,
    contrat_id UUID NOT NULL,
    region_id UUID,
    departement_id UUID,
    sous_prefecture_id UUID,
    date_debut DATE,
    FOREIGN KEY (contrat_id) REFERENCES contrat(id) ON DELETE CASCADE,
    FOREIGN KEY (region_id) REFERENCES tregion(id) ON DELETE SET NULL,
    FOREIGN KEY (departement_id) REFERENCES tdepartement(id) ON DELETE SET NULL,
    FOREIGN KEY (sous_prefecture_id) REFERENCES tsousprefecture(id) ON DELETE SET NULL
);

-- ============================================
-- USER ACTIONS TABLE (corrigée - ID en UUID)
-- ============================================

CREATE TABLE user_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    login_id VARCHAR(255) NOT NULL,
    username VARCHAR(255) NOT NULL,
    acteur_id VARCHAR(255) NOT NULL,
    action_type VARCHAR(100) NOT NULL,
    action_description TEXT,
    resource_type VARCHAR(100),
    resource_id VARCHAR(255),
    ip_address VARCHAR(45),
    user_agent TEXT,
    status VARCHAR(50) DEFAULT 'success',
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- INDEXES FOR PERFORMANCE
-- ============================================

CREATE INDEX idx_tdepartement_region_id ON tdepartement(region_id);
CREATE INDEX idx_tsousprefecture_departement_id ON tsousprefecture(departement_id);
CREATE INDEX idx_login_acteur_id ON login(acteur_id);
CREATE INDEX idx_administrateur_login_id ON administrateur(login_id);
CREATE INDEX idx_zone_intervention_acteur_id ON zone_d_intervention(acteur_id);
CREATE INDEX idx_zone_intervention_projet_id ON zone_d_intervention(projet_id);
CREATE INDEX idx_fic_personne_projet_id ON fic_personne(projet_id);
CREATE INDEX idx_fic_personne_projet_fic_personne_id ON fic_personne_projet(fic_personne_id);
CREATE INDEX idx_fic_personne_projet_projet_id ON fic_personne_projet(projet_id);
CREATE INDEX idx_fic_personne_projet_acteur_id ON fic_personne_projet(acteur_id);
CREATE INDEX idx_supervision_fic_personne_id ON supervision(fic_personne_id);
CREATE INDEX idx_contrat_fic_personne_id ON contrat(fic_personne_id);
CREATE INDEX idx_contrat_projet_id ON contrat(projet_id);
CREATE INDEX idx_contrat_engagement_id ON contrat(engagement_id);
CREATE INDEX idx_fic_personne_localisation_contrat_id ON fic_personne_localisation(contrat_id);
CREATE INDEX idx_projet_engagement_projet_id ON projet_engagement(projet_id);
CREATE INDEX idx_projet_engagement_engagement_id ON projet_engagement(engagement_id);
CREATE INDEX idx_user_actions_login_id ON user_actions(login_id);
CREATE INDEX idx_user_actions_username ON user_actions(username);
CREATE INDEX idx_user_actions_acteur_id ON user_actions(acteur_id);
CREATE INDEX idx_user_actions_resource_id ON user_actions(resource_id);
