from app.database.session import SessionLocal
from app.ingestion.document_service import create_document_record


db = SessionLocal()


try:
    document = create_document_record(
        db=db,
        filename="test_product_catalog.pdf",
    )

    print("Document created successfully!")
    print("Document ID:", document.id)
    print("Filename:", document.filename)

finally:
    db.close()