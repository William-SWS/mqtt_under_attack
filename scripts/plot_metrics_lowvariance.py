#!/usr/bin/env python3
"""
Gráfico de barras agrupadas: métricas de avaliação (%) por técnica de ML.

Lê reports_refactored/optuna_by_selector_results.csv, filtra um seletor de features
(default: LowVariance) e gera um PNG com:
  - Eixo X: técnicas de ML (modelos otimizados com Optuna)
  - Eixo Y: porcentagem (zoom 90-100%, com rótulos sobre as barras)
  - Séries: métricas percentuais (accuracy, precision, F1)

log_loss é excluída por não ser uma métrica percentual.
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
DEFAULT_OUTPUT = PROJ_ROOT / "reports_refactored" / "metrics_lowvariance_optuna.png"

METRICS = {"accuracy": "Accuracy", "precision": "Precision", "f1": "F1"}
MODEL_ORDER = ["DecisionTree", "GradientBoosting", "RandomForest", "LDA", "QDA", "GaussianNB"]
Y_MIN, Y_MAX = 90.0, 100.0


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
    parser.add_argument(
        "--seletor",
        default="LowVariance",
        help="Seletor de features a filtrar (default: LowVariance)",
    )
    return parser.parse_args()


def load_results(csv_path: Path, seletor: str) -> tuple[pd.DataFrame, int | None]:
    df = pd.read_csv(csv_path)
    required = {"seletor", "modelo", *METRICS}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Colunas ausentes em {csv_path}: {sorted(missing)}")

    df = df[df["seletor"] == seletor]
    if df.empty:
        available = sorted(pd.read_csv(csv_path)["seletor"].unique())
        raise ValueError(f"Seletor '{seletor}' não encontrado. Disponíveis: {available}")

    n_features = int(df["n_features"].iloc[0]) if "n_features" in df.columns else None
    long_df = df.melt(
        id_vars="modelo",
        value_vars=list(METRICS),
        var_name="metrica",
        value_name="valor",
    )
    long_df["valor"] = long_df["valor"] * 100
    long_df["metrica"] = long_df["metrica"].map(METRICS)
    return long_df, n_features


def plot_grouped_bars(
    long_df: pd.DataFrame, seletor: str, n_features: int | None, output_path: Path
) -> None:
    model_order = [m for m in MODEL_ORDER if m in set(long_df["modelo"])]

    fig, ax = plt.subplots(figsize=(12, 7))
    sns.barplot(
        data=long_df,
        x="modelo",
        y="valor",
        hue="metrica",
        order=model_order,
        hue_order=list(METRICS.values()),
        ax=ax,
    )

    # Rótulos de valor sobre cada barra
    for container in ax.containers:
        ax.bar_label(container, fmt="%.1f%%", fontsize=8, rotation=90, padding=2)

    features_info = f", {n_features} features" if n_features is not None else ""
    ax.set_ylim(Y_MIN, Y_MAX)
    ax.set_title(
        f"Métricas de Avaliação por Técnica de ML\n(seletor: {seletor} + Optuna{features_info})",
        fontsize=13,
    )
    ax.set_xlabel("Técnica de ML")
    ax.set_ylabel("Porcentagem (%)")
    ax.legend(title="Métrica", bbox_to_anchor=(1.01, 1), loc="upper left")
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    ax.set_axisbelow(True)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    args = parse_args()
    long_df, n_features = load_results(args.input, args.seletor)
    plot_grouped_bars(long_df, args.seletor, n_features, args.output)
    print(f"Gráfico salvo em: {args.output}")


if __name__ == "__main__":
    main()
