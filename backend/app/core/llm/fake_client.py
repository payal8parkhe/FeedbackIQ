import json
import re
import time
from decimal import Decimal
from pydantic import BaseModel
from app.core.llm.base import LLMResult
from app.core.llm.pricing import calculate_llm_cost
from app.domain.schemas import Sentiment, ReviewEnrichment, BatchEnrichment
from app.domain.taxonomy import TopicSlug

class FakeLLMClient:
    """
    Deterministic, high-fidelity Fake LLM Client for offline testing,
    smoke tests, and reproducible baseline evaluation.
    """
    def __init__(self, fail_next: bool = False, latency_ms: int = 15):
        self.fail_next = fail_next
        self.latency_ms = latency_ms
        self.call_count = 0

    def _infer_sentiment_and_topics(self, text: str) -> tuple[Sentiment, list[TopicSlug]]:
        lower = text.lower()
        
        # 1. Topic inference
        topics: list[TopicSlug] = []
        if any(w in lower for w in ["faceid", "password", "login", "2fa", "auth", "sign in"]):
            topics.append(TopicSlug.LOGIN_AUTH)
        if any(w in lower for w in ["price", "pricing", "tier", "expensive", "cost"]):
            topics.append(TopicSlug.BILLING_PRICING)
        if any(w in lower for w in ["cancel", "subscription", "renew"]):
            topics.append(TopicSlug.SUBSCRIPTION_CANCELLATION)
        if any(w in lower for w in ["refund", "charged", "double-charge", "payment", "card"]):
            topics.append(TopicSlug.REFUND_PAYMENT)
        if any(w in lower for w in ["crash", "freezes", "exits", "shut down", "blank screen"]):
            topics.append(TopicSlug.APP_CRASH)
        if any(w in lower for w in ["slow", "lag", "latency", "stutter", "snappy", "speed"]):
            topics.append(TopicSlug.SLOW_PERFORMANCE)
        if any(w in lower for w in ["battery", "warm", "drain", "heat"]):
            topics.append(TopicSlug.BATTERY_DRAIN)
        if any(w in lower for w in ["offline", "sync", "wifi", "wiped"]):
            topics.append(TopicSlug.OFFLINE_SYNC)
        if any(w in lower for w in ["ui", "navigation", "layout", "menu", "redesign"]):
            topics.append(TopicSlug.UI_NAVIGATION)
        if any(w in lower for w in ["dark mode", "contrast", "theme"]):
            topics.append(TopicSlug.DARK_MODE_DESIGN)
        if any(w in lower for w in ["search", "filter", "query"]):
            topics.append(TopicSlug.SEARCH_RETRIEVAL)
        if any(w in lower for w in ["export", "pdf", "csv", "import"]):
            topics.append(TopicSlug.EXPORT_IMPORT)
        if any(w in lower for w in ["slack", "webhook", "zapier", "api", "integration"]):
            topics.append(TopicSlug.INTEGRATIONS_API)
        if any(w in lower for w in ["support", "agent", "ticket", "reply", "unresponsive"]):
            topics.append(TopicSlug.CUSTOMER_SUPPORT)
        if any(w in lower for w in ["docs", "documentation", "guide"]):
            topics.append(TopicSlug.DOCUMENTATION)
        if any(w in lower for w in ["notification", "push", "spam"]):
            topics.append(TopicSlug.NOTIFICATION_OVERLOAD)
            
        if not topics:
            topics.append(TopicSlug.OTHER)
        # Cap at 5
        topics = topics[:5]

        # 2. Sentiment inference
        pos_words = ["love", "great", "blazing", "fast", "snappy", "awesome", "stellar", "clean", "intuitive", "works fine", "flawlessly"]
        neg_words = ["fail", "horrible", "crash", "worst", "unusable", "terrible", "stutter", "drain", "broken", "scam", "ruined", "cancelled", "laggy"]
        
        has_pos = any(w in lower for w in pos_words)
        has_neg = any(w in lower for w in neg_words) or "unacceptable" in lower or "never works" in lower
        
        if has_pos and has_neg:
            sentiment = Sentiment.mixed
        elif has_neg or "oh brilliant" in lower or "pure genius" in lower:  # Sarcasm
            sentiment = Sentiment.negative
        elif has_pos:
            sentiment = Sentiment.positive
        elif "needs" in lower or "please add" in lower:
            sentiment = Sentiment.neutral
        else:
            sentiment = Sentiment.neutral

        return sentiment, topics

    async def complete(
        self,
        *,
        system: str,
        user: str,
        schema: type[BaseModel] | None = None,
        model: str = "gpt-4o-mini",
        temperature: float = 0.0,
        max_tokens: int = 1024,
        purpose: str = "enrich",
        trace_id: str = "trace-test"
    ) -> LLMResult:
        self.call_count += 1
        
        # Check simulated failure
        if self.fail_next:
            self.fail_next = False
            return LLMResult(
                text="Internal server error simulating 500",
                parsed=None,
                input_tokens=100,
                output_tokens=10,
                cached_input_tokens=0,
                latency_ms=self.latency_ms,
                cost_usd=Decimal("0.00001"),
                model=model,
                request_id=f"req-err-{self.call_count}"
            )

        # 1. If Q&A / Answer purpose
        if purpose == "answer":
            # Extract review IDs present in user context
            ids = re.findall(r"\[R(\d+)\]", user)
            cited_ids = ids[:2] if ids else ["1"]
            citations_str = "".join(f"[R{cid}]" for cid in cited_ids)
            answer_text = f"Based on customer feedback, multiple users experienced this issue {citations_str}."
            raw_response = json.dumps({
                "answer": answer_text,
                "citations": [{"review_id": int(cid), "confidence": 0.95} for cid in cited_ids],
                "confidence": 0.92,
                "caveats": []
            })
            return LLMResult(
                text=raw_response,
                parsed=None,
                input_tokens=len(user) // 4,
                output_tokens=len(raw_response) // 4,
                cached_input_tokens=0,
                latency_ms=self.latency_ms,
                cost_usd=Decimal("0.0005"),
                model=model,
                request_id=f"req-ans-{self.call_count}"
            )

        # 2. If Enrichment purpose
        # Extract reviews from <review id="...">...</review>
        review_matches = re.findall(r'<review id="(\d+)">(.*?)</review>', user, re.DOTALL)
        
        enrichments = []
        for rid_str, text in review_matches:
            rid = int(rid_str)
            sentiment, topics = self._infer_sentiment_and_topics(text)
            summary = f"Customer reported {sentiment.value} feedback regarding {topics[0].value.replace('_', ' ')}."
            if len(summary) < 15:
                summary = summary + " Detailed assessment provided."
            enrichments.append(ReviewEnrichment(
                review_id=rid,
                sentiment=sentiment,
                topics=topics,
                summary=summary[:280],
                confidence=0.92
            ))

        # Check if single or batch
        if schema == BatchEnrichment or len(enrichments) > 1:
            batch_obj = BatchEnrichment(items=enrichments)
            raw_json_str = batch_obj.model_dump_json()
            parsed_obj = batch_obj
        elif schema == ReviewEnrichment and enrichments:
            raw_json_str = enrichments[0].model_dump_json()
            parsed_obj = enrichments[0]
        else:
            raw_json_str = json.dumps([e.model_dump() for e in enrichments])
            parsed_obj = None

        in_tok = len(system + user) // 4
        out_tok = len(raw_json_str) // 4
        cost = calculate_llm_cost(model, in_tok, out_tok, 0)

        return LLMResult(
            text=raw_json_str,
            parsed=parsed_obj,
            input_tokens=in_tok,
            output_tokens=out_tok,
            cached_input_tokens=0,
            latency_ms=self.latency_ms,
            cost_usd=cost,
            model=model,
            request_id=f"req-{self.call_count}"
        )
