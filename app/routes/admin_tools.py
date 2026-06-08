# -*- coding: utf-8 -*-
"""
Routes d'outils d'administration — accessibles uniquement aux admins (type_acteur = 'AD').
Regroupe : inspection BD, correction encodage, statistiques, export SQL.
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.database import get_db
from app.security import require_admin
from app.models import Users
from app.config import settings
from datetime import datetime
from io import StringIO

router = APIRouter(prefix="/api/admin/tools", tags=["Admin Tools"])


# ──────────────────────────────────────────────────────────────────────────────
# INSPECT — Structure & statistiques de la base
# ──────────────────────────────────────────────────────────────────────────────

@router.get("/db/tables")
def list_tables(
    db: Session = Depends(get_db),
    _: Users = Depends(require_admin),
):
    """Liste toutes les tables publiques de la base de données."""
    rows = db.execute(text("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name
    """)).fetchall()
    return {"tables": [r[0] for r in rows]}


@router.get("/db/stats")
def db_stats(
    db: Session = Depends(get_db),
    _: Users = Depends(require_admin),
):
    """Nombre de lignes par table (toutes les tables publiques)."""
    tables = db.execute(text("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name
    """)).fetchall()

    result = {}
    for (table,) in tables:
        try:
            count = db.execute(text(f'SELECT COUNT(*) FROM public."{table}"')).scalar()
            result[table] = count
        except Exception:
            result[table] = None
    return {"stats": result}


@router.get("/db/structure")
def db_structure(
    db: Session = Depends(get_db),
    _: Users = Depends(require_admin),
):
    """Structure complète : colonnes, types, nullable, clés primaires/étrangères."""
    columns = db.execute(text("""
        SELECT
            c.table_name,
            c.column_name,
            c.data_type,
            c.is_nullable,
            c.column_default,
            CASE WHEN tc.constraint_type = 'PRIMARY KEY' THEN true ELSE false END AS is_primary
        FROM information_schema.columns c
        LEFT JOIN information_schema.key_column_usage kcu
            ON c.table_name = kcu.table_name AND c.column_name = kcu.column_name
            AND c.table_schema = kcu.table_schema
        LEFT JOIN information_schema.table_constraints tc
            ON kcu.constraint_name = tc.constraint_name
            AND tc.constraint_type = 'PRIMARY KEY'
        WHERE c.table_schema = 'public'
        ORDER BY c.table_name, c.ordinal_position
    """)).fetchall()

    fkeys = db.execute(text("""
        SELECT
            tc.table_name,
            kcu.column_name,
            ccu.table_name  AS foreign_table,
            ccu.column_name AS foreign_column
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
            ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.constraint_column_usage ccu
            ON ccu.constraint_name = tc.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY'
        AND tc.table_schema = 'public'
        ORDER BY tc.table_name
    """)).fetchall()

    structure: dict = {}
    for table, col, dtype, nullable, default, is_pk in columns:
        structure.setdefault(table, {"columns": [], "foreign_keys": []})
        structure[table]["columns"].append({
            "name": col,
            "type": dtype,
            "nullable": nullable == "YES",
            "default": default,
            "primary_key": bool(is_pk),
        })

    for table, col, ftable, fcol in fkeys:
        if table in structure:
            structure[table]["foreign_keys"].append({
                "column": col,
                "references": f"{ftable}.{fcol}",
            })

    return {"structure": structure}


@router.get("/db/indexes")
def db_indexes(
    db: Session = Depends(get_db),
    _: Users = Depends(require_admin),
):
    """Liste tous les index de la base."""
    rows = db.execute(text("""
        SELECT
            tablename,
            indexname,
            indexdef
        FROM pg_indexes
        WHERE schemaname = 'public'
        ORDER BY tablename, indexname
    """)).fetchall()
    return {"indexes": [{"table": r[0], "name": r[1], "definition": r[2]} for r in rows]}


# ──────────────────────────────────────────────────────────────────────────────
# FIX — Correction d'encodage
# ──────────────────────────────────────────────────────────────────────────────

@router.get("/fix/encoding/preview")
def preview_encoding_issues(
    db: Session = Depends(get_db),
    _: Users = Depends(require_admin),
):
    """Liste les valeurs mal encodées (Ã©, Â, etc.) dans la table contrat."""
    rows = db.execute(text("""
        SELECT id, poste_nom FROM contrat
        WHERE poste_nom LIKE '%Ã%' OR poste_nom LIKE '%Â%'
        ORDER BY poste_nom
    """)).fetchall()

    previews = []
    for row_id, poste_nom in rows:
        try:
            fixed = poste_nom.encode("latin-1").decode("utf-8")
        except Exception:
            fixed = None
        previews.append({"id": row_id, "actuel": poste_nom, "corrige": fixed})

    return {"count": len(previews), "items": previews}


@router.post("/fix/encoding/apply")
def apply_encoding_fix(
    db: Session = Depends(get_db),
    _: Users = Depends(require_admin),
):
    """Corrige les erreurs d'encodage UTF-8 dans contrat.poste_nom."""
    rows = db.execute(text("""
        SELECT id, poste_nom FROM contrat
        WHERE poste_nom LIKE '%Ã%' OR poste_nom LIKE '%Â%'
    """)).fetchall()

    fixed_count = 0
    errors = []
    for row_id, poste_nom in rows:
        try:
            fixed = poste_nom.encode("latin-1").decode("utf-8")
            db.execute(
                text("UPDATE contrat SET poste_nom = :fixed WHERE id = :id"),
                {"fixed": fixed, "id": row_id},
            )
            fixed_count += 1
        except Exception as e:
            errors.append({"id": row_id, "error": str(e)})

    db.commit()
    return {"corrected": fixed_count, "errors": errors}


@router.get("/fix/encoding/fic_personne/preview")
def preview_encoding_fic_personne(
    db: Session = Depends(get_db),
    _: Users = Depends(require_admin),
):
    """Liste les noms/prénoms mal encodés dans fic_personne."""
    rows = db.execute(text("""
        SELECT id, nom, prenom FROM fic_personne
        WHERE nom LIKE '%Ã%' OR nom LIKE '%Â%'
           OR prenom LIKE '%Ã%' OR prenom LIKE '%Â%'
        ORDER BY nom
    """)).fetchall()

    previews = []
    for row_id, nom, prenom in rows:
        try:
            fixed_nom = nom.encode("latin-1").decode("utf-8")
            fixed_prenom = prenom.encode("latin-1").decode("utf-8")
        except Exception:
            fixed_nom = fixed_prenom = None
        previews.append({
            "id": row_id,
            "nom_actuel": nom, "nom_corrige": fixed_nom,
            "prenom_actuel": prenom, "prenom_corrige": fixed_prenom,
        })
    return {"count": len(previews), "items": previews}


@router.post("/fix/encoding/fic_personne/apply")
def apply_encoding_fic_personne(
    db: Session = Depends(get_db),
    _: Users = Depends(require_admin),
):
    """Corrige les erreurs d'encodage dans fic_personne.nom et prenom."""
    rows = db.execute(text("""
        SELECT id, nom, prenom FROM fic_personne
        WHERE nom LIKE '%Ã%' OR nom LIKE '%Â%'
           OR prenom LIKE '%Ã%' OR prenom LIKE '%Â%'
    """)).fetchall()

    fixed_count = 0
    errors = []
    for row_id, nom, prenom in rows:
        try:
            fixed_nom = nom.encode("latin-1").decode("utf-8")
            fixed_prenom = prenom.encode("latin-1").decode("utf-8")
            db.execute(
                text("UPDATE fic_personne SET nom = :nom, prenom = :prenom WHERE id = :id"),
                {"nom": fixed_nom, "prenom": fixed_prenom, "id": row_id},
            )
            fixed_count += 1
        except Exception as e:
            errors.append({"id": row_id, "error": str(e)})

    db.commit()
    return {"corrected": fixed_count, "errors": errors}


# ──────────────────────────────────────────────────────────────────────────────
# EXPORT SQL — Dump de structure
# ──────────────────────────────────────────────────────────────────────────────

@router.get("/export/schema")
def export_schema(
    db: Session = Depends(get_db),
    _: Users = Depends(require_admin),
):
    """Exporte la structure de la BD (CREATE TABLE) en fichier .sql téléchargeable."""
    tables = db.execute(text("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name
    """)).fetchall()

    output = StringIO()
    output.write(f"-- AFOR Emploi — Export structure\n")
    output.write(f"-- Généré le : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

    for (table,) in tables:
        try:
            cols = db.execute(text(f"""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = '{table}'
                ORDER BY ordinal_position
            """)).fetchall()

            output.write(f"-- Table: {table}\n")
            output.write(f'CREATE TABLE IF NOT EXISTS public."{table}" (\n')
            col_defs = []
            for col, dtype, nullable, default in cols:
                line = f'    "{col}" {dtype.upper()}'
                if default:
                    line += f" DEFAULT {default}"
                if nullable == "NO":
                    line += " NOT NULL"
                col_defs.append(line)
            output.write(",\n".join(col_defs))
            output.write("\n);\n\n")
        except Exception:
            pass

    output.seek(0)
    filename = f"schema_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/plain",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/export/data/{table_name}")
def export_table_csv(
    table_name: str,
    db: Session = Depends(get_db),
    _: Users = Depends(require_admin),
):
    """Exporte le contenu d'une table en CSV."""
    import csv

    # Vérifier que la table existe (sécurité injection SQL)
    exists = db.execute(text("""
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = :t
    """), {"t": table_name}).fetchone()

    if not exists:
        raise HTTPException(status_code=404, detail=f"Table '{table_name}' introuvable")

    rows = db.execute(text(f'SELECT * FROM public."{table_name}"')).fetchall()
    if not rows:
        raise HTTPException(status_code=204, detail="Table vide")

    keys = db.execute(text(f'SELECT * FROM public."{table_name}" LIMIT 0')).keys()

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(list(keys))
    for row in rows:
        writer.writerow(list(row))

    output.seek(0)
    filename = f"{table_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# ──────────────────────────────────────────────────────────────────────────────
# MIGRATION — Appliquer/vérifier le schéma
# ──────────────────────────────────────────────────────────────────────────────

@router.post("/migration/apply-schema")
def apply_schema(
    db: Session = Depends(get_db),
    _: Users = Depends(require_admin),
):
    """Réapplique le fichier migrations/schema.sql (idempotent — IF NOT EXISTS)."""
    from app.database import _run_schema_sql
    try:
        _run_schema_sql()
        return {"status": "ok", "message": "Schema appliqué avec succès"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/migration/missing-tables")
def check_missing_tables(
    db: Session = Depends(get_db),
    _: Users = Depends(require_admin),
):
    """Vérifie quelles tables du schéma attendu sont absentes de la BD."""
    expected = [
        "acteur", "administrateur", "contrat", "engagement",
        "fic_personne", "fic_personne_acteur", "fic_personne_localisation",
        "fic_personne_projet", "projet", "projet_engagement",
        "supervision", "tdepartement", "tregion", "tsousprefecture",
        "user_actions", "users", "zone_d_intervention",
    ]
    existing = [
        r[0] for r in db.execute(text("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public'
        """)).fetchall()
    ]
    missing = [t for t in expected if t not in existing]
    return {
        "expected": len(expected),
        "existing": len(existing),
        "missing": missing,
        "ok": len(missing) == 0,
    }
