#!/usr/bin/env python3
"""
Estatísticas de inferência por execução com IC95% para modelos LowVariance.

Lê api_inference/results_inference/*.json, calcula por run × modelo:
  mean, std, variance, CV, IC95% (lower/upper), n amostras
e gera:
  - CSV detalhado com todas as métricas
  - PNG com barras agrupadas (execuções no eixo X, modelos como séries)
    e error bars do IC95%, escala log no eixo Y
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
    PROJ_ROOT / "api_inference" / "results_inference" / ("inference_stats_by_run_lowvariance.csv")
)
DEFAULT_PNG = (
    PROJ_ROOT / "api_inference" / "results_inference" / ("inference_stats_by_run_lowvariance.png")
)

MODEL_ORDER = [
    "lowvariance_lda",
    "lowvariance_decisiontree",
    "lowvariance_gradientboosting",
    "lowvariance_randomforest",
    "lowvariance_svm",
]


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


def load_stats(input_dir: Path) -> pd.DataFrame:
    rows = []
    for json_path in sorted(input_dir.glob("*.json")):
        with open(json_path) as f:
            data = json.load(f)
        run_id = json_path.stem.split("_")[0]
        per_model = data.get("per_model", {})
        for model_id, info in per_model.items():
            if not model_id.startswith("lowvariance_"):
                continue
            times_list = info.get("inference_times_ms", [])
            if not times_list:
                continue
            times = np.array(times_list, dtype=float)
            n = len(times)
            mean = float(np.mean(times))
            std = float(np.std(times, ddof=1))
            variance = std**2
            cv = std / mean if mean > 0 else float("nan")
            se = std / np.sqrt(n)
            t_crit = float(stats.t.ppf(0.975, df=n - 1))
            ci_lower = mean - t_crit * se
            ci_upper = mean + t_crit * se
            rows.append(
                {
                    "run_id": run_id,
                    "model_id": model_id,
                    "n_samples": n,
                    "mean_ms": mean,
                    "std_ms": std,
                    "variance_ms": variance,
                    "cv": cv,
                    "ci95_lower": ci_lower,
                    "ci95_upper": ci_upper,
                }
            )
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    # Ordena runs cronologicamente e modelos por ordem predefinida
    df["run_order"] = df["run_id"].astype(str)
    df["model_order"] = df["model_id"].map({m: i for i, m in enumerate(MODEL_ORDER)})
    df = df.sort_values(["run_order", "model_order"]).reset_index(drop=True)
    return df


def save_csv(df: pd.DataFrame, csv_path: Path) -> None:
    out = df.drop(columns=["run_order", "model_order"], errors="ignore")
    out.to_csv(csv_path, index=False)
    print(f"CSV salvo em: {csv_path}")


def plot_grouped_bars(df: pd.DataFrame, png_path: Path) -> None:
    if df.empty:
        return

    runs = sorted(df["run_id"].unique())
    models = sorted(
        df["model_id"].unique(),
        key=lambda m: MODEL_ORDER.index(m) if m in MODEL_ORDER else 99,
    )
    n_runs = len(runs)
    n_models = len(models)

    x = np.arange(n_runs)
    bar_width = 0.15
    offsets = np.linspace(
        -bar_width * (n_models - 1) / 2,
        bar_width * (n_models - 1) / 2,
        n_models,
    )

    fig, ax = plt.subplots(figsize=(16, 8))
    colors = plt.cm.tab10(np.linspace(0, 1, n_models))

    for i, model in enumerate(models):
        model_data = df[df["model_id"] == model].set_index("run_id").reindex(runs)
        means = model_data["mean_ms"].values
        ci_lower = model_data["ci95_lower"].values
        ci_upper = model_data["ci95_upper"].values
        yerr = [means - ci_lower, ci_upper - means]

        label = model.replace("lowvariance_", "")
        ax.bar(
            x + offsets[i],
            means,
            bar_width,
            yerr=yerr,
            capsize=3,
            label=label,
            color=colors[i],
            edgecolor="black",
            linewidth=0.3,
        )

    ax.set_yscale("log")
    ax.set_xticks(x)
    ax.set_xticklabels(runs, fontsize=9)
    ax.set_title(
        "Tempo de Inferência por Execução com IC95% (Modelos LowVariance)",
        fontsize=14,
        fontweight="bold",
    )
    ax.set_xlabel("Execução")
    ax.set_ylabel("Tempo de inferência (ms)")
    ax.legend(
        title="Modelo",
        bbox_to_anchor=(1.01, 1),
        loc="upper left",
        fontsize=9,
    )
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    ax.set_axisbelow(True)

    fig.text(
        0.01,
        -0.02,
        "IC95% via t-Student · CV = coeficiente de variação · n = amostras por run. "
        "Runs com condições variadas (concorrência 15–50, OMP 5–100).",
        fontsize=8,
        color="dimgray",
    )

    png_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(png_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"PNG salvo em: {png_path}")


def main() -> None:
    args = parse_args()
    df = load_stats(args.input_dir)
    if df.empty:
        raise SystemExit("Nenhum modelo LowVariance encontrado nos JSONs.")

    save_csv(df, args.csv)
    plot_grouped_bars(df, args.png)

    n_runs = df["run_id"].nunique()
    n_models = df["model_id"].nunique()
    print(f"\nResumo: {n_runs} execuções × {n_models} modelos = {len(df)} combinações")
    print("\nAmostra (primeiras 5 linhas):")
    display_cols = [
        "run_id",
        "model_id",
        "n_samples",
        "mean_ms",
        "std_ms",
        "variance_ms",
        "cv",
        "ci95_lower",
        "ci95_upper",
    ]
    print(df[display_cols].head().to_string(index=False))


if __name__ == "__main__":
    main()
