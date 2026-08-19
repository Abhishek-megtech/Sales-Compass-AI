from pathlib import Path


ALLOWED_EXTENSIONS = {
    ".pdf",
    ".xlsx",
    ".xls",
    ".csv",
}


MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB


def validate_file(filename: str, file_size: int) -> None:
    """
    Validate uploaded document.

    Raises:
        ValueError: If the file is invalid.
    """

    if not filename:
        raise ValueError("Filename is required.")

    extension = Path(filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type: {extension}. "
            f"Allowed types: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    if file_size <= 0:
        raise ValueError("File is empty.")

    if file_size > MAX_FILE_SIZE:
        raise ValueError(
            f"File size exceeds the maximum limit of "
            f"{MAX_FILE_SIZE // (1024 * 1024)} MB."
        )