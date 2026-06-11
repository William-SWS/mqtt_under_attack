"""
Varredura automática de OMP_NUM_THREADS no Raspberry Pi.

Para cada valor de OMP (padrão: 5, 10, 20, 30, 40, 50, 100):
  1. Altera OMP_NUM_THREADS no docker-compose.yml do Pi via SSH
  2. Reinicia o container (docker compose down && up -d)
  3. Aguarda a API do Pi ficar saudável
  4. Executa o stress test (concurrency=50, requests=50)
  5. Salva JSON + CSV em results_inference/sweep/omp_{N}/

Ao final, gera results_inference/sweep/omp_summary.csv consolidado.

Uso:
    python sweep_omp.py
    python sweep_omp.py --pi-host 192.168.20.83 --omp-list "5,10,20" --concurrency 50 --requests 50
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import httpx

# ── garante que o módulo stress_api seja encontrável ────────
sys.path.insert(0, str(Path(__file__).resolve().parent))

from stress_api.core import StressTestRequest, run_stress_test
import asyncio


def ssh(host: str, cmd: str) -> subprocess.CompletedProcess:
    """Executa um comando via SSH no Pi e retorna o resultado."""
    full_cmd = ["ssh", host, cmd]
    return subprocess.run(
        full_cmd, capture_output=True, text=True, timeout=120,
    )


def set_omp_on_pi(host: str, omp_value: int) -> None:
    """Altera OMP_NUM_THREADS no docker-compose.yml do Pi e reinicia o container."""
    print(f"  [Pi] Alterando OMP_NUM_THREADS para {omp_value}...")

    # Atualiza a env var no docker-compose.yml
    result = ssh(
        host,
        f"cd ~/api_inference && "
        f"sed -i 's/OMP_NUM_THREADS: .*/OMP_NUM_THREADS: {omp_value}/' docker-compose.yml && "
        f"sed -i 's/OPENBLAS_NUM_THREADS: .*/OPENBLAS_NUM_THREADS: {omp_value}/' docker-compose.yml",
    )
    if result.returncode != 0:
        print(f"  [Pi] ERRO ao alterar docker-compose.yml: {result.stderr.strip()}")
        raise RuntimeError("Falha ao alterar OMP no Pi")

    # Reinicia o container (sem rebuild)
    result = ssh(
        host,
        "docker kill $(docker ps -q --filter publish=8000) 2>/dev/null; "
        "docker rm -f $(docker ps -aq --filter publish=8000) 2>/dev/null; "
        "sleep 2; "
        "cd ~/api_inference && docker compose up -d",
    )
    if result.returncode != 0:
        print(f"  [Pi] ERRO ao reiniciar container: {result.stderr.strip()}")
        raise RuntimeError("Falha ao reiniciar container no Pi")


def wait_for_api(url: str, timeout_sec: int = 120, interval_sec: int = 3) -> bool:
    """Aguarda a API do Pi responder GET /health.

    Retorna True se a API ficou saudável dentro do timeout.
    """
    print(f"  [PC] Aguardando API em {url}/health ...", end="", flush=True)
    deadline = time.time() + timeout_sec
    with httpx.Client(timeout=10.0) as client:
        while time.time() < deadline:
            try:
                resp = client.get(f"{url}/health")
                if resp.status_code == 200:
                    print(" OK")
                    return True
            except Exception:
                pass
            print(".", end="", flush=True)
            time.sleep(interval_sec)
    print(" TIMEOUT")
    return False


def run_single_stress(pi_url: str, concurrency: int, requests: int, omp_value: int) -> dict:
    """Executa um stress test contra o Pi e retorna o resultado.

    O output_dir é ajustado para results_inference/sweep/omp_{N}/
    para organizar os resultados por cenário.
    """
    output_dir = f"results_inference/sweep/omp_{omp_value}"
    print(f"  [PC] Stress test: concurrency={concurrency}, requests={requests}")
    print(f"  [PC] Resultados em: {output_dir}/")

    req = StressTestRequest(
        target_url=pi_url,
        endpoint="/benchmark",
        concurrency=concurrency,
        requests=requests,
        timeout=120.0,
        output_dir=output_dir,
    )

    return asyncio.run(run_stress_test(req))


def build_summary_csv(base_dir: str, omp_values: list[int]) -> str:
    """Consolida todos os resultados em um único CSV comparativo.

    Lê os JSONs de cada diretório omp_{N}/ e extrai:
    - omp_threads, model_id, n_samples, avg_ms, ci95_lower, ci95_upper
    - throughput, memory_used_mb, uvicorn_workers

    Returns:
        Caminho do CSV gerado.
    """
    rows: list[dict] = []
    base = Path(base_dir) / "results_inference" / "sweep"

    for omp in omp_values:
        omp_dir = base / f"omp_{omp}"
        if not omp_dir.exists():
            print(f"  [AVISO] Diretório não encontrado: {omp_dir}")
            continue

        jsons = sorted(omp_dir.glob("stress_test_*.json"))
        if not jsons:
            print(f"  [AVISO] Nenhum JSON em {omp_dir}")
            continue

        latest = jsons[-1]
        with open(latest) as f:
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
        print("  [AVISO] Nenhum dado para consolidar.")
        return ""

    summary_path = base / "omp_summary.csv"
    os.makedirs(base, exist_ok=True)

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

    print(f"\n  [PC] Resumo consolidado: {summary_path}")
    return str(summary_path)


def print_separator(title: str) -> None:
    width = 70
    side = (width - len(title) - 2) // 2
    print("\n" + "=" * width)
    print(" " * side + title + " " * (width - side - len(title)))
    print("=" * width)


def main():
    parser = argparse.ArgumentParser(description="Varredura OMP_NUM_THREADS no Pi")
    parser.add_argument("--pi-host", default="192.168.20.83", help="IP do Raspberry Pi")
    parser.add_argument(
        "--omp-list", default="5,10,20,30,40,50,100",
        help="Valores de OMP_NUM_THREADS separados por vírgula",
    )
    parser.add_argument("--concurrency", type=int, default=50, help="Concorrência do stress test")
    parser.add_argument("--requests", type=int, default=50, help="Requisições por cenário")
    parser.add_argument("--output-dir", default="results_inference",
                        help="Diretório base para resultados")
    args = parser.parse_args()

    omp_values = [int(v.strip()) for v in args.omp_list.split(",")]
    pi_url = f"http://{args.pi_host}:8000"

    print(f"Pi host:        {args.pi_host}")
    print(f"OMP values:     {omp_values}")
    print(f"Concurrency:    {args.concurrency}")
    print(f"Requests/test:  {args.requests}")
    print()

    for i, omp in enumerate(omp_values, 1):
        print_separator(f"CENÁRIO {i}/{len(omp_values)} — OMP_NUM_THREADS = {omp}")

        # 1. Altera OMP no Pi e reinicia container
        try:
            set_omp_on_pi(args.pi_host, omp)
        except RuntimeError as e:
            print(f"  [ERRO] {e}. Pulando cenário {omp}.")
            continue

        # 2. Aguarda API ficar saudável
        if not wait_for_api(pi_url, timeout_sec=120):
            print(f"  [ERRO] API do Pi não respondeu após alterar OMP para {omp}. Pulando.")
            continue

        # 3. Executa stress test
        try:
            result = run_single_stress(pi_url, args.concurrency, args.requests, omp)
        except Exception as e:
            print(f"  [ERRO] Stress test falhou para OMP={omp}: {e}")
            continue

        # 4. Exibe sumário
        print(result.get("_summary", "(sem sumário)"))

    # 5. Gera CSV consolidado
    print_separator("RESUMO CONSOLIDADO")
    build_summary_csv(args.output_dir, omp_values)

    print("\nVarredura concluída.")
    print(f"Resultados individuais:  {args.output_dir}/sweep/omp_*/")
    print(f"Resumo consolidado:     {args.output_dir}/sweep/omp_summary.csv")


if __name__ == "__main__":
    main()
