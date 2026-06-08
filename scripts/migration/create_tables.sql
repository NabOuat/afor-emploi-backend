-- ============================================
-- DATABASE SCHEMA V2 - EMPLOI
-- ============================================

-- Drop existing tables if they exist (in reverse dependency order)
DROP TABLE IF EXISTS fic_personne_localisation CASCADE;
DROP TABLE IF EXISTS contrat CASCADE;
DROP TABLE IF EXISTS supervision CASCADE;
DROP TABLE IF EXISTS fic_personne CASCADE;
DROP TABLE IF EXISTS zone_d_intervention CASCADE;
DROP TABLE IF EXISTS administrateur CASCADE;
DROP TABLE IF EXISTS login CASCADE;
DROP TABLE IF EXISTS projet CASCADE;
DROP TABLE IF EXISTS tsousprefecture CASCADE;
DROP TABLE IF EXISTS tdepartement CASCADE;
DROP TABLE IF EXISTS tregion CASCADE;
DROP TABLE IF EXISTS acteur CASCADE;

-- ============================================
-- GEOGRAPHIC HIERARCHY TABLES
-- ============================================

CREATE TABLE tregion (
    id CHARACTER VARYING PRIMARY KEY,
    nom CHARACTER VARYING NOT NULL
);

CREATE TABLE tdepartement (
    id CHARACTER VARYING PRIMARY KEY,
    nom CHARACTER VARYING NOT NULL,
    region_id CHARACTER VARYING NOT NULL,
    FOREIGN KEY (region_id) REFERENCES tregion(id) ON DELETE CASCADE
);

CREATE TABLE tsousprefecture (
    id CHARACTER VARYING PRIMARY KEY,
    nom CHARACTER VARYING NOT NULL,
    departement_id CHARACTER VARYING NOT NULL,
    FOREIGN KEY (departement_id) REFERENCES tdepartement(id) ON DELETE CASCADE
);

-- ============================================
-- ACTOR & AUTHENTICATION TABLES
-- ============================================

CREATE TABLE acteur (
    id CHARACTER VARYING PRIMARY KEY,
    nom CHARACTER VARYING NOT NULL,
    type_acteur CHARACTER VARYING NOT NULL,
    contact_1 CHARACTER VARYING,
    contact_2 CHARACTER VARYING,
    adresse_1 CHARACTER VARYING,
    adresse_2 CHARACTER VARYING,
    email_1 CHARACTER VARYING,
    email_2 CHARACTER VARYING,
    date_creation TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE login (
    id CHARACTER VARYING PRIMARY KEY,
    username CHARACTER VARYING NOT NULL UNIQUE,
    password CHARACTER VARYING NOT NULL,
    acteur_id CHARACTER VARYING NOT NULL UNIQUE,
    FOREIGN KEY (acteur_id) REFERENCES acteur(id) ON DELETE CASCADE
);

CREATE TABLE administrateur (
    id CHARACTER VARYING PRIMARY KEY,
    login_id CHARACTER VARYING NOT NULL UNIQUE,
    nom CHARACTER VARYING NOT NULL,
    prenom CHARACTER VARYING NOT NULL,
    email CHARACTER VARYING,
    contact CHARACTER VARYING,

    role CHARACTER VARYING,
    date_creation TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (login_id) REFERENCES login(id) ON DELETE CASCADE
);

-- ============================================
-- PROJECT & INTERVENTION ZONE TABLES
-- ============================================

CREATE TABLE projet (
    id CHARACTER VARYING PRIMARY KEY,
    nom CHARACTER VARYING NOT NULL,
    nom_complet CHARACTER VARYING
);

CREATE TABLE zone_d_intervention (
    id CHARACTER VARYING PRIMARY KEY,
    acteur_id CHARACTER VARYING NOT NULL,
    projet_id CHARACTER VARYING NOT NULL,
    region_id CHARACTER VARYING,
    departement_id CHARACTER VARYING,
    sous_prefecture_id CHARACTER VARYING,
    FOREIGN KEY (acteur_id) REFERENCES acteur(id) ON DELETE CASCADE,
    FOREIGN KEY (projet_id) REFERENCES projet(id) ON DELETE CASCADE,
    FOREIGN KEY (region_id) REFERENCES tregion(id) ON DELETE SET NULL,
    FOREIGN KEY (departement_id) REFERENCES tdepartement(id) ON DELETE SET NULL,
    FOREIGN KEY (sous_prefecture_id) REFERENCES tsousprefecture(id) ON DELETE SET NULL
);

-- ============================================
-- POSITION & PERSON TABLES
-- ============================================


CREATE TABLE fic_personne (
    id CHARACTER VARYING PRIMARY KEY,
    acteur_id CHARACTER VARYING NOT NULL,
    projet_id CHARACTER VARYING NOT NULL,
    nom CHARACTER VARYING NOT NULL,
    prenom CHARACTER VARYING NOT NULL,
    date_naissance DATE,
    genre CHARACTER VARYING,
    contact CHARACTER VARYING,
    FOREIGN KEY (acteur_id) REFERENCES acteur(id) ON DELETE CASCADE,
    FOREIGN KEY (projet_id) REFERENCES projet(id) ON DELETE CASCADE
);

-- ============================================
-- SUPERVISION & CONTRACT TABLES
-- ============================================

CREATE TABLE supervision (
    id CHARACTER VARYING PRIMARY KEY,
    fic_personne_id CHARACTER VARYING NOT NULL,
    superviseur_id CHARACTER VARYING,
    date_debut DATE,
    date_fin DATE,
    FOREIGN KEY (fic_personne_id) REFERENCES fic_personne(id) ON DELETE CASCADE
);

CREATE TABLE contrat (
    id CHARACTER VARYING PRIMARY KEY,
    fic_personne_id CHARACTER VARYING NOT NULL,
    poste_nom CHARACTER VARYING NOT NULL,
    categorie_poste CHARACTER VARYING,
    diplome CHARACTER VARYING,
    type_personne CHARACTER VARYING,
    ecole CHARACTER VARYING,
    date_debut DATE NOT NULL,
    date_fin DATE,
    autre TEXT,
    FOREIGN KEY (fic_personne_id) REFERENCES fic_personne(id) ON DELETE CASCADE
);

CREATE TABLE fic_personne_localisation (
    id CHARACTER VARYING PRIMARY KEY,
    contrat_id CHARACTER VARYING NOT NULL,
    region_id CHARACTER VARYING,
    departement_id CHARACTER VARYING,
    sous_prefecture_id CHARACTER VARYING,
    date_debut DATE,
    FOREIGN KEY (contrat_id) REFERENCES contrat(id) ON DELETE CASCADE,
    FOREIGN KEY (region_id) REFERENCES tregion(id) ON DELETE SET NULL,
    FOREIGN KEY (departement_id) REFERENCES tdepartement(id) ON DELETE SET NULL,
    FOREIGN KEY (sous_prefecture_id) REFERENCES tsousprefecture(id) ON DELETE SET NULL
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
CREATE INDEX idx_fic_personne_acteur_id ON fic_personne(acteur_id);
CREATE INDEX idx_fic_personne_projet_id ON fic_personne(projet_id);
CREATE INDEX idx_supervision_fic_personne_id ON supervision(fic_personne_id);
CREATE INDEX idx_contrat_fic_personne_id ON contrat(fic_personne_id);
CREATE INDEX idx_fic_personne_localisation_contrat_id ON fic_personne_localisation(contrat_id);
