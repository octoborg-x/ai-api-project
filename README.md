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
- Swappable model config via environment variables

## Stack
Python · FastAPI · Pydantic · OpenRouter (OpenAI-compatible SDK) · tenacity

## Architecture
Client → FastAPI → LLM Client (retry/timeout wrapper) → OpenRouter → Model

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