from pathlib import Path

from app.ingestion.extract_text import extract_text
from app.ingestion.text_cleaner import clean_text
from app.ingestion.chunker import chunk_text


file_path = Path("test_documents/test.pdf")


sections = extract_text(file_path)


for section in sections:

    raw_text = section["text"]

    cleaned_text = clean_text(raw_text)

    chunks = chunk_text(cleaned_text)

    print("\n" + "=" * 60)

    print(
        f"Page: {section.get('page_number')}"
    )

    print(
        f"Total chunks: {len(chunks)}"
    )

    for index, chunk in enumerate(
        chunks,
        start=1
    ):

        print("\n" + "-" * 60)

        print(f"Chunk {index}")

        print("-" * 60)

        print(chunk)