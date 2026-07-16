from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd


@dataclass(frozen=True)
class RunSummary:
    filename: str
    timestamp: str
    endpoint: str
    concurrency: int | None
    requests: int | None
    duration_sec: float | None
    successful: int | None
    failed: int | None
    timeouts: int | None
    throughput_req_per_sec: float | None
    latency_avg_ms: float | None
    latency_p95_ms: float | None
    load_before: float | None
    load_after: float | None
    memory_used_before_mb: float | None
    memory_used_after_mb: float | None


def _safe_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _safe_int(value: Any) -> int | None:
    try:
        if value is None:
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def discover_results_dir() -> Path:
    return Path(__file__).resolve().parent / "results_inference"


def load_benchmark_table(results_dir: Path) -> pd.DataFrame:
    candidates = sorted(results_dir.glob("t*.csv"))
    if not candidates:
        candidates = sorted(results_dir.glob("*.csv"))
    if not candidates:
        raise FileNotFoundError("No stress CSV found in results_inference/")
    csv_path = candidates[-1]

    df = pd.read_csv(csv_path)
    expected_columns = {
        "model_id",
        "n_requests",
        "inference_time_ms_avg",
        "inference_time_ms_std",
        "inference_time_ms_min",
        "inference_time_ms_max",
        "inference_time_ms_p50",
        "inference_time_ms_ci95_lower",
        "inference_time_ms_ci95_upper",
        "accuracy",
    }
    missing = expected_columns - set(df.columns)
    if missing:
        raise ValueError(f"Benchmark CSV missing columns: {sorted(missing)}")

    return df.sort_values(["inference_time_ms_avg", "accuracy"], ascending=[True, False]).reset_index(drop=True)


def discover_run_jsons(results_dir: Path) -> list[Path]:
    patterns = ["t*.json", "*.json"]
    paths: list[Path] = []
    for pattern in patterns:
        paths.extend(results_dir.glob(pattern))

    unique_paths = {path.resolve(): path for path in paths}
    return sorted(unique_paths.values())


def load_run_summaries(results_dir: Path) -> pd.DataFrame:
    rows: list[RunSummary] = []
    for path in discover_run_jsons(results_dir):
        payload = _load_json(path)
        test_info = payload.get("test_info", {})
        results = payload.get("results", {})
        latency = payload.get("latency_ms", {})
        system_before = payload.get("system_before") or {}
        system_after = payload.get("system_after") or {}

        rows.append(
            RunSummary(
                filename=path.name,
                timestamp=str(test_info.get("timestamp", "")),
                endpoint=str(test_info.get("endpoint", "")),
                concurrency=_safe_int(test_info.get("concurrency")),
                requests=_safe_int(test_info.get("requests")),
                duration_sec=_safe_float(test_info.get("duration_sec")),
                successful=_safe_int(results.get("successful")),
                failed=_safe_int(results.get("failed")),
                timeouts=_safe_int(results.get("timeouts")),
                throughput_req_per_sec=_safe_float(results.get("throughput_req_per_sec")),
                latency_avg_ms=_safe_float(latency.get("average")),
                latency_p95_ms=_safe_float(latency.get("p95")),
                load_before=_safe_float(system_before.get("load_avg_1min")),
                load_after=_safe_float(system_after.get("load_avg_1min")),
                memory_used_before_mb=_safe_float(system_before.get("memory_used_mb")),
                memory_used_after_mb=_safe_float(system_after.get("memory_used_mb")),
            )
        )

    df = pd.DataFrame([row.__dict__ for row in rows])
    if df.empty:
        return df
    return df.sort_values("timestamp").reset_index(drop=True)


