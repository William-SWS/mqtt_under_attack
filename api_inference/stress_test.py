from __future__ import annotations

import argparse
import asyncio
import json
import os
import statistics
import time
from dataclasses import asdict, dataclass, field
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

    def summary(self) -> str:
        return f"""
=== Stress Test Results ===
Target URL:       {self.total_requests} requests
Concurrency:      {self.successful + self.failed} total
Total duration:   {self.total_duration_sec:.2f}s

--- Results ---
Successful:       {self.successful}
Failed:           {self.failed}
Timeouts:         {self.timeouts}
Error rate:       {(self.failed / max(self.total_requests, 1)) * 100:.1f}%

--- Throughput ---
Requests/sec:     {self.throughput:.1f}

--- Latency (ms) ---
Average:          {self.avg_latency_ms:.1f}
Min:              {self.min_ms:.1f}
Max:              {self.max_ms:.1f}
P50 (median):     {self.p50_ms:.1f}
P95:              {self.p95_ms:.1f}
P99:              {self.p99_ms:.1f}
"""

    def to_dict(self, args: argparse.Namespace, system_before: dict | None, system_after: dict | None) -> dict:
        return {
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


async def fetch_system_stats(client: httpx.AsyncClient, url: str) -> dict | None:
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
    results: list[float],
    errors: list[str],
) -> None:
    async with semaphore:
        try:
            start = time.perf_counter()
            if method == "POST":
                await client.post(url, timeout=timeout)
            else:
                await client.get(url, timeout=timeout)
            elapsed = (time.perf_counter() - start) * 1000
            results.append(elapsed)
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
    errors: list[str] = []
    semaphore = asyncio.Semaphore(concurrency)

    async with httpx.AsyncClient() as client:
        start = time.perf_counter()
        tasks = [
            send_request(client, full_url, method, timeout, semaphore, latencies, errors)
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

    print(f"Starting stress test...")
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
                print(f"  System stats (before):")
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
        print(f"JSON saved: {filepath}")

    asyncio.run(run())


if __name__ == "__main__":
    main()
