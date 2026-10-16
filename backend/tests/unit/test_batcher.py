import pytest
from app.core.enrichment.batcher import Batcher

class DummyItem:
    def __init__(self, id: int, clean_text: str):
        self.id = id
        self.clean_text = clean_text


def test_batcher_empty_items():
    batcher = Batcher(max_items=10, max_tokens=1000)
    batches = batcher.pack([])
    assert batches == []


def test_batcher_respects_max_items():
    items = [DummyItem(i, f"Short review number {i}") for i in range(35)]
    batcher = Batcher(max_items=10, max_tokens=10000)
    batches = batcher.pack(items)

    assert len(batches) >= 4
    for b in batches:
        assert len(b) <= 10


def test_batcher_never_drops_or_duplicates_items():
    items = [DummyItem(i, f"Review text with variable length {i * 'word '}") for i in range(25)]
    batcher = Batcher(max_items=8, max_tokens=500)
    batches = batcher.pack(items)

    unpacked_ids = [item.id for b in batches for item in b]
    assert len(unpacked_ids) == len(items)
    assert set(unpacked_ids) == {item.id for item in items}


def test_batcher_first_fit_decreasing_order():
    items = [
        DummyItem(1, "short"),
        DummyItem(2, "a much longer review text that takes up more tokens than the first one"),
        DummyItem(3, "medium text here")
    ]
    batcher = Batcher(max_items=5, max_tokens=2000)
    batches = batcher.pack(items)
    assert len(batches) == 1
    # Longest item should be placed first
    assert batches[0][0].id == 2
