import re

class QueryRouter:
    """Classifies user queries into aggregate vs evidence vs unanswerable."""
    
    AGGREGATE_PATTERNS = [
        r"what are.*complaining about",
        r"top (issues|complaints|problems|topics)",
        r"most common (issues|bugs|complaints)",
        r"how many (users|reviews|people|customers)",
        r"distribution of sentiment",
        r"trend.*(rising|falling|increasing)",
        r"what is rising",
        r"breakdown by topic",
    ]

    UNANSWERABLE_PATTERNS = [
        r"weather",
        r"capital of",
        r"recipe for",
        r"who is the president",
        r"stock price of",
    ]

    def route(self, query: str) -> str:
        q_lower = query.strip().lower()

        for pattern in self.UNANSWERABLE_PATTERNS:
            if re.search(pattern, q_lower):
                return "unanswerable"

        for pattern in self.AGGREGATE_PATTERNS:
            if re.search(pattern, q_lower):
                return "aggregate"

        return "evidence"
