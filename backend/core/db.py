"""Shared database/environment helpers for backend modules."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

DEFAULT_DATABASE_URL = "postgresql+psycopg2://floatchat_user:1234@localhost:5432/floatchat"


def load_backend_env() -> None:
    """Load backend .env first, then fallback to process/global env."""
    backend_dir = Path(__file__).resolve().parents[1]
    load_dotenv(backend_dir / ".env")
    load_dotenv()


def normalize_database_url(url: str) -> str:
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg2://", 1)
    return url


def get_database_url(default: str = DEFAULT_DATABASE_URL) -> str:
    load_backend_env()
    return normalize_database_url(os.getenv("DATABASE_URL", default))


def build_engine(database_url: str | None = None) -> Engine:
    return create_engine(database_url or get_database_url())


def build_session_local(engine: Engine | None = None):
    return sessionmaker(autocommit=False, autoflush=False, bind=engine or build_engine())
