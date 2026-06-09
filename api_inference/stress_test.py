from __future__ import annotations

import argparse
import asyncio
import statistics
import time
from dataclasses import dataclass, field
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

    args = parser.parse_args()
    method = "POST" if args.endpoint.startswith("/benchmark") else "GET"

    print(f"Starting stress test...")
    print(f"  URL:         {args.url}{args.endpoint}")
    print(f"  Method:      {method}")
    print(f"  Concurrency: {args.concurrency}")
    print(f"  Requests:    {args.requests}")
    print(f"  Timeout:     {args.timeout}s")
    print()

    result = asyncio.run(
        run_stress_test(
            url=args.url,
            endpoint=args.endpoint,
            method=method,
            concurrency=args.concurrency,
            requests=args.requests,
            timeout=args.timeout,
        )
    )
    print(result.summary())


if __name__ == "__main__":
    main()
