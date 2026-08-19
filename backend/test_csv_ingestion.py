from pathlib import Path

from app.ingestion.extract_text import extract_text
from app.ingestion.text_cleaner import clean_text


file_path = Path(
    "test_documents/test.csv"
)

sections = extract_text(file_path)

print("=" * 60)
print("CSV EXTRACTION")
print("=" * 60)

print("Total rows:", len(sections))

for section in sections:

    cleaned = clean_text(
        section["text"]
    )

    print("\n" + "-" * 60)

    print("Row:", section["row_number"])

    print("\nText:")
    print(cleaned)