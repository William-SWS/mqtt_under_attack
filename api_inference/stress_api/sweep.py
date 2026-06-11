"""
Módulo de varredura automática de OMP_NUM_THREADS.

Integrado como endpoint POST /sweep na stress_api.
"""

from __future__ import annotations

import asyncio
import csv
import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any

import httpx
from pydantic import BaseModel, Field

from stress_api.core import StressTestRequest, run_stress_test


class SweepRequest(BaseModel):
    """Parâmetros da varredura de OMP_NUM_THREADS."""
    pi_host: str = Field("192.168.20.83", description="IP do Raspberry Pi")
    pi_port: int = Field(8000, ge=1, le=65535, description="Porta da API no Pi")
    omp_list: str = Field(
        "5,10,20,30,40,50,100",
        description="Valores de OMP_NUM_THREADS separados por vírgula",
    )
    concurrency: int = Field(50, ge=1, description="Concorrência do stress test")
    requests_per_test: int = Field(50, ge=1, description="Requisições por cenário")
    timeout_per_request: float = Field(120.0, ge=10.0, description="Timeout por requisição")
    output_dir: str = Field("results_inference", description="Diretório base para resultados")


# ── helpers de SSH ───────────────────────────────────────────


async def _ssh(host: str, cmd: str) -> str:
    """Executa um comando no Pi via SSH (offload para thread)."""
    loop = asyncio.get_running_loop()

    def run() -> str:
        result = subprocess.run(
            ["ssh", host, cmd],
            capture_output=True, text=True, timeout=120,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"SSH falhou: {cmd[:60]!r} -> {result.stderr.strip()}"
            )
        return result.stdout.strip()

    return await loop.run_in_executor(None, run)


async def _set_omp_on_pi(host: str, omp_value: int) -> None:
    """Altera OMP_NUM_THREADS e OPENBLAS_NUM_THREADS no docker-compose do Pi e reinicia."""
    cmds = [
        f"cd ~/api_inference && sed -i 's/OMP_NUM_THREADS: .*/OMP_NUM_THREADS: {omp_value}/' docker-compose.yml",
        f"cd ~/api_inference && sed -i 's/OPENBLAS_NUM_THREADS: .*/OPENBLAS_NUM_THREADS: {omp_value}/' docker-compose.yml",
        "cd ~/api_inference && docker compose up -d",
    ]
    for cmd in cmds:
        await _ssh(host, cmd)


async def _wait_for_api(url: str, timeout_sec: int = 120) -> bool:
    """Aguarda a API do Pi responder GET /health."""
    deadline = time.time() + timeout_sec
    async with httpx.AsyncClient(timeout=10.0) as client:
        while time.time() < deadline:
            try:
                resp = await client.get(f"{url}/health")
                if resp.status_code == 200:
                    return True
            except Exception:
                pass
            await asyncio.sleep(3)
    return False


# ── execução por cenário ──────────────────────────────────────


async def _run_single(
    pi_url: str,
    concurrency: int,
    requests: int,
    timeout: float,
    omp_value: int,
    output_dir: str,
) -> dict[str, Any]:
    """Executa um stress test e salva em results_inference/sweep/omp_{N}/."""
    test_dir = os.path.join(output_dir, "sweep", f"omp_{omp_value}")
    req = StressTestRequest(
        target_url=pi_url,
        endpoint="/benchmark",
        concurrency=concurrency,
        requests=requests,
        timeout=timeout,
        output_dir=test_dir,
    )
    return await run_stress_test(req)


# ── sumário consolidado ─────────────────────────────────────


