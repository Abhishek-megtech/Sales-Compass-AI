from pathlib import Path

from app.database.session import SessionLocal
from app.ingestion.service import ingest_document


db = SessionLocal()

try:

    file_path = Path(
        "test_documents/test.xlsx"
    )

    result = ingest_document(
        db=db,
        filename=file_path.name,
        file_content=file_path.read_bytes(),
    )

    print("=" * 60)
    print("EXCEL INGESTION")
    print("=" * 60)

    print("Document ID:", result["document_id"])
    print("Total chunks:", len(result["chunks"]))

    for chunk in result["chunks"]:

        print("\n" + "-" * 60)

        print("Chunk ID:", chunk.chunk_id)
        print("Document ID:", chunk.document_id)

        print("\nText:")
        print(chunk.text)

        print("\nMetadata:")
        print(chunk.metadata)

finally:
    db.close()