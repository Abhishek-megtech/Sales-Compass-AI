"""
Integration tests — indexer.py (full end-to-end Phase 4)

Tests the complete pipeline: ChunkInput → embed → Qdrant → PostgreSQL.

Requires both QDRANT_URL and DATABASE_URL to be set.
Skipped automatically if either is missing.

Tests:
1. index_chunk succeeds for a valid chunk
2. Result has success=True and a qdrant_point_id
3. chunk_id appears in Qdrant payload
4. chunk_id appears in PostgreSQL record
5. chunk_id is identical in both systems (the link)
6. Re-indexing same chunk_id is idempotent
7. Invalid chunk (empty text) returns success=False
8. Invalid chunk (no chunk_id) returns success=False
9. index_chunks processes a batch correctly
10. Batch with one bad chunk does not abort the rest
"""

import os
import uuid
import pytest

from dotenv import load_dotenv

load_dotenv(
    dotenv_path=os.path.join(
        os.path.dirname(__file__), "..", ".env"
    )
)

_qdrant_ok = bool(os.getenv("QDRANT_URL", "").strip())
_pg_ok = bool(os.getenv("DATABASE_URL", "").strip())

pytestmark = pytest.mark.skipif(
    not (_qdrant_ok and _pg_ok),
    reason="QDRANT_URL or DATABASE_URL not set — skipping indexer integration tests.",
)

from app.knowledge_indexing.indexer import index_chunk, index_chunks
from app.knowledge_indexing.models import ChunkInput, ChunkMetadata
from app.knowledge_indexing.qdrant_service import get_point_by_chunk_id
from app.knowledge_indexing.postgres_service import get_chunk_by_id
from tests.fixtures import SAMPLE_CHUNK, SAMPLE_CHUNK_2, make_chunk


@pytest.fixture
def unique_chunk():
    """A fresh chunk with a unique chunk_id for each test."""
    return make_chunk(
        chunk_id=f"indexer-test-{uuid.uuid4().hex}",
        text="BD 43/40 is a walk-behind scrubber-dryer with a 43-litre solution tank.",
    )


class TestIndexChunkSuccess:
    def test_index_chunk_returns_success(self, unique_chunk):
        result = index_chunk(unique_chunk)
        assert result.success is True, f"Expected success, got error: {result.error}"

    def test_result_has_chunk_id(self, unique_chunk):
        result = index_chunk(unique_chunk)
        assert result.chunk_id == unique_chunk.chunk_id

    def test_result_has_qdrant_point_id(self, unique_chunk):
        result = index_chunk(unique_chunk)
        assert result.success is True
        assert result.qdrant_point_id is not None
        assert isinstance(result.qdrant_point_id, str)
        assert len(result.qdrant_point_id) > 0

    def test_result_has_no_error_on_success(self, unique_chunk):
        result = index_chunk(unique_chunk)
        assert result.success is True
        assert result.error is None


class TestChunkIdLinkage:
    """
    CRITICAL: chunk_id must be present in BOTH Qdrant and PostgreSQL,
    using the exact same value, so the two stores can be cross-queried.
    """

    def test_chunk_id_in_qdrant_payload(self, unique_chunk):
        result = index_chunk(unique_chunk)
        assert result.success is True

        qdrant_payload = get_point_by_chunk_id(unique_chunk.chunk_id)
        assert qdrant_payload is not None, "Point not found in Qdrant."
        assert qdrant_payload.get("chunk_id") == unique_chunk.chunk_id

    def test_chunk_id_in_postgres(self, unique_chunk):
        result = index_chunk(unique_chunk)
        assert result.success is True

        pg_record = get_chunk_by_id(unique_chunk.chunk_id)
        assert pg_record is not None, "Record not found in PostgreSQL."
        assert pg_record["chunk_id"] == unique_chunk.chunk_id

    def test_chunk_id_identical_in_both_systems(self, unique_chunk):
        """chunk_id in Qdrant payload == chunk_id in PG record == input chunk_id"""
        result = index_chunk(unique_chunk)
        assert result.success is True

        qdrant_payload = get_point_by_chunk_id(unique_chunk.chunk_id)
        pg_record = get_chunk_by_id(unique_chunk.chunk_id)

        assert qdrant_payload is not None
        assert pg_record is not None

        qdrant_chunk_id = qdrant_payload.get("chunk_id")
        pg_chunk_id = pg_record["chunk_id"]

        assert qdrant_chunk_id == pg_chunk_id == unique_chunk.chunk_id, (
            f"chunk_id mismatch: qdrant='{qdrant_chunk_id}', "
            f"pg='{pg_chunk_id}', input='{unique_chunk.chunk_id}'"
        )

    def test_metadata_stored_in_postgres(self, unique_chunk):
        result = index_chunk(unique_chunk)
        assert result.success is True

        pg_record = get_chunk_by_id(unique_chunk.chunk_id)
        assert pg_record is not None
        assert pg_record["sku"] == unique_chunk.metadata.sku
        assert pg_record["category"] == unique_chunk.metadata.category
        assert pg_record["manufacturer"] == unique_chunk.metadata.manufacturer
        assert pg_record["filename"] == unique_chunk.metadata.filename
        assert pg_record["page_number"] == unique_chunk.metadata.page_number

    def test_metadata_in_qdrant_payload(self, unique_chunk):
        result = index_chunk(unique_chunk)
        assert result.success is True

        payload = get_point_by_chunk_id(unique_chunk.chunk_id)
        assert payload is not None
        assert payload.get("sku") == unique_chunk.metadata.sku
        assert payload.get("filename") == unique_chunk.metadata.filename


