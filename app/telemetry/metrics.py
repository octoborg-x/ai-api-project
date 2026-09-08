# Prices per 1M tokens, in USD. Update if you switch models.
import logging

# Free models are $0 — but structure this to work for paid models too.
MODEL_PRICING = {
    "cohere/north-mini-code:free": {"input": 0.0, "output": 0.0},
}

logger = logging.getLogger(__name__)


def calculate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    pricing = MODEL_PRICING.get(model, {"input": 0.0, "output": 0.0})
    input_cost = (prompt_tokens / 1_000_000) * pricing["input"]
    output_cost = (completion_tokens / 1_000_000) * pricing["output"]
    return round(input_cost + output_cost, 6)


def record_call(
    *,
    model: str,
    tier: str,
    prompt_tokens: int | None,
    completion_tokens: int | None,
    latency_ms: float,
    status: str,
    attempt: int,
) -> None:
    """Emit one structured LLM telemetry event without storing prompt contents."""
    input_tokens = prompt_tokens if prompt_tokens is not None else None
    output_tokens = completion_tokens if completion_tokens is not None else None
    total_tokens = (
        input_tokens + output_tokens
        if input_tokens is not None and output_tokens is not None
        else None
    )
    cost = (
        calculate_cost(model, input_tokens, output_tokens)
        if input_tokens is not None and output_tokens is not None
        else None
    )
    extra = {
        "event": "llm.call",
        "model": model,
        "tier": tier,
        "latency_ms": latency_ms,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
        "cost_usd": cost,
        "status": status,
        "attempt": attempt,
    }
    logger.info("llm call", extra=extra)
