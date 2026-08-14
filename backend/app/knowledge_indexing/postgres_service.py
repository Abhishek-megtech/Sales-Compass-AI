"""
PostgreSQL Service — Phase 4, Knowledge Indexing.

Responsible ONLY for PostgreSQL metadata storage:
- Connecting to PostgreSQL via DATABASE_URL
- Creating the document_chunks table if it does not exist
- Upserting chunk metadata (idempotent)

Does NOT store embedding vectors — vectors live in Qdrant.
chunk_id is the shared key that links PostgreSQL records to Qdrant points.
"""

import logging
import os
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from dotenv import load_dotenv
from sqlalchemy import (
    create_engine,
    text,
    MetaData,
    Table,
    Column,
    Integer,
    String,
    DateTime,
    UniqueConstraint,
)
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

# Load environment variables from backend/.env
_env_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env")
load_dotenv(dotenv_path=os.path.abspath(_env_path))

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Schema definition
# ---------------------------------------------------------------------------

_metadata = MetaData()

document_chunks_table = Table(
    "document_chunks",
    _metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("chunk_id", String(255), nullable=False),
    Column("sku", String(255), nullable=True),
    Column("category", String(255), nullable=True),
    Column("manufacturer", String(255), nullable=True),
    Column("filename", String(500), nullable=True),
    Column("page_number", Integer, nullable=True),
    Column(
        "created_at",
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    ),
    Column(
        "updated_at",
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    ),
    UniqueConstraint("chunk_id", name="uq_document_chunks_chunk_id"),
)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

def _require_env(name: str) -> str:
    """Return the value of an env var, raising if absent or empty."""
    value = os.getenv(name, "").strip()
    if not value:
        raise EnvironmentError(
            f"Required environment variable '{name}' is not set. "
            "Check backend/.env."
        )
    return value


# ---------------------------------------------------------------------------
# Lazy singleton engine
# ---------------------------------------------------------------------------

_engine: Optional[Engine] = None


def _get_engine() -> Engine:
    """
    Return the shared SQLAlchemy Engine.

    Reads DATABASE_URL from environment on first call.
    """
    global _engine
    if _engine is None:
        database_url = _require_env("DATABASE_URL")
        logger.info("Creating SQLAlchemy engine.")
        try:
            # pool_pre_ping=True ensures stale connections are recycled
            _engine = create_engine(database_url, pool_pre_ping=True)
            logger.info("SQLAlchemy engine created.")
        except Exception as exc:
            logger.error("Failed to create SQLAlchemy engine: %s", exc)
            raise RuntimeError(
                "Could not create database engine. Check DATABASE_URL."
            ) from exc
    return _engine


# ---------------------------------------------------------------------------
# Table management
# ---------------------------------------------------------------------------

def ensure_table_exists() -> None:
    """
    Create the document_chunks table if it does not already exist.

    Safe to call on every application startup — uses CREATE TABLE IF NOT EXISTS
    semantics via SQLAlchemy's checkfirst=True.

    Raises
    ------
    RuntimeError
        If the table cannot be created.
    """
    engine = _get_engine()
    try:
        _metadata.create_all(engine, checkfirst=True)
        logger.info("Table 'document_chunks' is ready.")
    except SQLAlchemyError as exc:
        logger.error("Failed to create table 'document_chunks': %s", exc)
        raise RuntimeError("Could not ensure 'document_chunks' table exists.") from exc


# ---------------------------------------------------------------------------
# Upsert
# ---------------------------------------------------------------------------

def upsert_chunk_metadata(
    chunk_id: str,
    sku: Optional[str],
    category: Optional[str],
    manufacturer: Optional[str],
    filename: Optional[str],
    page_number: Optional[int],
) -> None:
    """
    Insert or update a chunk metadata record in PostgreSQL.

    Idempotent: if a record with the same chunk_id already exists,
    all metadata columns and updated_at are updated in place.

    chunk_id is the shared key linking this record to its Qdrant vector.

    Parameters
    ----------
    chunk_id : str
        Unique chunk identifier (must match the value stored in Qdrant payload).
    sku, category, manufacturer, filename, page_number : optional
        Metadata fields from the Document Ingestion Service.

    Raises
    ------
    ValueError
        If chunk_id is empty.
    RuntimeError
        If the database operation fails.
    """
    if not chunk_id or not chunk_id.strip():
        raise ValueError("chunk_id must be a non-empty string.")

    engine = _get_engine()
    now = datetime.now(timezone.utc)

    # PostgreSQL upsert using INSERT ... ON CONFLICT DO UPDATE
    upsert_sql = text(
        """
        INSERT INTO document_chunks
            (chunk_id, sku, category, manufacturer, filename, page_number,
             created_at, updated_at)
        VALUES
            (:chunk_id, :sku, :category, :manufacturer, :filename,
             :page_number, :created_at, :updated_at)
        ON CONFLICT (chunk_id)
        DO UPDATE SET
            sku          = EXCLUDED.sku,
            category     = EXCLUDED.category,
            manufacturer = EXCLUDED.manufacturer,
            filename     = EXCLUDED.filename,
            page_number  = EXCLUDED.page_number,
            updated_at   = EXCLUDED.updated_at
        """
    )

    params = {
        "chunk_id": chunk_id.strip(),
        "sku": sku,
        "category": category,
        "manufacturer": manufacturer,
        "filename": filename,
        "page_number": page_number,
        "created_at": now,
        "updated_at": now,
    }

    try:
        with engine.begin() as conn:
            conn.execute(upsert_sql, params)
        logger.debug("Upserted metadata for chunk_id='%s'.", chunk_id)
    except SQLAlchemyError as exc:
        logger.error(
            "PostgreSQL upsert failed for chunk_id='%s': %s",
            chunk_id,
            exc,
        )
        raise RuntimeError(
            f"Failed to upsert metadata for chunk_id='{chunk_id}' in PostgreSQL."
        ) from exc


# ---------------------------------------------------------------------------
# Read helper — for testing/verification only
# ---------------------------------------------------------------------------

def get_chunk_by_id(chunk_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch a chunk metadata record by chunk_id.

    Returns a dict with all stored columns, or None if not found.
    Provided for test/verification use only.
    """
    engine = _get_engine()
    query = text(
        """
        SELECT chunk_id, sku, category, manufacturer, filename,
               page_number, created_at, updated_at
        FROM document_chunks
        WHERE chunk_id = :chunk_id
        """
    )
    try:
        with engine.connect() as conn:
            row = conn.execute(query, {"chunk_id": chunk_id}).mappings().first()
            if row:
                return dict(row)
            return None
    except SQLAlchemyError as exc:
        logger.warning(
            "Could not fetch chunk_id='%s' from PostgreSQL: %s",
            chunk_id,
            exc,
        )
        return None
