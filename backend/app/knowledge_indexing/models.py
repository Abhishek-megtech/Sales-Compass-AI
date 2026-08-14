"""
Knowledge Indexing Service — input/output data contracts.

This module defines the shared data structures that form the interface
between the Document Ingestion Service (Phase 3) and the Knowledge
Indexing Service (Phase 4).

Phase 3 produces ChunkInput objects; Phase 4 consumes them.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ChunkMetadata:
    """
    Metadata attached to a document chunk.

    Fields match the documented metadata contract:
    - SKU, category, manufacturer, filename, page_number.

    All fields are optional strings/ints because not every document type
    will carry every field. Missing values default to None.
    """

    sku: Optional[str] = None
    category: Optional[str] = None
    manufacturer: Optional[str] = None
    filename: Optional[str] = None
    page_number: Optional[int] = None

    def to_dict(self) -> dict:
        """Return a plain dict suitable for Qdrant payload or PG insert."""
        return {
            "sku": self.sku,
            "category": self.category,
            "manufacturer": self.manufacturer,
            "filename": self.filename,
            "page_number": self.page_number,
        }


@dataclass
class ChunkInput:
    """
    The canonical input contract for the Knowledge Indexing Service.

    Produced by the Document Ingestion Service (Phase 3) and consumed
    by this service (Phase 4).

    chunk_id must be globally unique and stable across re-indexing runs.
    text must be a non-empty, clean string (whitespace-stripped).
    metadata carries the documented SKU/category/manufacturer/filename/page fields.
    """

    chunk_id: str
    text: str
    metadata: ChunkMetadata = field(default_factory=ChunkMetadata)

    @classmethod
    def from_dict(cls, data: dict) -> "ChunkInput":
        """
        Construct a ChunkInput from a plain dictionary.

        Accepts the documented JSON contract:
        {
            "chunk_id": "...",
            "text": "...",
            "metadata": {
                "sku": "...",
                "category": "...",
                "manufacturer": "...",
                "filename": "...",
                "page_number": 1
            }
        }
        """
        raw_meta = data.get("metadata", {})
        metadata = ChunkMetadata(
            sku=raw_meta.get("sku"),
            category=raw_meta.get("category"),
            manufacturer=raw_meta.get("manufacturer"),
            filename=raw_meta.get("filename"),
            page_number=raw_meta.get("page_number"),
        )
        return cls(
            chunk_id=data["chunk_id"],
            text=data["text"],
            metadata=metadata,
        )


@dataclass
class IndexingResult:
    """
    The output contract returned by the indexer after processing a chunk.

    chunk_id:        The same chunk_id that was submitted.
    success:         True if both Qdrant and PostgreSQL writes succeeded.
    qdrant_point_id: The UUID string used as the Qdrant point identifier.
    error:           Human-readable error message if success=False, else None.
    """

    chunk_id: str
    success: bool
    qdrant_point_id: Optional[str] = None
    error: Optional[str] = None
