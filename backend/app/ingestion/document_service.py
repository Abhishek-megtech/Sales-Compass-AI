from sqlalchemy.orm import Session

from app.database.models import Document


def create_document_record(
    db: Session,
    filename: str,
    uploaded_by: int | None = None,
) -> Document:
    """
    Create a document record in PostgreSQL.
    """

    document = Document(
        filename=filename,
        uploaded_by=uploaded_by,
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    return document