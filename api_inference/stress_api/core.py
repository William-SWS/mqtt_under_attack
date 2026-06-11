"""
Módulo principal de stress test para a API de inferência MQTT.

Orquestra requisições HTTP concorrentes contra a API alvo (Raspberry Pi),
coleta estatísticas de latência, agrega resultados por modelo e persiste
em JSON com timestamp.

Uso típico:
    from stress_api.core import StressTestRequest, run_stress_test
    result = await run_stress_test(StressTestRequest(target_url="http://192.168.20.83:8000"))
"""

from __future__ import annotations

import asyncio
import csv
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
    """Modelo Pydantic para os parâmetros do teste de estresse.

    Attributes:
        target_url: URL base da API alvo (ex: http://192.168.20.83:8000).
        endpoint: Caminho do endpoint a ser testado.
                  /benchmark executa todos os modelos compatíveis.
                  /benchmark/{model_id} executa apenas um modelo.
                  /health e /models são testes leves sem inferência.
        concurrency: Número de requisições simultâneas (controla o semáforo asyncio).
        requests: Total de requisições a enviar durante o teste.
        timeout: Tempo máximo em segundos para aguardar cada requisição.
        output_dir: Diretório relativo onde o JSON de resultados será salvo.
    """

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
        """Define o método HTTP baseado no endpoint."""
        return "POST" if self.endpoint.startswith("/benchmark") else "GET"


# ── helpers ──────────────────────────────────────────────────


def _extract_model_runs(body: dict[str, Any] | None) -> list[dict[str, Any]]:
    """Extrai a lista de resultados de modelos do corpo da resposta da API.

    A API /benchmark retorna {"results": [...]} (todos os modelos),
    enquanto /benchmark/{model_id} retorna {"result": {...}} (um modelo).
    Esta função normaliza ambos os formatos para uma lista.
    """
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
    """Agrupa as execuções por model_id e calcula estatísticas agregadas.

    Para cada modelo, calcula:
    - Média, desvio padrão, mínimo, máximo e mediana (P50) dos tempos
    - Intervalo de confiança de 95% (distribuição normal: z=1.96)
    - Média, mínima e máxima da acurácia

    Args:
        model_runs: Lista plana de dicionários, cada um representando
                    a execução de um modelo em uma requisição.

    Returns:
        Dicionário {model_id: {estatísticas}} pronto para serializar em JSON.
    """
    by_model: dict[str, list[dict]] = defaultdict(list)
    for run in model_runs:
        by_model[run["model_id"]].append(run)

    aggregated: dict[str, dict] = {}
    for model_id, runs in sorted(by_model.items()):
        # Converte inference_time_sec (segundos) para ms
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
        # rows e n_features devem ser consistentes entre requisições
        if len(rows_set) == 1:
            base["rows"] = rows_set.pop()
        if len(n_feat_set) == 1:
            base["n_features"] = n_feat_set.pop()

        if times:
            avg = statistics.mean(times)
            std = statistics.stdev(times) if len(times) > 1 else 0.0
            n = len(times)
            se = std / math.sqrt(n)
            z = 1.96  # percentil 97.5 da normal → IC 95% bilateral
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
    """Calcula estatísticas descritivas de latência HTTP.

    Retorna média, mínimo, máximo e percentis (P50, P95, P99)
    da lista de latências medidas em milissegundos.
    """
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
    """Monta o dicionário completo de resposta do stress test.

    Combina metadados do teste, estatísticas de latência,
    agregação por modelo e dados de sistema (antes/depois).
    """
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
    """Gera o texto de sumário para exibição no terminal.

    Inclui throughput, latências (P50/P95/P99) e, quando aplicável,
    as estatísticas por modelo com intervalo de confiança.
    """
    successful = len(latencies_ms)
    failed = len(errors)
    timeouts = errors.count("timeout")
    throughput = (
        successful / total_duration_sec if total_duration_sec > 0 else 0.0
    )
    lat = _latency_stats(latencies_ms)
    has_latency = bool(lat)

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
    ]

    if has_latency:
        lines.extend([
            "",
            "--- Latency (ms) ---",
            (
                f"Avg: {lat['average']:.1f}  |  Min: {lat['min']:.1f}  |  "
                f"Max: {lat['max']:.1f}"
            ),
            f"P50: {lat['p50']:.1f}  |  P95: {lat['p95']:.1f}  |  P99: {lat['p99']:.1f}",
        ])
    else:
        lines.append("")
        lines.append("--- Latency (ms) --- N/A (nenhuma requisicao bem-sucedida)")

    model_agg = _aggregate_model_stats(model_runs)
    if model_agg:
        lines.append("")
        lines.append("--- Per Model ---")
        for model_id, agg in model_agg.items():
            if "inference_time_ms_avg" in agg:
                avg = agg["inference_time_ms_avg"]
                p50 = agg["inference_time_ms_p50"]
                std = agg.get("inference_time_ms_std", 0.0)
                ci_lower = agg.get("inference_time_ms_ci95_lower")
                ci_upper = agg.get("inference_time_ms_ci95_upper")
                acc = agg.get("accuracy_avg", "N/A")
                ci_str = (
                    f"  ci95=[{ci_lower:.1f}, {ci_upper:.1f}]ms"
                    if ci_lower is not None and ci_upper is not None
                    else ""
                )
                lines.append(
                    f"  {model_id}: {agg['requests']}x  "
                    f"avg={avg:.1f}ms  "
                    f"p50={p50:.1f}ms  "
                    f"std={std:.1f}ms"
                    f"{ci_str}  "
                    f"acc={acc}"
                )

    return "\n".join(lines)


