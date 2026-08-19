from pathlib import Path
from uuid import uuid4


UPLOAD_DIR = Path("uploads/original")


def save_file(filename: str, file_content: bytes) -> Path:
    """
    Save the original uploaded file.

    Returns:
        Path: Path to the saved file.
    """

    UPLOAD_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    extension = Path(filename).suffix.lower()

    unique_filename = f"{uuid4()}{extension}"

    file_path = UPLOAD_DIR / unique_filename

    file_path.write_bytes(file_content)

    return file_path