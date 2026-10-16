class FeedbackIQError(Exception):
    """Base exception for all FeedbackIQ domain errors."""
    def __init__(self, message: str, code: str = "INTERNAL_ERROR"):
        super().__init__(message)
        self.message = message
        self.code = code


class ValidationError(FeedbackIQError):
    def __init__(self, message: str):
        super().__init__(message, code="SCHEMA_VALIDATION_ERROR")


class LLMClientError(FeedbackIQError):
    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message, code="LLM_PROVIDER_ERROR")
        self.status_code = status_code


class RateLimitExceededError(LLMClientError):
    def __init__(self, message: str = "LLM rate limit reached"):
        super().__init__(message, status_code=429)
        self.code = "RATE_LIMIT_EXCEEDED"


class CircuitBreakerOpenError(FeedbackIQError):
    def __init__(self, message: str = "Circuit breaker is OPEN"):
        super().__init__(message, code="CIRCUIT_BREAKER_OPEN")


class BudgetExceededError(FeedbackIQError):
    def __init__(self, message: str = "Daily USD budget exceeded"):
        super().__init__(message, code="BUDGET_EXCEEDED")


class CitationVerificationError(FeedbackIQError):
    def __init__(self, message: str):
        super().__init__(message, code="CITATION_VERIFICATION_FAILED")
