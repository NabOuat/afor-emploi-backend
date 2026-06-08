import os
import logging
from pathlib import Path
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session
from app.config import settings
from app.models import Base

logger = logging.getLogger(__name__)

_is_sqlite = "sqlite" in settings.DATABASE_URL

_engine_kwargs: dict = {
    "echo": False,
    "connect_args": {"check_same_thread": False} if _is_sqlite else {},
    "pool_pre_ping": True,
    "isolation_level": "READ COMMITTED",
}

# Pool de connexions optimisé pour PostgreSQL/Supabase
if not _is_sqlite:
    _engine_kwargs.update({
        "pool_size": 5,        # connexions maintenues en pool
        "max_overflow": 10,    # connexions supplémentaires si besoin
        "pool_timeout": 30,    # attente max pour une connexion (s)
        "pool_recycle": 1800,  # recycle les connexions après 30min
    })

engine = create_engine(settings.DATABASE_URL, **_engine_kwargs)

# Configurer UTF-8 pour PostgreSQL
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    if "postgresql" in settings.DATABASE_URL:
        dbapi_conn.set_client_encoding('UTF8')

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Chemin vers le fichier SQL de schéma (à la racine du projet, à côté de main.py)
_SCHEMA_FILE = Path(__file__).parent.parent / "migrations" / "schema.sql"


def _run_schema_sql() -> None:
    """
    Exécute le fichier schema.sql (CREATE TABLE IF NOT EXISTS + FK + index).
    Ne touche pas aux données existantes. Les erreurs non-fatales (FK déjà
    présente, index déjà présent) sont ignorées silencieusement.
    """
    if not _SCHEMA_FILE.exists():
        logger.warning("schema.sql introuvable (%s) — initialisation SQL ignorée", _SCHEMA_FILE)
        return

    sql_content = _SCHEMA_FILE.read_text(encoding="utf-8")

    # Découper en instructions individuelles sur les ';'
    statements = [s.strip() for s in sql_content.split(";") if s.strip()]

    with engine.connect() as conn:
        for stmt in statements:
            # Ignorer les commentaires purs et les lignes SET (déjà appliquées)
            first_word = stmt.lstrip("- \n").split()[0].upper() if stmt.lstrip("- \n").split() else ""
            if first_word in ("--", "SET"):
                continue
            try:
                conn.execute(text(stmt))
                conn.commit()
            except Exception as exc:
                conn.rollback()
                msg = str(exc).lower()
                # Ignorer : doublon de contrainte, index déjà existant
                if any(k in msg for k in ("already exists", "duplicate", "exist")):
                    continue
                logger.warning("schema.sql — instruction ignorée (%s): %.120s", type(exc).__name__, stmt)

    logger.info("schema.sql appliqué avec succès (%d instructions)", len(statements))


def init_db() -> None:
    # 1. SQLAlchemy crée les tables définies dans models.py
    Base.metadata.create_all(bind=engine)
    # 2. Le schéma SQL complet comble les tables/colonnes absentes des modèles
    if not _is_sqlite:
        _run_schema_sql()
