#!/usr/bin/env python3
"""
Fronteira de Pareto empírica: desempenho de classificação vs tempo de inferência.

Modelos LowVariance (lda, decisiontree, gradientboosting, randomforest, svm).
Métrica Y = (acurácia_stress + F1_treino) / 2.
Métrica X = tempo médio de inferência (ms) com IC95%.

Gera em paretto/:
  - pareto_frontier_lowvariance.csv (tabela com dominância)
  - pareto_frontier_lowvariance.png (gráfico estilo referência)
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
OUTPUT_CSV = PARETTO_DIR / "pareto_frontier_lowvariance.csv"
OUTPUT_PNG = PARETTO_DIR / "pareto_frontier_lowvariance.png"

# Acurácia do stress test (stress_report.md seção 3)
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
            "time_ms": row["mean_ms"],
            "ci95_lower": row["ci95_lower"],
            "ci95_upper": row["ci95_upper"],
        }
        for _, row in df.iterrows()
    }


def load_f1_scores() -> dict[str, float]:
    df = pd.read_csv(OPTUNA_CSV)
    lv = df[df["seletor"] == "LowVariance"]
    # Nomes no CSV: DecisionTree, GradientBoosting, etc. (capitalizados)
    name_map = {
        "lowvariance_lda": "LDA",
        "lowvariance_decisiontree": "DecisionTree",
        "lowvariance_gradientboosting": "GradientBoosting",
        "lowvariance_randomforest": "RandomForest",
        "lowvariance_svm": None,  # SVM não está no CSV de treino Optuna
    }
    result = {}
    for model_id, csv_name in name_map.items():
        if csv_name is None:
            continue
        row = lv[lv["modelo"] == csv_name]
        if not row.empty:
            result[model_id] = float(row["f1"].iloc[0])
    return result


def compute_combined(accuracy: float, f1: float | None) -> float:
    if f1 is None:
        return accuracy  # svm: sem F1, usa acurácia como proxy
    return (accuracy + f1) / 2


def compute_pareto(data: list[dict]) -> list[dict]:
    """Marca cada modelo como dominado ou não (fronteira de Pareto)."""
    for b in data:
        b["dominated"] = False
        b["pareto_frontier"] = True

    for i, b in enumerate(data):
        for j, a in enumerate(data):
            if i == j:
                continue
            # A domina B se: A melhor ou igual em tudo E estritamente melhor em ≥1
            a_better_combined = a["combined"] >= b["combined"]
            a_faster = a["time_ms"] <= b["time_ms"]
            a_strictly_better = a["combined"] > b["combined"] or a["time_ms"] < b["time_ms"]
            if a_better_combined and a_faster and a_strictly_better:
                b["dominated"] = True
                b["pareto_frontier"] = False
                break
    return data


def save_csv(data: list[dict], path: Path) -> None:
    df = pd.DataFrame(data)
    df = df[
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
    ]
    df.to_csv(path, index=False)
    print(f"CSV salvo em: {path}")


def plot_frontier(data: list[dict], path: Path) -> None:
    dominated = [d for d in data if d["dominated"]]
    frontier = [d for d in data if not d["dominated"]]

    fig, ax = plt.subplots(figsize=(14, 8))

    # Pontos dominados
    if dominated:
        ax.scatter(
            [d["time_ms"] for d in dominated],
            [d["combined"] * 100 for d in dominated],
            s=80,
            c="#1f77b4",
            label="Modelos dominados",
            zorder=3,
        )

    # Fronteira de Pareto
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

    # Linha tracejada conectando a fronteira (ordenada por tempo)
    if len(frontier) >= 2:
        frontier_sorted = sorted(frontier, key=lambda d: d["time_ms"])
        ax.plot(
            [d["time_ms"] for d in frontier_sorted],
            [d["combined"] * 100 for d in frontier_sorted],
            linestyle="--",
            color="#ff7f0e",
            alpha=0.6,
            label="Conexão visual da fronteira",
            zorder=2,
        )

    # Labels com caixas de texto e setas
    all_models = sorted(data, key=lambda d: d["time_ms"])
    y_max = max(d["combined"] * 100 for d in all_models)
    for d in all_models:
        label = d["model_id"].replace("lowvariance_", "")
        text = f"{label}\n({d['time_ms']:.1f} ms; {d['combined'] * 100:.2f}%)"
        xy = (d["time_ms"], d["combined"] * 100)
        idx = all_models.index(d)
        y_pos = d["combined"] * 100
        if y_pos > y_max - 2:
            xytext = (xy[0] * 1.3, y_pos - 1.5)
        elif idx % 2 == 0:
            xytext = (xy[0] * 1.3, y_pos + 1.0)
        else:
            xytext = (xy[0] * 0.7, y_pos - 1.5)
        arrowstyle = "->"

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
            arrowprops={"arrowstyle": arrowstyle, "color": "gray", "lw": 0.8},
            zorder=5,
        )

    ax.set_xscale("log")
    ax.set_title(
        "Fronteira de Pareto empírica entre desempenho de classificação\n"
        "e tempo de inferência (Modelos LowVariance)",
        fontsize=14,
        fontweight="bold",
    )
    ax.set_xlabel("Tempo de inferência (ms)")
    ax.set_ylabel("Desempenho combinado (%)")
    ax.legend(loc="lower right", fontsize=9)
    ax.grid(True, linestyle="--", alpha=0.3)
    ax.set_axisbelow(True)

    fig.text(
        0.01,
        -0.02,
        "Desempenho combinado = (acurácia_stress + F1_treino) / 2. "
        "IC95% do tempo via t-Student. SVM: sem F1 registrado, usa acurácia como proxy.",
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
            print(f"  [aviso] {model_id}: sem dados de tempo de inferência")
            continue
        t = times[model_id]
        f1 = f1_scores.get(model_id)
        combined = compute_combined(acc, f1)
        data.append(
            {
                "model_id": model_id,
                "time_ms": t["time_ms"],
                "ci95_lower": t["ci95_lower"],
                "ci95_upper": t["ci95_upper"],
                "accuracy": acc,
                "f1": f1 if f1 is not None else float("nan"),
                "combined": combined,
            }
        )

    data = compute_pareto(data)
    save_csv(data, OUTPUT_CSV)
    plot_frontier(data, OUTPUT_PNG)

    # Resumo no terminal
    print(f"\nFronteira de Pareto ({len(data)} modelos):")
    for d in sorted(data, key=lambda x: x["time_ms"]):
        status = "FRONTEIRA" if d["pareto_frontier"] else "dominado"
        f1_str = f"{d['f1']:.4f}" if pd.notna(d["f1"]) else "n/a"
        print(
            f"  {d['model_id']:30s}  time={d['time_ms']:>10.1f} ms  "
            f"acc={d['accuracy']:.3f}  f1={f1_str}  "
            f"combined={d['combined']:.4f}  [{status}]"
        )


if __name__ == "__main__":
    main()
