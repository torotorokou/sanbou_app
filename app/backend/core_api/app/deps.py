"""
Dependency injection and utilities for FastAPI.
"""
from typing import Generator
from sqlalchemy.orm import Session
from app.infra.db import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency for database session.
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
