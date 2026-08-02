#!/usr/bin/env python3
"""
Tempo médio de inferência com IC95% para modelos LowVariance (dados agregados).

Lê api_inference/results_inference/*.json, coleta todos os tempos de inferência
por modelo (pool de todas as execuções) e gera:
  - CSV com estatísticas detalhadas (média, desvio, n, IC95%)
  - PNG com barras de média e error bars do IC95%
"""

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

PROJ_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_DIR = PROJ_ROOT / "api_inference" / "results_inference"
DEFAULT_CSV = (
    PROJ_ROOT / "api_inference" / "results_inference" / ("inference_time_ci95_lowvariance.csv")
)
DEFAULT_PNG = (
    PROJ_ROOT / "api_inference" / "results_inference" / ("inference_time_ci95_lowvariance.png")
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=DEFAULT_INPUT_DIR,
        help=f"Diretório com os JSONs de stress (default: {DEFAULT_INPUT_DIR})",
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=DEFAULT_CSV,
        help=f"CSV de saída (default: {DEFAULT_CSV})",
    )
    parser.add_argument(
        "--png",
        type=Path,
        default=DEFAULT_PNG,
        help=f"PNG de saída (default: {DEFAULT_PNG})",
    )
    return parser.parse_args()


def load_all_times(input_dir: Path) -> dict[str, list[float]]:
    model_times: dict[str, list[float]] = {}
    model_runs: dict[str, set[str]] = {}
    for json_path in sorted(input_dir.glob("*.json")):
        with open(json_path) as f:
            data = json.load(f)
        per_model = data.get("per_model", {})
        run_id = json_path.stem.split("_")[0]  # e.g. "t01"
        for model_id, info in per_model.items():
            if not model_id.startswith("lowvariance_"):
                continue
            times = info.get("inference_times_ms", [])
            if not times:
                continue
            model_times.setdefault(model_id, []).extend(times)
            model_runs.setdefault(model_id, set()).add(run_id)
    return model_times, model_runs


def compute_stats(model_times: dict, model_runs: dict) -> pd.DataFrame:
    rows = []
    for model_id, times in model_times.items():
        arr = np.array(times, dtype=float)
        n = len(arr)
        mean = float(np.mean(arr))
        std = float(np.std(arr, ddof=1))
        se = std / np.sqrt(n)
        t_crit = float(stats.t.ppf(0.975, df=n - 1))
        ci_lower = mean - t_crit * se
        ci_upper = mean + t_crit * se
        rows.append(
            {
                "model_id": model_id,
                "n_samples": n,
                "n_runs": len(model_runs.get(model_id, set())),
                "mean_ms": mean,
                "std_ms": std,
                "ci95_lower": ci_lower,
                "ci95_upper": ci_upper,
            }
        )
    df = pd.DataFrame(rows).sort_values("mean_ms").reset_index(drop=True)
    return df


def save_csv(df: pd.DataFrame, csv_path: Path) -> None:
    df.to_csv(csv_path, index=False)
    print(f"CSV salvo em: {csv_path}")


def plot_bars(df: pd.DataFrame, png_path: Path) -> None:
    labels = df["model_id"].str.replace("lowvariance_", "")
    means = df["mean_ms"]
    ci_lower = df["mean_ms"] - df["ci95_lower"]
    ci_upper = df["ci95_upper"] - df["mean_ms"]

    fig, ax = plt.subplots(figsize=(12, 7))
    bars = ax.bar(
        labels,
        means,
        yerr=[ci_lower, ci_upper],
        capsize=5,
        color="#1f77b4",
        edgecolor="black",
        linewidth=0.5,
    )

    # Rótulos de média sobre cada barra
    for bar, val in zip(bars, means):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() * 1.05,
            f"{val:.1f} ms",
            ha="center",
            va="bottom",
            fontsize=8,
        )

    ax.set_yscale("log")
    ax.set_title(
        "Tempo Médio de Inferência com IC95% (Modelos LowVariance)",
        fontsize=14,
        fontweight="bold",
    )
    ax.set_xlabel("Modelo")
    ax.set_ylabel("Tempo de inferência (ms)")
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    ax.set_axisbelow(True)

    fig.text(
        0.01,
        -0.02,
        "IC95% calculado via t-Student · n = total de requisições agregadas. "
        "Runs com condições variadas (concorrência 15–50, OMP 5–100); "
        "a média agregada é ponderada pelas condições de cada execução.",
        fontsize=8,
        color="dimgray",
    )

    png_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(png_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"PNG salvo em: {png_path}")


def main() -> None:
    args = parse_args()
    model_times, model_runs = load_all_times(args.input_dir)
    if not model_times:
        raise SystemExit("Nenhum modelo LowVariance encontrado nos JSONs.")

    df = compute_stats(model_times, model_runs)
    save_csv(df, args.csv)
    plot_bars(df, args.png)

    print(f"\nResumo ({len(df)} modelos):")
    for _, row in df.iterrows():
        print(
            f"  {row['model_id']:30s}  mean={row['mean_ms']:>10.1f} ms  "
            f"IC95%=[{row['ci95_lower']:>10.1f}, {row['ci95_upper']:>10.1f}]  "
            f"n={row['n_samples']} ({row['n_runs']} runs)"
        )


if __name__ == "__main__":
    main()
