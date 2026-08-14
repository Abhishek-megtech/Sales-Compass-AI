"""
Integration tests — qdrant_service.py

Tests require a live Qdrant connection (QDRANT_URL must be set in .env).
Skipped automatically if the env var is missing.

Tests:
1. Qdrant client can connect
2. Collection can be created/verified
3. A vector can be upserted
4. The upserted point has the correct chunk_id in its payload
5. Re-upserting the same chunk_id is idempotent (no duplicates)
6. chunk_id_to_point_id is deterministic
7. Upsert with empty vector raises ValueError
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

# Skip all tests in this module if QDRANT_URL is not configured
pytestmark = pytest.mark.skipif(
    not os.getenv("QDRANT_URL", "").strip(),
    reason="QDRANT_URL not set — skipping Qdrant integration tests.",
)

from app.knowledge_indexing.qdrant_service import (
    ensure_collection_exists,
    upsert_vector,
    get_point_by_chunk_id,
    chunk_id_to_point_id,
)
from app.knowledge_indexing.embedding_service import (
    generate_embedding,
    get_embedding_dimension,
)


@pytest.fixture(scope="module")
def vector_size():
    return get_embedding_dimension()


@pytest.fixture(scope="module")
def sample_vector(vector_size):
    return generate_embedding("Test vector for Qdrant integration test.")


@pytest.fixture(scope="module")
def unique_chunk_id():
    """A unique chunk_id for this test run, to avoid cross-test pollution."""
    return f"qdrant-test-{uuid.uuid4().hex}"


class TestQdrantConnection:
    def test_collection_can_be_ensured(self, vector_size):
        """Should not raise — creates collection if absent."""
        ensure_collection_exists(vector_size=vector_size)

    def test_collection_idempotent(self, vector_size):
        """Calling ensure_collection_exists twice should not raise."""
        ensure_collection_exists(vector_size=vector_size)
        ensure_collection_exists(vector_size=vector_size)


class TestQdrantUpsert:
    def test_upsert_returns_point_id(self, unique_chunk_id, sample_vector, vector_size):
        ensure_collection_exists(vector_size=vector_size)
        payload = {
            "sku": "TEST-SKU",
            "category": "Test Category",
            "manufacturer": "Test Manufacturer",
            "filename": "test.pdf",
            "page_number": 1,
        }
        point_id = upsert_vector(
            chunk_id=unique_chunk_id,
            vector=sample_vector,
            payload=payload,
        )
        assert isinstance(point_id, str)
        assert len(point_id) > 0

    def test_upserted_payload_has_chunk_id(self, unique_chunk_id, sample_vector, vector_size):
        ensure_collection_exists(vector_size=vector_size)
        payload = {"sku": "TEST-SKU", "category": "Test", "manufacturer": "X",
                   "filename": "test.pdf", "page_number": 1}
        upsert_vector(chunk_id=unique_chunk_id, vector=sample_vector, payload=payload)

        stored = get_point_by_chunk_id(unique_chunk_id)
        assert stored is not None, "Point should exist in Qdrant after upsert."
        assert stored.get("chunk_id") == unique_chunk_id

    def test_upsert_idempotent_no_duplicates(self, unique_chunk_id, sample_vector, vector_size):
        """Re-upserting the same chunk_id should overwrite, not duplicate."""
        ensure_collection_exists(vector_size=vector_size)
        payload = {"sku": "UPDATED-SKU", "category": "Updated", "manufacturer": "Y",
                   "filename": "updated.pdf", "page_number": 2}

        # Upsert twice
        upsert_vector(chunk_id=unique_chunk_id, vector=sample_vector, payload=payload)
        upsert_vector(chunk_id=unique_chunk_id, vector=sample_vector, payload=payload)

        # Should be retrievable and have the latest payload
        stored = get_point_by_chunk_id(unique_chunk_id)
        assert stored is not None
        assert stored.get("sku") == "UPDATED-SKU"

    def test_empty_vector_raises(self, unique_chunk_id):
        with pytest.raises(ValueError, match="empty vector"):
            upsert_vector(
                chunk_id=unique_chunk_id,
                vector=[],
                payload={},
            )


class TestPointIdDeterminism:
    def test_same_chunk_id_gives_same_point_id(self):
        pid1 = chunk_id_to_point_id("stable-chunk-id")
        pid2 = chunk_id_to_point_id("stable-chunk-id")
        assert pid1 == pid2

    def test_different_chunk_ids_give_different_point_ids(self):
        pid1 = chunk_id_to_point_id("chunk-aaa")
        pid2 = chunk_id_to_point_id("chunk-bbb")
        assert pid1 != pid2

    def test_point_id_is_valid_uuid_format(self):
        pid = chunk_id_to_point_id("some-chunk-id")
        # Should parse as a valid UUID without raising
        parsed = uuid.UUID(pid)
        assert str(parsed) == pid
