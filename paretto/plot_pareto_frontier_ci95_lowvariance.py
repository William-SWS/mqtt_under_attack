#!/usr/bin/env python3
"""
Fronteira de Pareto empírica: desempenho vs tempo dentro do IC95%.

Usa um único registro de benchmark (t16 — 5 modelos, 50 amostras cada,
mesma concorrência). O tempo de inferência de cada modelo é representado
pelo intervalo de confiança de 95% (lower / upper bounds).

Gera em paretto/:
  - pareto_frontier_ci95_lowvariance.csv
  - pareto_frontier_ci95_lowvariance.png
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
OUTPUT_CSV = PARETTO_DIR / "pareto_frontier_ci95_lowvariance.csv"
OUTPUT_PNG = PARETTO_DIR / "pareto_frontier_ci95_lowvariance.png"

# modelos lowvariance no CSV de stress
LOWVARIANCE_MODELS = [
    "lowvariance_lda",
    "lowvariance_decisiontree",
    "lowvariance_gradientboosting",
    "lowvariance_randomforest",
    "lowvariance_svm",
]

# mapeamento para nomes no CSV do Optuna
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
            "time_ms_lower": float(row["inference_time_ms_ci95_lower"]),
            "time_ms_upper": float(row["inference_time_ms_ci95_upper"]),
            "time_ms_mean": float(row["inference_time_ms_avg"]),
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


def compute_pareto(
    data: list[dict], time_key: str, prefix: str
) -> list[dict]:
    for b in data:
        b[f"dominated_{prefix}"] = False
        b[f"pareto_frontier_{prefix}"] = True
    for i, b in enumerate(data):
        for j, a in enumerate(data):
            if i == j:
                continue
            a_better_acc = a["combined"] >= b["combined"]
            a_faster = a[time_key] <= b[time_key]
            a_strictly = a["combined"] > b["combined"] or a[time_key] < b[time_key]
            if a_better_acc and a_faster and a_strictly:
                b[f"dominated_{prefix}"] = True
                b[f"pareto_frontier_{prefix}"] = False
                break
    return data


def save_csv(data: list[dict], path: Path) -> None:
    pd.DataFrame(data)[
        [
            "model_id",
            "time_ms_mean",
            "time_ms_lower",
            "time_ms_upper",
            "accuracy",
            "f1",
            "combined",
            "dominated_lower",
            "pareto_frontier_lower",
            "dominated_upper",
            "pareto_frontier_upper",
        ]
    ].to_csv(path, index=False)
    print(f"CSV salvo em: {path}")


def plot_frontier(data: list[dict], path: Path) -> None:
    fig, ax = plt.subplots(figsize=(14, 8))

    for d in data:
        color = "#ff7f0e" if not d["dominated_lower"] else "#1f77b4"
        marker = "D" if not d["dominated_lower"] else "o"
        size = 100 if not d["dominated_lower"] else 80
        z = 4 if not d["dominated_lower"] else 3

        ax.errorbar(
            d["time_ms_mean"],
            d["combined"] * 100,
            xerr=[[d["time_ms_mean"] - d["time_ms_lower"]],
                  [d["time_ms_upper"] - d["time_ms_mean"]],
                  ],
            fmt="none",
            ecolor="gray",
            alpha=0.5,
            capsize=3,
            zorder=2,
        )
        ax.scatter(
            d["time_ms_mean"],
            d["combined"] * 100,
            s=size,
            c=color,
            marker=marker,
            zorder=z,
        )

    frontier_lower = sorted(
        [d for d in data if not d["dominated_lower"]], key=lambda d: d["time_ms_lower"]
    )
    frontier_upper = sorted(
        [d for d in data if not d["dominated_upper"]], key=lambda d: d["time_ms_upper"]
    )

    if len(frontier_lower) >= 2:
        ax.plot(
            [d["time_ms_lower"] for d in frontier_lower],
            [d["combined"] * 100 for d in frontier_lower],
            linestyle="--",
            color="#ff7f0e",
            alpha=0.4,
            label="Fronteira (CI95 lower)",
            zorder=2,
        )
    if len(frontier_upper) >= 2:
        ax.plot(
            [d["time_ms_upper"] for d in frontier_upper],
            [d["combined"] * 100 for d in frontier_upper],
            linestyle=":",
            color="#d62728",
            alpha=0.4,
            label="Fronteira (CI95 upper)",
            zorder=2,
        )

    all_models = sorted(data, key=lambda d: d["time_ms_mean"])
    y_max = max(d["combined"] * 100 for d in all_models)
    for idx, d in enumerate(all_models):
        label = d["model_id"].replace("lowvariance_", "")
        text = (
            f"{label}\n({d['time_ms_mean']:.1f} ms; {d['combined'] * 100:.2f}%)"
        )
        xy = (d["time_ms_mean"], d["combined"] * 100)
        y_pos = d["combined"] * 100
        if y_pos > y_max - 2:
            xytext = (xy[0] * 1.4, y_pos - 1.5)
        elif idx % 2 == 0:
            xytext = (xy[0] * 1.4, y_pos + 1.0)
        else:
            xytext = (xy[0] * 0.6, y_pos - 1.5)
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
        "Fronteira de Pareto\n"
        "Modelos LowVariance",
        fontsize=14,
        fontweight="bold",
    )
    ax.set_xlabel("Tempo de inferência (ms)")
    ax.set_ylabel("Desempenho combinado (%)")
    ax.legend(loc="lower right", fontsize=9)
    ax.grid(True, linestyle="--", alpha=0.3)
    ax.set_axisbelow(True)

    """fig.text(
        0.01,
        -0.02,
        "Desempenho combinado = (acurácia_stress + F1_treino) / 2. "
        "Barras = IC95% do tempo médio (t-Student, n=50). "
        "SVM: sem F1, usa acurácia como proxy. "
        "Fonte: t16_workers4_concurrency15_allmodels.csv (Raspberry Pi).",
        fontsize=8,
        color="dimgray",
    )
"""
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
                "time_ms_mean": b["time_ms_mean"],
                "time_ms_lower": b["time_ms_lower"],
                "time_ms_upper": b["time_ms_upper"],
                "accuracy": b["accuracy"],
                "f1": f1 if f1 is not None else float("nan"),
                "combined": compute_combined(b["accuracy"], f1),
            }
        )

    data = compute_pareto(data, "time_ms_lower", "lower")
    data = compute_pareto(data, "time_ms_upper", "upper")

    save_csv(data, OUTPUT_CSV)
    plot_frontier(data, OUTPUT_PNG)

    print(f"\nFronteira de Pareto com IC95% ({len(data)} modelos):")
    for d in sorted(data, key=lambda x: x["time_ms_mean"]):
        status_lower = "FRONTEIRA" if d["pareto_frontier_lower"] else "dominado"
        status_upper = "FRONTEIRA" if d["pareto_frontier_upper"] else "dominado"
        f1_str = f"{d['f1']:.4f}" if pd.notna(d.get("f1")) else "n/a"
        print(
            f"  {d['model_id']:30s}  "
            f"lower={d['time_ms_lower']:>9.1f}  "
            f"mean={d['time_ms_mean']:>9.1f}  "
            f"upper={d['time_ms_upper']:>9.1f}  "
            f"acc={d['accuracy']:.4f}  f1={f1_str}  "
            f"combined={d['combined']:.4f}  "
            f"[lower:{status_lower} | upper:{status_upper}]"
        )


if __name__ == "__main__":
    main()