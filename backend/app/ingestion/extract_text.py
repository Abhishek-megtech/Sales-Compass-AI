from pathlib import Path

import fitz
import pandas as pd


def extract_from_pdf(file_path: Path) -> list[dict]:
    """
    Extract PDF text page by page.
    """

    sections = []

    with fitz.open(file_path) as document:

        for page_number, page in enumerate(
            document,
            start=1
        ):
            text = page.get_text()

            sections.append(
                {
                    "source_type": "pdf",
                    "page_number": page_number,
                    "text": text,
                }
            )

    return sections


def extract_from_excel(file_path: Path) -> list[dict]:
    """
    Extract Excel data row by row.

    Each row represents a product/item and is kept
    as an independent section.
    """

    sheets = pd.read_excel(
        file_path,
        sheet_name=None
    )

    sections = []

    for sheet_name, dataframe in sheets.items():

        dataframe = dataframe.fillna("")

        for row_number, (_, row) in enumerate(
            dataframe.iterrows(),
            start=1
        ):

            fields = []

            for column, value in row.items():

                value = str(value).strip()

                if not value:
                    continue

                fields.append(
                    f"{column}: {value}"
                )

            text = "\n".join(fields)

            if not text:
                continue

            sections.append(
                {
                    "source_type": "excel",
                    "page_number": None,
                    "sheet_name": sheet_name,
                    "row_number": row_number,
                    "text": text,
                }
            )

    return sections


def extract_from_csv(file_path: Path) -> list[dict]:
    """
    Extract CSV data row by row.
    """

    dataframe = pd.read_csv(file_path)

    dataframe = dataframe.fillna("")

    sections = []

    for row_number, (_, row) in enumerate(
        dataframe.iterrows(),
        start=1
    ):

        fields = []

        for column, value in row.items():

            value = str(value).strip()

            if not value:
                continue

            fields.append(
                f"{column}: {value}"
            )

        text = "\n".join(fields)

        if not text:
            continue

        sections.append(
            {
                "source_type": "csv",
                "page_number": None,
                "row_number": row_number,
                "text": text,
            }
        )

    return sections


def extract_text(file_path: str | Path) -> list[dict]:
    """
    Detect file type and extract structured sections.
    """

    file_path = Path(file_path)

    extension = file_path.suffix.lower()

    if extension == ".pdf":
        return extract_from_pdf(file_path)

    if extension in {".xlsx", ".xls"}:
        return extract_from_excel(file_path)

    if extension == ".csv":
        return extract_from_csv(file_path)

    raise ValueError(
        f"Unsupported file type: {extension}"
    )