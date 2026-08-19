from pathlib import Path
from uuid import uuid4

from app.ingestion.extract_text import extract_text
from app.ingestion.text_cleaner import clean_text
from app.ingestion.chunker import chunk_text
from app.ingestion.metadata_extractor import extract_metadata
from app.ingestion.schemas import DocumentChunk


def process_document(
    file_path: str | Path,
    document_id: int | str,
) -> list[DocumentChunk]:
    """
    Complete document ingestion pipeline.

    File
      ↓
    Extraction
      ↓
    Cleaning
      ↓
    Chunking
      ↓
    Metadata extraction
    """

    file_path = Path(file_path)

    sections = extract_text(file_path)

    all_chunks = []

    for section in sections:

        raw_text = section.get("text", "")

        cleaned_text = clean_text(raw_text)

        if not cleaned_text:
            continue

        chunks = chunk_text(cleaned_text)

        for chunk in chunks:

            metadata = extract_metadata(
                text=chunk,
                filename=file_path.name,
                page_number=section.get(
                    "page_number"
                ),
                sheet_name=section.get(
                    "sheet_name"
                ),
                row_number=section.get("row_number")
            )

            document_chunk = DocumentChunk(
                chunk_id=str(uuid4()),
                document_id=document_id,
                text=chunk,
                metadata=metadata,
            )

            all_chunks.append(
                document_chunk
            )

    return all_chunks