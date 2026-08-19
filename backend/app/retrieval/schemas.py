from dataclasses import dataclass
from typing import Any


@dataclass
class RetrievedChunk:
    chunk_id: str | None
    document_id: int | str | None
    text: str
    score: float
    metadata: dict[str, Any]


@dataclass
class RetrievalResponse:
    query: str
    results: list[RetrievedChunk]
    total_results: int