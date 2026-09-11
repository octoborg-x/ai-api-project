# AI API Project

A production-style FastAPI backend for LLM integration — chat, streaming,
structured extraction, retry handling, cost tracking, and a Next.js AI Engineering Console.

## Monolith layout

The backend and frontend intentionally live in the same repository and are developed as one application boundary:

- `app/` — FastAPI backend and domain/infrastructure adapters
- `web/` — Next.js/React frontend
- `evals/` — evaluation datasets and runners
- `tests/` — backend tests

## Development Setup

To enable automatic linting and formatting on every commit:

```bash
pip install pre-commit
pre-commit install
```

In development, run FastAPI on port 8000 and Next.js on port 3000. Next.js proxies `/api/backend/*` to `BACKEND_URL`, keeping browser calls same-origin while preserving the backend boundary.

## Frontend

```bash
cd web
cp .env.example .env.local
npm install
npm run dev
```

Open http://localhost:3000.

The Week 1 console exposes:

- streaming playground
- three configured model tiers
- custom OpenAI-compatible provider UX boundary
- model comparison indices
- test suite indices
- evaluation dataset indices
- bearer-token auth UI
- rate-limit status
- structured observability/log readiness
- environment/configuration view

The UI intentionally does not calculate domain metrics or invent benchmark values. It is a thin presentation/control layer over backend APIs.

## Backend

Existing Python setup and `app/main.py` endpoints:

- `GET /health`
- `POST /chat`
- `POST /chat/stream`
- `POST /extract-ticket`

## Existing backend capabilities

- Single-turn chat with token/cost tracking
- Streaming responses
- Structured JSON extraction
- Retry logic with exponential backoff
- Differentiated 429/504/502/500 errors
- Deterministic cheap/balanced/powerful routing
- Per-call model/token/latency/cost/success telemetry
- Bearer-token authentication on `POST /chat`
- Process-local rate limiting and `Retry-After`

## Model routing

Routing is deterministic and adds no extra LLM call.

| Request | Tier |
|---|---|
| Classification / extraction | `cheap` |
| Normal chat | `balanced` |
| Complex reasoning, architecture, debugging, long prompts | `powerful` |

Configure:

```env
MODEL_NAME=your_existing_free_model
MODEL_CHEAP=your_free_cheap_model
MODEL_BALANCED=your_free_balanced_model
MODEL_POWERFUL=your_free_powerful_model
```
