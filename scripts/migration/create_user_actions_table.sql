-- Créer la table user_actions pour enregistrer toutes les actions des utilisateurs
CREATE TABLE IF NOT EXISTS user_actions (
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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (login_id) REFERENCES login(id) ON DELETE CASCADE,
    FOREIGN KEY (acteur_id) REFERENCES acteur(id) ON DELETE CASCADE
);

-- Créer des index pour améliorer les performances
CREATE INDEX idx_user_actions_login_id ON user_actions(login_id);
CREATE INDEX idx_user_actions_acteur_id ON user_actions(acteur_id);
CREATE INDEX idx_user_actions_created_at ON user_actions(created_at);
CREATE INDEX idx_user_actions_action_type ON user_actions(action_type);
CREATE INDEX idx_user_actions_username ON user_actions(username);

-- Types d'actions possibles:
-- LOGIN: Connexion utilisateur
-- LOGOUT: Déconnexion utilisateur
-- VIEW: Consultation de données
-- CREATE: Création de données
-- UPDATE: Modification de données
-- DELETE: Suppression de données
-- EXPORT: Export de données
-- IMPORT: Import de données
-- DOWNLOAD: Téléchargement de fichier
