import re

# Regex patterns for common PII
EMAIL_REGEX = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
PHONE_REGEX = re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")
CREDIT_CARD_REGEX = re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b")

def mask_pii(text: str) -> str:
    """Mask email, phone, and credit card numbers before any LLM call."""
    if not text:
        return ""
    text = EMAIL_REGEX.sub("[EMAIL_MASKED]", text)
    text = CREDIT_CARD_REGEX.sub("[CARD_MASKED]", text)
    text = PHONE_REGEX.sub("[PHONE_MASKED]", text)
    return text