def load_model_run_summaries(results_dir: Path, model_id: str) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for path in discover_run_jsons(results_dir):
        payload = _load_json(path)
        test_info = payload.get("test_info", {})
        results = payload.get("results", {})
        latency = payload.get("latency_ms", {})
        per_model = payload.get("per_model", {}).get(model_id)

        if not per_model:
            continue

        rows.append(
            {
                "timestamp": str(test_info.get("timestamp", "")),
                "filename": path.name,
                "concurrency": _safe_int(test_info.get("concurrency")),
                "requests": _safe_int(test_info.get("requests")),
                "successful": _safe_int(results.get("successful")),
                "failed": _safe_int(results.get("failed")),
                "timeouts": _safe_int(results.get("timeouts")),
                "throughput_req_per_sec": _safe_float(results.get("throughput_req_per_sec")),
                "latency_avg_ms": _safe_float(latency.get("average")),
                "load_before": _safe_float((payload.get("system_before") or {}).get("load_avg_1min")),
                "load_after": _safe_float((payload.get("system_after") or {}).get("load_avg_1min")),
                "model_requests": _safe_int(per_model.get("requests")),
                "model_inference_time_ms_avg": _safe_float(per_model.get("inference_time_ms_avg")),
                "model_inference_time_ms_p50": _safe_float(per_model.get("inference_time_ms_p50")),
                "model_inference_time_ms_min": _safe_float(per_model.get("inference_time_ms_min")),
                "model_inference_time_ms_max": _safe_float(per_model.get("inference_time_ms_max")),
                "model_accuracy": _safe_float(per_model.get("accuracy") or per_model.get("accuracy_avg")),
            }
        )

    df = pd.DataFrame(rows)
    if df.empty:
        return df
    return df.sort_values("timestamp").reset_index(drop=True)


def build_model_summary_table(df: pd.DataFrame) -> str:
    cols = [
        "model_id",
        "n_requests",
        "inference_time_ms_avg",
        "inference_time_ms_p50",
        "inference_time_ms_min",
        "inference_time_ms_max",
        "inference_time_ms_ci95_lower",
        "inference_time_ms_ci95_upper",
        "accuracy",
    ]
    table_df = df[cols].copy()
    table_df.insert(0, "speed_rank", range(1, len(table_df) + 1))
    return _dataframe_to_markdown(table_df)


def build_run_summary_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "_Nenhum JSON de stress encontrado._"

    cols = [
        "timestamp",
        "filename",
        "concurrency",
        "requests",
        "successful",
        "failed",
        "timeouts",
        "throughput_req_per_sec",
        "latency_avg_ms",
        "latency_p95_ms",
        "load_before",
        "load_after",
    ]
    table_df = df[cols].copy()
    return _dataframe_to_markdown(table_df)


def build_model_run_summary_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "_Nenhum run específico do modelo encontrado._"

    cols = [
        "timestamp",
        "filename",
        "concurrency",
        "requests",
        "successful",
        "failed",
        "timeouts",
        "throughput_req_per_sec",
        "latency_avg_ms",
        "model_inference_time_ms_avg",
        "model_inference_time_ms_p50",
        "model_inference_time_ms_min",
        "model_inference_time_ms_max",
        "model_accuracy",
        "load_before",
        "load_after",
    ]
    table_df = df[cols].copy()
    return _dataframe_to_markdown(table_df)


def build_speedup_table(models_df: pd.DataFrame, reference_models: list[str]) -> str:
    reference = models_df.set_index("model_id")
    if not set(reference_models).issubset(reference.index):
        return "_Dados insuficientes para montar a comparação de aceleração._"

    baseline_lda = float(reference.loc["lowvariance_lda", "inference_time_ms_avg"])
    baseline_dt = float(reference.loc["lowvariance_decisiontree", "inference_time_ms_avg"])
    baseline_gb = float(reference.loc["lowvariance_gradientboosting", "inference_time_ms_avg"])
    baseline_et = float(reference.loc["extratrees_gradientboosting", "inference_time_ms_avg"])

    comparison_df = models_df[models_df["model_id"].isin(reference_models)].copy()
    comparison_df["x_lda"] = comparison_df["inference_time_ms_avg"] / baseline_lda
    comparison_df["x_decisiontree"] = comparison_df["inference_time_ms_avg"] / baseline_dt
    comparison_df["x_gradientboosting"] = comparison_df["inference_time_ms_avg"] / baseline_gb
    comparison_df["x_extratrees"] = comparison_df["inference_time_ms_avg"] / baseline_et

    cols = [
        "model_id",
        "inference_time_ms_avg",
        "accuracy",
        "x_lda",
        "x_decisiontree",
        "x_gradientboosting",
        "x_extratrees",
    ]
    return _dataframe_to_markdown(comparison_df[cols].sort_values("inference_time_ms_avg", ascending=True).reset_index(drop=True))


def _dataframe_to_markdown(df: pd.DataFrame) -> str:
    if df.empty:
        return "_Sem dados para exibir._"

    display_df = df.copy()
    headers = list(display_df.columns)
    rows = []

    def format_cell(value: Any) -> str:
        if pd.isna(value):
            return "-"
        if isinstance(value, float):
            return f"{value:.3f}".rstrip("0").rstrip(".")
        return str(value)

    rows.append("| " + " | ".join(headers) + " |")
    rows.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for _, row in display_df.iterrows():
        cells = [format_cell(row[column]) for column in headers]
        rows.append("| " + " | ".join(cells) + " |")
    return "\n".join(rows)


