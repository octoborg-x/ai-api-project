# standard library
import json

# third-party
import logging
import os
import time
from collections.abc import AsyncGenerator

from dotenv import load_dotenv
from openai import APIError, APITimeoutError, AsyncOpenAI, RateLimitError
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

# local
from app.llm.router import route
from app.llm.schemas import TicketExtraction
from app.telemetry.metrics import calculate_cost, record_call

load_dotenv()

client = AsyncOpenAI(
    api_key=os.environ["OPENROUTER_API_KEY"],
    base_url="https://openrouter.ai/api/v1",
    timeout=30.0,  # seconds
)


logger = logging.getLogger(__name__)

llm_retry = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((APITimeoutError, RateLimitError, APIError)),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)


@llm_retry
async def _completion(model: str, messages: list[dict[str, str]]):
    return await client.chat.completions.create(model=model, messages=messages)


@llm_retry
async def ask(prompt: str) -> dict:
    decision = route("chat", prompt)
    started = time.perf_counter()
    success = False
    usage = None

    try:
        response = await _completion(
            decision.model,
            [{"role": "user", "content": prompt}],
        )
        usage = response.usage
        success = True
        return {
            "response": response.choices[0].message.content,
            "model": decision.model,
            "route": decision.tier,
            "prompt_tokens": usage.prompt_tokens,
            "completion_tokens": usage.completion_tokens,
            "estimated_cost_usd": calculate_cost(
                decision.model, usage.prompt_tokens, usage.completion_tokens
            ),
            "latency_ms": round((time.perf_counter() - started) * 1000, 2),
            "success": True,
        }
    finally:
        record_call(
            model=decision.model,
            tier=decision.tier,
            prompt_tokens=getattr(usage, "prompt_tokens", 0) if usage else 0,
            completion_tokens=getattr(usage, "completion_tokens", 0) if usage else 0,
            latency_ms=round((time.perf_counter() - started) * 1000, 2),
            success=success,
        )


async def ask_stream(prompt: str) -> AsyncGenerator[str, None]:
    stream = await client.chat.completions.create(
        model=route("chat", prompt).model,
        messages=[{"role": "user", "content": prompt}],
        stream=True,
    )
    async for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta


@llm_retry
async def extract_ticket_info(message: str) -> TicketExtraction:
    decision = route("extraction", message)
    started = time.perf_counter()
    success = False
    usage = None
    raw = ""

    prompt = f"""Extract structured information from this customer support message.

Respond with ONLY valid JSON, no other text, matching this exact structure:
{{
    "summary": "one sentence summary",
    "category": "billing" | "technical" | "account" | "other",
    "urgency": "low" | "medium" | "high",
    "customer_sentiment": "positive" | "neutral" | "negative"
}}

Customer message: {message}"""

    try:
        response = await _completion(
            decision.model,
            [{"role": "user", "content": prompt}],
        )
        usage = response.usage
        raw = response.choices[0].message.content.strip()

        if raw.startswith(chr(96) * 3):
            raw = raw.strip(chr(96)).removeprefix("json").strip()

        data = json.loads(raw)
        success = True
        return TicketExtraction(**data)
    except (json.JSONDecodeError, ValueError) as exc:
        raise ValueError(f"Model returned invalid structured output: {raw}") from exc
    finally:
        record_call(
            model=decision.model,
            tier=decision.tier,
            prompt_tokens=getattr(usage, "prompt_tokens", 0) if usage else 0,
            completion_tokens=getattr(usage, "completion_tokens", 0) if usage else 0,
            latency_ms=round((time.perf_counter() - started) * 1000, 2),
            success=success,
        )
