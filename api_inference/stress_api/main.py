"""
Servidor FastAPI para execução de testes de estresse contra a API de
inferência de modelos MQTT rodando no Raspberry Pi.

Uso:
    uvicorn stress_api.main:app --host 0.0.0.0 --port 8001

Endpoints:
    GET  /health   — health check do próprio servidor
    POST /run      — dispara um teste de estresse completo
    POST /sweep    — varredura automática de OMP_NUM_THREADS

O servidor roda na máquina local (PC) e faz requisições HTTP concorrentes
contra a API alvo (Raspberry Pi em 192.168.20.83:8000).
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException

from stress_api.core import StressTestRequest, run_stress_test
from stress_api.sweep import SweepRequest, run_sweep

app = FastAPI(
    title="MQTT Under Attack Stress Test API",
    description="Executa testes de estresse contra a API de inferencia no Raspberry Pi.",
    version="1.0.0",
)


@app.get("/health")
async def health() -> dict:
    """Verifica se o servidor de stress test está operacional."""
    return {"status": "ok"}


@app.post("/run")
async def run(req: StressTestRequest) -> dict:
    """Executa um teste de estresse completo contra a API alvo.

    O corpo da requisição deve conter os parâmetros do teste (target_url,
    endpoint, concurrency, requests, timeout). O retorno inclui estatísticas
    de latência, resultados por modelo e dados de sistema do Pi.

    Exemplo:
        curl -X POST http://localhost:8001/run \\
            -H "Content-Type: application/json" \\
            -d '{"target_url": "http://192.168.20.83:8000"}'
    """
    return await run_stress_test(req)


@app.post("/sweep")
async def sweep(req: SweepRequest) -> dict:
    """Executa varredura automática de OMP_NUM_THREADS no Pi.

    Para cada valor de OMP (padrão: 5, 10, 20, 30, 40, 50, 100):
      1. Altera OMP_NUM_THREADS no docker-compose.yml do Pi via SSH
      2. Reinicia o container
      3. Aguarda API saudável
      4. Executa stress test (concurrency=50, requests=50)
      5. Salva JSON + CSV em results_inference/sweep/omp_{N}/

    ATENÇÃO: Esta requisição leva vários minutos (um cenário por vez).

    Exemplo:
        curl -X POST http://localhost:8001/sweep \\
            -H "Content-Type: application/json" \\
            -d '{"pi_host": "192.168.20.83", "omp_list": "5,10,20"}'
    """
    try:
        return await run_sweep(req)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
