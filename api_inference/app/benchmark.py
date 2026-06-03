from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
import os
import time
from typing import Any

import joblib
import pandas as pd


CSV_COLUMNS = [
    "model_id",
    "model_file",
    "dataset_file",
    "rows",
    "n_features",
    "load_time_sec",
    "dataset_read_time_sec",
    "inference_time_sec",
    "inference_time_ms",
    "avg_inference_ms_per_row",
    "predictions_per_sec",
    "accuracy",
    "status",
    "error",
    "created_at",
]


@dataclass(frozen=True)
class Paths:
    root: Path
    models_dir: Path
    datasets_test_dir: Path
    results_dir: Path
    results_csv: Path


@dataclass(frozen=True)
class ModelInfo:
    model_id: str
    model_file: str
    dataset_file: str | None
    model_path: str
    dataset_path: str | None
    expected_features: int | None
    dataset_features: int | None
    rows: int | None
    compatible: bool
    status: str
    error: str


@dataclass(frozen=True)
class BenchmarkResult:
    model_id: str
    model_file: str
    dataset_file: str
    rows: int | None
    n_features: int | None
    load_time_sec: float | None
    dataset_read_time_sec: float | None
    inference_time_sec: float | None
    inference_time_ms: float | None
    avg_inference_ms_per_row: float | None
    predictions_per_sec: float | None
    accuracy: float | None
    status: str
    error: str
    created_at: str


def get_paths() -> Paths:
    root = Path(os.getenv("API_INFERENCE_ROOT", Path(__file__).resolve().parents[1]))
    models_dir = Path(os.getenv("MODELS_DIR", root / "models"))
    datasets_test_dir = Path(os.getenv("DATASETS_TEST_DIR", root / "datasets" / "test"))
    results_dir = Path(os.getenv("RESULTS_DIR", root / "results_inference"))
    results_csv = Path(os.getenv("RESULTS_CSV", results_dir / "iinference.csv"))
    return Paths(
        root=root,
        models_dir=models_dir,
        datasets_test_dir=datasets_test_dir,
        results_dir=results_dir,
        results_csv=results_csv,
    )


def health_status(paths: Paths | None = None) -> dict[str, Any]:
    paths = paths or get_paths()
    return {
        "status": "ok",
        "root": str(paths.root),
        "models_dir": str(paths.models_dir),
        "datasets_test_dir": str(paths.datasets_test_dir),
        "results_dir": str(paths.results_dir),
        "results_csv": str(paths.results_csv),
        "models_dir_exists": paths.models_dir.exists(),
        "datasets_test_dir_exists": paths.datasets_test_dir.exists(),
        "results_dir_exists": paths.results_dir.exists(),
    }


def model_id_from_path(model_path: Path) -> str:
    prefix = "optuna_by_selector_"
    stem = model_path.stem
    return stem[len(prefix) :] if stem.startswith(prefix) else stem


def expected_dataset_name(model_path: Path) -> str:
    return f"test_{model_path.stem}.csv"


def _model_feature_names(model: Any) -> list[str] | None:
    feature_names = getattr(model, "feature_names_in_", None)
    if feature_names is None:
        return None
    return [str(feature) for feature in feature_names]


def _read_dataset_header(dataset_path: Path) -> tuple[list[str], int]:
    header = pd.read_csv(dataset_path, nrows=0)
    rows = sum(1 for _ in dataset_path.open("r", encoding="utf-8")) - 1
    return list(header.columns), max(rows, 0)


def discover_models(paths: Paths | None = None) -> list[ModelInfo]:
    paths = paths or get_paths()
    models = []

    for model_path in sorted(paths.models_dir.glob("*.pkl")):
        dataset_path = paths.datasets_test_dir / expected_dataset_name(model_path)
        model_id = model_id_from_path(model_path)
        expected_features: list[str] | None = None
        dataset_features: list[str] | None = None
        rows: int | None = None
        error_parts: list[str] = []

        try:
            model = joblib.load(model_path)
            expected_features = _model_feature_names(model)
            if expected_features is None:
                expected_n_features = getattr(model, "n_features_in_", None)
                if expected_n_features is not None:
                    expected_features = [f"feature_{i}" for i in range(int(expected_n_features))]
        except Exception as exc:
            error_parts.append(f"model_load_error: {exc}")

        if not dataset_path.exists():
            error_parts.append(f"dataset_not_found: {dataset_path.name}")
        else:
            try:
                dataset_columns, rows = _read_dataset_header(dataset_path)
                dataset_features = [column for column in dataset_columns if column != "type"]
            except Exception as exc:
                error_parts.append(f"dataset_read_error: {exc}")

        if expected_features is not None and dataset_features is not None:
            if expected_features != dataset_features:
                missing = [feature for feature in expected_features if feature not in dataset_features]
                extra = [feature for feature in dataset_features if feature not in expected_features]
                wrong_order = not missing and not extra
                if missing:
                    error_parts.append(f"missing_features: {missing}")
                if extra:
                    error_parts.append(f"extra_features: {extra}")
                if wrong_order:
                    error_parts.append("feature_order_mismatch")

        compatible = not error_parts
        models.append(
            ModelInfo(
                model_id=model_id,
                model_file=model_path.name,
                dataset_file=dataset_path.name if dataset_path.exists() else None,
                model_path=str(model_path),
                dataset_path=str(dataset_path) if dataset_path.exists() else None,
                expected_features=len(expected_features) if expected_features is not None else None,
                dataset_features=len(dataset_features) if dataset_features is not None else None,
                rows=rows,
                compatible=compatible,
                status="compatible" if compatible else "incompatible",
                error="; ".join(error_parts),
            )
        )

    return models


