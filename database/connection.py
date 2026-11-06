"""
Database Connection Management
Provides SQLAlchemy session factories, connection pools, and SQLite/PostgreSQL compatibility.
"""

import os
from contextlib import contextmanager
from pathlib import Path
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.engine import Engine

from config.settings import DATABASE_URL, DEFAULT_DB_PATH, BASE_DIR

Base = declarative_base()

def get_engine(db_url: str = None) -> Engine:
    """Create and return an engine with foreign key enforcement."""
    url = db_url or DATABASE_URL
    is_sqlite = url.startswith("sqlite")
    
    if is_sqlite:
        # Extract path if relative or ensure dir exists
        DEFAULT_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        engine = create_engine(
            url,
            connect_args={"check_same_thread": False},
            echo=False
        )
        
        # Enforce SQLite foreign keys
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.close()
    else:
        # Standard PostgreSQL / MySQL engine configuration
        engine = create_engine(
            url,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            echo=False
        )
    return engine

# Global engine and sessionmaker
engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@contextmanager
def get_db():
    """Context manager for transactional database sessions."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def init_db(schema_path: str = None, engine_override=None):
    """Initialize database tables using schema.sql and SQLAlchemy Base."""
    eng = engine_override or engine
    
    # Run SQL file if provided or default
    path = Path(schema_path) if schema_path else BASE_DIR / "database" / "schema.sql"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            sql_statements = f.read()
        
        # In SQLite, execute raw script
        with eng.connect() as conn:
            raw_conn = conn.connection
            cursor = raw_conn.cursor()
            cursor.executescript(sql_statements)
            conn.commit()
    else:
        # Fallback to SQLAlchemy metadata creation
        Base.metadata.create_all(bind=eng)

def reset_db(engine_override=None):
    """Drop and recreate all tables."""
    eng = engine_override or engine
    Base.metadata.drop_all(bind=eng)
    init_db(engine_override=eng)