from app.ingestion.validators import validate_file
from app.ingestion.upload import save_file


def test_valid_file():
    filename = "products.pdf"
    content = b"This is a test PDF file"

    validate_file(
        filename=filename,
        file_size=len(content)
    )

    path = save_file(
        filename=filename,
        file_content=file_content
    )

    print("File validation: PASSED")
    print("File storage: PASSED")
    print(f"Saved to: {path}")


if __name__ == "__main__":
    test_valid_file()