# ── network ──────────────────────────────────────────────────


async def fetch_system_stats(
    client: httpx.AsyncClient, url: str
) -> dict[str, Any] | None:
    """Consulta o endpoint /stats da API alvo para capturar estado do sistema.

    Retorna uso de memória, CPUs, workers e load average do Pi.
    Se falhar (API ocupada ou instável), retorna None sem abortar o teste.
    """
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
    """Envia uma requisição HTTP para a API alvo com controle de concorrência.

    O semáforo (asyncio.Semaphore) garante que no máximo N requisições
    rodem simultaneamente. Cada requisição bem-sucedida registra:
    - latência da chamada HTTP (ms)
    - resultados dos modelos extraídos do corpo da resposta

    Args:
        client: Cliente HTTP compartilhado (httpx.AsyncClient).
        url: URL completa do endpoint alvo.
        method: Método HTTP (GET ou POST).
        timeout: Timeout da requisição em segundos.
        semaphore: Semáforo que limita a concorrência.
        latencies: Lista compartilhada para registrar latências.
        model_runs: Lista compartilhada para registrar resultados de modelos.
        errors: Lista compartilhada para registrar falhas.
    """
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
    """Função principal: executa o teste de estresse completo.

    Fluxo:
    1. Captura estado do sistema (Pi) antes do teste via GET /stats
    2. Dispara N requisições concorrentes contra o endpoint alvo
    3. Captura estado do sistema depois do teste
    4. Agrega resultados por modelo com IC 95%
    5. Salva JSON com timestamp em results_inference/
    6. Retorna dicionário completo com dados e sumário textual

    A concorrência é controlada por asyncio.Semaphore(concurrency),
    garantindo que o Pi não seja inundado com requisições além do
    limite configurado.
    """
    full_url = f"{request.target_url}{request.endpoint}"
    latencies: list[float] = []
    model_runs: list[dict[str, Any]] = []
    errors: list[str] = []
    semaphore = asyncio.Semaphore(request.concurrency)

    system_before: dict[str, Any] | None = None
    system_after: dict[str, Any] | None = None
    total_duration = 0.0

    async with httpx.AsyncClient() as client:
        system_before = await fetch_system_stats(client, request.target_url)

        start = time.perf_counter()
        try:
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
        except Exception:
            pass  # garante que o finally seja executado mesmo com crash
        finally:
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
    """Salva o resultado do stress test em JSON e CSV com timestamp.

    Gera dois arquivos no diretório configurado (padrão: results_inference/):
      - stress_test_YYYYMMDD_HHMMSS.json
      - stress_test_YYYYMMDD_HHMMSS.csv

    O diretório é criado automaticamente se não existir.

    Returns:
        Caminho absoluto do arquivo JSON salvo.
    """
    os.makedirs(request.output_dir, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")

    json_filename = f"stress_test_{timestamp}.json"
    json_path = os.path.join(request.output_dir, json_filename)
    data = build_response(
        request, latencies_ms, model_runs, errors, total_duration_sec,
        system_before, system_after, json_path,
    )
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    save_result_csv(
        request, latencies_ms, model_runs, errors, total_duration_sec,
        system_before, system_after, timestamp,
    )

    return json_path


def save_result_csv(
    request: StressTestRequest,
    latencies_ms: list[float],
    model_runs: list[dict[str, Any]],
    errors: list[str],
    total_duration_sec: float,
    system_before: dict[str, Any] | None,
    system_after: dict[str, Any] | None,
    timestamp: str,
) -> str:
    """Salva o resultado do stress test em CSV (uma linha por modelo).

    Colunas:
      - timestamp, target_url, endpoint, concurrency, requests
      - duration_sec, throughput_req_per_sec
      - uvicorn_workers, memory_used_mb, memory_available_mb, memory_total_mb
      - model_id, n_requests, inference_time_ms_*, accuracy_avg

    Returns:
        Caminho absoluto do arquivo CSV salvo.
    """
    csv_filename = f"stress_test_{timestamp}.csv"
    csv_path = os.path.join(request.output_dir, csv_filename)

    successful = len(latencies_ms)
    throughput = round(
        successful / total_duration_sec if total_duration_sec > 0 else 0.0, 2
    )
    workers = (
        system_before.get("uvicorn_workers", "N/A")
        if system_before
        else "N/A"
    )
    mem_used = (
        system_before.get("memory_used_mb", "N/A")
        if system_before
        else "N/A"
    )
    mem_avail = (
        system_before.get("memory_available_mb", "N/A")
        if system_before
        else "N/A"
    )
    mem_total = (
        system_before.get("memory_total_mb", "N/A")
        if system_before
        else "N/A"
    )

    fields = [
        "timestamp",
        "target_url",
        "endpoint",
        "concurrency",
        "requests",
        "duration_sec",
        "throughput_req_per_sec",
        "uvicorn_workers",
        "memory_used_mb",
        "memory_available_mb",
        "memory_total_mb",
        "model_id",
        "n_requests",
        "inference_time_ms_avg",
        "inference_time_ms_std",
        "inference_time_ms_min",
        "inference_time_ms_max",
        "inference_time_ms_p50",
        "inference_time_ms_ci95_lower",
        "inference_time_ms_ci95_upper",
        "accuracy_avg",
    ]

    meta = {
        "timestamp": timestamp,
        "target_url": request.target_url,
        "endpoint": request.endpoint,
        "concurrency": request.concurrency,
        "requests": request.requests,
        "duration_sec": round(total_duration_sec, 3),
        "throughput_req_per_sec": throughput,
        "uvicorn_workers": workers,
        "memory_used_mb": mem_used,
        "memory_available_mb": mem_avail,
        "memory_total_mb": mem_total,
    }

    model_agg = _aggregate_model_stats(model_runs)

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()

        if model_agg:
            for model_id, agg in model_agg.items():
                row = {**meta}
                row["model_id"] = model_id
                row["n_requests"] = agg.get("requests", "N/A")
                row["inference_time_ms_avg"] = agg.get("inference_time_ms_avg", "N/A")
                row["inference_time_ms_std"] = agg.get("inference_time_ms_std", "N/A")
                row["inference_time_ms_min"] = agg.get("inference_time_ms_min", "N/A")
                row["inference_time_ms_max"] = agg.get("inference_time_ms_max", "N/A")
                row["inference_time_ms_p50"] = agg.get("inference_time_ms_p50", "N/A")
                row["inference_time_ms_ci95_lower"] = agg.get("inference_time_ms_ci95_lower", "N/A")
                row["inference_time_ms_ci95_upper"] = agg.get("inference_time_ms_ci95_upper", "N/A")
                row["accuracy_avg"] = agg.get("accuracy_avg", "N/A")
                writer.writerow(row)
        else:
            # Endpoint sem modelo (ex: /health) — uma linha com N/A
            row = {**meta}
            row["model_id"] = "N/A"
            for col in fields[11:]:
                row.setdefault(col, "N/A")
            writer.writerow(row)

    return csv_path
