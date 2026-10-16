import json
import re
from typing import Any
from pydantic import ValidationError
from app.domain.schemas import ReviewEnrichment, BatchEnrichment
from app.domain.taxonomy import VALID_TOPIC_SLUGS

class EnrichmentParser:
    """
    Robust JSON parser and multi-stage validation ladder.
    Never fails the whole batch for one bad item.
    """

    @staticmethod
    def clean_json_string(text: str) -> str:
        """Strip markdown fences, leading/trailing conversational text."""
        text = text.strip()
        # Remove ```json ... ```
        fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        if fence_match:
            return fence_match.group(1).strip()
        
        # If starts with [ or {, isolate balanced structure
        start_bracket = text.find("[")
        start_brace = text.find("{")
        if start_bracket != -1 and (start_brace == -1 or start_bracket < start_brace):
            end_bracket = text.rfind("]")
            if end_bracket != -1:
                return text[start_bracket:end_bracket + 1]
        elif start_brace != -1:
            end_brace = text.rfind("}")
            if end_brace != -1:
                return text[start_brace:end_brace + 1]
        return text

    def parse_raw(self, raw_text: str) -> list[dict[str, Any]]:
        cleaned = self.clean_json_string(raw_text)
        try:
            parsed = json.loads(cleaned)
            if isinstance(parsed, dict):
                if "items" in parsed and isinstance(parsed["items"], list):
                    return parsed["items"]
                return [parsed]
            elif isinstance(parsed, list):
                return parsed
            return []
        except Exception:
            return []

    def validate_item(self, item_dict: dict[str, Any], original_text: str = "") -> ReviewEnrichment | None:
        """Validate single item against Pydantic schema and semantic invariants."""
        try:
            # 1. Pydantic schema validation
            enrichment = ReviewEnrichment.model_validate(item_dict)
            
            # 2. Invariant checks
            # Invariant A: Topics must all be valid slugs
            for t in enrichment.topics:
                if t not in VALID_TOPIC_SLUGS:
                    return None
            
            # Invariant B: Summary must not be verbatim copy of long review
            if original_text and len(original_text) > 100:
                if enrichment.summary.strip().lower() == original_text.strip().lower():
                    return None
            
            return enrichment
        except (ValidationError, Exception):
            return None

    def split_batch(
        self,
        raw_or_parsed: str | Any,
        expected_ids: list[int],
        original_texts_by_id: dict[int, str] | None = None
    ) -> tuple[dict[int, ReviewEnrichment], list[int]]:
        """
        Split items into valid (ok) and failed (bad) items.
        Returns:
            ok_map: {review_id: ReviewEnrichment}
            bad_ids: list[review_id] needing repair
        """
        original_texts_by_id = original_texts_by_id or {}
        items_list: list[dict[str, Any]] = []

        if isinstance(raw_or_parsed, BatchEnrichment):
            items_list = [item.model_dump() for item in raw_or_parsed.items]
        elif isinstance(raw_or_parsed, ReviewEnrichment):
            items_list = [raw_or_parsed.model_dump()]
        elif isinstance(raw_or_parsed, str):
            items_list = self.parse_raw(raw_or_parsed)
        elif isinstance(raw_or_parsed, list):
            items_list = raw_or_parsed

        ok_map: dict[int, ReviewEnrichment] = {}
        for item in items_list:
            if not isinstance(item, dict):
                continue
            rid = item.get("review_id")
            if rid in expected_ids:
                orig_text = original_texts_by_id.get(rid, "")
                validated = self.validate_item(item, original_text=orig_text)
                if validated:
                    ok_map[rid] = validated

        # Any expected_id not successfully validated goes to bad_ids for repair
        bad_ids = [rid for rid in expected_ids if rid not in ok_map]
        return ok_map, bad_ids
