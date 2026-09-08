"""Free, deterministic model routing for OpenRouter.

The router deliberately does not make a second LLM call to decide which model
to use. It uses the request type and a small complexity heuristic, so routing
itself adds no token cost.
"""

from dataclasses import dataclass
import os
import re


@dataclass(frozen=True)
class RouteDecision:
    tier: str
    model: str
    reason: str


def _model_for(tier: str) -> str:
    configured = os.getenv(f"MODEL_{tier.upper()}")
    if configured:
        return configured

    # Backward-compatible fallback: existing MODEL_NAME remains valid.
    return os.environ["MODEL_NAME"]


def route(task: str, prompt: str) -> RouteDecision:
    """Select a free-model tier without an additional LLM request.

    Task mapping:
    - classification/extraction -> cheap
    - normal chat -> balanced
    - complex reasoning -> powerful
    """
    normalized_task = task.lower().strip()
    text = prompt.lower()

    if normalized_task in {"classification", "extraction"}:
        tier = "cheap"
        reason = "structured classification/extraction task"
    else:
        complexity_markers = (
            "debug",
            "architecture",
            "system design",
            "compare",
            "trade-off",
            "tradeoff",
            "reason",
            "analyze",
            "analyse",
            "step by step",
            "complex",
            "code",
            "refactor",
        )
        long_prompt = len(text) >= 2500
        has_complexity_marker = any(
            re.search(rf"\b{re.escape(marker)}\b", text)
            for marker in complexity_markers
        )

        if long_prompt or has_complexity_marker:
            tier = "powerful"
            reason = "complexity heuristic matched"
        else:
            tier = "balanced"
            reason = "normal chat request"

    return RouteDecision(tier=tier, model=_model_for(tier), reason=reason)
