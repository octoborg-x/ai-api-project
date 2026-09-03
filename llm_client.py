import os
import json
from dotenv import load_dotenv
from openai import AsyncOpenAI
from typing import AsyncGenerator, TYPE_CHECKING

if TYPE_CHECKING:
    from app import TicketExtraction

load_dotenv()

client = AsyncOpenAI(
    api_key=os.environ["OPENROUTER_API_KEY"],
    base_url="https://openrouter.ai/api/v1",
)

MODEL = os.environ["MODEL_NAME"]


async def ask(prompt: str) -> dict:
    response = await client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    return {
        "response": response.choices[0].message.content,
        "prompt_tokens": response.usage.prompt_tokens,
        "completion_tokens": response.usage.completion_tokens,
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
