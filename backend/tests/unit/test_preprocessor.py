import pytest
from app.core.preprocess.clean import normalize_text
from app.core.preprocess.pii import mask_pii
from app.core.preprocess.truncate import truncate_review

def test_normalize_text_collapses_whitespace_and_strips_html():
    raw = "   <div>Hello   \n\n\tworld!</div>  <p>App is great</p> "
    cleaned = normalize_text(raw)
    assert cleaned == "Hello world! App is great"


def test_mask_pii_removes_emails_and_cards():
    text = "Contact me at alice.smith@example.com or call 555-123-4567. Card was 4532-1234-5678-9012."
    masked = mask_pii(text)
    assert "[EMAIL_MASKED]" in masked
    assert "alice.smith@example.com" not in masked
    assert "[PHONE_MASKED]" in masked
    assert "[CARD_MASKED]" in masked
    assert "4532" not in masked


def test_truncate_review_head_and_tail():
    long_text = "START_" + ("x" * 2500) + "_END"
    truncated = truncate_review(long_text, max_chars=2000, head_chars=100, tail_chars=50)
    assert len(truncated) < 200
    assert truncated.startswith("START_")
    assert truncated.endswith("_END")
    assert "[truncated]" in truncated
