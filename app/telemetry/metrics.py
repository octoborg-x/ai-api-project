# Prices per 1M tokens, in USD. Update if you switch models.
import logging

# Free models are $0 — but structure this to work for paid models too.
MODEL_PRICING = {
    "cohere/north-mini-code:free": {"input": 0.0, "output": 0.0},
}


def calculate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    pricing = MODEL_PRICING.get(model, {"input": 0.0, "output": 0.0})
    input_cost = (prompt_tokens / 1_000_000) * pricing["input"]
    output_cost = (completion_tokens / 1_000_000) * pricing["output"]
    return round(input_cost + output_cost, 6)


logger = logging.getLogger(__name__)


def record_call(
    *,
    model: str,
    tier: str,
    prompt_tokens: int,
    completion_tokens: int,
    latency_ms: float,
    success: bool,
) -> None:
    """Emit one structured telemetry event without storing prompt contents."""
    logger.info(
        "llm_call model=%s tier=%s prompt_tokens=%d completion_tokens=%d "
        "total_tokens=%d latency_ms=%.2f cost_usd=%.6f success=%s",
        model,
        tier,
        prompt_tokens,
        completion_tokens,
        prompt_tokens + completion_tokens,
        latency_ms,
        calculate_cost(model, prompt_tokens, completion_tokens),
        success,
    )
