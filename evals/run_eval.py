#!/usr/bin/env python3
"""Week 1 LLM evaluation runner for the existing FastAPI API."""
from __future__ import annotations
import argparse, json, math, statistics, time, urllib.error, urllib.request
from pathlib import Path
from typing import Any
ROOT=Path(__file__).resolve().parents[1]
EVALS=ROOT/"evals"; RESULTS=ROOT/"results"; RESULTS.mkdir(exist_ok=True)

def post_json(url:str,payload:dict[str,Any],timeout:float=45.0):
    body=json.dumps(payload).encode("utf-8")
    req=urllib.request.Request(url,data=body,headers={"Content-Type":"application/json"},method="POST")
    started=time.perf_counter()
    try:
        with urllib.request.urlopen(req,timeout=timeout) as response:
            raw=response.read().decode("utf-8"); status=response.status
    except urllib.error.HTTPError as exc:
        raw=exc.read().decode("utf-8",errors="replace"); status=exc.code
    elapsed=(time.perf_counter()-started)*1000
    try: data=json.loads(raw)
    except json.JSONDecodeError: data={"raw":raw}
    return status,data,elapsed

def contains_all(text:str,items:list[str])->bool:
    low=text.lower(); return all(x.lower() in low for x in items)
def contains_none(text:str,items:list[str])->bool:
    low=text.lower(); return not any(x.lower() in low for x in items)

def eval_chat(case,data,status):
    if status!=200 or "response" not in data: return False,{"outcome":"api_error","reason":"api_failure_or_missing_response","status":status}
    answer=str(data["response"]); exp=case["expected"]
    a=contains_all(answer,exp.get("must_contain_concepts",[]))
    b=contains_none(answer,exp.get("must_not_contain",[]))
    return a and b,{"outcome":"pass" if a and b else "model_failure","concepts_ok":a,"forbidden_ok":b}

def eval_extraction(case,data,status):
    if status!=200: return False,{"outcome":"api_error","reason":"api_failure","status":status}
    req={"summary","category","urgency","customer_sentiment"}
    schema=req.issubset(data.keys()) and all(isinstance(data[k],str) for k in req)
    enums=data.get("category") in {"billing","technical","account","other"} and data.get("urgency") in {"low","medium","high"} and data.get("customer_sentiment") in {"positive","neutral","negative"}
    exp=case["expected"]; summary=contains_all(str(data.get("summary","")),exp["summary_keywords"])
    exact=data.get("category")==exp["category"] and data.get("urgency")==exp["urgency"] and data.get("customer_sentiment")==exp["customer_sentiment"]
    passed=schema and enums and exact and summary
    return passed,{"outcome":"pass" if passed else "model_failure","schema_valid":schema,"enum_valid":enums,"summary_ok":summary,"exact_fields_ok":exact}

def percentile(values,p):
    if not values:return None
    values=sorted(values)
    if len(values)==1:return values[0]
    rank=(len(values)-1)*p; lo=math.floor(rank); hi=math.ceil(rank)
    return values[lo] if lo==hi else values[lo]+(values[hi]-values[lo])*(rank-lo)

def run_suite(name,cases,base_url):
    rows=[]
    for case in cases:
        if name=="extraction":
            endpoint="/extract-ticket"; payload={"message":case["input"]}
        else:
            endpoint="/chat"
            prompt=("Answer directly and accurately. Do not invent facts. If ambiguous, "
                    "state what is missing or ask a focused clarification. For multilingual "
                    "input, answer in the input language.\n\n"+case["input"])
            payload={"prompt":prompt}
        try:
            status,data,lat=post_json(base_url+endpoint,payload)
            passed,details=eval_extraction(case,data,status) if name=="extraction" else eval_chat(case,data,status)
            rows.append({"id":case["id"],"passed":passed,"status":status,"latency_ms":round(lat,2),"details":details,
                         "usage":{"prompt_tokens":data.get("prompt_tokens"),"completion_tokens":data.get("completion_tokens"),
                                  "total_tokens":(data.get("prompt_tokens") or 0)+(data.get("completion_tokens") or 0),
                                  "estimated_cost_usd":data.get("estimated_cost_usd")}})
        except Exception as exc:
            rows.append({"id":case["id"],"passed":False,"status":None,"latency_ms":None,"details":{"reason":"client_error","error":str(exc)},"usage":{}})
    return summarize(name,rows)

