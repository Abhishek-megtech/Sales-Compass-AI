from typing import Optional

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=1,
        description="User search query",
    )

    top_k: int = Field(
        default=5,
        ge=1,
        le=100,
    )

    score_threshold: float = Field(
        default=0.0,
        ge=-1.0,
        le=1.0,
    )

    sku: Optional[str] = None
    category: Optional[str] = None
    manufacturer: Optional[str] = None
    document_id: Optional[int] = None