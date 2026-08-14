"""
Integration tests — postgres_service.py

Tests require a live PostgreSQL connection (DATABASE_URL must be set in .env).
Skipped automatically if the env var is missing.

Tests:
1. PostgreSQL engine can be created
2. document_chunks table can be created/verified (idempotent)
3. A metadata record can be inserted
4. Inserted record has the correct chunk_id
5. All documented metadata fields are stored correctly
6. Re-inserting the same chunk_id updates the record (upsert)
7. chunk_id uniqueness is enforced (only one record per chunk_id)
8. Empty chunk_id raises ValueError
9. Timestamps are present
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

pytestmark = pytest.mark.skipif(
    not os.getenv("DATABASE_URL", "").strip(),
    reason="DATABASE_URL not set — skipping PostgreSQL integration tests.",
)

from app.knowledge_indexing.postgres_service import (
    ensure_table_exists,
    upsert_chunk_metadata,
    get_chunk_by_id,
)


@pytest.fixture(scope="module")
def unique_chunk_id():
    return f"pg-test-{uuid.uuid4().hex}"


class TestPostgreSQLConnection:
    def test_table_can_be_ensured(self):
        """Should not raise — creates table if absent."""
        ensure_table_exists()

    def test_table_ensure_is_idempotent(self):
        """Calling twice should not raise."""
        ensure_table_exists()
        ensure_table_exists()


class TestPostgreSQLUpsert:
    def test_insert_returns_without_error(self, unique_chunk_id):
        ensure_table_exists()
        upsert_chunk_metadata(
            chunk_id=unique_chunk_id,
            sku="SKU-TEST-001",
            category="Test Category",
            manufacturer="Test Manufacturer",
            filename="test_document.pdf",
            page_number=1,
        )

    def test_inserted_record_is_retrievable(self, unique_chunk_id):
        ensure_table_exists()
        upsert_chunk_metadata(
            chunk_id=unique_chunk_id,
            sku="SKU-TEST-001",
            category="Test Category",
            manufacturer="Test Manufacturer",
            filename="test_document.pdf",
            page_number=1,
        )
        record = get_chunk_by_id(unique_chunk_id)
        assert record is not None, "Record should be retrievable after insert."
        assert record["chunk_id"] == unique_chunk_id

    def test_all_metadata_fields_stored(self, unique_chunk_id):
        ensure_table_exists()
        upsert_chunk_metadata(
            chunk_id=unique_chunk_id,
            sku="BD-4340",
            category="Floor Cleaning",
            manufacturer="Karcher",
            filename="BD 43-40.pdf",
            page_number=3,
        )
        record = get_chunk_by_id(unique_chunk_id)
        assert record is not None
        assert record["sku"] == "BD-4340"
        assert record["category"] == "Floor Cleaning"
        assert record["manufacturer"] == "Karcher"
        assert record["filename"] == "BD 43-40.pdf"
        assert record["page_number"] == 3

    def test_upsert_updates_existing_record(self, unique_chunk_id):
        """Re-inserting same chunk_id should update fields, not create duplicate."""
        ensure_table_exists()
        upsert_chunk_metadata(
            chunk_id=unique_chunk_id,
            sku="ORIGINAL-SKU",
            category="Original",
            manufacturer="Original Mfr",
            filename="original.pdf",
            page_number=1,
        )
        upsert_chunk_metadata(
            chunk_id=unique_chunk_id,
            sku="UPDATED-SKU",
            category="Updated",
            manufacturer="Updated Mfr",
            filename="updated.pdf",
            page_number=99,
        )
        record = get_chunk_by_id(unique_chunk_id)
        assert record is not None
        assert record["sku"] == "UPDATED-SKU"
        assert record["page_number"] == 99

    def test_upsert_no_duplicate_records(self, unique_chunk_id):
        """
        Upserting the same chunk_id multiple times should not create duplicates.
        We verify by checking the chunk_id is still unique (one record).
        """
        from sqlalchemy import text
        from app.knowledge_indexing.postgres_service import _get_engine

        ensure_table_exists()
        for _ in range(3):
            upsert_chunk_metadata(
                chunk_id=unique_chunk_id,
                sku="NO-DUP-SKU",
                category="Cat",
                manufacturer="Mfr",
                filename="file.pdf",
                page_number=1,
            )

        engine = _get_engine()
        with engine.connect() as conn:
            count = conn.execute(
                text("SELECT COUNT(*) FROM document_chunks WHERE chunk_id = :cid"),
                {"cid": unique_chunk_id},
            ).scalar()
        assert count == 1, f"Expected 1 record, found {count} — duplicates detected!"

    def test_null_metadata_fields_allowed(self):
        """Optional metadata fields should accept None values."""
        ensure_table_exists()
        chunk_id = f"null-meta-test-{uuid.uuid4().hex}"
        upsert_chunk_metadata(
            chunk_id=chunk_id,
            sku=None,
            category=None,
            manufacturer=None,
            filename=None,
            page_number=None,
        )
        record = get_chunk_by_id(chunk_id)
        assert record is not None
        assert record["sku"] is None
        assert record["page_number"] is None

    def test_timestamps_are_present(self, unique_chunk_id):
        ensure_table_exists()
        upsert_chunk_metadata(
            chunk_id=unique_chunk_id,
            sku="TS-TEST",
            category=None,
            manufacturer=None,
            filename=None,
            page_number=None,
        )
        record = get_chunk_by_id(unique_chunk_id)
        assert record is not None
        assert record["created_at"] is not None
        assert record["updated_at"] is not None


class TestPostgreSQLValidation:
    def test_empty_chunk_id_raises(self):
        with pytest.raises(ValueError, match="chunk_id"):
            upsert_chunk_metadata(
                chunk_id="",
                sku=None,
                category=None,
                manufacturer=None,
                filename=None,
                page_number=None,
            )

    def test_whitespace_chunk_id_raises(self):
        with pytest.raises(ValueError, match="chunk_id"):
            upsert_chunk_metadata(
                chunk_id="   ",
                sku=None,
                category=None,
                manufacturer=None,
                filename=None,
                page_number=None,
            )
