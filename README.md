# AI API Project

Part of an 8-week AI Engineer upskilling plan. Week 1: Python + LLM APIs.

## What this is (Day 1)

A minimal Python client that connects to an LLM via the OpenRouter API
(OpenAI-compatible), with environment-based configuration.

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

\`\`\`bash
python main.py
\`\`\`

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
