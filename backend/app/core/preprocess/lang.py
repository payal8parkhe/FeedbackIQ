def detect_language(text: str) -> str:
    """Simple heuristic language check. English is primary for v1."""
    if not text:
        return "en"
    # Basic ASCII / Latin check
    ascii_chars = sum(1 for c in text if ord(c) < 128)
    ratio = ascii_chars / len(text)
    return "en" if ratio > 0.8 else "other"
