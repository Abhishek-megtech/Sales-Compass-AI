from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from app.ingestion.service import ingest_document


router = APIRouter(
    prefix="/upload",
    tags=["Document Ingestion"],
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@router.post("")
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Upload and process a PDF, Excel, or CSV document.
    """

    try:

        file_content = await file.read()

        result = ingest_document(
            db=db,
            filename=file.filename,
            file_content=file_content,
        )

        return {
            "success": True,
            "document_id": result["document_id"],
            "filename": result["filename"],
            "chunks_created": len(result["chunks"]),
            "chunks":[
                {
                    "chunk_id":chunk.chunk_id,
                    "document_id":chunk.document_id,
                    "text":chunk.text,
                    "metadata":chunk.metadata,
                }
                for chunk in result["chunks"]
            ]
        }

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e),
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Document ingestion failed: {str(e)}",
        )

