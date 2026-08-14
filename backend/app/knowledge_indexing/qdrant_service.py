"""
Qdrant Service — Phase 4, Knowledge Indexing.

Responsible ONLY for Qdrant operations:
- Connecting to Qdrant
- Ensuring the collection exists
- Upserting vectors with their metadata payload

Does NOT implement search/retrieval — that belongs to Phase 5.
"""

import logging
import os
import uuid
from typing import Dict, Any, List, Optional

from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant_models
from qdrant_client.http.exceptions import UnexpectedResponse

# Load environment variables from backend/.env
# The path is resolved relative to this file's location so it works
# regardless of the working directory the caller uses.
_env_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env")
load_dotenv(dotenv_path=os.path.abspath(_env_path))

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration — loaded exclusively from environment variables.
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
# Lazy singleton client
# ---------------------------------------------------------------------------

_client: Optional[QdrantClient] = None


def _get_client() -> QdrantClient:
    """
    Return the shared QdrantClient.

    Reads QDRANT_URL and QDRANT_API_KEY from environment on first call.
    The API key may be empty for local/unauthenticated Qdrant instances.
    """
    global _client
    if _client is None:
        qdrant_url = _require_env("QDRANT_URL")
        api_key = os.getenv("QDRANT_API_KEY", "").strip() or None  # None = no auth

        logger.info("Connecting to Qdrant at %s", qdrant_url)
        try:
            _client = QdrantClient(url=qdrant_url, api_key=api_key)
            logger.info("Qdrant client created.")
        except Exception as exc:
            logger.error("Failed to create Qdrant client: %s", exc)
            raise RuntimeError("Could not connect to Qdrant.") from exc
    return _client


def _get_collection_name() -> str:
    """Return the Qdrant collection name from the environment."""
    return _require_env("QDRANT_COLLECTION_NAME")


# ---------------------------------------------------------------------------
# Collection management
# ---------------------------------------------------------------------------

def ensure_collection_exists(vector_size: int) -> None:
    """
    Create the Qdrant collection if it does not already exist.

    Parameters
    ----------
    vector_size : int
        The dimension of the embedding vectors (e.g. 384 for bge-small-en).
        Passed in by the indexer so this module never hard-codes it.

    Raises
    ------
    RuntimeError
        If the collection cannot be created.
    """
    client = _get_client()
    collection_name = _get_collection_name()

    try:
        existing = [c.name for c in client.get_collections().collections]
        if collection_name in existing:
            logger.info("Qdrant collection '%s' already exists.", collection_name)
            return

        logger.info(
            "Creating Qdrant collection '%s' (vector_size=%d, distance=Cosine).",
            collection_name,
            vector_size,
        )
        client.create_collection(
            collection_name=collection_name,
            vectors_config=qdrant_models.VectorParams(
                size=vector_size,
                distance=qdrant_models.Distance.COSINE,
            ),
        )
        logger.info("Collection '%s' created successfully.", collection_name)

    except Exception as exc:
        logger.error(
            "Failed to ensure Qdrant collection '%s' exists: %s",
            collection_name,
            exc,
        )
        raise RuntimeError(
            f"Could not ensure Qdrant collection '{collection_name}' exists."
        ) from exc


# ---------------------------------------------------------------------------
# Point ID helpers
# ---------------------------------------------------------------------------

# Stable namespace UUID for deterministic point IDs.
# Using UUID5(namespace, chunk_id) means the same chunk_id always maps
# to the same Qdrant point UUID, making re-indexing idempotent.
_POINT_ID_NAMESPACE = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")


def chunk_id_to_point_id(chunk_id: str) -> str:
    """
    Convert a chunk_id string to a deterministic UUID string.

    The same chunk_id always produces the same UUID, so upserting an
    already-indexed chunk replaces the existing point rather than
    creating a duplicate.
    """
    return str(uuid.uuid5(_POINT_ID_NAMESPACE, chunk_id))


# ---------------------------------------------------------------------------
# Vector upsert
# ---------------------------------------------------------------------------

def upsert_vector(
    chunk_id: str,
    vector: List[float],
    payload: Dict[str, Any],
) -> str:
    """
    Upsert a vector into the Qdrant collection.

    Uses chunk_id-derived UUID as the point ID so the operation is
    idempotent — re-indexing the same chunk overwrites the existing point.

    Parameters
    ----------
    chunk_id : str
        Unique chunk identifier. Used to derive the deterministic point ID
        and also stored in the payload for cross-system lookup.
    vector : List[float]
        The embedding vector produced by embedding_service.
    payload : Dict[str, Any]
        Metadata to store alongside the vector.
        Should include: chunk_id, sku, category, manufacturer,
        filename, page_number.

    Returns
    -------
    str
        The Qdrant point UUID (deterministic, derived from chunk_id).

    Raises
    ------
    ValueError
        If vector is empty.
    RuntimeError
        If the Qdrant upsert fails.
    """
    if not vector:
        raise ValueError("Cannot upsert an empty vector into Qdrant.")

    client = _get_client()
    collection_name = _get_collection_name()
    point_id = chunk_id_to_point_id(chunk_id)

    # Always include chunk_id in the payload for cross-system linking.
    full_payload = {"chunk_id": chunk_id, **payload}

    try:
        client.upsert(
            collection_name=collection_name,
            points=[
                qdrant_models.PointStruct(
                    id=point_id,
                    vector=vector,
                    payload=full_payload,
                )
            ],
        )
        logger.debug(
            "Upserted vector for chunk_id='%s' as point_id='%s' in '%s'.",
            chunk_id,
            point_id,
            collection_name,
        )
    except Exception as exc:
        logger.error(
            "Qdrant upsert failed for chunk_id='%s': %s",
            chunk_id,
            exc,
        )
        raise RuntimeError(
            f"Failed to upsert vector for chunk_id='{chunk_id}' into Qdrant."
        ) from exc

    return point_id


# ---------------------------------------------------------------------------
# Retrieval helper for testing (NOT for Phase 5 — used only in tests to
# verify that a point was successfully stored)
# ---------------------------------------------------------------------------

def get_point_by_chunk_id(chunk_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch a Qdrant point by its chunk_id.

    This is provided solely for test/verification purposes.
    Phase 5 (Retrieval Service) will implement semantic search separately.

    Returns the point payload dict or None if not found.
    """
    client = _get_client()
    collection_name = _get_collection_name()
    point_id = chunk_id_to_point_id(chunk_id)

    try:
        results = client.retrieve(
            collection_name=collection_name,
            ids=[point_id],
            with_payload=True,
        )
        if results:
            return results[0].payload
        return None
    except Exception as exc:
        logger.warning(
            "Could not retrieve point for chunk_id='%s': %s",
            chunk_id,
            exc,
        )
        return None
