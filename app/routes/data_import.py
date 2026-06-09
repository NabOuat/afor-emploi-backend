# -*- coding: utf-8 -*-
"""
Import de données CSV vers la base — piloté depuis l'interface admin.

Deux modes :
  • table cible directe (mapping colonne→colonne automatique par nom)
  • preset AFOR (transformation ancien schéma → nouveau schéma)

Sécurité : admin uniquement. Toujours prévisualiser (preview) avant execute.
Upsert par clé primaire : si l'id existe → mise à jour (écrasement), sinon insertion.

Ordre d'import recommandé :
  1. tregion → tdepartement → tsousprefecture
  2. projet
  3. toperateur_foncier, tagence_execution, tecole_partenaire  (→ acteur)
  4. fic_personne
  5. contrat
  6. zone_d_intervention
"""
import csv
import io
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy import text, inspect
from sqlalchemy.orm import Session

from app.database import get_db
from app.security import require_admin
from app.models import Users

router = APIRouter(prefix="/api/admin/import", tags=["Admin Tools"])


# ──────────────────────────────────────────────────────────────────────────────
# PRESETS — transformations ancien schéma AFOR → nouveau schéma
# ──────────────────────────────────────────────────────────────────────────────
# Chaque preset décrit :
#   target      : table cible
#   columns     : noms des colonnes pour CSV sans en-tête (positionnels)
#   map         : { colonne_source : colonne_cible }
#   const       : { colonne_cible : valeur_constante }
#   coalesce    : { colonne_cible : [colonnes_source...] }  (1ʳᵉ non vide)
#   null_values : liste de valeurs à traiter comme NULL (ex. placeholders)
#   note        : aide affichée dans l'UI

