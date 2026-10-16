def truncate_review(text: str, max_chars: int = 2000, head_chars: int = 1200, tail_chars: int = 400) -> str:
    """
    Truncate long reviews by keeping the informative head and tail.
    Avoids losing key complaints or final conclusions often at the end.
    """
    if len(text) <= max_chars:
        return text
    head = text[:head_chars]
    tail = text[-tail_chars:]
    return f"{head} ... [truncated] ... {tail}"
