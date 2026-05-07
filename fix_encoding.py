"""
fix_encoding.py
═══════════════
Script à exécuter UNE SEULE FOIS pour corriger les caractères corrompus
dans la base de données (problème UTF-8 / CP437 / Latin-1).

Exemples de corruption :
  ├® → é
  ├¬ → ê
  ├â┬¬ → ê  (double encodage)

Utilisation :
  python fix_encoding.py --dry-run    # aperçu sans modification
  python fix_encoding.py              # correction réelle
"""

import sys
import os
import argparse

# Force UTF-8 sur stdout (nécessaire sous Windows CP1252)
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ── Répertoire du script = racine du backend
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# ── Force le répertoire de travail sur la racine backend
#    pour que pydantic_settings trouve le .env au bon endroit
os.chdir(SCRIPT_DIR)
sys.path.insert(0, SCRIPT_DIR)

from app.config import settings
from app.database import SessionLocal
from sqlalchemy import text as sql_text

# ──────────────────────────────────────────────────────────────
# DETECTION & CORRECTION
# ──────────────────────────────────────────────────────────────

# Caractères qui signalent un problème d'encodage
SUSPICIOUS = set('├┬┤┼╬╦╣╠╗╔╝╚╞╡╢╖╕╪╫╩╥╤╟╜╛╙╘╓╒║═╏╎╍╌╋╊╉╈╇╆╅╄╃╂╁╀')


def is_corrupted(text: str | None) -> bool:
    if not text:
        return False
    return any(c in SUSPICIOUS for c in text)


def fix_encoding(text: str | None) -> str | None:
    """
    Corrige un texte avec caractères corrompus (simple ou double encodage).

    Chaîne typique de corruption double :
      ê  →  UTF-8 bytes 0xC3 0xAA  →  vus comme Latin-1 (Ã + ª)
          →  ré-encodés en UTF-8 (0xC3 0x83 0xC2 0xAA)
          →  vus comme CP437  →  ├ â ┬ ¬   (stocké en BDD)

    Correction :
      Pass 1 (CP437 → UTF-8) : ├â┬¬ → Ãª
      Pass 2 (Latin-1 → UTF-8): Ãª  → ê
    """
    if not text:
        return text

    result = text

    # Pass 1 : dé-corrompre les caractères box-drawing CP437
    if is_corrupted(result):
        try:
            result = result.encode('cp437').decode('utf-8')
        except (UnicodeEncodeError, UnicodeDecodeError):
            try:
                result = result.encode('latin-1').decode('utf-8')
            except (UnicodeEncodeError, UnicodeDecodeError):
                return text  # pas corrigeable

    # Pass 2 : dé-corrompre le mojibake Latin-1 résiduel (Ãª → ê, Ã© → é…)
    if any(ord(c) > 127 for c in result):
        try:
            result = result.encode('latin-1').decode('utf-8')
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass  # pas de double encodage, résultat du pass 1 conservé

    return result


# ──────────────────────────────────────────────────────────────
# COLONNES À CORRIGER
# (table, colonne_id, colonnes_texte)
# ──────────────────────────────────────────────────────────────

TARGETS = [
    ("fic_personne", "id", ["nom", "prenom", "contact"]),
    ("contrat",      "id", ["poste_nom", "poste", "categorie_poste",
                             "type_contrat", "diplome", "ecole",
                             "type_personne"]),
]


# ──────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────

def run(dry_run: bool = True):
    db = SessionLocal()
    total_fixed = 0

    print("=" * 60)
    print(f"  Mode : {'APERCU (dry-run)' if dry_run else '[!] MODIFICATION REELLE'}")
    print("=" * 60)

    try:
        for table, id_col, columns in TARGETS:
            cols_select = ", ".join([id_col] + columns)
            rows = db.execute(sql_text(f"SELECT {cols_select} FROM {table}")).fetchall()

            for row in rows:
                row_id   = row[0]
                row_data = dict(zip([id_col] + columns, row))
                updates  = {}

                for col in columns:
                    original = row_data.get(col)
                    if not is_corrupted(original):
                        continue
                    fixed = fix_encoding(original)
                    if fixed != original:
                        updates[col] = fixed
                        print(f"  [{table}.{col}] id={str(row_id)[:8]}…")
                        print(f"    AVANT : {original}")
                        print(f"    APRÈS : {fixed}")

                if updates and not dry_run:
                    set_clause = ", ".join(f"{c} = :{c}" for c in updates)
                    updates[id_col] = row_id
                    db.execute(
                        sql_text(f"UPDATE {table} SET {set_clause} WHERE {id_col} = :{id_col}"),
                        updates,
                    )
                    total_fixed += len(updates)

        if not dry_run:
            db.commit()
            print(f"\n[OK] {total_fixed} valeur(s) corrigee(s) et sauvegardees.")
        else:
            print(f"\n[INFO] Dry-run termine - aucune modification appliquee.")
            print("       Relancez avec :  python fix_encoding.py  (sans --dry-run)")

    except Exception as e:
        db.rollback()
        print(f"\n[ERREUR] {e}")
        raise
    finally:
        db.close()


def diagnose():
    """Affiche un échantillon brut de la BDD pour voir les vrais caractères stockés."""
    db = SessionLocal()
    print("=" * 60)
    print("  DIAGNOSTIC - Contenu brut de la base de donnees")
    print("=" * 60)
    try:
        # Echantillon contrat
        rows = db.execute(sql_text(
            "SELECT id, poste_nom, poste, categorie_poste, diplome, ecole FROM contrat LIMIT 10"
        )).fetchall()

        print("\n--- TABLE contrat (10 premieres lignes) ---")
        for r in rows:
            print(f"  id={str(r[0])[:8]}...")
            for col, val in zip(["poste_nom","poste","categorie_poste","diplome","ecole"], r[1:]):
                if val:
                    # Affiche les codes Unicode des caracteres suspects
                    suspects = [(i, c, hex(ord(c))) for i, c in enumerate(val) if ord(c) > 127]
                    print(f"    {col}: {repr(val)}")
                    if suspects:
                        print(f"      Chars non-ASCII: {suspects[:5]}")

        # Echantillon fic_personne
        rows2 = db.execute(sql_text(
            "SELECT id, nom, prenom FROM fic_personne LIMIT 5"
        )).fetchall()

        print("\n--- TABLE fic_personne (5 premieres lignes) ---")
        for r in rows2:
            print(f"  id={str(r[0])[:8]}... | nom={repr(r[1])} | prenom={repr(r[2])}")

    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Corrige l'encodage dans la BDD AFOR Emploi")
    parser.add_argument("--dry-run",    action="store_true", default=False,
                        help="Affiche les corrections sans les appliquer")
    parser.add_argument("--diagnose",   action="store_true", default=False,
                        help="Affiche le contenu brut de la BDD pour diagnostic")
    args = parser.parse_args()

    if args.diagnose:
        diagnose()
    else:
        run(dry_run=args.dry_run)
