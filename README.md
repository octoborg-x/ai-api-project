# AI API Project

Part of an 8-week AI Engineer upskilling plan. Week 1: Python + LLM APIs.

## What this is

A Python backend that connects to an LLM via OpenRouter (OpenAI-compatible
API), exposed through FastAPI. Supports plain chat, streaming responses,
and structured JSON extraction with schema validation.

## Stack

- Python 3.12
- OpenRouter (OpenAI SDK, compatible endpoint)
- python-dotenv

## Setup

\`\`\`bash
python3 -m venv venv
source venv/bin/activate
pip install openai python-dotenv
\`\`\`

Create a `.env` file:
\`\`\`
OPENROUTER_API_KEY=your_key_here
MODEL_NAME=cohere/north-mini-code:free
\`\`\`

## Run
See [commands reference](cmd_reference.md#L21)

## Progress log
- **Day 1**: Basic API client working. Model and API key externalized
  to `.env` (no hardcoded values, fail-fast if missing). Inspected raw
  response object and token usage fields.

- **Day 2**: Sync streaming implemented (`stream=True`, iterate chunks).
  Converted to async using `AsyncOpenAI` + `async for` — needed for
  handling concurrent users in FastAPI (Day 3+).

- **Day 3**: Wrapped LLM client in FastAPI. Added `/health` and `/chat`
  endpoints with Pydantic request/response validation. Swagger docs
  auto-generated at `/docs`.

- **Day 4**: Added streaming endpoint `/chat/stream` using FastAPI's
  StreamingResponse + an async generator (`ask_stream`). Tested with
  `curl -N`. Introduced to SSE (`text/event-stream`) concept.

- **Day 5**: Added structured JSON output extraction. `TicketExtraction`
  Pydantic model with `Literal`-constrained fields (category, urgency,
  sentiment) to force the LLM into a fixed schema. Handled two failure
  modes: malformed JSON from the model (markdown code fences, extra
  text) and schema violations (Pydantic validation). New endpoint:
  `POST /extract-ticket`.

