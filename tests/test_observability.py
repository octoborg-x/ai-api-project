import json
import logging

from app.telemetry.logging import JsonFormatter
from app.telemetry.metrics import record_call


def test_json_formatter_emits_structured_fields(caplog):
    logger = logging.getLogger("test.observability")

    with caplog.at_level(logging.INFO, logger=logger.name):
        logger.info(
            "llm call",
            extra={
                "event": "llm.call",
                "model": "test/model",
                "tier": "balanced",
                "latency_ms": 1234.0,
                "input_tokens": 500,
                "output_tokens": 200,
                "total_tokens": 700,
                "cost_usd": 0.002,
                "status": "success",
            },
        )

    payload = json.loads(JsonFormatter().format(caplog.records[-1]))
    assert payload["event"] == "llm.call"
    assert payload["model"] == "test/model"
    assert payload["input_tokens"] == 500
    assert payload["output_tokens"] == 200
    assert payload["total_tokens"] == 700
    assert payload["status"] == "success"
    assert "request_id" in payload
    assert "trace_id" in payload


def test_record_call_does_not_log_prompt_contents(caplog):
    logger = logging.getLogger("app.telemetry.metrics")

    with caplog.at_level(logging.INFO, logger=logger.name):
        record_call(
            model="test/model",
            tier="cheap",
            prompt_tokens=10,
            completion_tokens=5,
            latency_ms=25.5,
            status="success",
        )

    message = caplog.records[-1].getMessage()
    assert "secret customer prompt" not in message
    assert "input_tokens=10" not in message
