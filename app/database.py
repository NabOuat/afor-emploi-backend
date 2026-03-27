from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from app.config import settings
from app.models import Base

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

def init_db():
    Base.metadata.create_all(bind=engine)
