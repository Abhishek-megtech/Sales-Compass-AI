from fastapi import APIRouter, HTTPException

from app.retrieval.api_schemas import SearchRequest
from app.retrieval.retriever import retrieve


router = APIRouter(
    prefix="/search",
    tags=["Retrieval"],
)


@router.post("")
def search(request: SearchRequest):

    try:

        response = retrieve(
            query=request.query,
            top_k=request.top_k,
            score_threshold=request.score_threshold,
            sku=request.sku,
            category=request.category,
            manufacturer=request.manufacturer,
            document_id=request.document_id,
        )

        return response

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e),
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Retrieval failed: {str(e)}",
        )