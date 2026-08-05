#!/usr/bin/env python3
"""
Gráfico de barras agrupadas: acurácia por técnica de seleção de features.

Lê reports_refactored/optuna_by_selector_results.csv (modelos otimizados com Optuna)
e gera um PNG com:
  - Eixo X: técnicas de seleção de features (ordenadas pela melhor acurácia)
  - Eixo Y: acurácia (zoom 0.90-0.98, com rótulos sobre as barras)
  - Séries: modelos otimizados (uma barra por modelo em cada seletor)
"""

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # roda sem display

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

PROJ_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = PROJ_ROOT / "reports_refactored" / "optuna_by_selector_results.csv"
DEFAULT_OUTPUT = PROJ_ROOT / "reports_refactored" / "accuracy_by_selector_optuna.png"

MODEL_ORDER = ["DecisionTree", "GradientBoosting", "RandomForest", "LDA", "QDA", "GaussianNB"]
Y_MIN, Y_MAX = 0.90, 0.98


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help=f"CSV de resultados (default: {DEFAULT_INPUT})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"PNG de saída (default: {DEFAULT_OUTPUT})",
    )
    return parser.parse_args()


def load_results(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    required = {"seletor", "modelo", "accuracy"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Colunas ausentes em {csv_path}: {sorted(missing)}")
    return df


def plot_grouped_bars(df: pd.DataFrame, output_path: Path) -> None:
    # Ordena seletores pela melhor acurácia (desc), mantendo a ordem do CSV em empates
    best_by_selector = df.groupby("seletor", sort=False)["accuracy"].max()
    selector_order = best_by_selector.sort_values(ascending=False, kind="stable").index.tolist()

    hue_order = [m for m in MODEL_ORDER if m in set(df["modelo"])]

    fig, ax = plt.subplots(figsize=(14, 7))
    sns.barplot(
        data=df,
        x="seletor",
        y="accuracy",
        hue="modelo",
        order=selector_order,
        hue_order=hue_order,
        ax=ax,
    )

    # Rótulos de valor sobre cada barra
    for container in ax.containers:
        ax.bar_label(container, fmt="%.4f", fontsize=7, rotation=90, padding=2)

    ax.set_ylim(Y_MIN, Y_MAX)
    ax.set_title(
        "Acurácia por Técnica de Seleção de Features\n",
        fontsize=13,
    )
    ax.set_xlabel("Técnica de Seleção de Features")
    ax.set_ylabel("Acurácia")
    ax.legend(title="Modelo", bbox_to_anchor=(1.01, 1), loc="upper left")
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    ax.set_axisbelow(True)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    args = parse_args()
    df = load_results(args.input)
    plot_grouped_bars(df, args.output)
    print(f"Gráfico salvo em: {args.output}")


if __name__ == "__main__":
    main()
