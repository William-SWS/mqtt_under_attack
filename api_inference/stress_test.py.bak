from __future__ import annotations

import argparse
import asyncio
import json
import math
import os
import statistics
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

import httpx


@dataclass
class StressResult:
    total_requests: int
    successful: int
    failed: int
    timeouts: int
    total_duration_sec: float
    latencies_ms: list[float] = field(default_factory=list)
    model_runs: list[dict[str, Any]] = field(default_factory=list)

    @property
    def throughput(self) -> float:
        return self.successful / self.total_duration_sec if self.total_duration_sec > 0 else 0.0

    @property
    def avg_latency_ms(self) -> float:
        return statistics.mean(self.latencies_ms) if self.latencies_ms else 0.0

    @property
    def p50_ms(self) -> float:
        return statistics.median(self.latencies_ms) if self.latencies_ms else 0.0

    @property
    def p95_ms(self) -> float:
        if not self.latencies_ms:
            return 0.0
        sorted_lat = sorted(self.latencies_ms)
        idx = int(len(sorted_lat) * 0.95)
        return sorted_lat[idx]

    @property
    def p99_ms(self) -> float:
        if not self.latencies_ms:
            return 0.0
        sorted_lat = sorted(self.latencies_ms)
        idx = int(len(sorted_lat) * 0.99)
        return sorted_lat[idx]

    @property
    def min_ms(self) -> float:
        return min(self.latencies_ms) if self.latencies_ms else 0.0

    @property
    def max_ms(self) -> float:
        return max(self.latencies_ms) if self.latencies_ms else 0.0

    def _aggregate_models(self) -> dict[str, dict[str, Any]]:
        by_model: dict[str, list[dict]] = defaultdict(list)
        for run in self.model_runs:
            by_model[run["model_id"]].append(run)

        aggregated: dict[str, dict] = {}
        for model_id, runs in sorted(by_model.items()):
            times = [r["inference_time_sec"] * 1000 for r in runs if r.get("inference_time_sec") is not None]
            accs = [r["accuracy"] for r in runs if r.get("accuracy") is not None]
            rows_set = {r["rows"] for r in runs if r.get("rows") is not None}
            n_feat_set = {r["n_features"] for r in runs if r.get("n_features") is not None}

            base = {
                "requests": len(runs),
                "rows": rows_set.pop() if len(rows_set) == 1 else list(rows_set),
                "n_features": n_feat_set.pop() if len(n_feat_set) == 1 else list(n_feat_set),
            }

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

    def summary(self) -> str:
        lines = [
            "",
            "=== Stress Test Results ===",
            f"Total duration:   {self.total_duration_sec:.2f}s",
            "",
            "--- Results ---",
            f"Successful:       {self.successful}",
            f"Failed:           {self.failed}",
            f"Timeouts:         {self.timeouts}",
            f"Error rate:       {(self.failed / max(self.total_requests, 1)) * 100:.1f}%",
            "",
            "--- Throughput ---",
            f"Requests/sec:     {self.throughput:.1f}",
            "",
            "--- Latency (ms) ---",
            f"Average:          {self.avg_latency_ms:.1f}",
            f"Min:              {self.min_ms:.1f}",
            f"Max:              {self.max_ms:.1f}",
            f"P50 (median):     {self.p50_ms:.1f}",
            f"P95:              {self.p95_ms:.1f}",
            f"P99:              {self.p99_ms:.1f}",
        ]

        aggregated = self._aggregate_models()
        if aggregated:
            lines.extend(["", "--- Per Model ---"])
            for model_id, agg in aggregated.items():
                if "inference_time_ms_avg" in agg:
                    ci = agg.get("inference_time_ms_ci95_lower")
                    if ci is not None:
                        ci_str = f"ci95=[{agg['inference_time_ms_ci95_lower']:.1f}, {agg['inference_time_ms_ci95_upper']:.1f}]ms"
                    else:
                        ci_str = ""
                    lines.append(
                        f"  {model_id}: {agg['requests']}x  "
                        f"avg={agg['inference_time_ms_avg']:.1f}ms  "
                        f"p50={agg['inference_time_ms_p50']:.1f}ms  "
                        f"std={agg.get('inference_time_ms_std', '?'):.1f}ms  "
                        f"{ci_str}  "
                        f"acc={agg.get('accuracy_avg', 'N/A')}"
                    )

        return "\n".join(lines)

    def to_dict(self, args: argparse.Namespace, system_before: dict | None, system_after: dict | None) -> dict:
        d = {
            "test_info": {
                "timestamp": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "url": args.url,
                "endpoint": args.endpoint,
                "method": "POST" if args.endpoint.startswith("/benchmark") else "GET",
                "concurrency": args.concurrency,
                "requests": args.requests,
                "timeout_sec": args.timeout,
                "duration_sec": round(self.total_duration_sec, 3),
            },
            "results": {
                "successful": self.successful,
                "failed": self.failed,
                "timeouts": self.timeouts,
                "error_rate_pct": round((self.failed / max(self.total_requests, 1)) * 100, 2),
                "throughput_req_per_sec": round(self.throughput, 2),
            },
            "latency_ms": {
                "average": round(self.avg_latency_ms, 2),
                "min": round(self.min_ms, 2),
                "max": round(self.max_ms, 2),
                "p50": round(self.p50_ms, 2),
                "p95": round(self.p95_ms, 2),
                "p99": round(self.p99_ms, 2),
                "all": [round(lat, 3) for lat in self.latencies_ms],
            },
            "system_before": system_before,
            "system_after": system_after,
        }

        aggregated = self._aggregate_models()
        if aggregated:
            d["per_model"] = aggregated

        return d


