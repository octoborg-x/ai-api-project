#!/usr/bin/env python3
"""Run the Week 1 LLM evaluation suites against the local API."""
from __future__ import annotations

import argparse
import json
import math
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
EVALS = ROOT / "evals"
RESULTS = EVALS / "results"
RESULTS.mkdir(exist_ok=True)


def post_json(url: str, payload: dict[str, Any], timeout: float = 45.0):
    started = time.perf_counter()
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode()
            status = response.status
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode(errors="replace")
        status = exc.code
    except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
        return None, {"error": str(exc)}, (time.perf_counter() - started) * 1000

    elapsed = (time.perf_counter() - started) * 1000
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        data = {"raw": raw}
    return status, data, elapsed


def contains_all(text: str, items: list[str]) -> bool:
    lowered = text.lower()
    return all(item.lower() in lowered for item in items)


def contains_none(text: str, items: list[str]) -> bool:
    lowered = text.lower()
    return not any(item.lower() in lowered for item in items)


def evaluate_chat(case: dict[str, Any], data: dict[str, Any], status: int | None):
    if status != 200 or "response" not in data:
        return False, {"outcome": "api_error", "status": status}
    answer = str(data["response"])
    expected = case["expected"]
    concepts_ok = contains_all(answer, expected.get("must_contain_concepts", []))
    forbidden_ok = contains_none(answer, expected.get("must_not_contain", []))
    passed = concepts_ok and forbidden_ok
    return passed, {
        "outcome": "pass" if passed else "model_failure",
        "concepts_ok": concepts_ok,
        "forbidden_ok": forbidden_ok,
    }


def evaluate_extraction(
    case: dict[str, Any], data: dict[str, Any], status: int | None
):
    if status != 200:
        return False, {"outcome": "api_error", "status": status}
    required = {"summary", "category", "urgency", "customer_sentiment"}
    schema_valid = required.issubset(data) and all(
        isinstance(data[field], str) for field in required
    )
    enums_valid = (
        data.get("category") in {"billing", "technical", "account", "other"}
        and data.get("urgency") in {"low", "medium", "high"}
        and data.get("customer_sentiment")
        in {"positive", "neutral", "negative"}
    )
    expected = case["expected"]
    summary_ok = contains_all(
        str(data.get("summary", "")), expected["summary_keywords"]
    )
    exact_ok = all(data.get(field) == expected[field] for field in (
        "category", "urgency", "customer_sentiment"
    ))
    passed = schema_valid and enums_valid and summary_ok and exact_ok
    return passed, {
        "outcome": "pass" if passed else "model_failure",
        "schema_valid": schema_valid,
        "enum_valid": enums_valid,
        "summary_ok": summary_ok,
        "exact_fields_ok": exact_ok,
    }


def evaluate_classification(
    case: dict[str, Any], data: dict[str, Any], status: int | None
):
    if status != 200:
        return False, {"outcome": "api_error", "status": status}
    passed = data.get("category") == case["expected"]["category"]
    return passed, {
        "outcome": "pass" if passed else "model_failure",
        "category_ok": passed,
        "predicted_category": data.get("category"),
        "expected_category": case["expected"]["category"],
    }


def percentile(values: list[float], p: float):
    if not values:
        return None
    ordered = sorted(values)
    rank = (len(ordered) - 1) * p
    low, high = math.floor(rank), math.ceil(rank)
    if low == high:
        return round(ordered[low], 2)
    return round(ordered[low] + (ordered[high] - ordered[low]) * (rank - low), 2)