def summarize(name,rows):
    total=len(rows)
    api_errors=sum(1 for r in rows if r["details"].get("outcome")=="api_error")
    evaluated=[r for r in rows if r["details"].get("outcome") in {"pass","model_failure"}]
    passed=sum(1 for r in evaluated if r["details"].get("outcome")=="pass")
    model_failures=len(evaluated)-passed
    schema_checks=[r["details"].get("schema_valid") for r in evaluated if "schema_valid" in r["details"]]
    schema_valid=sum(1 for x in schema_checks if x)
    lats=[r["latency_ms"] for r in rows if r["latency_ms"] is not None]
    inp=sum((r["usage"].get("prompt_tokens") or 0) for r in rows)
    out=sum((r["usage"].get("completion_tokens") or 0) for r in rows)
    costs=sum((r["usage"].get("estimated_cost_usd") or 0) for r in rows)
    return {"suite":name,"total_cases":total,"evaluated_cases":len(evaluated),
            "passed":passed,"model_failures":model_failures,"api_errors":api_errors,
            "accuracy":round(passed/len(evaluated),4) if evaluated else None,
            "failure_rate":round(model_failures/len(evaluated),4) if evaluated else None,
            "api_error_rate":round(api_errors/total,4) if total else 0,
            "structured_output_validity":round(schema_valid/len(schema_checks),4) if schema_checks else None,
            "latency_ms":
def load(name): return json.loads((EVALS/f"{name}_cases.json").read_text(encoding="utf-8"))

def print_report(r):
    print("\nLLM EVALUATION\n"+"─"*42)
    print(f"Suite                 {r['suite']}"); print(f"Cases                 {r['total_cases']}")
    print(f"Passed                {r["passed"]}"); print(f"Model failures        {r["model_failures"]}"); print(f"API errors            {r["api_errors"]}")
    print(f"Model accuracy        {r["accuracy"]:.1%}" if r["accuracy"] is not None else "Model accuracy        N/A"); print(f"Model failure rate    {r["failure_rate"]:.1%}" if r["failure_rate"] is not None else "Model failure rate    N/A"); print(f"API error rate        {r["api_error_rate"]:.1%}")
    print(f"Technical failure     {r['technical_failure_rate']:.1%}")
    if r["structured_output_validity"] is not None:
        print(f"Structured validity   {r['structured_output_validity']:.1%}")
    l=r["latency_ms"]; print("\nLatency"); print(f"  Average             {l['average']} ms"); print(f"  P50                 {l['p50']} ms"); print(f"  P95                 {l['p95']} ms"); print(f"  P99                 {l['p99']} ms")
    t=r["tokens"]; print("\nTokens"); print(f"  Input               {t['input']}"); print(f"  Output              {t['output']}"); print(f"  Total               {t['total']}"); print(f"  Average/request     {t['average_total_per_case']}")
    c=r["cost"]; print("\nCost"); print(f"  Total               USD {c['total_usd']:.6f}"); print(f"  Average/request     USD {c['average_per_request_usd']:.6f}")
    print("\nStatus                "+("PASS" if r["failed"]==0 else "REVIEW FAILURES"))

def main():
    p=argparse.ArgumentParser(); p.add_argument("--base-url",default="http://127.0.0.1:8000")
    p.add_argument("--suite",choices=["all","chat","extraction","adversarial"],default="all"); a=p.parse_args()
    names=["chat","extraction","adversarial"] if a.suite=="all" else [a.suite]
    reports=[run_suite(n,load(n),a.base_url.rstrip("/")) for n in names]
    for r in reports: print_report(r)
    total=sum(r["total_cases"] for r in reports); evaluated=sum(r["evaluated_cases"] for r in reports); passed=sum(r["passed"] for r in reports); api_errors=sum(r["api_errors"] for r in reports)
    stamp=time.strftime("%Y%m%d-%H%M%S"); path=RESULTS/f"eval-{stamp}.json"
    path.write_text(json.dumps({"timestamp":stamp,"base_url":a.base_url,"total_cases":total,"evaluated_cases":evaluated,"passed":passed,"model_failures":evaluated-passed,"api_errors":api_errors,"model_accuracy":passed/evaluated if evaluated else None,"api_error_rate":api_errors/total if total else 0,"suites":reports},indent=2),encoding="utf-8")
    print(f"\nSaved detailed results to {path}")
if __name__=="__main__": main()
