from dataclasses import dataclass
from typing import Any


@dataclass
class DocumentChunk:
    chunk_id: str
    document_id: int | str
    text: str
    metadata: dict[str, Any]