def create_tradeoff_plot(models_df: pd.DataFrame, output_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(11, 7), dpi=160)

    x = models_df["inference_time_ms_avg"]
    y = models_df["accuracy"]
    sizes = 90 + models_df["n_requests"].fillna(0) * 2

    scatter = ax.scatter(
        x,
        y,
        s=sizes,
        c=range(len(models_df)),
        cmap="viridis",
        alpha=0.85,
        edgecolor="black",
        linewidth=0.6,
    )

    for _, row in models_df.iterrows():
        ax.annotate(
            row["model_id"],
            (row["inference_time_ms_avg"], row["accuracy"]),
            textcoords="offset points",
            xytext=(6, 6),
            fontsize=8,
        )

    ax.set_title("Trade-off entre latência média e acurácia por modelo")
    ax.set_xlabel("Inference time médio (ms)")
    ax.set_ylabel("Accuracy")
    ax.grid(True, alpha=0.25)
    cbar = fig.colorbar(scatter, ax=ax)
    cbar.set_label("Ordem dos modelos no ranking de latência")

    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)


def create_stability_plot(runs_df: pd.DataFrame, output_path: Path) -> None:
    if runs_df.empty:
        return

    plot_df = runs_df.copy()
    plot_df["label"] = plot_df["timestamp"].str.replace("T", " ", regex=False).str.slice(0, 16)

    fig, axes = plt.subplots(2, 1, figsize=(12, 9), dpi=160, sharex=True)

    axes[0].bar(
        plot_df["label"],
        plot_df["successful"].fillna(0),
        color="#4c78a8",
        label="Sucessos",
    )
    axes[0].bar(
        plot_df["label"],
        plot_df["timeouts"].fillna(0),
        bottom=plot_df["successful"].fillna(0),
        color="#f58518",
        label="Timeouts",
    )
    axes[0].set_ylabel("Requisições")
    axes[0].set_title("Estabilidade dos testes de stress por execução")
    axes[0].legend(loc="upper left")
    axes[0].grid(True, axis="y", alpha=0.25)

    ax2 = axes[1]
    ax2.plot(plot_df["label"], plot_df["throughput_req_per_sec"], marker="o", color="#54a24b", label="Throughput (req/s)")
    ax2.set_ylabel("Throughput (req/s)")
    ax2.grid(True, axis="y", alpha=0.25)

    ax3 = ax2.twinx()
    ax3.plot(plot_df["label"], plot_df["latency_avg_ms"], marker="s", color="#e45756", label="Latência média HTTP (ms)")
    ax3.set_ylabel("Latência média HTTP (ms)")

    handles1, labels1 = ax2.get_legend_handles_labels()
    handles2, labels2 = ax3.get_legend_handles_labels()
    ax2.legend(handles1 + handles2, labels1 + labels2, loc="upper left")

    axes[1].set_xlabel("Execução")
    axes[1].tick_params(axis="x", rotation=35)

    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)


def _format_run_metric(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:.3f}".rstrip("0").rstrip(".")


def _format_multiplier(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:.1f}x"


