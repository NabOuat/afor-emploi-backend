-- Migration: Créer la table de jonction fic_personne_projet pour la relation many-to-many
-- Entre fic_personne et projet

-- Créer la table de jonction
CREATE TABLE IF NOT EXISTS fic_personne_projet (
    id VARCHAR(36) PRIMARY KEY,
    fic_personne_id VARCHAR(36) NOT NULL,
    projet_id VARCHAR(36) NOT NULL,
    date_debut DATE,
    date_fin DATE,
    FOREIGN KEY (fic_personne_id) REFERENCES fic_personne(id) ON DELETE CASCADE,
    FOREIGN KEY (projet_id) REFERENCES projet(id) ON DELETE CASCADE,
    UNIQUE(fic_personne_id, projet_id)
);

-- Créer un index pour les requêtes fréquentes
CREATE INDEX idx_fic_personne_projet_fic_personne_id ON fic_personne_projet(fic_personne_id);
CREATE INDEX idx_fic_personne_projet_projet_id ON fic_personne_projet(projet_id);

-- Migrer les données existantes depuis la colonne projet_id de fic_personne
-- (si la colonne existe encore)
INSERT INTO fic_personne_projet (id, fic_personne_id, projet_id, date_debut, date_fin)
SELECT 
    CONCAT(fp.id, '-', fp.projet_id),
    fp.id,
    fp.projet_id,
    NULL,
    NULL
FROM fic_personne fp
WHERE fp.projet_id IS NOT NULL
ON CONFLICT (fic_personne_id, projet_id) DO NOTHING;

-- Note: La colonne projet_id de fic_personne peut être supprimée après vérification
-- ALTER TABLE fic_personne DROP COLUMN projet_id;
