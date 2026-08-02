#!/usr/bin/env python3
"""
Fronteira de Pareto empírica: desempenho vs mediana do tempo de inferência.

Usa um único registro de benchmark (t16 — 5 modelos, 50 amostras cada,
mesma concorrência). O tempo de inferência é a mediana (p50) das 50
requisições por modelo.

Gera em paretto/:
  - pareto_frontier_median_lowvariance.csv
  - pareto_frontier_median_lowvariance.png
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd

PROJ_ROOT = Path(__file__).resolve().parents[1]
PARETTO_DIR = PROJ_ROOT / "paretto"
STRESS_CSV = (
    PROJ_ROOT
    / "api_inference"
    / "results_inference"
    / "t16_workers4_concurrency15_allmodels.csv"
)
OPTUNA_CSV = PROJ_ROOT / "reports_refactored" / "optuna_by_selector_results.csv"
OUTPUT_CSV = PARETTO_DIR / "pareto_frontier_median_lowvariance.csv"
OUTPUT_PNG = PARETTO_DIR / "pareto_frontier_median_lowvariance.png"

LOWVARIANCE_MODELS = [
    "lowvariance_lda",
    "lowvariance_decisiontree",
    "lowvariance_gradientboosting",
    "lowvariance_randomforest",
    "lowvariance_svm",
]

OPTUNA_NAME_MAP = {
    "lowvariance_lda": "LDA",
    "lowvariance_decisiontree": "DecisionTree",
    "lowvariance_gradientboosting": "GradientBoosting",
    "lowvariance_randomforest": "RandomForest",
    "lowvariance_svm": None,
}


def load_benchmark_record() -> dict[str, dict]:
    df = pd.read_csv(STRESS_CSV)
    result = {}
    for _, row in df.iterrows():
        model_id = row["model_id"]
        if model_id not in LOWVARIANCE_MODELS:
            continue
        result[model_id] = {
            "time_ms_p50": float(row["inference_time_ms_p50"]),
            "accuracy": float(row["accuracy"]),
        }
    return result


def load_f1_scores() -> dict[str, float]:
    df = pd.read_csv(OPTUNA_CSV)
    lv = df[df["seletor"] == "LowVariance"]
    result = {}
    for model_id, csv_name in OPTUNA_NAME_MAP.items():
        if csv_name is None:
            continue
        row = lv[lv["modelo"] == csv_name]
        if not row.empty:
            result[model_id] = float(row["f1"].iloc[0])
    return result


def compute_combined(accuracy: float, f1: float | None) -> float:
    return accuracy if f1 is None else (accuracy + f1) / 2


def compute_pareto(data: list[dict]) -> list[dict]:
    for b in data:
        b["dominated"] = False
        b["pareto_frontier"] = True
    for i, b in enumerate(data):
        for j, a in enumerate(data):
            if i == j:
                continue
            if (
                a["combined"] >= b["combined"]
                and a["time_ms_p50"] <= b["time_ms_p50"]
                and (a["combined"] > b["combined"] or a["time_ms_p50"] < b["time_ms_p50"])
            ):
                b["dominated"] = True
                b["pareto_frontier"] = False
                break
    return data


def save_csv(data: list[dict], path: Path) -> None:
    pd.DataFrame(data)[
        [
            "model_id",
            "time_ms_p50",
            "accuracy",
            "f1",
            "combined",
            "dominated",
            "pareto_frontier",
        ]
    ].to_csv(path, index=False)
    print(f"CSV salvo em: {path}")


def plot_frontier(data: list[dict], path: Path) -> None:
    dominated = [d for d in data if d["dominated"]]
    frontier = [d for d in data if not d["dominated"]]

    fig, ax = plt.subplots(figsize=(14, 8))

    if dominated:
        ax.scatter(
            [d["time_ms_p50"] for d in dominated],
            [d["combined"] * 100 for d in dominated],
            s=80,
            c="#1f77b4",
            label="Modelos dominados",
            zorder=3,
        )
    if frontier:
        ax.scatter(
            [d["time_ms_p50"] for d in frontier],
            [d["combined"] * 100 for d in frontier],
            s=100,
            c="#ff7f0e",
            marker="D",
            label="Soluções não dominadas (fronteira de Pareto)",
            zorder=4,
        )
    if len(frontier) >= 2:
        fs = sorted(frontier, key=lambda d: d["time_ms_p50"])
        ax.plot(
            [d["time_ms_p50"] for d in fs],
            [d["combined"] * 100 for d in fs],
            linestyle="--",
            color="#ff7f0e",
            alpha=0.6,
            label="Conexão visual da fronteira",
            zorder=2,
        )

    all_models = sorted(data, key=lambda d: d["time_ms_p50"])
    y_max = max(d["combined"] * 100 for d in all_models)
    for idx, d in enumerate(all_models):
        label = d["model_id"].replace("lowvariance_", "")
        text = f"{label}\n({d['time_ms_p50']:.1f} ms; {d['combined'] * 100:.2f}%)"
        xy = (d["time_ms_p50"], d["combined"] * 100)
        y_pos = d["combined"] * 100
        if y_pos > y_max - 2:
            xytext = (xy[0] * 1.3, y_pos - 1.5)
        elif idx % 2 == 0:
            xytext = (xy[0] * 1.3, y_pos + 1.0)
        else:
            xytext = (xy[0] * 0.7, y_pos - 1.5)
        ax.annotate(
            text,
            xy=xy,
            xytext=xytext,
            fontsize=8,
            ha="center",
            va="center",
            bbox={
                "boxstyle": "round,pad=0.3",
                "facecolor": "white",
                "alpha": 0.85,
                "edgecolor": "gray",
            },
            arrowprops={"arrowstyle": "->", "color": "gray", "lw": 0.8},
            zorder=5,
        )

    ax.set_xscale("log")
    ax.set_title(
        "Fronteira de Pareto",
        fontsize=14,
        fontweight="bold",
    )
    ax.set_xlabel("Tempo de inferência(ms)")
    ax.set_ylabel("Desempenho combinado (%)")
    ax.legend(loc="lower right", fontsize=9)
    ax.grid(True, linestyle="--", alpha=0.3)
    ax.set_axisbelow(True)

    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"PNG salvo em: {path}")


def main() -> None:
    benchmark = load_benchmark_record()
    f1_scores = load_f1_scores()

    data = []
    for model_id in LOWVARIANCE_MODELS:
        if model_id not in benchmark:
            print(f"  [aviso] {model_id}: não encontrado no CSV de stress")
            continue
        b = benchmark[model_id]
        f1 = f1_scores.get(model_id)
        data.append(
            {
                "model_id": model_id,
                "time_ms_p50": b["time_ms_p50"],
                "accuracy": b["accuracy"],
                "f1": f1 if f1 is not None else float("nan"),
                "combined": compute_combined(b["accuracy"], f1),
            }
        )

    data = compute_pareto(data)
    save_csv(data, OUTPUT_CSV)
    plot_frontier(data, OUTPUT_PNG)

    print(f"\nFronteira de Pareto com mediana p50 ({len(data)} modelos):")
    for d in sorted(data, key=lambda x: x["time_ms_p50"]):
        status = "FRONTEIRA" if d["pareto_frontier"] else "dominado"
        f1_str = f"{d['f1']:.4f}" if pd.notna(d.get("f1")) else "n/a"
        print(
            f"  {d['model_id']:30s}  "
            f"p50={d['time_ms_p50']:>9.1f} ms  "
            f"acc={d['accuracy']:.4f}  f1={f1_str}  "
            f"combined={d['combined']:.4f}  [{status}]"
        )


if __name__ == "__main__":
    main()
