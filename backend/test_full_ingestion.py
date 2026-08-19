from pathlib import Path

from app.ingestion.pipeline import process_document


file_path = Path(
    "test_documents/test.pdf"
)

document_id = 1


chunks = process_document(
    file_path=file_path,
    document_id=document_id,
)


print("\n" + "=" * 60)
print("DOCUMENT INGESTION RESULT")
print("=" * 60)

print(f"Total chunks: {len(chunks)}")


for index, chunk in enumerate(
    chunks,
    start=1
):

    print("\n" + "-" * 60)

    print(f"CHUNK {index}")

    print("-" * 60)

    print("Chunk ID:")
    print(chunk.chunk_id)

    print("\nDocument ID:")
    print(chunk.document_id)

    print("\nText:")
    print(chunk.text)

    print("\nMetadata:")
    print(chunk.metadata)