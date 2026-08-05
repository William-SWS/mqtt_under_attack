#!/usr/bin/env python3
"""
Gráfico de barras: uso de memória final do sistema por execução de stress test.

Lê api_inference/results_inference/*.json e gera um PNG com:
  - Eixo X: execução (t01..t16, em ordem cronológica) com o cenário de cada run
    (concorrência e OMP_NUM_THREADS extraídos do nome do arquivo)
  - Eixo Y: memória final do sistema em MB (system_after.memory_used_mb)
  - Barras coloridas por nível de concorrência (legenda)
  - Apenas execuções que benchmarkaram modelos LowVariance e têm medição pós-teste
"""

import argparse
import json
from pathlib import Path
import re

import matplotlib

matplotlib.use("Agg")  # roda sem display

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import pandas as pd

PROJ_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_DIR = PROJ_ROOT / "api_inference" / "results_inference"
DEFAULT_OUTPUT = (
    PROJ_ROOT / "api_inference" / "results_inference" / ("memory_final_by_execution.png")
)

PALETTE = ["#1f77b4", "#d62728", "#2ca02c", "#ff7f0e", "#9467bd"]

# Mapeamento de OMP_NUM_THREADS reconstruído do histórico de commits:
#   t03..t09 = sweep 5,10,20,30,40,50,100 (commits 837e27c, 1a20507, 63a9e47,
#              3305e0c, 7500473, ce07070, 0ac3f04; default do sweep_omp.py)
#   t11..t13 = runs SVM 100/50/40 (commits 3388e52, 47e1040; também no filename)
# t01, t02, t10, t14, t15, t16: valor não documentado no git.
OMP_THREADS_BY_RUN = {
    "t01": 5,
    "t02": 5,
    "t03": 5,
    "t04": 10,
    "t05": 20,
    "t06": 30,
    "t07": 40,
    "t08": 50,
    "t09": 100,
    "t11": 100,
    "t12": 50,
    "t13": 40,
    "t16": 40,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=DEFAULT_INPUT_DIR,
        help=f"Diretório com os JSONs de stress (default: {DEFAULT_INPUT_DIR})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"PNG de saída (default: {DEFAULT_OUTPUT})",
    )
    return parser.parse_args()


def load_runs(input_dir: Path) -> tuple[pd.DataFrame, list[str]]:
    rows = []
    excluded = []
    for json_path in sorted(input_dir.glob("*.json")):
        run_id = re.match(r"(t\d+)", json_path.name)
        run_id = run_id.group(1) if run_id else json_path.stem

        with open(json_path) as f:
            data = json.load(f)

        lowvariance_models = [m for m in data.get("per_model", {}) if m.startswith("lowvariance_")]
        mem_after = (data.get("system_after") or {}).get("memory_used_mb")

        if not lowvariance_models:
            excluded.append(f"{run_id}: sem modelos LowVariance benchmarkados")
            continue
        if mem_after is None:
            excluded.append(f"{run_id}: sem memory_used_after_mb")
            continue

        # OMP_NUM_THREADS não é gravado no JSON: vem do histórico de commits
        # (t03-t13) com fallback para o nome do arquivo
        omp_match = re.search(r"threads(\d+)", json_path.name)
        omp_threads = OMP_THREADS_BY_RUN.get(run_id)
        if omp_threads is None and omp_match:
            omp_threads = int(omp_match.group(1))
        rows.append(
            {
                "run": run_id,
                "timestamp": data["test_info"]["timestamp"],
                "memory_after_mb": float(mem_after),
                "concurrency": int(data["test_info"]["concurrency"]),
                "omp_threads": omp_threads,
            }
        )

    df = pd.DataFrame(rows).sort_values("timestamp").reset_index(drop=True)
    return df, excluded


def tick_label(row: pd.Series) -> str:
    lines = [row["run"], f"c={row['concurrency']}"]
    if pd.notna(row["omp_threads"]):
        lines.append(f"OMP={int(row['omp_threads'])}")
    else:
        lines.append("OMP n/d")
    return "\n".join(lines)


def plot_bars(df: pd.DataFrame, output_path: Path) -> None:
    concurrencies = sorted(df["concurrency"].unique(), reverse=True)
    color_map = {c: PALETTE[i % len(PALETTE)] for i, c in enumerate(concurrencies)}
    colors = df["concurrency"].map(color_map)

    fig, ax = plt.subplots(figsize=(13, 7))
    bars = ax.bar(df["run"], df["memory_after_mb"], color=colors)
    ax.bar_label(bars, fmt="%.0f MB", fontsize=9, padding=2)

    ax.set_xticks(range(len(df)))
    ax.set_xticklabels(df.apply(tick_label, axis=1), fontsize=8.5)

    legend_handles = [
        mpatches.Patch(color=color_map[c], label=f"{c} requisições simultâneas")
        for c in concurrencies
    ]
    ax.legend(
        handles=legend_handles,
        title="Cenário (concorrência)",
        bbox_to_anchor=(1.01, 1),
        loc="upper left",
    )

    fig.suptitle(
        "Uso de Memória Final do Sistema por Execução de Stress Test",
        fontsize=14,
        fontweight="bold",
    )
    ax.set_title(
        "Raspberry Pi · execuções com modelos LowVariance · ordem cronológica",
        fontsize=10,
    )
    ax.set_xlabel("Execução")
    ax.set_ylabel("Memória final (MB)")
    ax.set_ylim(top=ax.get_ylim()[1] * 1.12)  # espaço para os rótulos
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    ax.set_axisbelow(True)

    fig.text(
        0.01,
        -0.03,
        "c = concorrência (req. simultâneas) · OMP = OMP_NUM_THREADS · "
        "Config. fixa: 4 uvicorn workers · thread pool = 8 · 4 vCPUs (Pi). "
        "t03–t09: sweep OMP 5→100 (git history); t11–t13: SVM OMP variado; "
        "t01,t02,t16: OMP=5/5/40 (informado manualmente); t10: OMP n/d.",
        fontsize=8,
        color="dimgray",
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    args = parse_args()
    df, excluded = load_runs(args.input_dir)
    if df.empty:
        raise SystemExit("Nenhuma execução válida encontrada.")

    plot_bars(df, args.output)
    print(f"Gráfico salvo em: {args.output}")
    print(f"Execuções no gráfico: {len(df)}")
    for reason in excluded:
        print(f"  excluída -> {reason}")


if __name__ == "__main__":
    main()