def run_suite(name: str, cases: list[dict[str, Any]], base_url: str):
    rows = []
    for case in cases:
        if name in {"extraction", "classification"}:
            endpoint = "/extract-ticket"
            payload = {"message": case["input"]}
        else:
            endpoint = "/chat"
            payload = {"prompt": (
                "Answer directly and accurately. Do not invent facts. "
                "If ambiguous, state what is missing or ask a focused "
                "clarification. For multilingual input, answer in the "
                "input language.\n\n" + case["input"]
            )}
        status, data, latency = post_json(base_url + endpoint, payload)
        if name == "extraction":
            passed, details = evaluate_extraction(case, data, status)
        elif name == "classification":
            passed, details = evaluate_classification(case, data, status)
        else:
            passed, details = evaluate_chat(case, data, status)
        usage = data if isinstance(data, dict) else {}
        rows.append({
            "id": case["id"],
            "passed": passed,
            "status": status,
            "latency_ms": round(latency, 2),
            "details": details,
            "usage": {
                "prompt_tokens": usage.get("prompt_tokens"),
                "completion_tokens": usage.get("completion_tokens"),
                "total_tokens": (usage.get("prompt_tokens") or 0)
                + (usage.get("completion_tokens") or 0),
                "estimated_cost_usd": usage.get("estimated_cost_usd"),
            },
        })
    return summarize(name, rows), rows


def summarize(name: str, rows: list[dict[str, Any]]):
    total = len(rows)
    api_errors = sum(row["details"].get("outcome") == "api_error" for row in rows)
    evaluated = [
        row for row in rows
        if row["details"].get("outcome") in {"pass", "model_failure"}
    ]
    passed = sum(row["details"].get("outcome") == "pass" for row in evaluated)
    schema_checks = [
        row["details"]["schema_valid"]
        for row in evaluated if "schema_valid" in row["details"]
    ]
    latencies = [row["latency_ms"] for row in rows]
    input_tokens = sum(row["usage"]["prompt_tokens"] or 0 for row in rows)
    output_tokens = sum(row["usage"]["completion_tokens"] or 0 for row in rows)
    cost = sum(row["usage"]["estimated_cost_usd"] or 0 for row in rows)
    return {
        "suite": name,
        "total_cases": total,
        "evaluated_cases": len(evaluated),
        "passed": passed,
        "model_failures": len(evaluated) - passed,
        "api_errors": api_errors,
        "accuracy": round(passed / len(evaluated), 4) if evaluated else None,
        "model_failure_rate": round((len(evaluated) - passed) / len(evaluated), 4)
        if evaluated else None,
        "api_error_rate": round(api_errors / total, 4) if total else 0,
        "structured_output_validity": round(sum(schema_checks) / len(schema_checks), 4)
        if schema_checks else None,
        "latency_ms": {
            "average": round(sum(latencies) / len(latencies), 2) if latencies else None,
            "p50": percentile(latencies, 0.50),
            "p95": percentile(latencies, 0.95),
            "p99": percentile(latencies, 0.99),
        },
        "tokens": {
            "input": input_tokens,
            "output": output_tokens,
            "total": input_tokens + output_tokens,
        },
        "cost": {
            "total_usd": round(cost, 6),
            "average_per_request_usd": round(cost / total, 6) if total else 0,
        },
    }


def load(name: str):
    return json.loads((EVALS / f"{name}_cases.json").read_text(encoding="utf-8"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument(
        "--suite",
        choices=["all", "chat", "extraction", "classification", "adversarial"],
        default="all",
    )
    args = parser.parse_args()
    names = (
        ["chat", "extraction", "classification", "adversarial"]
        if args.suite == "all" else [args.suite]
    )
    reports, detailed = [], []
    for name in names:
        report, rows = run_suite(name, load(name), args.base_url.rstrip("/"))
        reports.append(report)
        detailed.extend(rows)
        print(
            f"{name}: accuracy={report['accuracy']} "
            f"model_failures={report['model_failures']} "
            f"api_errors={report['api_errors']} "
            f"p95={report['latency_ms']['p95']}ms"
        )

    stamp = time.strftime("%Y%m%d-%H%M%S")
    output = RESULTS / f"eval-{stamp}.json"
    output.write_text(json.dumps({
        "timestamp": stamp,
        "base_url": args.base_url,
        "suites": reports,
        "details": detailed,
    }, indent=2), encoding="utf-8")
    print(f"Saved detailed results to {output}")


if __name__ == "__main__":
    main()
