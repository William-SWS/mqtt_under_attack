from __future__ import annotations

from fastapi import FastAPI

from stress_api.core import StressTestRequest, run_stress_test

app = FastAPI(
    title="MQTT Under Attack Stress Test API",
    description="Executa testes de estresse contra a API de inferencia no Raspberry Pi.",
    version="1.0.0",
)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/run")
async def run(req: StressTestRequest) -> dict:
    return await run_stress_test(req)
