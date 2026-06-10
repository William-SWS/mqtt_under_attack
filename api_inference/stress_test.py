from __future__ import annotations

import argparse
import asyncio

from stress_api.core import StressTestRequest, run_stress_test


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Stress test for MQTT Under Attack Inference API"
    )
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        dest="target_url",
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

    request = StressTestRequest(
        target_url=args.target_url,
        endpoint=args.endpoint,
        concurrency=args.concurrency,
        requests=args.requests,
        timeout=args.timeout,
        output_dir=args.output_dir,
    )

    print(f"Starting stress test...")
    print(f"  URL:         {request.target_url}{request.endpoint}")
    print(f"  Method:      {request.method}")
    print(f"  Concurrency: {request.concurrency}")
    print(f"  Requests:    {request.requests}")
    print(f"  Timeout:     {request.timeout}s")
    print()

    result = asyncio.run(run_stress_test(request))

    print(result["_summary"])
    print(f"\nJSON saved: {result.get('results_file', 'N/A')}")


if __name__ == "__main__":
    main()
