# Model Routing Performance Testing

This guide explains how to test the model router as an AI infrastructure component and produce useful performance statistics.

## 1. What to test

Do not only test whether the router selects the expected tier. Measure whether the routing decision produces a useful quality/performance trade-off.

Test these dimensions:

- Routing distribution
- Model actually selected
- Success/failure rate
- Prompt tokens
- Completion tokens
- Total tokens
- Latency
- Estimated cost
- Response quality / task accuracy

For free OpenRouter models, the immediate estimated cost may be $0.00, but keep cost measurement enabled so the system can later support paid models without changing the observability design.

## 2. Routing test matrix

Start with a controlled set of prompts.

| Prompt type | Example | Expected tier |
|---|---|---|
| Classification | Classify this ticket as billing or technical | cheap |
| Extraction | Extract the category and urgency | cheap |
| Normal chat | What is FastAPI? | balanced |
| Normal explanation | Explain how retries work | balanced |
| Complex reasoning | Design a production RAG architecture | powerful |
| Complex debugging | Debug this distributed system and explain the trade-offs | powerful |

The exact model IDs should remain configurable because OpenRouter free-model availability can change.

## 3. Run a benchmark

Create a benchmark with approximately 50–100 prompts covering:

- simple classification
- structured extraction
- normal questions
- coding questions
- debugging
- architecture/system design
- reasoning and comparison tasks

Run every prompt through the same application routing path.

For each request, record data equivalent to:

```json
{
  "request_id": "req_001",
  "task": "chat",
  "route": "balanced",
  "model": "provider/model:free",
  "success": true,
  "prompt_tokens": 120,
  "completion_tokens": 250,
  "total_tokens": 370,
  "latency_ms": 1830,
  "estimated_cost_usd": 0
}
```

Do not store the user's prompt in telemetry just to measure performance.

## 4. Statistics to calculate

### Routing distribution

Example:

```text
Total requests: 100

Cheap:       32
Balanced:    51
Powerful:    17
```

Calculate:

```text
route_percentage = route_requests / total_requests * 100
```

### Reliability

For each tier calculate:

```text
success_rate = successful_requests / total_requests * 100
failure_rate = failed_requests / total_requests * 100
```

Example:

| Tier | Requests | Success rate |
|---|---:|---:|
| cheap | 32 | 100% |
| balanced | 51 | 98% |
| powerful | 17 | 100% |

### Latency

Calculate at least:

- average latency
- median latency
- P95 latency

P95 is especially useful because average latency can hide slow requests.

Example:

| Tier | Avg latency | P95 latency |
|---|---:|---:|
| cheap | 1.2 s | 2.1 s |
| balanced | 1.8 s | 3.4 s |
| powerful | 3.1 s | 5.2 s |

### Token usage

Calculate:

- average input tokens
- average output tokens
- total tokens
- average total tokens per request

Example:

| Tier | Input | Output | Total |
|---|---:|---:|---:|
| cheap | 4,200 | 3,100 | 7,300 |
| balanced | 8,900 | 11,200 | 20,100 |
| powerful | 5,400 | 9,800 | 15,200 |

### Cost

Calculate estimated cost from the model and token usage.

For free models:

```text
estimated_cost_usd = 0
```

Keep the calculation in the system anyway. When a paid model is introduced, the same telemetry can immediately show the financial impact.

## 5. Measure quality, not just infrastructure metrics

A router is useful only if its decisions maintain acceptable answer quality.

Compare the results by tier:

| Tier | Accuracy | Avg latency | Avg tokens |
|---|---:|---:|---:|
| cheap | 82% | 1.2 s | 230 |
| balanced | 91% | 1.8 s | 370 |
| powerful | 94% | 3.1 s | 894 |

These numbers are illustrative. Your benchmark must produce the real values.

The important question is:

> Does routing improve the quality/performance trade-off compared with sending every request to one model?

## 6. Baseline comparison

Run the same benchmark in two modes.

### Baseline

Send every request to one model:

```text
100 prompts → one model
```

### Routed

Send every request through the router:

```text
100 prompts
     ↓
  router
  ↙ ↓ ↘
cheap balanced powerful
```

Compare:

| Metric | Baseline | Routed |
|---|---:|---:|
| Success rate | ... | ... |
| Avg latency | ... | ... |
| P95 latency | ... | ... |
| Total tokens | ... | ... |
| Estimated cost | ... | ... |
| Quality score | ... | ... |

This is the experiment that demonstrates whether the routing system actually provides value.

## 7. Recommended dashboard

A useful first dashboard can show:

```text
AI MODEL ROUTER
────────────────────────────────

Requests             100
Success rate          99%
Avg latency          1.94 s
P95 latency           4.20 s
Total tokens        42,600
Estimated cost       $0.00


ROUTING DISTRIBUTION
────────────────────────────────

Cheap                 32%
Balanced              51%
Powerful              17%


LATENCY BY TIER
────────────────────────────────

Cheap                 1.2 s
Balanced              1.8 s
Powerful              3.1 s
```

A simple `GET /metrics` endpoint can expose aggregated statistics for a dashboard later.

Example response:

```json
{
  "total_requests": 100,
  "success_rate": 0.99,
  "routes": {
    "cheap": {
      "requests": 32,
      "success_rate": 1.0,
      "avg_latency_ms": 1200,
      "avg_tokens": 228
    },
    "balanced": {
      "requests": 51,
      "success_rate": 0.98,
      "avg_latency_ms": 1800,
      "avg_tokens": 394
    },
    "powerful": {
      "requests": 17,
      "success_rate": 1.0,
      "avg_latency_ms": 3100,
      "avg_tokens": 894
    }
  }
}
```

## 8. Important validation

Before trusting the dashboard, verify that token usage is actually returned by OpenRouter and propagated through the evaluation layer.

If token fields are missing or reported as zero, latency statistics may still be valid while token and cost statistics are not.

Never present missing token data as zero usage unless the provider explicitly reported zero.

## 9. What this demonstrates

A successful experiment gives you more than a model-selection feature.

It demonstrates:

- model routing
- provider abstraction
- observability
- token accounting
- latency measurement
- reliability measurement
- cost tracking
- benchmark design
- baseline comparison
- production-oriented AI infrastructure thinking

The end goal is not simply:

> "I made three models available."

It is:

> "I built a measurable routing system and evaluated its quality, latency, reliability, token usage, and cost trade-offs."
