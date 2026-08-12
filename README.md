# MQTT Under Attack

<a target="_blank" href="https://cookiecutter-data-science.drivendata.org/">
    <img src="https://img.shields.io/badge/CCDS-Project%20template-328F97?logo=cookiecutter" />
</a>

Machine learning pipeline for detecting **DoS (Denial of Service) attacks in MQTT networks**,
using the *MQTT Under Attack Dataset*. The project covers the full workflow — data cleaning,
temporal feature engineering, feature selection, ensembling, Optuna hyperparameter tuning and
evaluation — plus a separate FastAPI service for benchmarking trained models, including
deployment on a Raspberry Pi for edge-inference scenarios.

Best result to date: a **DecisionTree tuned with Optuna** on the LowVariance feature subset
reaches **F1 ≈ 0.975** with only 12 features and ~96 ms batch inference time on a Raspberry Pi
(see [`reports_refactored/RELATORIO_FINAL.md`](reports_refactored/RELATORIO_FINAL.md) and
[`paretto/`](paretto/) for the full accuracy/time/memory trade-off analysis).

## Project layout

This repo has **two independent parts** with separate dependencies — do not mix their
environments:

```
├── main.py                    <- Legacy pipeline orchestrator (data -> train -> evaluate)
├── scripts/                   <- Modular pipeline steps used by main.py
│   ├── data_loader.py         <- Load raw CSV, compute gap features, clean, split & scale
│   ├── train.py                <- Optuna-tuned training for 6 algorithms
│   ├── evaluate.py             <- Metrics, confusion matrices, reports
│   └── pi_inference.py         <- Lightweight real-time inference script for Raspberry Pi
│
├── notebooks/                 <- Exploratory notebooks (EDA, feature/gap studies, pipeline drafts)
├── notebooks_refactored/      <- Cleaned-up pipeline notebooks
│   └── 03_pipeline_05_05.ipynb <- ⭐ Primary/authoritative pipeline (Ensemble V2 + Optuna)
│
├── data/
│   ├── raw/                   <- Original MQTT Under Attack Dataset (DoS/Intrusion/MitM CSVs)
│   ├── processed/             <- Cleaned data, gap features, per-selector feature sets
│   └── inference/             <- Train/test splits paired with each selector+model combo
│
├── models_optimized/          <- .joblib models from the legacy main.py pipeline
├── models/models_ensemble_v2/ <- .pkl models from the authoritative notebook pipeline
│
├── reports_refactored/        <- Metrics, confusion matrices, plots (source of truth for results)
├── paretto/                   <- Pareto-frontier analysis (accuracy vs. time vs. memory)
│
├── api_inference/             <- Standalone FastAPI benchmark service (own requirements.txt)
├── docs/                      <- MkDocs project (data dictionary, pipeline docs)
├── raspberry_deploy.md        <- Guide to deploy models_optimized/*.joblib on a Raspberry Pi
└── AGENTS.md                  <- Up-to-date engineering notes (read this if you're modifying code)
```

> `AGENTS.md` is the most current reference for contributors — it documents known pitfalls,
> the authoritative pipeline entrypoint, and deploy gotchas that this README summarizes below.

## Requirements

- Python `3.13.x` (pinned to `3.13.9` in `pyproject.toml`; `environment.yml` uses `3.13.11`)
- Conda (recommended) or `venv`

## Getting started (root pipeline)

Clone the repo and create an environment:

```bash
# with conda (recommended)
conda env create -f environment.yml
conda activate mqtt

# or with venv
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
```

Install dependencies:

```bash
make requirements
# equivalent to: pip install -U pip && pip install -r requirements.txt
```

(Optional) copy `.env.example` to `.env` and set `DATA_DIR` if your data lives outside the repo:

```bash
cp .env.example .env
# DATA_DIR=/absolute/path/to/data   (defaults to <repo>/data if unset)
```

Make sure the raw dataset is in place:

```
data/raw/MQTT Under Attack Dataset/DoS.csv
```

### Option A — Run the authoritative pipeline (recommended)

The canonical, up-to-date pipeline lives in the notebook, not in `main.py`:

```bash
jupyter lab notebooks_refactored/03_pipeline_05_05.ipynb
```

Run all cells top to bottom. It produces the artifacts under `reports_refactored/` and the
models under `models/models_ensemble_v2/`. `notebooks_refactored/04_pipeline.ipynb` and
`04_svm.ipynb` extend this with additional experiments.

### Option B — Run the legacy script pipeline

`main.py` is a draft orchestrator (reduced Optuna trial budget for slower models) that chains
`scripts/data_loader.py → scripts/train.py → scripts/evaluate.py`:

```bash
python main.py
```

This trains 6 algorithms (LDA, QDA, GaussianNB, DecisionTree, RandomForest, GradientBoosting),
saving models to `models_optimized/` and reports to `reports_optimized/`.

You can also run each stage individually:

```bash
python scripts/data_loader.py
python scripts/train.py
python scripts/evaluate.py
```

### Lint & format

```bash
make lint     # ruff format --check + ruff check
make format   # ruff check --fix + ruff format
```

## Running the inference benchmark API

`api_inference/` is a separate FastAPI service used to measure inference latency/throughput of
the trained models (e.g. on a Raspberry Pi). It has its **own** `requirements.txt` — use a
separate virtual environment:

```bash
cd api_inference
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt

uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Try it out:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/models
curl -X POST http://localhost:8000/benchmark
```

Or with Docker:

```bash
cd api_inference
docker compose build
docker compose up -d
```

Full details (endpoints, CSV output columns, Raspberry Pi deployment, stress testing with
`stress_test.py` / `stress_api/`) are documented in
[`api_inference/README.md`](api_inference/README.md) and
[`api_inference/STRESS_README.md`](api_inference/STRESS_README.md).

## Deploying to a Raspberry Pi

Two deployment paths exist:

- **Real-time/edge inference** with the legacy `.joblib` models — see
  [`raspberry_deploy.md`](raspberry_deploy.md) (uses `scripts/pi_inference.py`, which needs
  `paho-mqtt`, not included in the root `requirements.txt`).
- **Benchmark API in Docker** — see the Raspberry Pi section of
  [`api_inference/README.md`](api_inference/README.md).

## Documentation

More detailed docs (data dictionary, gap-feature methodology, correlation matrix, selected
features) live under [`docs/`](docs/), served locally with MkDocs:

```bash
cd docs
pip install mkdocs
mkdocs serve
```

The full narrative of the refactored pipeline's methodology is in
[`docs/pipeline_refactored.md`](docs/pipeline_refactored.md), and the final consolidated
results are in [`reports_refactored/RELATORIO_FINAL.md`](reports_refactored/RELATORIO_FINAL.md).

## Known gotchas

- `fillna(0)` **before** the train/test split causes data leakage — always impute after
  splitting (e.g. via `SimpleImputer`). This is fixed in the refactored notebooks but still
  present in `scripts/data_loader.py`.
- `scipy.stats.mode` rejects string arrays on newer `scipy` — use `pandas.DataFrame().mode()`
  instead.
- Ensembling *before* Optuna tuning dilutes strong models — always tune first, ensemble after.
- CSV test datasets fed to the inference API must match the model's `feature_names_in_` exactly.

--------
