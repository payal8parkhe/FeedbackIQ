import unicodedata
import re

def normalize_text(text: str) -> str:
    """Normalize unicode, collapse whitespace, strip HTML tags."""
    if not text:
        return ""
    # Unicode NFKC normalization
    text = unicodedata.normalize("NFKC", text)
    # Strip HTML tags
    text = re.sub(r"<[^>]+>", " ", text)
    # Collapse multiple whitespace / tabs / newlines into single spaces
    text = re.sub(r"\s+", " ", text)
    return text.strip()