PRESETS: dict[str, dict[str, Any]] = {

    # ── Référentiels géographiques ────────────────────────────────────────────

    "tregion": {
        "label": "Régions (Tregion.csv → tregion)",
        "target": "tregion",
        "columns": ["id", "nom"],
        "map": {"id": "id", "nom": "nom"},
        "note": "Format : id(01-33), nom. Pas d'en-tête dans le fichier.",
    },

    "tdepartement": {
        "label": "Départements (Tdep.csv → tdepartement)",
        "target": "tdepartement",
        "columns": ["id", "nom", "region_id"],
        "map": {"id": "id", "nom": "nom", "region_id": "region_id"},
        "note": "Importer les régions d'abord. Format : id, nom, region_id.",
    },

    "tsousprefecture": {
        "label": "Sous-préfectures (TSP.csv → tsousprefecture)",
        "target": "tsousprefecture",
        "columns": ["id", "nom", "departement_id"],
        "map": {"id": "id", "nom": "nom", "departement_id": "departement_id"},
        "note": "Importer les départements d'abord. Format : id, nom, departement_id.",
    },

    # ── Projets ───────────────────────────────────────────────────────────────

    "projet": {
        "label": "Projets (Projet.csv → projet)",
        "target": "projet",
        "columns": ["id", "nom", "nom_complet", "_col4"],
        "map": {"id": "id", "nom": "nom", "nom_complet": "nom_complet"},
        "note": "Format : id(code), nom_court, nom_complet, (ignoré). Ex : PRESFOR, PRESFOR, PRESFOR.",
    },

    # ── Acteurs : 4 tables anciennes → table unifiée acteur ───────────────────

    "toperateur_foncier": {
        "label": "Opérateurs fonciers (TOperateur.csv → acteur OF)",
        "target": "acteur",
        "columns": [
            "id", "nom", "contact_1", "contact_2",
            "adresse_1", "adresse_2", "email_1", "email_2", "_col9",
        ],
        "const": {"type_acteur": "OF"},
        "map": {
            "id": "id", "nom": "nom",
            "contact_1": "contact_1", "contact_2": "contact_2",
            "adresse_1": "adresse_1", "adresse_2": "adresse_2",
            "email_1": "email_1", "email_2": "email_2",
        },
        "note": "9 colonnes : id, nom, tel1, tel2, adresse1, adresse2, email1, email2, (ignoré).",
    },

    "tagence_execution": {
        "label": "Agences AFOR (Tagencedex.csv → acteur AF)",
        "target": "acteur",
        "columns": ["id", "nom", "contact_1", "_col4"],
        "const": {"type_acteur": "AF"},
        "map": {"id": "id", "nom": "nom", "contact_1": "contact_1"},
        "note": "4 colonnes : id(ex. AFOR, AFOR-DSIG…), nom, contact, (ignoré). Type AF = entité AFOR.",
    },

    "tecole_partenaire": {
        "label": "Écoles partenaires (Tecole.csv → acteur ECOLE)",
        "target": "acteur",
        "columns": ["id", "nom", "_col3"],
        "const": {"type_acteur": "ECOLE"},
        "map": {"id": "id", "nom": "nom"},
        "note": "3 colonnes : id(numérique), nom, (ignoré). IDs numériques (1, 2, 3…).",
    },

    # ── Employés ──────────────────────────────────────────────────────────────

    "fic_personne": {
        "label": "Employés (fic_personne.csv → fic_personne)",
        "target": "fic_personne",
        "columns": [
            "id", "nom", "prenom", "contact", "date_naissance", "genre",
            "_type_old", "acteur_id",
            "_col9", "_col10", "diplome", "_col12", "matricule", "date_creation", "_col15",
        ],
        "map": {
            "id": "id", "nom": "nom", "prenom": "prenom",
            "contact": "contact", "date_naissance": "date_naissance",
            "genre": "genre", "acteur_id": "acteur_id",
            "diplome": "diplome", "matricule": "matricule",
        },
        "null_values": ["XXXXXXXX", "Inconnu", "INCONNU", "inconnu", "N/A", "n/a", ""],
        "note": (
            "15 colonnes. acteur_id (col 8) est un UUID direct vers la table acteur. "
            "ATTENTION : beaucoup de matricules sont 'XXXXXXXX' → mis à NULL pour respecter "
            "la contrainte UNIQUE. Importer les acteurs (opérateurs) d'abord."
        ),
    },

    # ── Contrats ──────────────────────────────────────────────────────────────

    "contrat": {
        "label": "Contrats (Contrat.csv → contrat)",
        "target": "contrat",
        "columns": [
            "id", "poste_nom", "date_debut", "date_fin", "categorie_poste",
            "fic_personne_id", "engagement_id", "type_contrat", "poste", "ecole",
        ],
        "map": {
            "id": "id",
            "poste_nom": "poste_nom",
            "date_debut": "date_debut",
            "date_fin": "date_fin",
            "categorie_poste": "categorie_poste",
            "fic_personne_id": "fic_personne_id",
            "engagement_id": "engagement_id",
            "type_contrat": "type_contrat",
            "poste": "poste",
            "ecole": "ecole",
        },
        "null_values": ["Inconnu", "INCONNU", "inconnu", "INCONNU", "N/A", ""],
        "note": (
            "10 colonnes. projet_id absent dans l'ancien CSV → NULL après import. "
            "Vous pouvez l'affecter manuellement via la page Projets. "
            "Importer fic_personne d'abord."
        ),
    },

    # ── Zones d'intervention ──────────────────────────────────────────────────

    "zone_d_intervention": {
        "label": "Zones d'intervention (Zone D4INTERVETION.csv → zone_d_intervention)",
        "target": "zone_d_intervention",
        "columns": [
            "id", "projet_id", "region_id", "acteur_id", "_col5", "_col6",
        ],
        "map": {
            "id": "id",
            "projet_id": "projet_id",
            "region_id": "region_id",
            "acteur_id": "acteur_id",
        },
        "note": (
            "6 colonnes. Colonne 3 = region_id (format 01-33, vérifié à 100%). "
            "Importer tregion, projets et acteurs d'abord."
        ),
    },

    # ── Localisations employés ────────────────────────────────────────────────

    "fic_personne_localisation": {
        "label": "Localisations employés (fic_personneLoca.csv → fic_personne_localisation)",
        "target": "fic_personne_localisation",
        "columns": [
            "id", "contrat_id", "departement_id", "sous_prefecture_id",
            "_col5", "_type_loc", "_col7",
        ],
        "map": {
            "id": "id",
            "contrat_id": "contrat_id",
            "departement_id": "departement_id",
            "sous_prefecture_id": "sous_prefecture_id",
        },
        "note": (
            "7 colonnes. La colonne 2 contient les contrat_id (vérifié : 1163/1163 UUIDs "
            "correspondent à la table contrat). Importer les contrats d'abord."
        ),
    },
}


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _table_columns(db: Session, table: str) -> list[str]:
    insp = inspect(db.get_bind())
    if table not in insp.get_table_names():
        raise HTTPException(404, f"Table « {table} » introuvable en base")
    return [c["name"] for c in insp.get_columns(table)]