async def fetch_system_stats(client: httpx.AsyncClient, url: str) -> dict | None:
    try:
        resp = await client.get(f"{url}/stats", timeout=10.0)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return None


def _extract_model_runs(body: dict[str, Any] | None) -> list[dict[str, Any]]:
    if body is None:
        return []
    if "results" in body:
        return body["results"]
    if "result" in body:
        return [body["result"]]
    return []


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
    url: str,
    endpoint: str,
    method: str,
    concurrency: int,
    requests: int,
    timeout: float,
) -> StressResult:
    full_url = f"{url}{endpoint}"
    latencies: list[float] = []
    model_runs: list[dict[str, Any]] = []
    errors: list[str] = []
    semaphore = asyncio.Semaphore(concurrency)

    async with httpx.AsyncClient() as client:
        start = time.perf_counter()
        tasks = [
            send_request(client, full_url, method, timeout, semaphore, latencies, model_runs, errors)
            for _ in range(requests)
        ]
        await asyncio.gather(*tasks)
        total_duration = time.perf_counter() - start

    timeouts = errors.count("timeout")
    successful = len(latencies)
    failed = len(errors)

    return StressResult(
        total_requests=requests,
        successful=successful,
        failed=failed,
        timeouts=timeouts,
        total_duration_sec=total_duration,
        latencies_ms=latencies,
        model_runs=model_runs,
    )


def save_result(result: StressResult, args: argparse.Namespace, output_dir: str,
                 system_before: dict | None, system_after: dict | None) -> str:
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    filename = f"stress_test_{timestamp}.json"
    filepath = os.path.join(output_dir, filename)
    data = result.to_dict(args, system_before, system_after)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return filepath


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Stress test for MQTT Under Attack Inference API"
    )
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="Base URL of the API (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--endpoint",
        default="/health",
        choices=["/health", "/models", "/benchmark", "/benchmark/lowvariance_gradientboosting"],
        help="Endpoint to stress test (default: /health)",
    )
    parser.add_argument(
        "-c", "--concurrency",
        type=int,
        default=10,
        help="Number of concurrent requests (default: 10)",
    )
    parser.add_argument(
        "-n", "--requests",
        type=int,
        default=100,
        help="Total number of requests to send (default: 100)",
    )
    parser.add_argument(
        "-t", "--timeout",
        type=float,
        default=300.0,
        help="Request timeout in seconds (default: 300)",
    )
    parser.add_argument(
        "--output-dir",
        default="results_inference",
        help="Directory to save JSON results (default: results_inference)",
    )

    args = parser.parse_args()
    method = "POST" if args.endpoint.startswith("/benchmark") else "GET"

    print("Starting stress test...")
    print(f"  URL:         {args.url}{args.endpoint}")
    print(f"  Method:      {method}")
    print(f"  Concurrency: {args.concurrency}")
    print(f"  Requests:    {args.requests}")
    print(f"  Timeout:     {args.timeout}s")
    print()

    async def run() -> None:
        async with httpx.AsyncClient() as client:
            system_before = await fetch_system_stats(client, args.url)
            if system_before:
                mem = system_before.get("memory_used_mb")
                cpu = system_before.get("cpu_count")
                workers = system_before.get("uvicorn_workers")
                print("  System stats (before):")
                print(f"    Workers: {workers}  |  CPU cores: {cpu}  |  RAM used: {mem} MB")
                print()

        result = await run_stress_test(
            url=args.url,
            endpoint=args.endpoint,
            method=method,
            concurrency=args.concurrency,
            requests=args.requests,
            timeout=args.timeout,
        )

        async with httpx.AsyncClient() as client:
            system_after = await fetch_system_stats(client, args.url)

        print(result.summary())

        filepath = save_result(result, args, args.output_dir, system_before, system_after)
        print(f"\nJSON saved: {filepath}")

    asyncio.run(run())


if __name__ == "__main__":
    main()
