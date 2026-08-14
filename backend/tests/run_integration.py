# -*- coding: utf-8 -*-
import os
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
"""
Phase 4 — Knowledge Indexing Service
Integration runner / smoke test script.

Run this script directly to verify the complete Phase 4 pipeline without
needing pytest. It will:

1. Load BAAI/bge-small-en and verify the embedding dimension
2. Connect to Qdrant and ensure the collection exists
3. Connect to PostgreSQL and ensure the table exists
4. Index a sample chunk end-to-end
5. Verify chunk_id appears in BOTH Qdrant and PostgreSQL
6. Re-index the same chunk and verify idempotency (no duplicates)
7. Index a batch of 3 chunks
8. Test error handling for invalid input

Usage:
    cd c:\\Users\\abhis\\OneDrive\\Desktop\\salescompass-ai
    .\\venv\\Scripts\\python.exe backend/tests/run_integration.py
"""

import logging
import os
import sys
import uuid

# Ensure backend/ is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

# Configure logging so the output is readable
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("phase4.integration")

# ─────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────

PASS = "[PASS]"
FAIL = "[FAIL]"
SKIP = "[SKIP]"

results: list[tuple[str, str]] = []


def check(label: str, condition: bool, detail: str = "") -> None:
    status = PASS if condition else FAIL
    msg = f"{status}  {label}"
    if detail:
        msg += f"  [{detail}]"
    print(msg)
    results.append((label, status))


def section(title: str) -> None:
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


# ─────────────────────────────────────────────────
# Step 1: Embedding
# ─────────────────────────────────────────────────

section("Step 1: Embedding Service")

try:
    from app.knowledge_indexing.embedding_service import (
        generate_embedding,
        get_embedding_dimension,
        EXPECTED_EMBEDDING_DIM,
    )

    dim = get_embedding_dimension()
    check("Model loaded (BAAI/bge-small-en)", True, f"dim={dim}")
    check("Embedding dimension is 384", dim == EXPECTED_EMBEDDING_DIM, f"got {dim}")

    vec = generate_embedding("BD 43/40 walk-behind scrubber-dryer with 43-litre tank.")
    check("Embedding generated", len(vec) == EXPECTED_EMBEDDING_DIM, f"len={len(vec)}")
    check("Embedding values are floats", all(isinstance(v, float) for v in vec))

    try:
        generate_embedding("")
        check("Empty text raises ValueError", False, "no exception raised")
    except ValueError:
        check("Empty text raises ValueError", True)

except Exception as exc:
    check("Embedding service", False, str(exc))
    print(f"\n  FATAL: Cannot continue without embedding service.\n  {exc}")
    sys.exit(1)

# ─────────────────────────────────────────────────
# Step 2: Qdrant
# ─────────────────────────────────────────────────

section("Step 2: Qdrant Service")

qdrant_ok = bool(os.getenv("QDRANT_URL", "").strip())
if not qdrant_ok:
    print(f"{SKIP}  QDRANT_URL not set — skipping Qdrant tests.")
    results.append(("Qdrant tests", SKIP))
else:
    try:
        from app.knowledge_indexing.qdrant_service import (
            ensure_collection_exists,
            upsert_vector,
            get_point_by_chunk_id,
            chunk_id_to_point_id,
        )

        ensure_collection_exists(vector_size=dim)
        check("Qdrant collection ensured", True)

        test_cid = f"integration-qdrant-{uuid.uuid4().hex}"
        payload = {"sku": "INT-SKU-001", "category": "Test", "manufacturer": "X",
                   "filename": "test.pdf", "page_number": 1}
        point_id = upsert_vector(chunk_id=test_cid, vector=vec, payload=payload)
        check("Vector upserted", isinstance(point_id, str) and len(point_id) > 0)

        stored = get_point_by_chunk_id(test_cid)
        check("Point retrieved from Qdrant", stored is not None)
        check("chunk_id in Qdrant payload", stored and stored.get("chunk_id") == test_cid)

        pid1 = chunk_id_to_point_id("determinism-test")
        pid2 = chunk_id_to_point_id("determinism-test")
        check("Point ID is deterministic", pid1 == pid2)

    except Exception as exc:
        check("Qdrant service", False, str(exc))

# ─────────────────────────────────────────────────
# Step 3: PostgreSQL
# ─────────────────────────────────────────────────

section("Step 3: PostgreSQL Service")

pg_ok = bool(os.getenv("DATABASE_URL", "").strip())
if not pg_ok:
    print(f"{SKIP}  DATABASE_URL not set — skipping PostgreSQL tests.")
    results.append(("PostgreSQL tests", SKIP))
