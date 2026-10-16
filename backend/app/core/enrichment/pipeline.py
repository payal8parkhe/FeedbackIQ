import time
from dataclasses import dataclass
from decimal import Decimal
from typing import Any
from jinja2 import Template
from pathlib import Path

from app.config import settings
from app.core.enrichment.batcher import Batcher
from app.core.enrichment.cache import TwoTierCache, compute_cache_key
from app.core.enrichment.parser import EnrichmentParser
from app.core.embeddings.base import Embedder
from app.core.embeddings.local import LocalEmbedder
from app.core.llm.base import LLMClient
from app.core.preprocess.clean import normalize_text
from app.core.preprocess.pii import mask_pii
from app.core.preprocess.truncate import truncate_review
from app.core.preprocess.lang import detect_language
from app.domain.models import Review, Enrichment
from app.domain.schemas import ReviewEnrichment, BatchEnrichment
from app.domain.taxonomy import CONTROLLED_TAXONOMY, TAXONOMY_VERSION

@dataclass
class ChunkReport:
    total_reviews: int
    cache_hits: int
    llm_processed: int
    valid_count: int
    repaired_count: int
    failed_count: int
    total_cost_usd: Decimal
    total_input_tokens: int
    total_output_tokens: int
    elapsed_ms: int
    results: dict[int, ReviewEnrichment]


class EnrichmentPipeline:
    def __init__(
        self,
        llm_client: LLMClient,
        embedder: Embedder | None = None,
        cache: TwoTierCache | None = None,
        model: str = "gpt-4o-mini",
        prompt_version: str = "v1",
        taxonomy_version: str = TAXONOMY_VERSION,
        batch_size: int = 15,
        naive_mode: bool = False,  # If True, runs 1 review per call for baseline
    ):
        self.llm = llm_client
        self.embedder = embedder or LocalEmbedder()
        self.cache = cache or TwoTierCache()
        self.model = model
        self.prompt_version = prompt_version
        self.taxonomy_version = taxonomy_version
        self.batch_size = batch_size
        self.naive_mode = naive_mode
        self.batcher = Batcher(max_items=batch_size, max_tokens=settings.BATCH_MAX_TOKENS)
        self.parser = EnrichmentParser()

        # Load jinja prompt template
        prompt_path = Path(__file__).resolve().parent.parent / "prompts" / f"enrich_{prompt_version}.jinja"
        if prompt_path.exists():
            self.template = Template(prompt_path.read_text(encoding="utf-8"))
        else:
            self.template = Template("Review: {{ reviews }}")

    def preprocess(self, raw_text: str, rid: int, source: str = "appstore", rating: int | None = None) -> Review:
        normalized = normalize_text(raw_text)
        masked = mask_pii(normalized)
        truncated = truncate_review(masked, max_chars=settings.MAX_REVIEW_CHARS)
        lang = detect_language(truncated)
        
        import hashlib
        h = hashlib.sha256(f"{normalized}{source}".encode("utf-8")).hexdigest()
        
        from datetime import datetime
        return Review(
            id=rid,
            source=source,
            content_hash=h,
            raw_text=raw_text,
            clean_text=truncated,
            language=lang,
            rating=rating,
            created_at=datetime.utcnow()
        )

    async def _repair_single_item(self, review: Review, trace_id: str) -> ReviewEnrichment | None:
        """Single-item retry repair prompt appending schema feedback."""
        system_repair = (
            "You are a structured data extractor. Return a single JSON object matching ReviewEnrichment.\n"
            "Format: {\"review_id\": <id>, \"sentiment\": \"positive|neutral|negative|mixed\", "
            "\"topics\": [\"<valid_slug>\"], \"summary\": \"<10-300 chars>\", \"confidence\": 0.9}"
        )
        user_repair = f"<review id=\"{review.id}\">{review.clean_text}</review>"
        
        try:
            res = await self.llm.complete(
                system=system_repair,
                user=user_repair,
                schema=ReviewEnrichment,
                model=self.model,
                temperature=0.0,
                purpose="repair",
                trace_id=trace_id
            )
            parsed_list = self.parser.parse_raw(res.text)
            if parsed_list:
                return self.parser.validate_item(parsed_list[0], original_text=review.clean_text)
            return None
        except Exception:
            return None

    async def enrich_chunk(self, reviews: list[Review], trace_id: str = "trace-chunk") -> ChunkReport:
        start_time = time.perf_counter()
        
        total_reviews = len(reviews)
        cache_hits = 0
        total_cost = Decimal("0.0")
        total_in_tok = 0
        total_out_tok = 0
        repaired_count = 0
        failed_count = 0

        # 1. Compute Cache Keys
        keys = {r.id: compute_cache_key(self.model, self.prompt_version, self.taxonomy_version, r.clean_text) for r in reviews}
        cached_results = await self.cache.get_many(list(keys.values()))

        results: dict[int, ReviewEnrichment] = {}
        misses: list[Review] = []

        for r in reviews:
            k = keys[r.id]
            if k in cached_results:
                validated = self.parser.validate_item(cached_results[k], original_text=r.clean_text)
                if validated:
                    results[r.id] = validated
                    cache_hits += 1
                    continue
            misses.append(r)

        # 2. Process Misses
        if misses:
            # If naive mode: 1 review per call. Else: use batcher
            batches = [[r] for r in misses] if self.naive_mode else self.batcher.pack(misses)

            for batch in batches:
                rendered_user = self.template.render(
                    taxonomy=CONTROLLED_TAXONOMY,
                    reviews=batch
                )
                system_prompt = (
                    "You are FeedbackIQ enrichment model. Extract structured feedback strictly obeying the taxonomy and JSON schema."
                )

                schema_to_use = ReviewEnrichment if len(batch) == 1 else BatchEnrichment
                
                resp = await self.llm.complete(
                    system=system_prompt,
                    user=rendered_user,
                    schema=schema_to_use,
                    model=self.model,
                    temperature=0.0,
                    purpose="enrich",
                    trace_id=trace_id
                )

                total_cost += resp.cost_usd
                total_in_tok += resp.input_tokens
                total_out_tok += resp.output_tokens

                expected_ids = [r.id for r in batch]
                texts_by_id = {r.id: r.clean_text for r in batch}
                ok_map, bad_ids = self.parser.split_batch(
                    resp.parsed or resp.text,
                    expected_ids=expected_ids,
                    original_texts_by_id=texts_by_id
                )
                results.update(ok_map)

                # 3. Per-item repair for bad_ids
                for bad_id in bad_ids:
                    bad_review = next(r for r in batch if r.id == bad_id)
                    repaired = await self._repair_single_item(bad_review, trace_id=trace_id)
                    if repaired:
                        results[bad_id] = repaired
                        repaired_count += 1
                    else:
                        failed_count += 1

            # 4. Save to cache
            cache_to_set = {
                keys[rid]: results[rid].model_dump()
                for rid in results
                if rid in keys
            }
            if cache_to_set:
                await self.cache.set_many(cache_to_set)

        elapsed_ms = int((time.perf_counter() - start_time) * 1000)

        return ChunkReport(
            total_reviews=total_reviews,
            cache_hits=cache_hits,
            llm_processed=len(misses),
            valid_count=len(results),
            repaired_count=repaired_count,
            failed_count=failed_count,
            total_cost_usd=total_cost,
            total_input_tokens=total_in_tok,
            total_output_tokens=total_out_tok,
            elapsed_ms=elapsed_ms,
            results=results
        )
