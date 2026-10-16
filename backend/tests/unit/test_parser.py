import pytest
from app.core.enrichment.parser import EnrichmentParser
from app.domain.schemas import Sentiment
from app.domain.taxonomy import TopicSlug

def test_parser_strips_code_fences():
    parser = EnrichmentParser()
    raw = "```json\n[{\"review_id\": 1, \"sentiment\": \"positive\", \"topics\": [\"login_auth\"], \"summary\": \"Fast login experience reported\", \"confidence\": 0.95}]\n```"
    parsed = parser.parse_raw(raw)
    assert len(parsed) == 1
    assert parsed[0]["review_id"] == 1


def test_parser_split_batch_separates_valid_and_bad_items():
    parser = EnrichmentParser()
    raw = [
        # Valid item
        {"review_id": 101, "sentiment": "negative", "topics": ["app_crash"], "summary": "App crashed after update", "confidence": 0.9},
        # Invalid topic slug
        {"review_id": 102, "sentiment": "negative", "topics": ["invented_non_existent_topic"], "summary": "Bad item", "confidence": 0.9},
        # Missing summary length bounds
        {"review_id": 103, "sentiment": "positive", "topics": ["login_auth"], "summary": "Too short", "confidence": 0.9}
    ]
    ok_map, bad_ids = parser.split_batch(raw, expected_ids=[101, 102, 103])
    assert 101 in ok_map
    assert ok_map[101].sentiment == Sentiment.negative
    assert 102 in bad_ids
    assert 103 in bad_ids
