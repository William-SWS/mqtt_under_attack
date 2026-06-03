from __future__ import annotations

from fastapi import FastAPI, HTTPException

from app.benchmark import (
    get_paths,
    health_status,
    public_model_info,
    public_result,
    run_all_benchmarks,
    run_benchmark,
    update_single_result,
    write_results,
)


app = FastAPI(
    title="MQTT Under Attack Inference Benchmark API",
    description="Runs batch inference benchmarks for trained MQTT DoS models.",
    version="1.0.0",
)


@app.get("/health")
def health() -> dict:
    return health_status()


@app.get("/models")
def models() -> dict:
    model_info = public_model_info()
    return {
        "count": len(model_info),
        "compatible_count": sum(1 for model in model_info if model["compatible"]),
        "models": model_info,
    }


@app.post("/benchmark")
def benchmark_all() -> dict:
    paths = get_paths()
    results = run_all_benchmarks(paths)
    csv_path = write_results(results, paths)
    return {
        "count": len(results),
        "results_csv": str(csv_path),
        "results": [public_result(result) for result in results],
    }


@app.post("/benchmark/{model_id}")
def benchmark_one(model_id: str) -> dict:
    paths = get_paths()
    result = run_benchmark(model_id, paths)
    if result.status != "success":
        raise HTTPException(status_code=404, detail=public_result(result))
    csv_path = update_single_result(result, paths)
    return {
        "results_csv": str(csv_path),
        "result": public_result(result),
    }
