"""
Indexer — Phase 4, Knowledge Indexing.

Orchestration layer that wires together:
  embedding_service → qdrant_service → postgres_service

Flow per chunk:
  chunk → validate → generate embedding → upsert vector (Qdrant)
       → upsert metadata (PostgreSQL) → return IndexingResult

chunk_id flows unchanged through all three steps and is stored
in both Qdrant payload and PostgreSQL record, making the two
systems cross-queryable.

This module is the public API that Phase 3 (Document Ingestion)
and tests call. The individual *_service modules are not called
directly from outside this package.
"""

import logging
from typing import List

from .embedding_service import generate_embedding, get_embedding_dimension
from .models import ChunkInput, ChunkMetadata, IndexingResult
from .postgres_service import ensure_table_exists, upsert_chunk_metadata
from .qdrant_service import ensure_collection_exists, upsert_vector

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# One-time setup
# ---------------------------------------------------------------------------

_initialized: bool = False


def _ensure_infrastructure() -> None:
    """
    Ensure Qdrant collection and PostgreSQL table exist.

    Called lazily on the first index operation. Safe to call repeatedly —
    both operations are idempotent.
    """
    global _initialized
    if _initialized:
        return

    vector_size = get_embedding_dimension()
    ensure_collection_exists(vector_size=vector_size)
    ensure_table_exists()
    _initialized = True
    logger.info("Indexing infrastructure ready (vector_size=%d).", vector_size)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def _validate_chunk(chunk: ChunkInput) -> None:
    """
    Validate a ChunkInput before indexing.

    Raises
    ------
    ValueError
        If chunk_id or text is missing/empty.
    TypeError
        If chunk is not a ChunkInput instance.
    """
    if not isinstance(chunk, ChunkInput):
        raise TypeError(
            f"Expected ChunkInput, got {type(chunk).__name__}."
        )
    if not chunk.chunk_id or not str(chunk.chunk_id).strip():
        raise ValueError("chunk_id must be a non-empty string.")
    if not chunk.text or not str(chunk.text).strip():
        raise ValueError(
            f"chunk_id='{chunk.chunk_id}': text must be a non-empty string."
        )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def index_chunk(chunk: ChunkInput) -> IndexingResult:
    """
    Index a single chunk: embed → store in Qdrant → store in PostgreSQL.

    Parameters
    ----------
    chunk : ChunkInput
        A clean text chunk with metadata, produced by the Document
        Ingestion Service (Phase 3).

    Returns
    -------
    IndexingResult
        success=True  if both Qdrant and PostgreSQL writes succeeded.
        success=False with an error message if any step failed.
        The qdrant_point_id is returned on success for traceability.
    """
    # --- 1. Validate ---
    try:
        _validate_chunk(chunk)
    except (ValueError, TypeError) as exc:
        logger.warning("Chunk validation failed: %s", exc)
        return IndexingResult(
            chunk_id=getattr(chunk, "chunk_id", "<unknown>"),
            success=False,
            error=str(exc),
        )

    chunk_id = chunk.chunk_id.strip()
    logger.info("Indexing chunk_id='%s'.", chunk_id)

    # --- 2. Ensure infrastructure (idempotent) ---
    try:
        _ensure_infrastructure()
    except Exception as exc:
        logger.error("Infrastructure setup failed: %s", exc)
        return IndexingResult(chunk_id=chunk_id, success=False, error=str(exc))

    # --- 3. Generate embedding ---
    try:
        vector = generate_embedding(chunk.text)
    except Exception as exc:
        logger.error(
            "Embedding failed for chunk_id='%s': %s", chunk_id, exc
        )
        return IndexingResult(chunk_id=chunk_id, success=False, error=str(exc))

    # --- 4. Build Qdrant payload from chunk metadata ---
    meta = chunk.metadata if isinstance(chunk.metadata, ChunkMetadata) else ChunkMetadata()
    payload = meta.to_dict()

    # --- 5. Upsert vector into Qdrant ---
    try:
        point_id = upsert_vector(
            chunk_id=chunk_id,
            vector=vector,
            payload=payload,
        )
    except Exception as exc:
        logger.error(
            "Qdrant upsert failed for chunk_id='%s': %s", chunk_id, exc
        )
        return IndexingResult(chunk_id=chunk_id, success=False, error=str(exc))

    # --- 6. Upsert metadata into PostgreSQL ---
    try:
        upsert_chunk_metadata(
            chunk_id=chunk_id,
            sku=meta.sku,
            category=meta.category,
            manufacturer=meta.manufacturer,
            filename=meta.filename,
            page_number=meta.page_number,
        )
    except Exception as exc:
        logger.error(
            "PostgreSQL upsert failed for chunk_id='%s': %s", chunk_id, exc
        )
        return IndexingResult(chunk_id=chunk_id, success=False, error=str(exc))

    logger.info(
        "Successfully indexed chunk_id='%s' → qdrant_point_id='%s'.",
        chunk_id,
        point_id,
    )
    return IndexingResult(
        chunk_id=chunk_id,
        success=True,
        qdrant_point_id=point_id,
    )


def index_chunks(chunks: List[ChunkInput]) -> List[IndexingResult]:
    """
    Index a list of chunks, processing each sequentially.

    Parameters
    ----------
    chunks : List[ChunkInput]
        List of clean text chunks from the Document Ingestion Service.

    Returns
    -------
    List[IndexingResult]
        One result per input chunk, in the same order.
        Individual failures do NOT abort the remaining chunks.
    """
    if not chunks:
        logger.warning("index_chunks called with an empty list.")
        return []

    results: List[IndexingResult] = []
    total = len(chunks)
    logger.info("Indexing batch of %d chunk(s).", total)

    for i, chunk in enumerate(chunks, start=1):
        result = index_chunk(chunk)
        results.append(result)
        status = "OK" if result.success else f"FAILED: {result.error}"
        logger.info(
            "[%d/%d] chunk_id='%s' → %s",
            i,
            total,
            getattr(chunk, "chunk_id", "<unknown>"),
            status,
        )

    successful = sum(1 for r in results if r.success)
    logger.info(
        "Batch complete: %d/%d chunks indexed successfully.",
        successful,
        total,
    )
    return results
