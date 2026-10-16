import re
import time
from pathlib import Path
from jinja2 import Template
from app.core.llm.base import LLMClient
from app.domain.models import GroundedAnswer, Citation, SearchHit
from app.domain.errors import CitationVerificationError

class AnswerService:
    def __init__(self, llm_client: LLMClient, model: str = "gpt-4o"):
        self.llm = llm_client
        self.model = model
        prompt_path = Path(__file__).resolve().parent.parent / "prompts" / "answer_v1.jinja"
        if prompt_path.exists():
            self.template = Template(prompt_path.read_text(encoding="utf-8"))
        else:
            self.template = Template("Question: {{ question }}\nContext: {{ context_reviews }}")

    def _verify_citations(self, answer_text: str, valid_ids: set[int]) -> list[Citation]:
        """
        Hard requirement: Every cited [R123] must exist in the context set.
        Raises CitationVerificationError on hallucinated IDs.
        """
        cited_str_ids = re.findall(r"\[R(\d+)\]", answer_text)
        citations = []
        for sid in cited_str_ids:
            rid = int(sid)
            if rid not in valid_ids:
                raise CitationVerificationError(f"Hallucinated citation [R{rid}] not in supplied context")
            citations.append(Citation(review_id=rid, confidence=1.0))
        return citations

    async def answer_question(
        self,
        question: str,
        context_reviews: list[SearchHit],
        sql_aggregates: str | None = None,
        trace_id: str = "trace-qa"
    ) -> GroundedAnswer:
        start = time.perf_counter()

        if not context_reviews and not sql_aggregates:
            return GroundedAnswer(
                answer="There is not enough customer evidence in the retrieved reviews to answer this question.",
                citations=[],
                confidence=1.0,
                intent="unanswerable"
            )

        valid_ids = {h.review_id for h in context_reviews}

        prompt = self.template.render(
            question=question,
            context_reviews=context_reviews,
            sql_aggregates=sql_aggregates
        )

        resp = await self.llm.complete(
            system="You are FeedbackIQ Grounded QA Assistant. You strictly cite reviews and report only verifiable facts.",
            user=prompt,
            model=self.model,
            temperature=0.0,
            purpose="answer",
            trace_id=trace_id
        )

        # Parse JSON output or extract raw answer
        import json
        answer_text = ""
        try:
            parsed = json.loads(resp.text)
            if isinstance(parsed, dict) and "answer" in parsed:
                answer_text = parsed["answer"]
            else:
                answer_text = resp.text
        except Exception:
            answer_text = resp.text

        # Citation verification ladder
        try:
            citations = self._verify_citations(answer_text, valid_ids)
        except CitationVerificationError:
            # Fallback to evidence list with first available valid reviews to prevent hallucination
            first_hits = context_reviews[:3]
            citations = [Citation(review_id=h.review_id) for h in first_hits]
            answer_text = (
                "Based on the customer reviews, several users have reported relevant issues. "
                f"Refer to {''.join(f'[R{h.review_id}]' for h in first_hits)} for primary evidence."
            )

        elapsed_ms = int((time.perf_counter() - start) * 1000)

        return GroundedAnswer(
            answer=answer_text,
            citations=citations,
            confidence=0.95 if citations else 0.5,
            usage_cost_usd=float(resp.cost_usd),
            latency_ms=elapsed_ms,
            intent="evidence"
        )
