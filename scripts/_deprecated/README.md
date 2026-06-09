# Scripts dépréciés (archivés)

Ces scripts ont été archivés ici le **2026-06-09** car ils sont **non fonctionnels**
et/ou **remplacés par l'interface web**.

## `import/` — imports `fic_personne` (CASSÉS)

- `cli_import.py`, `gui_import.py`, `gui_import_v2.py`, `gui_import_custom.py`

Tous dépendent de `from import_service import FicPersonneImporter`, or le module
**`import_service.py` n'existe nulle part dans le projet** → ces scripts ne peuvent
pas s'exécuter.

➡️ Remplacés par l'import web : onglet **Base de données → Importer**
(`POST /api/import-export/import-employees`, modèle Excel complet).

## `tools/` — application Flask annexe (CASSÉE)

- `app.py` : 2ᵉ application Flask distincte du backend FastAPI. Dépend de
  `import_service` **et** `db`, tous deux absents.
- `config.py` : configuration utilisée uniquement par `app.py`.

➡️ Les fonctions « vérifier acteurs/projets » sont couvertes par les pages web
**Acteurs** et **Projets**.

## Conservé (toujours utilisable)

`scripts/tools/engagement_manager.py` reste en place — mais sa fonction
(gestion des engagements + liaison aux projets) est désormais reproduite dans
l'interface web : **Sidebar admin → Engagements** (`/admin/engagements`).

> Suppression définitive possible une fois la migration validée. Le projet
> n'étant pas sous git, ces fichiers ont été déplacés (réversible) plutôt que
> supprimés.
