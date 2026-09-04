# standard library
import os
import json
from typing import AsyncGenerator

# third-party
from dotenv import load_dotenv
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from openai import AsyncOpenAI, APIError, APITimeoutError, RateLimitError

# local
from models import TicketExtraction
from pricing import calculate_cost

load_dotenv()

client = AsyncOpenAI(
    api_key=os.environ["OPENROUTER_API_KEY"],
    base_url="https://openrouter.ai/api/v1",
    timeout=30.0,  # seconds
)

MODEL = os.environ["MODEL_NAME"]


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((APITimeoutError, RateLimitError, APIError)),
    reraise=True,
)
async def ask(prompt: str) -> dict:
    response = await client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    usage = response.usage
    return {
        "response": response.choices[0].message.content,
        "prompt_tokens": response.usage.prompt_tokens,
        "completion_tokens": response.usage.completion_tokens,
        "estimated_cost_usd": calculate_cost(
            MODEL, usage.prompt_tokens, usage.completion_tokens
        ),
    }


async def ask_stream(prompt: str) -> AsyncGenerator[str, None]:
    stream = await client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        stream=True,
    )
    async for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((APITimeoutError, RateLimitError, APIError)),
    reraise=True,
)
async def extract_ticket_info(message: str) -> TicketExtraction:
    prompt = f"""Extract structured information from this customer support message.

Respond with ONLY valid JSON, no other text, matching this exact structure:
{{
    "summary": "one sentence summary",
    "category": "billing" | "technical" | "account" | "other",
    "urgency": "low" | "medium" | "high",
    "customer_sentiment": "positive" | "neutral" | "negative"
}}

Customer message: {message}"""

    response = await client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.choices[0].message.content.strip()

    # Some models wrap JSON in markdown code fences — strip if present
    if raw.startswith("```"):
        raw = raw.strip("`").removeprefix("json").strip()

    try:
        data = json.loads(raw)
        return TicketExtraction(**data)
    except (json.JSONDecodeError, ValueError) as e:
        raise ValueError(f"Model returned invalid structured output: {raw}") from e
