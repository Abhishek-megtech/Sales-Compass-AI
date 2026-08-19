from pathlib import Path

import pandas as pd
import fitz

from app.ingestion.extract_text import extract_text


TEST_DIR = Path("test_documents")

TEST_DIR.mkdir(exist_ok=True)


def create_test_pdf():
    file_path = TEST_DIR / "test.pdf"

    document = fitz.open()

    page = document.new_page()

    page.insert_text(
        (50, 50),
        "Product: Industrial Router\n"
        "SKU: RT-1001\n"
        "Manufacturer: Cisco\n"
        "Category: Networking"
    )

    document.save(file_path)
    document.close()

    return file_path


def create_test_excel():
    file_path = TEST_DIR / "test.xlsx"

    dataframe = pd.DataFrame(
        {
            "SKU": ["RT-1001", "SW-2001"],
            "Product": [
                "Industrial Router",
                "Network Switch"
            ],
            "Manufacturer": [
                "Cisco",
                "Cisco"
            ],
            "Category": [
                "Networking",
                "Networking"
            ],
        }
    )

    dataframe.to_excel(
        file_path,
        index=False
    )

    return file_path


def create_test_csv():
    file_path = TEST_DIR / "test.csv"

    dataframe = pd.DataFrame(
        {
            "SKU": ["RT-1001", "SW-2001"],
            "Product": [
                "Industrial Router",
                "Network Switch"
            ],
            "Manufacturer": [
                "Cisco",
                "Cisco"
            ],
        }
    )

    dataframe.to_csv(
        file_path,
        index=False
    )

    return file_path


def test_extraction(file_path):
    print("\n" + "=" * 50)
    print(f"Testing: {file_path}")

    results = extract_text(file_path)

    print(f"Extracted sections: {len(results)}")

    for result in results:

        print("\n---")

        if result.get("page_number"):
            print(
                f"Page: {result['page_number']}"
            )

        if result.get("sheet_name"):
            print(
                f"Sheet: {result['sheet_name']}"
            )

        print("Text:")
        print(result["text"])


if __name__ == "__main__":

    pdf = create_test_pdf()
    excel = create_test_excel()
    csv = create_test_csv()

    test_extraction(pdf)
    test_extraction(excel)
    test_extraction(csv)