#!/usr/bin/env python3
"""
Fronteira de Pareto empírica: desempenho vs tempo POR REGISTRO individual.

Igual ao plot_pareto_frontier_lowvariance.py, mas divide os tempos de batch
(18925 linhas por requisição) para obter ms por registro individual.

Gera em paretto/:
  - pareto_frontier_per_record_lowvariance.csv
  - pareto_frontier_per_record_lowvariance.png
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd

PROJ_ROOT = Path(__file__).resolve().parents[1]
PARETTO_DIR = PROJ_ROOT / "paretto"
INFERENCE_CSV = (
    PROJ_ROOT / "api_inference" / "results_inference" / "inference_time_ci95_lowvariance.csv"
)
OPTUNA_CSV = PROJ_ROOT / "reports_refactored" / "optuna_by_selector_results.csv"
OUTPUT_CSV = PARETTO_DIR / "pareto_frontier_per_record_lowvariance.csv"
OUTPUT_PNG = PARETTO_DIR / "pareto_frontier_per_record_lowvariance.png"

# ponytail: 18925 linhas em cada dataset de teste — confirmado via wc -l
N_ROWS = 18925

ACCURACY = {
    "lowvariance_lda": 0.924,
    "lowvariance_decisiontree": 0.969,
    "lowvariance_gradientboosting": 0.975,
    "lowvariance_randomforest": 0.974,
    "lowvariance_svm": 0.929,
}


def load_inference_times() -> dict[str, dict]:
    df = pd.read_csv(INFERENCE_CSV)
    return {
        row["model_id"]: {
            "time_ms": row["mean_ms"] / N_ROWS,
            "ci95_lower": row["ci95_lower"] / N_ROWS,
            "ci95_upper": row["ci95_upper"] / N_ROWS,
        }
        for _, row in df.iterrows()
    }


def load_f1_scores() -> dict[str, float]:
    df = pd.read_csv(OPTUNA_CSV)
    lv = df[df["seletor"] == "LowVariance"]
    name_map = {
        "lowvariance_lda": "LDA",
        "lowvariance_decisiontree": "DecisionTree",
        "lowvariance_gradientboosting": "GradientBoosting",
        "lowvariance_randomforest": "RandomForest",
        "lowvariance_svm": None,
    }
    return {
        model_id: float(lv[lv["modelo"] == csv_name]["f1"].iloc[0])
        for model_id, csv_name in name_map.items()
        if csv_name is not None and not lv[lv["modelo"] == csv_name].empty
    }


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
                and a["time_ms"] <= b["time_ms"]
                and (a["combined"] > b["combined"] or a["time_ms"] < b["time_ms"])
            ):
                b["dominated"] = True
                b["pareto_frontier"] = False
                break
    return data


def save_csv(data: list[dict], path: Path) -> None:
    pd.DataFrame(data)[
        [
            "model_id",
            "time_ms",
            "ci95_lower",
            "ci95_upper",
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
            [d["time_ms"] for d in dominated],
            [d["combined"] * 100 for d in dominated],
            s=80,
            c="#1f77b4",
            label="Modelos dominados",
            zorder=3,
        )
    if frontier:
        ax.scatter(
            [d["time_ms"] for d in frontier],
            [d["combined"] * 100 for d in frontier],
            s=100,
            c="#ff7f0e",
            marker="D",
            label="Soluções não dominadas (fronteira de Pareto)",
            zorder=4,
        )
    if len(frontier) >= 2:
        fs = sorted(frontier, key=lambda d: d["time_ms"])
        ax.plot(
            [d["time_ms"] for d in fs],
            [d["combined"] * 100 for d in fs],
            linestyle="--",
            color="#ff7f0e",
            alpha=0.6,
            label="Conexão visual da fronteira",
            zorder=2,
        )

    all_models = sorted(data, key=lambda d: d["time_ms"])
    y_max = max(d["combined"] * 100 for d in all_models)
    for idx, d in enumerate(all_models):
        label = d["model_id"].replace("lowvariance_", "")
        text = f"{label}\n({d['time_ms'] * 1000:.3f} ms; {d['combined'] * 100:.2f}%)"
        xy = (d["time_ms"], d["combined"] * 100)
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
        "Fronteira de Pareto empírica entre desempenho de classificação\n"
        "e tempo de inferência por registro (Modelos LowVariance)",
        fontsize=14,
        fontweight="bold",
    )
    ax.set_xlabel("Tempo de inferência por registro (ms)")
    ax.set_ylabel("Desempenho combinado (%)")
    ax.legend(loc="lower right", fontsize=9)
    ax.grid(True, linestyle="--", alpha=0.3)
    ax.set_axisbelow(True)

    fig.text(
        0.01,
        -0.02,
        "Desempenho combinado = (acurácia_stress + F1_treino) / 2. "
        "Tempos divididos por 18925 (linhas por dataset de teste). "
        "IC95% via t-Student. SVM: sem F1, usa acurácia como proxy.",
        fontsize=8,
        color="dimgray",
    )

    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"PNG salvo em: {path}")


def main() -> None:
    times = load_inference_times()
    f1_scores = load_f1_scores()

    data = []
    for model_id, acc in ACCURACY.items():
        if model_id not in times:
            print(f"  [aviso] {model_id}: sem dados de tempo")
            continue
        t = times[model_id]
        f1 = f1_scores.get(model_id)
        data.append(
            {
                "model_id": model_id,
                "time_ms": t["time_ms"],
                "ci95_lower": t["ci95_lower"],
                "ci95_upper": t["ci95_upper"],
                "accuracy": acc,
                "f1": f1 if f1 is not None else float("nan"),
                "combined": compute_combined(acc, f1),
            }
        )

    data = compute_pareto(data)
    save_csv(data, OUTPUT_CSV)
    plot_frontier(data, OUTPUT_PNG)

    print(f"\nFronteira de Pareto por registro ({len(data)} modelos):")
    for d in sorted(data, key=lambda x: x["time_ms"]):
        status = "FRONTEIRA" if d["pareto_frontier"] else "dominado"
        f1_str = f"{d['f1']:.4f}" if pd.notna(d["f1"]) else "n/a"
        print(
            f"  {d['model_id']:30s}  time={d['time_ms'] * 1000:>8.3f} ms/reg  "
            f"acc={d['accuracy']:.3f}  f1={f1_str}  "
            f"combined={d['combined']:.4f}  [{status}]"
        )


if __name__ == "__main__":
    main()
