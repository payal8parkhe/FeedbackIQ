from dataclasses import dataclass
from typing import TypeVar, Generic

T = TypeVar("T")

@dataclass
class BatchBin(Generic[T]):
    items: list[T]
    current_tokens: int

    def add(self, item: T, tokens: int):
        self.items.append(item)
        self.current_tokens += tokens


class Batcher:
    """
    First-fit decreasing bin packing for reviews.
    Optimizes LLM batch calls under constraints of max_items and max_tokens.
    """
    def __init__(self, max_items: int = 15, max_tokens: int = 6000, overhead_tokens: int = 200):
        self.max_items = max_items
        self.max_tokens = max_tokens
        self.overhead_tokens = overhead_tokens

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """Heuristic token estimation: ~4 chars per token, minimum 1 token."""
        return max(1, len(text) // 4)

    def pack(self, items: list[T], text_getter: callable = lambda x: getattr(x, "clean_text", str(x))) -> list[list[T]]:
        if not items:
            return []

        # Pair items with their estimated token count
        item_tokens = [(item, self.estimate_tokens(text_getter(item))) for item in items]
        
        # Sort items descending by token size (First-Fit Decreasing)
        item_tokens.sort(key=lambda x: x[1], reverse=True)

        bins: list[BatchBin[T]] = []

        for item, tok in item_tokens:
            placed = False
            for b in bins:
                # Check if fits in bin
                if len(b.items) + 1 <= self.max_items and (b.current_tokens + tok + self.overhead_tokens) <= self.max_tokens:
                    b.add(item, tok)
                    placed = True
                    break
            
            if not placed:
                # Start new bin
                new_bin = BatchBin(items=[], current_tokens=0)
                new_bin.add(item, tok)
                bins.append(new_bin)

        return [b.items for b in bins]
