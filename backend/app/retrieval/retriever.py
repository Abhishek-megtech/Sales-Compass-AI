import os
from typing import Optional

from dotenv import load_dotenv
from qdrant_client.models import FieldCondition, Filter, MatchValue

from app.database.qdrant import client
from app.retrieval.embedder import embedder
from app.retrieval.schemas import (
    RetrievedChunk,
    RetrievalResponse,
)


load_dotenv()


COLLECTION_NAME = "product_chunks_test"

TOP_K = int(
    os.getenv("RETRIEVAL_TOP_K", "5")
)

SCORE_THRESHOLD = float(
    os.getenv(
        "RETRIEVAL_SCORE_THRESHOLD",
        "0.0"
    )
)


def build_filter(
    sku: Optional[str] = None,
    category: Optional[str] = None,
    manufacturer: Optional[str] = None,
    document_id: Optional[int] = None,
):
    conditions = []

    if sku is not None:
        conditions.append(
            FieldCondition(
                key="sku",
                match=MatchValue(
                    value=sku
                ),
            )
        )

    if category is not None:
        conditions.append(
            FieldCondition(
                key="category",
                match=MatchValue(
                    value=category
                ),
            )
        )

    if manufacturer is not None:
        conditions.append(
            FieldCondition(
                key="manufacturer",
                match=MatchValue(
                    value=manufacturer
                ),
            )
        )

    if document_id is not None:
        conditions.append(
            FieldCondition(
                key="document_id",
                match=MatchValue(
                    value=document_id
                ),
            )
        )

    if not conditions:
        return None

    return Filter(
        must=conditions
    )


def retrieve(
    query: str,
    top_k: int = TOP_K,
    score_threshold: float = SCORE_THRESHOLD,
    sku: Optional[str] = None,
    category: Optional[str] = None,
    manufacturer: Optional[str] = None,
    document_id: Optional[int] = None,
) -> RetrievalResponse:

    # -----------------------------
    # Validate query
    # -----------------------------

    if not query or not query.strip():
        raise ValueError(
            "Query cannot be empty."
        )

    # -----------------------------
    # Validate top_k
    # -----------------------------

    if top_k <= 0:
        raise ValueError(
            "top_k must be greater than 0."
        )

    if top_k > 100:
        raise ValueError(
            "top_k cannot be greater than 100."
        )

    # -----------------------------
    # Validate score threshold
    # -----------------------------

    if score_threshold < -1.0:
        raise ValueError(
            "score_threshold cannot be below -1.0."
        )

    if score_threshold > 1.0:
        raise ValueError(
            "score_threshold cannot be above 1.0."
        )

    # -----------------------------
    # Query embedding
    # -----------------------------

    query_vector = embedder.embed_query(
        query
    )

    # -----------------------------
    # Metadata filter
    # -----------------------------

    query_filter = build_filter(
        sku=sku,
        category=category,
        manufacturer=manufacturer,
        document_id=document_id,
    )

    # -----------------------------
    # Qdrant search
    # -----------------------------

    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        query_filter=query_filter,
        limit=top_k,
        score_threshold=score_threshold,
        with_payload=True,
    ).points

    # -----------------------------
    # Format results
    # -----------------------------

    retrieved_chunks = []

    for result in results:

        payload = result.payload or {}

        retrieved_chunks.append(
            RetrievedChunk(
                chunk_id=payload.get(
                    "chunk_id"
                ),
                document_id=payload.get(
                    "document_id"
                ),
                text=payload.get(
                    "text",
                    ""
                ),
                score=float(
                    result.score
                ),
                metadata={
                    "sku": payload.get("sku"),
                    "category": payload.get(
                        "category"
                    ),
                    "manufacturer": payload.get(
                        "manufacturer"
                    ),
                    "filename": payload.get(
                        "filename"
                    ),
                    "page_number": payload.get(
                        "page_number"
                    ),
                    "sheet_name": payload.get(
                        "sheet_name"
                    ),
                    "row_number": payload.get(
                        "row_number"
                    ),
                },
            )
        )

    return RetrievalResponse(
        query=query,
        results=retrieved_chunks,
        total_results=len(
            retrieved_chunks
        ),
    )