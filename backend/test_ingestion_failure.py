from app.database.session import SessionLocal
from app.ingestion.service import ingest_document


db = SessionLocal()


try:

    fake_file = b"This is not a real PDF."

    try:

        ingest_document(
            db=db,
            filename="broken.pdf",
            file_content=fake_file,
        )

    except Exception as e:

        print("Ingestion failed as expected.")
        print("Error:", e)

finally:

    db.close()