def _build_summary_csv(output_dir: str, omp_values: list[int]) -> str:
    """Consolida todos os JSONs em um CSV comparativo."""
    rows: list[dict] = []
    base = Path(output_dir) / "sweep"

    for omp in omp_values:
        omp_dir = base / f"omp_{omp}"
        if not omp_dir.is_dir():
            continue
        jsons = sorted(omp_dir.glob("stress_test_*.json"))
        if not jsons:
            continue

        with open(jsons[-1]) as f:
            data = json.load(f)

        ti = data["test_info"]
        sb = data.get("system_before") or {}
        res = data["results"]
        pm = data.get("per_model", {})

        meta = {
            "omp_threads": omp,
            "timestamp": ti["timestamp"],
            "concurrency": ti["concurrency"],
            "requests_total": ti["requests"],
            "duration_sec": ti["duration_sec"],
            "throughput_req_per_sec": res["throughput_req_per_sec"],
            "error_rate_pct": res["error_rate_pct"],
            "uvicorn_workers": sb.get("uvicorn_workers", "N/A"),
            "memory_used_mb": sb.get("memory_used_mb", "N/A"),
            "memory_total_mb": sb.get("memory_total_mb", "N/A"),
        }

        if pm:
            for model_id, agg in sorted(pm.items()):
                row = {**meta}
                row["model_id"] = model_id
                row["n_samples"] = agg.get("requests", "N/A")
                row["inference_time_ms_avg"] = agg.get("inference_time_ms_avg", "N/A")
                row["inference_time_ms_ci95_lower"] = agg.get("inference_time_ms_ci95_lower", "N/A")
                row["inference_time_ms_ci95_upper"] = agg.get("inference_time_ms_ci95_upper", "N/A")
                rows.append(row)
        else:
            row = {**meta}
            row["model_id"] = "N/A"
            for k in ("n_samples", "inference_time_ms_avg",
                      "inference_time_ms_ci95_lower", "inference_time_ms_ci95_upper"):
                row[k] = "N/A"
            rows.append(row)

    if not rows:
        return ""

    summary_path = base / "omp_summary.csv"
    base.mkdir(parents=True, exist_ok=True)

    fields = [
        "omp_threads", "timestamp", "concurrency", "requests_total",
        "duration_sec", "throughput_req_per_sec", "error_rate_pct",
        "uvicorn_workers", "memory_used_mb", "memory_total_mb",
        "model_id", "n_samples",
        "inference_time_ms_avg", "inference_time_ms_ci95_lower",
        "inference_time_ms_ci95_upper",
    ]

    with open(summary_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    return str(summary_path)


# ── sweep principal ──────────────────────────────────────────


async def run_sweep(req: SweepRequest) -> dict[str, Any]:
    """Executa a varredura completa de OMP_NUM_THREADS.

    Para cada valor de OMP:
      1. Altera OMP_NUM_THREADS no docker-compose.yml do Pi via SSH
      2. Reinicia o container
      3. Aguarda API saudável
      4. Executa stress test
      5. Salva JSON + CSV

    Retorna dicionário com resumo de cada cenário + caminho do CSV consolidado.
    """
    omp_values = [int(v.strip()) for v in req.omp_list.split(",")]
    pi_url = f"http://{req.pi_host}:{req.pi_port}"

    results: dict[str, Any] = {
        "sweep_info": {
            "pi_host": req.pi_host,
            "pi_port": req.pi_port,
            "omp_values": omp_values,
            "concurrency": req.concurrency,
            "requests_per_test": req.requests_per_test,
            "timeout_per_request": req.timeout_per_request,
            "output_dir": req.output_dir,
        },
        "scenarios": {},
        "failed_scenarios": [],
    }

    for omp in omp_values:
        label = f"omp_{omp}"
        try:
            await _set_omp_on_pi(req.pi_host, omp)
        except RuntimeError as e:
            results["scenarios"][label] = {"status": "error", "detail": str(e)}
            results["failed_scenarios"].append(label)
            continue

        api_ok = await _wait_for_api(pi_url)
        if not api_ok:
            results["scenarios"][label] = {
                "status": "error",
                "detail": "API do Pi não respondeu após reinicialização",
            }
            results["failed_scenarios"].append(label)
            continue

        try:
            stress_result = await _run_single(
                pi_url, req.concurrency, req.requests_per_test,
                req.timeout_per_request, omp, req.output_dir,
            )
            results["scenarios"][label] = {
                "status": "ok",
                "duration_sec": stress_result["test_info"]["duration_sec"],
                "throughput_req_per_sec": stress_result["results"]["throughput_req_per_sec"],
                "error_rate_pct": stress_result["results"]["error_rate_pct"],
                "successful": stress_result["results"]["successful"],
                "failed": stress_result["results"]["failed"],
                "results_dir": os.path.join(req.output_dir, "sweep", f"omp_{omp}"),
            }
        except Exception as e:
            results["scenarios"][label] = {"status": "error", "detail": str(e)}
            results["failed_scenarios"].append(label)

    summary_path = _build_summary_csv(req.output_dir, omp_values)
    results["summary_file"] = summary_path

    return results