def _table_pk(db: Session, table: str) -> Optional[str]:
    insp = inspect(db.get_bind())
    pk = insp.get_pk_constraint(table).get("constrained_columns") or []
    return pk[0] if pk else None


def _parse_csv(raw: bytes, columns: Optional[list[str]] = None) -> tuple[list[str], list[dict[str, str]]]:
    """Décode (utf-8 puis latin-1) et parse le CSV (délimiteur , ou ; auto).

    Si *columns* est fourni, le CSV est traité comme sans en-tête et les noms
    de colonnes sont assignés positionnellement (presets AFOR sans header row).
    """
    try:
        text_data = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text_data = raw.decode("latin-1")

    sample = text_data[:4096]
    delimiter = ";" if sample.count(";") > sample.count(",") else ","

    if columns:
        reader = csv.DictReader(io.StringIO(text_data), fieldnames=columns, delimiter=delimiter)
        rows = [dict(r) for r in reader]
        return list(columns), rows
    else:
        reader = csv.DictReader(io.StringIO(text_data), delimiter=delimiter)
        headers = list(reader.fieldnames or [])
        rows = [dict(r) for r in reader]
        return headers, rows


def _norm(v: Any) -> Optional[str]:
    if v is None:
        return None
    s = str(v).strip()
    return s if s != "" else None


def _build_mapping(preset_key: Optional[str], target: Optional[str], headers: list[str]):
    """Retourne (target_table, colmap, const, coalesce, null_values).
    Sans preset : mapping automatique colonne→colonne sur les noms identiques."""
    if preset_key:
        p = PRESETS.get(preset_key)
        if not p:
            raise HTTPException(400, f"Preset « {preset_key} » inconnu")
        return (
            p["target"],
            dict(p.get("map", {})),
            dict(p.get("const", {})),
            dict(p.get("coalesce", {})),
            list(p.get("null_values", [])),
        )
    if not target:
        raise HTTPException(400, "Indiquez un preset ou une table cible")
    colmap = {h: h for h in headers}
    return target, colmap, {}, {}, []


def _transform_row(
    row: dict,
    colmap: dict,
    const: dict,
    coalesce: dict,
    target_cols: list[str],
    null_values: Optional[list[str]] = None,
) -> dict:
    null_set = set(null_values or [])
    out: dict[str, Any] = {}

    for src, dst in colmap.items():
        if dst in target_cols and src in row:
            v = _norm(row[src])
            out[dst] = None if (v in null_set) else v

    for dst, val in const.items():
        if dst in target_cols:
            out[dst] = val

    for dst, sources in coalesce.items():
        if dst in target_cols:
            picked = None
            for s in sources:
                picked = _norm(row.get(s))
                if picked and picked not in null_set:
                    break
                else:
                    picked = None
            out[dst] = picked

    return out


# ──────────────────────────────────────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────────────────────────────────────

@router.get("/presets")
def list_presets(_: Users = Depends(require_admin)):
    """Liste les presets disponibles (pour le menu déroulant de l'UI)."""
    return {
        "presets": [
            {"key": k, "label": p["label"], "target": p["target"], "note": p.get("note", "")}
            for k, p in PRESETS.items()
        ]
    }


