from pathlib import Path

from app.database.session import SessionLocal
from app.ingestion.service import ingest_document


db = SessionLocal()


try:

    file_path = Path(
        "test_documents/test.pdf"
    )

    file_content = file_path.read_bytes()

    result = ingest_document(
        db=db,
        filename=file_path.name,
        file_content=file_content,
    )

    print("\n" + "=" * 60)
    print("INGESTION SUCCESSFUL")
    print("=" * 60)

    print("\nDocument ID:")
    print(result["document_id"])

    print("\nFilename:")
    print(result["filename"])

    print("\nSaved File:")
    print(result["file_path"])

    print("\nTotal Chunks:")
    print(len(result["chunks"]))

    for chunk in result["chunks"]:

        print("\n" + "-" * 60)

        print("Chunk ID:")
        print(chunk.chunk_id)

        print("Document ID:")
        print(chunk.document_id)

        print("Text:")
        print(chunk.text)

        print("Metadata:")
        print(chunk.metadata)

finally:

    db.close()