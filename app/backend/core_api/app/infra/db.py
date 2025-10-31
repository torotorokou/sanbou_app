"""
Database infrastructure: SQLAlchemy engine and session management.
Supports schema-based multi-tenancy with minimal privileges.
Optimized with connection pooling for performance.
"""
from typing import Generator
from functools import lru_cache
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.pool import NullPool
import os

# Environment variables
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/db")

# Convert postgresql:// to postgresql+psycopg:// for SQLAlchemy 2.x + psycopg3
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    """
    Get or create a shared SQLAlchemy engine with optimized connection pooling.
    Uses lru_cache to ensure only one engine instance is created.
    
    Pool settings:
    - pool_size: Number of connections to maintain
    - max_overflow: Additional connections beyond pool_size
    - pool_pre_ping: Verify connections before using (prevents stale connections)
    - pool_recycle: Recycle connections after N seconds (prevents long-lived issues)
    """
    return create_engine(
        DATABASE_URL,
        pool_size=8,
        max_overflow=8,
        pool_pre_ping=True,
        pool_recycle=1800,  # 30 minutes
        echo=os.getenv("SQL_ECHO", "false").lower() == "true",
        future=True,
    )


# Create engine with connection pooling
# For worker (long-running), consider NullPool to avoid stale connections
engine = get_engine()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for FastAPI endpoints to get a database session.
    Automatically commits on success, rolls back on error.
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

