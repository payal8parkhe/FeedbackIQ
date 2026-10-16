from app.config import settings
from app.core.enrichment.pipeline import EnrichmentPipeline
from app.core.embeddings.local import LocalEmbedder
from app.core.embeddings.hosted import HostedEmbedder
from app.core.llm.fake_client import FakeLLMClient
from app.core.llm.openai_client import OpenAIClient
from app.core.llm.anthropic_client import AnthropicClient
from app.core.qa.answer import AnswerService
from app.db.repositories import global_repository, ReviewRepository

def get_repository() -> ReviewRepository:
    return global_repository

def get_llm_client():
    if settings.LLM_PROVIDER == "openai" and settings.OPENAI_API_KEY:
        return OpenAIClient()
    elif settings.LLM_PROVIDER == "anthropic" and settings.ANTHROPIC_API_KEY:
        return AnthropicClient()
    return FakeLLMClient()

def get_embedder():
    if settings.LLM_PROVIDER == "openai" and settings.OPENAI_API_KEY:
        return HostedEmbedder()
    return LocalEmbedder()

def get_enrichment_pipeline() -> EnrichmentPipeline:
    return EnrichmentPipeline(
        llm_client=get_llm_client(),
        embedder=get_embedder(),
        model=settings.ENRICH_MODEL,
        prompt_version=settings.PROMPT_VERSION
    )

def get_answer_service() -> AnswerService:
    return AnswerService(
        llm_client=get_llm_client(),
        model=settings.ANSWER_MODEL
    )