@router.post("/preview")
async def preview_import(
    file: UploadFile = File(...),
    preset: Optional[str] = Form(None),
    target_table: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    _: Users = Depends(require_admin),
):
    """Analyse le CSV sans rien écrire : colonnes, mapping, échantillon transformé."""
    raw = await file.read()

    # Récupérer les noms de colonnes depuis le preset (CSV sans en-tête)
    preset_columns: Optional[list[str]] = None
    if preset and preset in PRESETS:
        preset_columns = PRESETS[preset].get("columns")

    headers, rows = _parse_csv(raw, columns=preset_columns)
    if not headers or not rows:
        raise HTTPException(400, "CSV vide ou illisible")

    target, colmap, const, coalesce, null_values = _build_mapping(preset, target_table, headers)
    target_cols = _table_columns(db, target)
    pk = _table_pk(db, target)

    used_sources = set(colmap.keys()) | {s for srcs in coalesce.values() for s in srcs}
    # Ignorer les colonnes internes commençant par _ (colonnes ignorées du preset)
    unmatched_sources = [h for h in headers if h not in used_sources and not h.startswith("_")]
    covered_targets = set(colmap.values()) | set(const.keys()) | set(coalesce.keys())
    uncovered_targets = [c for c in target_cols if c not in covered_targets]

    sample = [
        _transform_row(r, colmap, const, coalesce, target_cols, null_values)
        for r in rows[:5]
    ]

    return {
        "target_table": target,
        "primary_key": pk,
        "source_headers": [h for h in headers if not h.startswith("_")],
        "target_columns": target_cols,
        "unmatched_sources": unmatched_sources,
        "uncovered_targets": uncovered_targets,
        "total_rows": len(rows),
        "sample": sample,
        "note": PRESETS[preset].get("note", "") if preset else "",
    }


@router.post("/execute")
async def execute_import(
    file: UploadFile = File(...),
    preset: Optional[str] = Form(None),
    target_table: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    _: Users = Depends(require_admin),
):
    """Importe réellement (upsert par clé primaire : écrase si l'id existe)."""
    raw = await file.read()

    preset_columns: Optional[list[str]] = None
    if preset and preset in PRESETS:
        preset_columns = PRESETS[preset].get("columns")

    headers, rows = _parse_csv(raw, columns=preset_columns)
    if not headers or not rows:
        raise HTTPException(400, "CSV vide ou illisible")

    target, colmap, const, coalesce, null_values = _build_mapping(preset, target_table, headers)
    target_cols = _table_columns(db, target)
    pk = _table_pk(db, target)
    if not pk:
        raise HTTPException(400, f"La table « {target} » n'a pas de clé primaire simple — upsert impossible")

    written = skipped = 0
    errors: list[dict] = []

    for i, row in enumerate(rows, start=1):
        data = _transform_row(row, colmap, const, coalesce, target_cols, null_values)
        # Ne garder que les colonnes non-NULL (+ la pk même si None pour déclencher skip)
        data = {k: v for k, v in data.items() if v is not None or k == pk}
        if not data.get(pk):
            skipped += 1
            continue

        cols = list(data.keys())
        set_cols = [c for c in cols if c != pk]
        placeholders = ", ".join(f":{c}" for c in cols)
        col_list = ", ".join(f'"{c}"' for c in cols)

        try:
            if set_cols:
                updates = ", ".join(f'"{c}" = EXCLUDED."{c}"' for c in set_cols)
                sql = (
                    f'INSERT INTO public."{target}" ({col_list}) VALUES ({placeholders}) '
                    f'ON CONFLICT ("{pk}") DO UPDATE SET {updates}'
                )
            else:
                sql = (
                    f'INSERT INTO public."{target}" ({col_list}) VALUES ({placeholders}) '
                    f'ON CONFLICT ("{pk}") DO NOTHING'
                )
            with db.begin_nested():  # savepoint : isole chaque ligne
                db.execute(text(sql), data)
            written += 1
        except Exception as e:
            errors.append({"ligne": i, "erreur": str(e)[:200]})
            if len(errors) > 50:
                break
            continue

    db.commit()
    return {
        "target_table": target,
        "total_rows": len(rows),
        "ecrits": written,
        "ignores": skipped,
        "erreurs": errors,
    }
