from app.llm.router import route


def test_extraction_uses_cheap_tier(monkeypatch):
    monkeypatch.setenv("MODEL_NAME", "fallback/model")
    monkeypatch.setenv("MODEL_CHEAP", "cheap/model")
    decision = route("extraction", "classify this ticket")
    assert decision.tier == "cheap"
    assert decision.model == "cheap/model"


def test_normal_chat_uses_balanced_tier(monkeypatch):
    monkeypatch.setenv("MODEL_NAME", "fallback/model")
    monkeypatch.setenv("MODEL_BALANCED", "balanced/model")
    decision = route("chat", "Hello, how are you?")
    assert decision.tier == "balanced"
    assert decision.model == "balanced/model"


def test_complex_chat_uses_powerful_tier(monkeypatch):
    monkeypatch.setenv("MODEL_NAME", "fallback/model")
    monkeypatch.setenv("MODEL_POWERFUL", "powerful/model")
    decision = route(
        "chat",
        "Analyze this system design and compare the architecture trade-offs.",
    )
    assert decision.tier == "powerful"
    assert decision.model == "powerful/model"


def test_router_falls_back_to_existing_model(monkeypatch):
    monkeypatch.setenv("MODEL_NAME", "existing/model")
    monkeypatch.delenv("MODEL_CHEAP", raising=False)
    decision = route("classification", "billing")
    assert decision.model == "existing/model"
