import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker

# Load .env from the project root when running outside Docker
load_dotenv(Path(__file__).resolve().parents[3] / ".env")


def get_database_url() -> URL:
    """Built from POSTGRES_* variables. POSTGRES_HOST defaults to localhost (scripts on your machine);
    docker-compose sets POSTGRES_HOST=db for the backend container.
    URL.create() escapes special characters (@, :, /, #) in the password safely."""
    return URL.create(
        drivername="postgresql+psycopg2",
        username=os.getenv("POSTGRES_USER", "supportiq"),
        password=os.getenv("POSTGRES_PASSWORD", "change_me"),
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        database=os.getenv("POSTGRES_DB", "supportiq"),
        # cloud databases (Neon, Supabase) require SSL: set POSTGRES_SSLMODE=require
        query={"sslmode": os.environ["POSTGRES_SSLMODE"]} if os.getenv("POSTGRES_SSLMODE") else {},
    )


engine = create_engine(get_database_url(), pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False)


def get_db():
    """FastAPI dependency (used from Phase 5)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
