#!/usr/bin/env python3
"""
Gráfico de barras agrupadas: tempo de execução por técnica de ML.

Lê reports_refactored/timing_results.csv, filtra um seletor de features
(default: LowVariance) nas etapas de otimização Optuna e treino final,
e gera um PNG com:
  - Eixo X: técnicas de ML (ordenadas pelo tempo total decrescente)
  - Eixo Y: tempo em segundos (escala linear, com rótulos sobre as barras)
  - Séries: etapas (Otimização Optuna, Treino Final)
"""

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # roda sem display

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

PROJ_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = PROJ_ROOT / "reports_refactored" / "timing_results.csv"
DEFAULT_OUTPUT = PROJ_ROOT / "reports_refactored" / "timing_lowvariance.png"

STAGES = {
    "optuna_by_selector_optimization": "Otimização (Optuna)",
    "optuna_by_selector_training": "Treino Final",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help=f"CSV de timings (default: {DEFAULT_INPUT})",
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


def load_timings(csv_path: Path, seletor: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    required = {"stage", "seletor", "modelo", "status", "tempo_total_sec"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Colunas ausentes em {csv_path}: {sorted(missing)}")

    mask = df["stage"].isin(STAGES) & (df["seletor"] == seletor) & (df["status"] == "success")
    df = df[mask].copy()
    if df.empty:
        raise ValueError(f"Nenhum registro para o seletor '{seletor}' nas etapas {list(STAGES)}")

    df["etapa"] = df["stage"].map(STAGES)
    return df


def plot_grouped_bars(df: pd.DataFrame, seletor: str, output_path: Path) -> None:
    # Ordena modelos pelo tempo total (otimização + treino) decrescente
    total_by_model = df.groupby("modelo")["tempo_total_sec"].sum()
    model_order = total_by_model.sort_values(ascending=False).index.tolist()

    fig, ax = plt.subplots(figsize=(12, 7))
    sns.barplot(
        data=df,
        x="modelo",
        y="tempo_total_sec",
        hue="etapa",
        order=model_order,
        hue_order=list(STAGES.values()),
        ax=ax,
    )

    # Rótulos de valor sobre cada barra (2 casas: valores ~0.07s precisam aparecer)
    for container in ax.containers:
        ax.bar_label(container, fmt="%.2fs", fontsize=8, rotation=90, padding=2)

    ax.set_title(
        f"Tempo de Execução por Técnica de ML\n(seletor: {seletor}, 12 features)",
        fontsize=13,
    )
    ax.set_xlabel("Técnica de ML")
    ax.set_ylabel("Tempo (s)")
    ax.set_ylim(top=ax.get_ylim()[1] * 1.15)  # espaço para os rótulos
    ax.legend(title="Etapa", bbox_to_anchor=(1.01, 1), loc="upper left")
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    ax.set_axisbelow(True)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    args = parse_args()
    df = load_timings(args.input, args.seletor)
    plot_grouped_bars(df, args.seletor, args.output)
    print(f"Gráfico salvo em: {args.output}")


if __name__ == "__main__":
    main()