else:
    try:
        from app.knowledge_indexing.postgres_service import (
            ensure_table_exists,
            upsert_chunk_metadata,
            get_chunk_by_id,
        )

        ensure_table_exists()
        check("document_chunks table ensured", True)

        pg_cid = f"integration-pg-{uuid.uuid4().hex}"
        upsert_chunk_metadata(
            chunk_id=pg_cid,
            sku="INT-SKU-002",
            category="Floor Cleaning",
            manufacturer="Karcher",
            filename="BD 43-40.pdf",
            page_number=2,
        )
        check("Metadata upserted", True)

        record = get_chunk_by_id(pg_cid)
        check("Record retrievable from PostgreSQL", record is not None)
        check("chunk_id in PostgreSQL record", record and record["chunk_id"] == pg_cid)
        check("Metadata fields correct",
              record and record["sku"] == "INT-SKU-002" and record["page_number"] == 2)
        check("Timestamps present",
              record and record["created_at"] is not None and record["updated_at"] is not None)

        # Idempotency
        upsert_chunk_metadata(
            chunk_id=pg_cid, sku="UPDATED-SKU", category="Updated",
            manufacturer="Y", filename="updated.pdf", page_number=99,
        )
        upsert_chunk_metadata(
            chunk_id=pg_cid, sku="UPDATED-SKU", category="Updated",
            manufacturer="Y", filename="updated.pdf", page_number=99,
        )
        from sqlalchemy import text as sa_text
        from app.knowledge_indexing.postgres_service import _get_engine
        engine = _get_engine()
        with engine.connect() as conn:
            count = conn.execute(
                sa_text("SELECT COUNT(*) FROM document_chunks WHERE chunk_id = :cid"),
                {"cid": pg_cid},
            ).scalar()
        check("No duplicate PG records after re-upsert", count == 1, f"count={count}")

    except Exception as exc:
        check("PostgreSQL service", False, str(exc))

# ─────────────────────────────────────────────────
# Step 4: Full end-to-end indexer
# ─────────────────────────────────────────────────

section("Step 4: Full End-to-End Indexer")

if not (qdrant_ok and pg_ok):
    print(f"{SKIP}  Both QDRANT_URL and DATABASE_URL required — skipping.")
    results.append(("End-to-end indexer", SKIP))
else:
    try:
        from app.knowledge_indexing.indexer import index_chunk, index_chunks
        from app.knowledge_indexing.models import ChunkInput, ChunkMetadata
        from app.knowledge_indexing.qdrant_service import get_point_by_chunk_id
        from app.knowledge_indexing.postgres_service import get_chunk_by_id

        e2e_cid = f"integration-e2e-{uuid.uuid4().hex}"
        chunk = ChunkInput(
            chunk_id=e2e_cid,
            text=(
                "The BD 43/40 is a walk-behind scrubber-dryer designed for "
                "medium-sized areas. It combines ease of use with high cleaning "
                "performance, featuring a 43-litre solution tank."
            ),
            metadata=ChunkMetadata(
                sku="BD-4340",
                category="Floor Cleaning",
                manufacturer="Karcher",
                filename="BD 43-40.pdf",
                page_number=1,
            ),
        )

        result = index_chunk(chunk)
        check("index_chunk returns success=True", result.success, result.error or "")
        check("qdrant_point_id returned", result.qdrant_point_id is not None)
        check("result.chunk_id matches input", result.chunk_id == e2e_cid)

        # Verify cross-system linkage
        qdrant_payload = get_point_by_chunk_id(e2e_cid)
        pg_record = get_chunk_by_id(e2e_cid)

        check("chunk_id in Qdrant payload", qdrant_payload and qdrant_payload.get("chunk_id") == e2e_cid)
        check("chunk_id in PostgreSQL record", pg_record and pg_record["chunk_id"] == e2e_cid)
        check(
            "chunk_id identical in both systems",
            qdrant_payload and pg_record and
            qdrant_payload.get("chunk_id") == pg_record["chunk_id"] == e2e_cid,
        )

        # Idempotency
        result2 = index_chunk(chunk)
        check("Re-index returns success=True", result2.success, result2.error or "")
        check("Re-index same point_id", result.qdrant_point_id == result2.qdrant_point_id)

        from sqlalchemy import text as sa_text
        from app.knowledge_indexing.postgres_service import _get_engine
        engine = _get_engine()
        with engine.connect() as conn:
            count = conn.execute(
                sa_text("SELECT COUNT(*) FROM document_chunks WHERE chunk_id = :cid"),
                {"cid": e2e_cid},
            ).scalar()
        check("No PG duplicates after re-index", count == 1, f"count={count}")

        # Error handling
        bad_chunk = ChunkInput(chunk_id="bad-empty", text="", metadata=ChunkMetadata())
        bad_result = index_chunk(bad_chunk)
        check("Empty text → success=False", not bad_result.success)
        check("Empty text → error message present", bool(bad_result.error))

        # Batch
        batch = [
            ChunkInput(
                chunk_id=f"batch-e2e-{uuid.uuid4().hex}",
                text=f"Batch chunk {i}: product description for integration test.",
                metadata=ChunkMetadata(sku=f"BATCH-{i}", category="Test",
                                       manufacturer="M", filename="f.pdf", page_number=i),
            )
            for i in range(3)
        ]
        batch_results = index_chunks(batch)
        check("Batch of 3 — all succeed", all(r.success for r in batch_results),
              str([r.error for r in batch_results if not r.success]))

    except Exception as exc:
        check("End-to-end indexer", False, str(exc))
        logger.exception("End-to-end test failed")

# ─────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────

section("Summary")
passed = sum(1 for _, s in results if s == PASS)
failed = sum(1 for _, s in results if s == FAIL)
skipped = sum(1 for _, s in results if s == SKIP)
total = len(results)

print(f"\n  Total: {total}  |  {PASS}: {passed}  |  {FAIL}: {failed}  |  {SKIP}: {skipped}\n")

if failed > 0:
    print("  Failed checks:")
    for label, status in results:
        if status == FAIL:
            print(f"    {FAIL}  {label}")
    sys.exit(1)

print("  All checks passed!\n")
sys.exit(0)
