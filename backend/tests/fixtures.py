"""
Test fixtures for Phase 4 Knowledge Indexing tests.

Provides sample ChunkInput objects that stand in for Phase 3 output.
Phase 3 (Document Ingestion) is not yet implemented; these fixtures
allow Phase 4 to be tested independently.
"""

import uuid
from app.knowledge_indexing.models import ChunkInput, ChunkMetadata


def make_chunk(
    chunk_id: str = None,
    text: str = "This is a sample product description for testing purposes.",
    sku: str = "BD-4340",
    category: str = "Cleaning Equipment",
    manufacturer: str = "Karcher",
    filename: str = "BD 43-40.pdf",
    page_number: int = 1,
) -> ChunkInput:
    """
    Build a valid ChunkInput for testing.

    All parameters have sensible defaults so callers can override only
    what they need.
    """
    if chunk_id is None:
        chunk_id = f"test-chunk-{uuid.uuid4().hex[:8]}"

    return ChunkInput(
        chunk_id=chunk_id,
        text=text,
        metadata=ChunkMetadata(
            sku=sku,
            category=category,
            manufacturer=manufacturer,
            filename=filename,
            page_number=page_number,
        ),
    )


def make_chunk_from_dict(data: dict) -> ChunkInput:
    """
    Build a ChunkInput using the documented JSON contract format.

    Useful for testing the from_dict path.
    """
    return ChunkInput.from_dict(data)


# ---------------------------------------------------------------------------
# Pre-built sample fixtures
# ---------------------------------------------------------------------------

SAMPLE_CHUNK = make_chunk(
    chunk_id="sample-chunk-001",
    text=(
        "The BD 43/40 is a walk-behind scrubber-dryer designed for "
        "medium-sized areas. It combines ease of use with high cleaning "
        "performance, featuring a 43-litre solution tank and disc brush system."
    ),
    sku="BD-4340",
    category="Floor Cleaning",
    manufacturer="Karcher",
    filename="BD 43-40.pdf",
    page_number=1,
)

SAMPLE_CHUNK_2 = make_chunk(
    chunk_id="sample-chunk-002",
    text=(
        "NT 40/1 Ap L EU is a wet and dry vacuum cleaner with a 40-litre "
        "stainless steel container. Suitable for professional use in "
        "construction sites and workshops."
    ),
    sku="NT-401-APL",
    category="Vacuum Cleaners",
    manufacturer="Karcher",
    filename="NT 40-1 APL _EU.pdf",
    page_number=2,
)

SAMPLE_DICT_CHUNK = {
    "chunk_id": "sample-dict-chunk-001",
    "text": "Block Jointing Mortar is a polymer-modified cement-based adhesive.",
    "metadata": {
        "sku": "BJM-001",
        "category": "Construction Materials",
        "manufacturer": "Infra.Market",
        "filename": "Block Jointing Mortar - TDS-Infra.Market .pdf",
        "page_number": 1,
    },
}
