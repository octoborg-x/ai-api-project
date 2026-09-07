# Prices per 1M tokens, in USD. Update if you switch models.
# Free models are $0 — but structure this to work for paid models too.
MODEL_PRICING = {
    "cohere/north-mini-code:free": {"input": 0.0, "output": 0.0},
}


def calculate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    pricing = MODEL_PRICING.get(model, {"input": 0.0, "output": 0.0})
    input_cost = (prompt_tokens / 1_000_000) * pricing["input"]
    output_cost = (completion_tokens / 1_000_000) * pricing["output"]
    return round(input_cost + output_cost, 6)
