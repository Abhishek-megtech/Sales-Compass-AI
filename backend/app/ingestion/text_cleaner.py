import re
import unicodedata


def normalize_unicode(text: str) -> str:
    """
    Normalize Unicode characters.
    """

    return unicodedata.normalize(
        "NFKC",
        text
    )


def normalize_whitespace(text: str) -> str:
    """
    Normalize spaces and blank lines.
    """

    # Convert tabs to spaces
    text = text.replace("\t", " ")

    # Remove trailing/leading whitespace from each line
    lines = [
        line.strip()
        for line in text.splitlines()
    ]

    # Remove completely empty lines
    lines = [
        line
        for line in lines
        if line
    ]

    # Collapse multiple spaces
    lines = [
        re.sub(r"\s+", " ", line)
        for line in lines
    ]

    # Join lines with a single newline
    text = "\n".join(lines)

    return text


def clean_text(text: str) -> str:
    """
    Complete text-cleaning pipeline.
    """

    if not text:
        return ""

    text = normalize_unicode(text)

    text = normalize_whitespace(text)

    return text.strip()