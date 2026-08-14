"""
Knowledge Indexing Service — public package API.

Phase 3 (Document Ingestion) should call:

    from app.knowledge_indexing import index_chunk, index_chunks, ChunkInput, ChunkMetadata

Example usage:

    from app.knowledge_indexing import index_chunk, ChunkInput, ChunkMetadata

    chunk = ChunkInput(
        chunk_id="doc-001-page-1-chunk-0",
        text="This product is a high-performance industrial cleaner.",
        metadata=ChunkMetadata(
            sku="BD-4340",
            category="Cleaning Equipment",
            manufacturer="Karcher",
            filename="BD 43-40.pdf",
            page_number=1,
        ),
    )

    result = index_chunk(chunk)
    if result.success:
        print(f"Indexed: qdrant_point_id={result.qdrant_point_id}")
    else:
        print(f"Indexing failed: {result.error}")
"""

from .indexer import index_chunk, index_chunks
from .models import ChunkInput, ChunkMetadata, IndexingResult

__all__ = [
    "index_chunk",
    "index_chunks",
    "ChunkInput",
    "ChunkMetadata",
    "IndexingResult",
]