def build_report(models_df: pd.DataFrame, runs_df: pd.DataFrame, tradeoff_plot: Path, stability_plot: Path) -> str:
    top_fast = models_df.iloc[0]
    balanced_candidates = models_df[models_df["model_id"].isin(["lowvariance_decisiontree", "lowvariance_gradientboosting", "extratrees_gradientboosting"])]
    top_balanced = balanced_candidates.sort_values(["accuracy", "inference_time_ms_avg"], ascending=[False, True]).iloc[0]
    top_accuracy = models_df.sort_values(["accuracy", "inference_time_ms_avg"], ascending=[False, True]).iloc[0]
    svm_runs = load_model_run_summaries(discover_results_dir(), "lowvariance_svm")
    svm_model = models_df[models_df["model_id"] == "lowvariance_svm"].iloc[0]
    lda_model = models_df[models_df["model_id"] == "lowvariance_lda"].iloc[0]
    decisiontree_model = models_df[models_df["model_id"] == "lowvariance_decisiontree"].iloc[0]
    gradientboosting_model = models_df[models_df["model_id"] == "lowvariance_gradientboosting"].iloc[0]
    extratrees_model = models_df[models_df["model_id"] == "extratrees_gradientboosting"].iloc[0]
    svm_vs_lda = float(svm_model["inference_time_ms_avg"]) / float(lda_model["inference_time_ms_avg"])
    svm_vs_dt = float(svm_model["inference_time_ms_avg"]) / float(decisiontree_model["inference_time_ms_avg"])
    svm_vs_gb = float(svm_model["inference_time_ms_avg"]) / float(gradientboosting_model["inference_time_ms_avg"])
    svm_vs_et = float(svm_model["inference_time_ms_avg"]) / float(extratrees_model["inference_time_ms_avg"])

    report_lines = [
        "# Relatório de Stress Test da API de Inferência MQTT",
        "",
        f"**Data de geração:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "**Fonte dos dados:** arquivos JSON/CSV em `api_inference/results_inference/`",
        "**Alvo do stress test:** API de inferência no Raspberry Pi via `/benchmark`",
        "",
        "## 1. Contexto do experimento",
        "",
        "Os artefatos desta pasta registram a execução da API de inferência sob carga concorrente. A API de stress dispara requisições HTTP contra o Raspberry Pi e mede latência, throughput, taxa de falha, timeouts e o comportamento por modelo.",
        "",
        "## 2. Resumo executivo",
        "",
        f"- Modelo mais rápido no conjunto consolidado: **{top_fast['model_id']}** ({float(top_fast['inference_time_ms_avg']):.3f} ms).",
        f"- Melhor compromisso entre velocidade e qualidade observado: **{top_balanced['model_id']}** ({float(top_balanced['inference_time_ms_avg']):.3f} ms, accuracy {float(top_balanced['accuracy']):.4f}).",
        f"- Maior acurácia entre os modelos consolidados: **{top_accuracy['model_id']}** ({float(top_accuracy['accuracy']):.4f}).",
        "- O ambiente mostra sinais claros de saturação sob concorrência alta: aumenta a fila, sobe a latência média e surgem timeouts.",
        "",
        "## 3. Tabela consolidada dos modelos",
        "",
        build_model_summary_table(models_df),
        "",
        "## 4. Legenda das métricas",
        "",
        "| Campo | Significado | Leitura prática |",
        "|---|---|---|",
        "| `inference_time_ms_avg` | Média do tempo de inferência por requisição | Principal métrica para comparar rapidez dos modelos |",
        "| `inference_time_ms_p50` | Mediana do tempo de inferência | Mostra o comportamento típico sem os extremos |",
        "| `inference_time_ms_min/max` | Menor e maior tempo observado | Indicam dispersão e caudas de latência |",
        "| `inference_time_ms_ci95_lower/upper` | Intervalo de confiança de 95% | Ajuda a avaliar estabilidade estatística |",
        "| `accuracy` | Proporção de acertos | Mede qualidade preditiva, mas não substitui latência |",
        "| `concurrency` | Requisições simultâneas enviadas pela API de stress | Mede pressão concorrente sobre o Raspberry Pi |",
        "| `requests` | Total de requisições no teste | Define o tamanho da amostra do teste |",
        "| `successful` / `failed` / `timeouts` | Resultado agregado das requisições | Indicam estabilidade operacional sob carga |",
        "| `throughput_req_per_sec` | Vazão de requisições por segundo | Mostra capacidade efetiva de processamento |",
        "| `latency_avg_ms` / `latency_p95_ms` | Latência HTTP da requisição de stress | Reflete o comportamento da API como serviço |",
        "| `load_before` / `load_after` | Load average do Raspberry Pi antes/depois | Mostra o impacto sistêmico do teste |",
        "",
        "## 5. Resumo das execuções de stress",
        "",
        build_run_summary_table(runs_df),
        "",
        "## 6. Destaque do SVM e divergências observadas",
        "",
        "### 6.1 Runs específicos com SVM",
        "",
        build_model_run_summary_table(svm_runs),
        "",
        "### 6.2 Comparação do SVM com os modelos leves e com os demais pesos do conjunto",
        "",
        build_speedup_table(
            models_df,
            [
                "lowvariance_lda",
                "lowvariance_decisiontree",
                "lowvariance_gradientboosting",
                "extratrees_gradientboosting",
                "lowvariance_randomforest",
                "lowvariance_svm",
            ],
        ),
        "",
        f"- Em relação ao **lowvariance_lda**, o SVM é cerca de **{_format_multiplier(svm_vs_lda)}** mais lento.",
        f"- Em relação ao **lowvariance_decisiontree**, o SVM é cerca de **{_format_multiplier(svm_vs_dt)}** mais lento.",
        f"- Em relação ao **lowvariance_gradientboosting**, o SVM é cerca de **{_format_multiplier(svm_vs_gb)}** mais lento.",
        f"- Em relação ao **extratrees_gradientboosting**, o SVM é cerca de **{_format_multiplier(svm_vs_et)}** mais lento.",
        f"- Nos runs específicos do SVM, a taxa de sucesso variou de **{svm_runs['successful'].min()}/{int(svm_runs['requests'].max())}** até **{svm_runs['successful'].max()}/{int(svm_runs['requests'].max())}**, mostrando que o gargalo não é apenas a precisão do modelo, mas o acúmulo de fila e o tempo de resposta do Raspberry Pi.",
        f"- O run consolidado de **{svm_model['model_id']}** ainda fecha todas as requisições em carga mais baixa, mas o custo médio de inferência permanece em **{_format_run_metric(float(svm_model['inference_time_ms_avg']))} ms**, muito acima do restante do conjunto.",
        "",
        "## 7. Interpretação dos resultados",
        "",
        "1. O menor tempo de inferência não é o único critério relevante. O modelo mais rápido tende a sacrificar um pouco de acurácia, mas entrega o melhor comportamento quando a prioridade é resposta ágil.",
        "2. Modelos de boosting oferecem acurácia alta, porém a latência cresce rapidamente sob concorrência, o que pressiona o Raspberry Pi.",
        "3. RandomForest e SVM são os mais custosos em tempo de inferência e os mais sensíveis a filas e timeouts em cenários agressivos de stress.",
        "4. A estabilidade do sistema depende menos da leitura dos dados e mais da etapa de `predict`, que é onde o custo computacional realmente se concentra.",
        "5. O aumento de `concurrency` sem ajuste de threads/cores no Pi produz degradação evidente: throughput baixo, latências altas e maior risco de timeout.",
        "",
        "## 8. Figuras",
        "",
        f"### 8.1 Trade-off entre latência e acurácia\n\n![Trade-off entre latência e acurácia]({tradeoff_plot.name})",
        "",
        f"### 8.2 Estabilidade por execução\n\n![Estabilidade por execução]({stability_plot.name})",
        "",
        "## 9. Conclusão",
        "",
        "Os dados sugerem que o sistema no Raspberry Pi deve ser tratado como um ambiente de borda sensível a concorrência. Para operação prática, o melhor caminho é equilibrar latência e acurácia, evitando modelos muito pesados quando a carga simultânea for alta. O SVM é o caso mais extremo de divergência: ele não adiciona ganho de precisão suficiente para compensar o salto de latência e os timeouts observados nos runs mais pesados. O gráfico de trade-off ajuda a escolher o modelo; o gráfico de estabilidade mostra quando o Pi começa a saturar.",
        "",
        "## 10. Próximo passo recomendado",
        "",
        "Adicionar um segundo experimento com a mesma carga lógica, mas variando `concurrency` de forma controlada para identificar o ponto de inflexão de saturação do Raspberry Pi e formalizar o limite operacional recomendado.",
        "",
    ]

    return "\n".join(report_lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate stress test report and plots")
    parser.add_argument("--results-dir", default=None, help="Directory with JSON/CSV stress results")
    parser.add_argument("--output-report", default=None, help="Path for the generated Markdown report")
    parser.add_argument("--tradeoff-plot", default=None, help="Path for the model trade-off figure")
    parser.add_argument("--stability-plot", default=None, help="Path for the execution stability figure")
    args = parser.parse_args()

    results_dir = Path(args.results_dir).resolve() if args.results_dir else discover_results_dir()
    if not results_dir.exists():
        raise FileNotFoundError(f"Results directory not found: {results_dir}")

    models_df = load_benchmark_table(results_dir)
    runs_df = load_run_summaries(results_dir)

    output_report = Path(args.output_report).resolve() if args.output_report else results_dir / "stress_report.md"
    tradeoff_plot = Path(args.tradeoff_plot).resolve() if args.tradeoff_plot else results_dir / "stress_tradeoff.png"
    stability_plot = Path(args.stability_plot).resolve() if args.stability_plot else results_dir / "stress_stability.png"

    create_tradeoff_plot(models_df, tradeoff_plot)
    create_stability_plot(runs_df, stability_plot)

    report = build_report(models_df, runs_df, tradeoff_plot, stability_plot)
    output_report.write_text(report, encoding="utf-8")

    print(f"Report written to: {output_report}")
    print(f"Trade-off plot written to: {tradeoff_plot}")
    print(f"Stability plot written to: {stability_plot}")


if __name__ == "__main__":
    main()