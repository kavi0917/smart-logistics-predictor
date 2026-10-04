import logging
import time

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import get_settings

logger = logging.getLogger("logistics.db")
settings = get_settings()

def _normalize_url(url: str) -> str:
    """Force the psycopg2 driver for plain postgresql:// URLs (SQLAlchemy 2.1 would otherwise pick psycopg3)."""
    for prefix in ("postgresql://", "postgres://"):
        if url.startswith(prefix):
            return "postgresql+psycopg2://" + url[len(prefix):]
    return url


DATABASE_URL = _normalize_url(settings.database_url)
_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args=_connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def get_db():
    """FastAPI dependency: one DB session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db(retries: int = 20, delay: float = 2.0):
    """Create tables. Retries so the API can start while PostgreSQL is still booting."""
    from app import models  # noqa: F401  (registers tables)

    for attempt in range(1, retries + 1):
        try:
            Base.metadata.create_all(bind=engine)
            logger.info("Database tables ready")
            return
        except Exception as exc:  # pragma: no cover - only hit while DB is starting
            logger.warning("Database not ready (attempt %s/%s): %s", attempt, retries, exc.__class__.__name__)
            time.sleep(delay)
    raise RuntimeError("Could not connect to the database")
