"""
Utilitaires de logging pour AFOR Emploi.
Wrapping du module logging standard avec formatage structure.
"""

import logging
import sys

# ─── Configuration du logger ─────────────────────────────────────────────────

_formatter = logging.Formatter(
    fmt="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

_handler = logging.StreamHandler(sys.stdout)
_handler.setFormatter(_formatter)

app_logger = logging.getLogger("afor_emploi")
app_logger.setLevel(logging.DEBUG)

if not app_logger.handlers:
    app_logger.addHandler(_handler)

app_logger.propagate = False


# ─── Fonctions utilitaires ───────────────────────────────────────────────────

def log_employee_creation(data: dict, acteur_id: str) -> None:
    """Log structure lors de la creation d'un employe."""
    nom       = data.get("nom", "?")
    prenom    = data.get("prenom", "?")
    matricule = data.get("matricule") or "-"
    app_logger.info(
        f"[CREATION_EMPLOYEE] acteur={acteur_id} | "
        f"nom={nom} {prenom} | matricule={matricule}"
    )


def log_db_operation(operation: str, table: str, data: dict) -> None:
    """Log structure pour une operation base de donnees."""
    record_id = data.get("id", "?")
    extras = " | ".join(f"{k}={v}" for k, v in data.items() if k != "id")
    app_logger.debug(
        f"[DB:{operation}] table={table} | id={record_id}"
        + (f" | {extras}" if extras else "")
    )


def log_error(context: str, error: str, extra: dict = None) -> None:
    """Log d'une erreur avec contexte metier."""
    details = ""
    if extra:
        details = " | " + " | ".join(f"{k}={v}" for k, v in extra.items())
    app_logger.error(f"[ERROR:{context}] {error}{details}")