class TestIdempotency:
    def test_reindex_same_chunk_returns_success(self, unique_chunk):
        result1 = index_chunk(unique_chunk)
        result2 = index_chunk(unique_chunk)
        assert result1.success is True
        assert result2.success is True

    def test_reindex_same_point_id(self, unique_chunk):
        """Same chunk_id must always produce the same Qdrant point ID."""
        result1 = index_chunk(unique_chunk)
        result2 = index_chunk(unique_chunk)
        assert result1.qdrant_point_id == result2.qdrant_point_id

    def test_reindex_no_pg_duplicates(self, unique_chunk):
        """Re-indexing must not create duplicate PostgreSQL records."""
        from sqlalchemy import text
        from app.knowledge_indexing.postgres_service import _get_engine

        index_chunk(unique_chunk)
        index_chunk(unique_chunk)
        index_chunk(unique_chunk)

        engine = _get_engine()
        with engine.connect() as conn:
            count = conn.execute(
                text("SELECT COUNT(*) FROM document_chunks WHERE chunk_id = :cid"),
                {"cid": unique_chunk.chunk_id},
            ).scalar()
        assert count == 1, f"Expected 1 PG record, found {count} — duplicates!"


class TestInvalidChunks:
    def test_empty_text_returns_failure(self):
        bad_chunk = ChunkInput(
            chunk_id="bad-empty-text",
            text="",
            metadata=ChunkMetadata(sku="X"),
        )
        result = index_chunk(bad_chunk)
        assert result.success is False
        assert result.error is not None

    def test_whitespace_text_returns_failure(self):
        bad_chunk = ChunkInput(
            chunk_id="bad-whitespace",
            text="    ",
            metadata=ChunkMetadata(sku="X"),
        )
        result = index_chunk(bad_chunk)
        assert result.success is False

    def test_empty_chunk_id_returns_failure(self):
        bad_chunk = ChunkInput(
            chunk_id="",
            text="Some valid text.",
            metadata=ChunkMetadata(sku="X"),
        )
        result = index_chunk(bad_chunk)
        assert result.success is False

    def test_non_chunk_input_returns_failure(self):
        result = index_chunk({"chunk_id": "x", "text": "y"})  # type: ignore
        assert result.success is False


class TestBatchIndexing:
    def test_index_chunks_processes_all(self):
        chunks = [
            make_chunk(
                chunk_id=f"batch-test-{uuid.uuid4().hex}",
                text=f"Batch test chunk number {i}.",
            )
            for i in range(3)
        ]
        results = index_chunks(chunks)
        assert len(results) == 3
        assert all(r.success for r in results)

    def test_index_chunks_empty_list(self):
        results = index_chunks([])
        assert results == []

    def test_bad_chunk_does_not_abort_batch(self):
        bad = ChunkInput(chunk_id="batch-bad", text="", metadata=ChunkMetadata())
        good = make_chunk(
            chunk_id=f"batch-good-{uuid.uuid4().hex}",
            text="This is a valid chunk in the batch.",
        )
        results = index_chunks([bad, good])
        assert len(results) == 2
        assert results[0].success is False  # bad chunk
        assert results[1].success is True   # good chunk
