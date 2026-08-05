from __future__ import annotations

import asyncio

from fastapi import FastAPI, HTTPException

from app.benchmark import (
    get_paths,
    health_status,
    public_model_info,
    public_result,
    run_all_benchmarks,
    run_benchmark,
    system_stats,
    update_single_result,
    write_results,
)


app = FastAPI(
    title="MQTT Under Attack Inference Benchmark API",
    description="Runs batch inference benchmarks for trained MQTT DoS models.",
    version="1.1.0",
)


@app.get("/health")
async def health() -> dict:
    return await asyncio.to_thread(health_status)


@app.get("/models")
async def models() -> dict:
    model_info = await asyncio.to_thread(public_model_info)
    return {
        "count": len(model_info),
        "compatible_count": sum(1 for model in model_info if model["compatible"]),
        "models": model_info,
    }


@app.post("/benchmark")
async def benchmark_all() -> dict:
    paths = get_paths()
    results = await asyncio.to_thread(run_all_benchmarks, paths)
    csv_path = await asyncio.to_thread(write_results, results, paths)
    return {
        "count": len(results),
        "results_csv": str(csv_path),
        "results": [public_result(result) for result in results],
    }


@app.get("/stats")
async def stats() -> dict:
    return await asyncio.to_thread(system_stats)


@app.post("/benchmark/{model_id}")
async def benchmark_one(model_id: str) -> dict:
    paths = get_paths()
    result = await asyncio.to_thread(run_benchmark, model_id, paths)
    if result.status != "success":
        raise HTTPException(status_code=404, detail=public_result(result))
    csv_path = await asyncio.to_thread(update_single_result, result, paths)
    return {
        "results_csv": str(csv_path),
        "result": public_result(result),
    }
