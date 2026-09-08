"""Structured request/trace context and JSON logging helpers."""

import contextvars
import json
import logging
import sys
import uuid
from typing import Any

_request_id = contextvars.ContextVar("request_id", default=None)
_trace_id = contextvars.ContextVar("trace_id", default=None)


def set_request_context(request_id: str | None = None, trace_id: str | None = None):
    rid = request_id or f"req_{uuid.uuid4().hex}"
    tid = trace_id or f"trace_{uuid.uuid4().hex}"
    return _request_id.set(rid), _trace_id.set(tid)


def clear_request_context(tokens) -> None:
    request_token, trace_token = tokens
    _request_id.reset(request_token)
    _trace_id.reset(trace_token)


def get_request_id() -> str:
    return _request_id.get() or f"req_{uuid.uuid4().hex}"


def get_trace_id() -> str:
    return _trace_id.get() or f"trace_{uuid.uuid4().hex}"


class JsonFormatter(logging.Formatter):
    """Render log records as one JSON object per line."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname.lower(),
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": get_request_id(),
            "trace_id": get_trace_id(),
        }
        for key in ("event", "model", "tier", "latency_ms", "input_tokens",
                    "output_tokens", "total_tokens", "cost_usd", "status",
                    "attempt", "error_type"):
            if hasattr(record, key):
                payload[key] = getattr(record, key)
        return json.dumps(payload, separators=(",", ":"))


def configure_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(logging.INFO)
