"""
Embedding Service — Phase 4, Knowledge Indexing.

Responsible ONLY for generating embedding vectors from text.
Uses BAAI/bge-small-en via sentence-transformers.

No Qdrant, no PostgreSQL, no ingestion logic here.
"""

import logging
from typing import List

from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Model constant
# ---------------------------------------------------------------------------

MODEL_NAME = "BAAI/bge-small-en"

# Expected embedding dimension for BAAI/bge-small-en.
# Determined from the model card; used for validation only.
EXPECTED_EMBEDDING_DIM = 384

# ---------------------------------------------------------------------------
# Lazy singleton — model is loaded once on first use and reused.
# Loading a transformer model is expensive (~500ms); we never want to
# reload it for every chunk.
# ---------------------------------------------------------------------------

_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    """
    Return the shared SentenceTransformer model instance.

    Loads the model on first call. Subsequent calls return the cached
    instance without re-loading. Thread-safe for read-after-write because
    Python's GIL prevents simultaneous writes to the module-level variable
    in the single-threaded contexts this service runs in.
    """
    global _model
    if _model is None:
        logger.info("Loading embedding model: %s", MODEL_NAME)
        try:
            _model = SentenceTransformer(MODEL_NAME)
            logger.info(
                "Model %s loaded. Embedding dimension: %d",
                MODEL_NAME,
                _model.get_sentence_embedding_dimension(),
            )
        except Exception as exc:
            logger.error("Failed to load embedding model %s: %s", MODEL_NAME, exc)
            raise RuntimeError(
                f"Embedding model could not be loaded: {MODEL_NAME}"
            ) from exc
    return _model


def get_embedding_dimension() -> int:
    """
    Return the embedding dimension of the loaded model.

    This is used by the Qdrant service to configure the collection
    vector size correctly, without hard-coding a magic number.
    """
    return _get_model().get_sentence_embedding_dimension()


def generate_embedding(text: str) -> List[float]:
    """
    Generate an embedding vector for the given text.

    Parameters
    ----------
    text : str
        Clean text from the Document Ingestion Service.
        Must be non-empty after stripping whitespace.

    Returns
    -------
    List[float]
        A 384-dimensional embedding vector (BAAI/bge-small-en output).

    Raises
    ------
    ValueError
        If text is empty or contains only whitespace.
    RuntimeError
        If the model fails to encode (propagated from sentence-transformers).
    """
    if not isinstance(text, str):
        raise ValueError(
            f"Expected text to be a str, got {type(text).__name__}"
        )

    stripped = text.strip()
    if not stripped:
        raise ValueError(
            "Cannot generate embedding for empty or whitespace-only text."
        )

    model = _get_model()

    try:
        # encode() returns a numpy ndarray; convert to plain Python list
        # so the result is JSON-serialisable and Qdrant-compatible.
        embedding = model.encode(stripped, convert_to_numpy=True)
        vector: List[float] = embedding.tolist()
    except Exception as exc:
        logger.error("Embedding generation failed for text (length=%d): %s", len(stripped), exc)
        raise RuntimeError("Failed to generate embedding vector.") from exc

    logger.debug(
        "Generated embedding for text (length=%d), vector dim=%d",
        len(stripped),
        len(vector),
    )

    return vector
