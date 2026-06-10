from __future__ import annotations

import asyncio
import json
import math
import os
import statistics
import time
from collections import defaultdict
from datetime import UTC, datetime
from typing import Any

import httpx
from pydantic import BaseModel, Field


class StressTestRequest(BaseModel):
    target_url: str = Field(
        ..., description="URL base da API alvo (ex: http://192.168.20.83:8000)"
    )
    endpoint: str = Field(
        "/benchmark",
        description="Endpoint para testar (/benchmark, /health, /models, ou /benchmark/{model_id})",
    )
    concurrency: int = Field(5, ge=1, description="Requisições simultâneas")
    requests: int = Field(20, ge=1, description="Total de requisições")
    timeout: float = Field(600.0, ge=1.0, description="Timeout por requisição (s)")
    output_dir: str = Field(
        "results_inference", description="Diretório para salvar o JSON"
    )

    @property
    def method(self) -> str:
        return "POST" if self.endpoint.startswith("/benchmark") else "GET"


# ── helpers ──────────────────────────────────────────────────


def _extract_model_runs(body: dict[str, Any] | None) -> list[dict[str, Any]]:
    if body is None:
        return []
    if "results" in body:
        return body["results"]
    if "result" in body:
        return [body["result"]]
    return []


def _aggregate_model_stats(
    model_runs: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    by_model: dict[str, list[dict]] = defaultdict(list)
    for run in model_runs:
        by_model[run["model_id"]].append(run)

    aggregated: dict[str, dict] = {}
    for model_id, runs in sorted(by_model.items()):
        times = [
            r["inference_time_sec"] * 1000
            for r in runs
            if r.get("inference_time_sec") is not None
        ]
        accs = [r["accuracy"] for r in runs if r.get("accuracy") is not None]
        rows_set = {r["rows"] for r in runs if r.get("rows") is not None}
        n_feat_set = {r["n_features"] for r in runs if r.get("n_features") is not None}

        base: dict[str, Any] = {
            "requests": len(runs),
        }
        if len(rows_set) == 1:
            base["rows"] = rows_set.pop()
        if len(n_feat_set) == 1:
            base["n_features"] = n_feat_set.pop()

        if times:
            avg = statistics.mean(times)
            std = statistics.stdev(times) if len(times) > 1 else 0.0
            n = len(times)
            se = std / math.sqrt(n)
            z = 1.96
            base.update({
                "inference_time_ms_avg": round(avg, 3),
                "inference_time_ms_std": round(std, 3),
                "inference_time_ms_min": round(min(times), 3),
                "inference_time_ms_max": round(max(times), 3),
                "inference_time_ms_p50": round(statistics.median(times), 3),
                "inference_time_ms_ci95_lower": round(avg - z * se, 3),
                "inference_time_ms_ci95_upper": round(avg + z * se, 3),
                "inference_times_ms": [round(t, 3) for t in times],
            })
        if accs:
            base.update({
                "accuracy_avg": round(statistics.mean(accs), 4),
                "accuracy_min": round(min(accs), 4),
                "accuracy_max": round(max(accs), 4),
                "accuracies": [round(a, 4) for a in accs],
            })

        aggregated[model_id] = base

    return aggregated


def _latency_stats(latencies_ms: list[float]) -> dict[str, Any]:
    if not latencies_ms:
        return {}
    sorted_lat = sorted(latencies_ms)
    n = len(sorted_lat)
    return {
        "average": round(statistics.mean(sorted_lat), 2),
        "min": round(sorted_lat[0], 2),
        "max": round(sorted_lat[-1], 2),
        "p50": round(statistics.median(sorted_lat), 2),
        "p95": round(sorted_lat[int(n * 0.95)], 2),
        "p99": round(sorted_lat[int(n * 0.99)], 2),
        "all": [round(l, 3) for l in sorted_lat],
    }


def build_response(
    request: StressTestRequest,
    latencies_ms: list[float],
    model_runs: list[dict[str, Any]],
    errors: list[str],
    total_duration_sec: float,
    system_before: dict[str, Any] | None,
    system_after: dict[str, Any] | None,
    results_file: str | None,
) -> dict[str, Any]:
    successful = len(latencies_ms)
    failed = len(errors)
    timeouts = errors.count("timeout")

    d: dict[str, Any] = {
        "test_info": {
            "timestamp": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "target_url": request.target_url,
            "endpoint": request.endpoint,
            "method": request.method,
            "concurrency": request.concurrency,
            "requests": request.requests,
            "timeout_sec": request.timeout,
            "duration_sec": round(total_duration_sec, 3),
        },
        "results": {
            "successful": successful,
            "failed": failed,
            "timeouts": timeouts,
            "error_rate_pct": round(
                (failed / max(request.requests, 1)) * 100, 2
            ),
            "throughput_req_per_sec": round(
                successful / total_duration_sec if total_duration_sec > 0 else 0.0, 2
            ),
        },
        "latency_ms": _latency_stats(latencies_ms),
        "system_before": system_before,
        "system_after": system_after,
        "results_file": results_file,
    }

    model_agg = _aggregate_model_stats(model_runs)
    if model_agg:
        d["per_model"] = model_agg

    return d


def format_summary(
    request: StressTestRequest,
    latencies_ms: list[float],
    model_runs: list[dict[str, Any]],
    errors: list[str],
    total_duration_sec: float,
) -> str:
    successful = len(latencies_ms)
    failed = len(errors)
    timeouts = errors.count("timeout")
    throughput = (
        successful / total_duration_sec if total_duration_sec > 0 else 0.0
    )
    lat = _latency_stats(latencies_ms)

    lines = [
        "",
        "=== Stress Test Results ===",
        f"Target: {request.target_url}{request.endpoint}",
        f"Duration: {total_duration_sec:.2f}s  |  Concurrency: {request.concurrency}",
        "",
        "--- Results ---",
        f"Successful: {successful}  |  Failed: {failed}  |  Timeouts: {timeouts}",
        f"Error rate: {(failed / max(request.requests, 1)) * 100:.1f}%",
        f"Throughput: {throughput:.1f} req/s",
        "",
        "--- Latency (ms) ---",
        f"Avg: {lat.get('average', '?'):.1f}  |  Min: {lat.get('min', '?'):.1f}  |  Max: {lat.get('max', '?'):.1f}",
        f"P50: {lat.get('p50', '?'):.1f}  |  P95: {lat.get('p95', '?'):.1f}  |  P99: {lat.get('p99', '?'):.1f}",
    ]

    model_agg = _aggregate_model_stats(model_runs)
    if model_agg:
        lines.append("")
        lines.append("--- Per Model ---")
        for model_id, agg in model_agg.items():
            if "inference_time_ms_avg" in agg:
                ci = agg.get("inference_time_ms_ci95_lower")
                ci_str = (
                    f"ci95=[{agg['inference_time_ms_ci95_lower']:.1f}, {agg['inference_time_ms_ci95_upper']:.1f}]ms"
                    if ci is not None
                    else ""
                )
                lines.append(
                    f"  {model_id}: {agg['requests']}x  "
                    f"avg={agg['inference_time_ms_avg']:.1f}ms  "
                    f"p50={agg['inference_time_ms_p50']:.1f}ms  "
                    f"std={agg.get('inference_time_ms_std', '?'):.1f}ms  "
                    f"{ci_str}  "
                    f"acc={agg.get('accuracy_avg', 'N/A')}"
                )

    return "\n".join(lines)


# ── network ──────────────────────────────────────────────────


async def fetch_system_stats(
    client: httpx.AsyncClient, url: str
) -> dict[str, Any] | None:
    try:
        resp = await client.get(f"{url}/stats", timeout=10.0)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return None


async def send_request(
    client: httpx.AsyncClient,
    url: str,
    method: str,
    timeout: float,
    semaphore: asyncio.Semaphore,
    latencies: list[float],
    model_runs: list[dict[str, Any]],
    errors: list[str],
) -> None:
    async with semaphore:
        try:
            start = time.perf_counter()
            if method == "POST":
                resp = await client.post(url, timeout=timeout)
            else:
                resp = await client.get(url, timeout=timeout)
            elapsed = (time.perf_counter() - start) * 1000
            latencies.append(elapsed)

            body = resp.json() if resp.status_code == 200 and resp.text else None
            runs = _extract_model_runs(body)
            for run in runs:
                run["_request_latency_ms"] = round(elapsed, 3)
            model_runs.extend(runs)

        except httpx.TimeoutException:
            errors.append("timeout")
        except Exception as exc:
            errors.append(str(exc))


async def run_stress_test(
    request: StressTestRequest,
) -> dict[str, Any]:
    full_url = f"{request.target_url}{request.endpoint}"
    latencies: list[float] = []
    model_runs: list[dict[str, Any]] = []
    errors: list[str] = []
    semaphore = asyncio.Semaphore(request.concurrency)

    system_before: dict[str, Any] | None = None
    system_after: dict[str, Any] | None = None

    async with httpx.AsyncClient() as client:
        system_before = await fetch_system_stats(client, request.target_url)

        start = time.perf_counter()
        tasks = [
            send_request(
                client,
                full_url,
                request.method,
                request.timeout,
                semaphore,
                latencies,
                model_runs,
                errors,
            )
            for _ in range(request.requests)
        ]
        await asyncio.gather(*tasks)
        total_duration = time.perf_counter() - start

        system_after = await fetch_system_stats(client, request.target_url)

    results_file = save_result(
        request, latencies, model_runs, errors, total_duration,
        system_before, system_after,
    )

    response = build_response(
        request, latencies, model_runs, errors, total_duration,
        system_before, system_after, results_file,
    )
    response["_summary"] = format_summary(
        request, latencies, model_runs, errors, total_duration,
    )
    return response


# ── persistence ──────────────────────────────────────────────


def save_result(
    request: StressTestRequest,
    latencies_ms: list[float],
    model_runs: list[dict[str, Any]],
    errors: list[str],
    total_duration_sec: float,
    system_before: dict[str, Any] | None,
    system_after: dict[str, Any] | None,
) -> str:
    os.makedirs(request.output_dir, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    filename = f"stress_test_{timestamp}.json"
    filepath = os.path.join(request.output_dir, filename)
    data = build_response(
        request, latencies_ms, model_runs, errors, total_duration_sec,
        system_before, system_after, filepath,
    )
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return filepath
