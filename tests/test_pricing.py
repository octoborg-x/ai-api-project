from app.telemetry import metrics as pricing


def test_free_model_cost_is_zero():
    assert pricing.calculate_cost("cohere/north-mini-code:free", 1000, 500) == 0.0


def test_known_paid_model_uses_input_and_output_rates(monkeypatch):
    monkeypatch.setitem(
        pricing.MODEL_PRICING, "test/model", {"input": 2.0, "output": 4.0}
    )
    assert pricing.calculate_cost("test/model", 1000, 500) == 0.004


def test_unknown_model_fails_safe_to_zero_cost():
    assert pricing.calculate_cost("unknown/model", 1234, 5678) == 0.0
