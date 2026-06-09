# AGENTS.md — MQTT Under Attack

> Context for agent sessions. Read before making changes.

## Active Branch

`refactor-pipeline` — all work happens here.

## Python

Pinned to `==3.13.9` (`pyproject.toml`). Use `make requirements` or `pip install -r requirements.txt`.

## Lint / Format

- `make lint` — ruff format --check + ruff check
- `make format` — ruff check --fix + ruff format
- line-length: 99 (`pyproject.toml`)

## Two separate environments

| Directory | What | Deps |
|---|---|---|
| root | Pipeline (notebooks/scripts) | `requirements.txt` |
| `api_inference/` | FastAPI benchmark API | `api_inference/requirements.txt` |

They have different `scikit-learn` / `pandas` version ranges. Do not mix.

## Pipeline entrypoints

| Entrypoint | Status |
|---|---|
| `notebooks_refactored/03_pipeline_05_05.ipynb` | **Primary** — Ensemble V2 + Optuna |
| `main.py` | Legacy script pipeline (uses `scripts/`) |
| `scripts/data_loader.py → train.py → evaluate.py` | Orchestrated by `main.py` |

The notebook is the source of truth. `main.py` was a draft orchestrator with `n_trials=2` for slow models.

## Deploy models

Location: `models/models_ensemble_v2/optuna/` (`.pkl` via joblib).

Best model: `lowvariance_gradientboosting` — 12 features, 995 KB, F1=0.9754.

## Inference API (`api_inference/`)

- Async FastAPI (`async def` + `asyncio.to_thread()` for CPU-bound work)
- Endpoints: `GET /health`, `GET /models`, `GET /stats`, `POST /benchmark`, `POST /benchmark/{model_id}`
- Docker: `UVICORN_WORKERS` env var controls process count (default 4)
- Stress test client: `stress_test.py` (standalone, uses httpx)
- Results saved as `results_inference/iinference.csv` + `stress_test_YYYYMMDD_HHMMSS.json`

### Docker flow (Raspberry Pi)

```bash
rsync -av api_inference/ pi@192.168.20.83:~/api_inference/
ssh pi@192.168.20.83
cd ~/api_inference && docker compose build && docker compose up -d
```

OpenMP oversubscription risk with `workers > 1`. Set `OMP_NUM_THREADS=1` if needed.

## Config

- `.env` file: `DATA_DIR` overrides data path (defaults to `PROJ_ROOT/data`)
- `api_inference/`: `API_INFERENCE_ROOT`, `UVICORN_WORKERS` env vars

## Deploy gotchas

- `pi_inference.py` requires `paho-mqtt` (not in root requirements.txt)
- SCP only the `.pkl` files, not the full models directory
- CSV test datasets must match model `feature_names_in_` exactly

## Historical notebook issues (do not repeat)

1. `fillna(0)` pre-split causes data leakage — always impute post-split via `SimpleImputer`
2. `scipy.stats.mode` rejects string arrays in newer scipy — use `pandas.DataFrame().mode()` instead
3. Ensemble before Optuna dilutes strong models — ensemble only after optimization
