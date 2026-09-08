# AI API Project

A production-style FastAPI backend for LLM integration — chat, streaming,
structured extraction, retry handling, and cost tracking. Built as
Project 1 of an 8-week AI Engineer upskilling plan.

## Features
- Single-turn chat with token/cost tracking
- Streaming responses (SSE-style, chunked)
- Structured JSON extraction with schema validation (Pydantic `Literal` fields)
- Retry logic with exponential backoff on transient failures
- Differentiated error handling (429/504/502/500)
- Deterministic model routing across cheap, balanced, and powerful tiers
- Per-call model, token, latency, cost, and success telemetry
- Swappable model config via environment variables
- Bearer-token authentication on `POST /chat`
- Process-local rate limiting before authentication
- Rate-limit response headers and `Retry-After` handling

## Stack
Python · FastAPI · Pydantic · OpenRouter (OpenAI-compatible SDK) · tenacity

## Architecture
Client → `app.main` → `app.llm.client` → OpenRouter → Model

Application code is organized under `app/`; LLM schemas live in `app/llm/schemas.py`, routing and provider/retry logic in `app/llm/router.py` and `app/llm/client.py`, and cost/telemetry helpers in `app/telemetry/metrics.py`.

Evaluation datasets and generated reports live under `evals/`.

## Setup
[keep your existing setup steps]

## Endpoints
- `GET /health`
- `POST /chat`
- `POST /chat/stream`
- `POST /extract-ticket`

## Design decisions
- Config externalized to `.env`, fails loudly (no silent defaults) if missing
- Retry only on transient errors (timeout, rate limit) — not on 4xx client errors
- Dev tools (black, pylint, pre-commit) kept separate from runtime deps

## Progress log
[keep your daily log — this is good, don't remove it]

## Model routing

Routing is deterministic and adds no extra LLM call.

| Request | Tier |
|---|---|
| Classification / extraction | `cheap` |
| Normal chat | `balanced` |
| Complex reasoning, architecture, debugging, long prompts | `powerful` |

Configure the three OpenRouter models with:

```env
MODEL_NAME=your_existing_free_model
MODEL_CHEAP=your_free_cheap_model
MODEL_BALANCED=your_free_balanced_model
MODEL_POWERFUL=your_free_powerful_model
```

If a tier variable is omitted, it falls back to `MODEL_NAME`, so the existing setup keeps working.

The `/chat` response now exposes the selected tier/model plus prompt tokens, completion tokens, estimated cost, latency, and success. Structured calls emit the same fields through structured logs without storing prompt contents.

Routing tests live in `tests/test_router.py`.
