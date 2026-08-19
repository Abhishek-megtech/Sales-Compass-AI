from pathlib import Path

from app.ingestion.extract_text import extract_text
from app.ingestion.text_cleaner import clean_text


file_path = Path("test_documents/test.pdf")


sections = extract_text(file_path)


for section in sections:

    raw_text = section["text"]

    cleaned_text = clean_text(raw_text)

    print("\n" + "=" * 50)

    print(
        f"Page: {section.get('page_number')}"
    )

    print("\nRAW:")
    print(raw_text)

    print("\nCLEANED:")
    print(cleaned_text) 