import re
from pathlib import Path


def extract_sku(text: str) -> str | None:

    patterns = [
        r"\bSKU\s*[:#-]?\s*([A-Za-z0-9._/-]+)",
        r"\bProduct\s*Code\s*[:#-]?\s*([A-Za-z0-9._/-]+)",
        r"\bItem\s*Code\s*[:#-]?\s*([A-Za-z0-9._/-]+)",
        r"\bPart\s*Number\s*[:#-]?\s*([A-Za-z0-9._/-]+)",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:
            return match.group(1).strip()

    return None


def extract_category(text: str) -> str | None:

    pattern = r"\bCategory\s*[:#-]?\s*(.+)"

    match = re.search(
        pattern,
        text,
        re.IGNORECASE
    )

    if match:
        return match.group(1).strip()

    return None


def extract_manufacturer(text: str) -> str | None:

    pattern = (
        r"\bManufacturer\s*[:#-]?\s*(.+)"
    )

    match = re.search(
        pattern,
        text,
        re.IGNORECASE
    )

    if match:
        return match.group(1).strip()

    return None


def extract_metadata(
    text: str,
    filename: str,
    page_number: int | None = None,
    sheet_name: str | None = None,
    row_number: int | None = None,
) -> dict:

    return {
        "filename": Path(filename).name,
        "page_number": page_number,
        "sheet_name": sheet_name,
        "row_number": row_number,
        "sku": extract_sku(text),
        "category": extract_category(text),
        "manufacturer": extract_manufacturer(text),
    }

