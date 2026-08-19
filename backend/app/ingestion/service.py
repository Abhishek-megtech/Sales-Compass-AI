from pathlib import Path

from sqlalchemy.orm import Session

from app.ingestion.document_service import create_document_record
from app.ingestion.pipeline import process_document
from app.ingestion.upload import save_file
from app.ingestion.validators import validate_file


def ingest_document(
    db: Session,
    filename: str,
    file_content: bytes,
    uploaded_by: int | None = None,
):
    """
    Complete document ingestion flow.

    1. Validate
    2. Save original
    3. Create PostgreSQL document record
    4. Extract, clean, chunk and extract metadata
    5. Return structured chunks

    If processing fails, the database record and saved file
    are cleaned up.
    """

    # -----------------------------
    # 1. Validate
    # -----------------------------

    validate_file(
        filename=filename,
        file_size=len(file_content),
    )

    file_path = None
    document = None

    try:

        # -----------------------------
        # 2. Save original file
        # -----------------------------

        file_path = save_file(
            filename=filename,
            file_content=file_content,
        )

        # -----------------------------
        # 3. Create PostgreSQL record
        # -----------------------------

        document = create_document_record(
            db=db,
            filename=filename,
            uploaded_by=uploaded_by,
        )

        # -----------------------------
        # 4. Process document
        # -----------------------------

        chunks = process_document(
            file_path=file_path,
            document_id=document.id,
        )

        # -----------------------------
        # 5. Return result
        # -----------------------------

        return {
            "document_id": document.id,
            "filename": document.filename,
            "file_path": str(file_path),
            "chunks": chunks,
        }

    except Exception:

        # Rollback current database transaction
        db.rollback()

        # Remove database record if it was created
        if document is not None:

            db.delete(document)
            db.commit()

        # Remove saved file if it exists
        if file_path is not None:

            path = Path(file_path)

            if path.exists():
                path.unlink()

        raise