def _empty_result(model_id: str, model_file: str, dataset_file: str, error: str) -> BenchmarkResult:
    return BenchmarkResult(
        model_id=model_id,
        model_file=model_file,
        dataset_file=dataset_file,
        rows=None,
        n_features=None,
        load_time_sec=None,
        dataset_read_time_sec=None,
        inference_time_sec=None,
        inference_time_ms=None,
        avg_inference_ms_per_row=None,
        predictions_per_sec=None,
        accuracy=None,
        status="error",
        error=error,
        created_at=datetime.now(UTC).isoformat(),
    )


def run_benchmark(model_id: str, paths: Paths | None = None) -> BenchmarkResult:
    paths = paths or get_paths()
    model_info_by_id = {model.model_id: model for model in discover_models(paths)}
    model_info = model_info_by_id.get(model_id)
    if model_info is None:
        return _empty_result(model_id, "", "", f"model_id_not_found: {model_id}")
    if not model_info.compatible:
        return _empty_result(
            model_info.model_id,
            model_info.model_file,
            model_info.dataset_file or "",
            model_info.error,
        )

    model_path = Path(model_info.model_path)
    dataset_path = Path(model_info.dataset_path or "")
    created_at = datetime.now(UTC).isoformat()

    try:
        load_start = time.perf_counter()
        model = joblib.load(model_path)
        load_time_sec = time.perf_counter() - load_start

        dataset_start = time.perf_counter()
        dataset = pd.read_csv(dataset_path)
        dataset_read_time_sec = time.perf_counter() - dataset_start

        if "type" not in dataset.columns:
            raise ValueError("dataset does not contain required 'type' column")

        x_test = dataset.drop(columns=["type"])
        y_test = dataset["type"]
        expected_features = _model_feature_names(model)
        if expected_features is not None and expected_features != list(x_test.columns):
            raise ValueError("dataset feature columns do not match model.feature_names_in_")

        model.predict(x_test.head(1))

        inference_start = time.perf_counter()
        predictions = model.predict(x_test)
        inference_time_sec = time.perf_counter() - inference_start

        rows = int(len(x_test))
        inference_time_ms = inference_time_sec * 1000.0
        avg_inference_ms_per_row = inference_time_ms / rows if rows else None
        predictions_per_sec = rows / inference_time_sec if inference_time_sec > 0 else None
        accuracy = float((predictions == y_test.to_numpy()).mean()) if rows else None

        return BenchmarkResult(
            model_id=model_info.model_id,
            model_file=model_info.model_file,
            dataset_file=model_info.dataset_file or dataset_path.name,
            rows=rows,
            n_features=int(x_test.shape[1]),
            load_time_sec=load_time_sec,
            dataset_read_time_sec=dataset_read_time_sec,
            inference_time_sec=inference_time_sec,
            inference_time_ms=inference_time_ms,
            avg_inference_ms_per_row=avg_inference_ms_per_row,
            predictions_per_sec=predictions_per_sec,
            accuracy=accuracy,
            status="success",
            error="",
            created_at=created_at,
        )
    except Exception as exc:
        return _empty_result(model_info.model_id, model_info.model_file, dataset_path.name, str(exc))


def _results_to_frame(results: list[BenchmarkResult]) -> pd.DataFrame:
    rows = [asdict(result) for result in results]
    return pd.DataFrame(rows, columns=CSV_COLUMNS)


def write_results(results: list[BenchmarkResult], paths: Paths | None = None) -> Path:
    paths = paths or get_paths()
    paths.results_dir.mkdir(parents=True, exist_ok=True)
    _results_to_frame(results).to_csv(paths.results_csv, index=False)
    return paths.results_csv


def update_single_result(result: BenchmarkResult, paths: Paths | None = None) -> Path:
    paths = paths or get_paths()
    paths.results_dir.mkdir(parents=True, exist_ok=True)

    if paths.results_csv.exists():
        existing = pd.read_csv(paths.results_csv)
        existing = existing[existing["model_id"] != result.model_id]
        updated = pd.concat([existing, _results_to_frame([result])], ignore_index=True)
        updated = updated.reindex(columns=CSV_COLUMNS)
    else:
        updated = _results_to_frame([result])

    updated.to_csv(paths.results_csv, index=False)
    return paths.results_csv


def run_all_benchmarks(paths: Paths | None = None) -> list[BenchmarkResult]:
    paths = paths or get_paths()
    compatible_models = [model for model in discover_models(paths) if model.compatible]
    return [run_benchmark(model.model_id, paths) for model in compatible_models]


def public_model_info(paths: Paths | None = None) -> list[dict[str, Any]]:
    return [asdict(model) for model in discover_models(paths)]


def public_result(result: BenchmarkResult) -> dict[str, Any]:
    return asdict(result)
