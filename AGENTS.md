# AGENTS.md — MQTT Under Attack

> Context for agent sessions. Read before making changes.

## Refatoração em curso: treino unificado (projeto-curso)

Decisões em `docs/decisions.md` (log append-only), vocabulário em `GLOSSARY.md`, spec e tickets em
`docs/issues/` (`0000-*` é a spec, `01`–`08` são os tickets, em ordem de dependência).

**Alvo:** pacote `src/mqtt_dos/` + notebook `notebooks/training.ipynb`: 7 modelos (LDA, QDA, GaussianNB,
DecisionTree, RandomForest, GradientBoosting, SVM) × 6 seletores (LowVariance, ANOVA, MutualInformation,
Lasso, LinearSVC, ExtraTrees), Optuna com o protocolo do paper WPMC, artefatos em `outputs/<run_name>/`.
Cada modelo salvo é um `Pipeline` que aceita features brutas.

**Este repo é um curso.** O usuário digita o código seguindo as aulas, então:
- implementar um ticket = escrever a aula `docs/NN-slug.md` com a skill `mkdocs-project-course`
  (`/mkdocs-project-course init`, depois `/mkdocs-project-course <ticket>` e `/mkdocs-project-course progresso`);
- **não** escreva `src/` nem `tests/` por conta própria; só com pedido explícito do usuário;
- nunca faça commit, push ou PR; no máximo sugira a mensagem de commit;
- registre toda decisão nova no fim de `docs/decisions.md` (nunca reescreva entradas antigas);
- docs em pt-BR, identificadores de código em inglês.

**Intocáveis nesta fase:** `api_inference/`, `scripts/` (e `main.py`, que os orquestra), `paretto/`,
`04_pipeline.ipynb`, `04_svm.ipynb` e seus artefatos. Nada é apagado; a lista de limpeza futura está na spec.
O código novo não escreve em `api_inference/` nem em `models/`/`reports_refactored/`.

**Comandos do novo projeto:** `uv sync`, `uv run pytest`, `uv run ruff check`, `uv run ruff format --check`,
`uv run mkdocs serve`. O ruff verifica só `src/`, `tests/` e `notebooks/training.ipynb` (o código antigo já
falha no ruff e não pode ser alterado). O notebook usa o kernel `.venv/bin/python`, e `tests/test_notebook.py`
o executa inteiro.

**Exceções à regra do curso:** a usuária pediu explicitamente que o agente implementasse as aulas 01-1, 01-2
e 01-3 (decisões 34 e 38). A partir da aula 02 a usuária digita o código (decisão 39): escreva só as aulas.

## Notas herdadas do CLAUDE.md anterior

- Estratégias de valores ausentes avaliadas historicamente: `fillna(0)` global antes do split (vaza),
  `SimpleImputer(constant, 0)` pós-split (adotada) e `SimpleImputer(median)` (piora LDA/QDA).
- DecisionTree foi o modelo com maior F1 (~0.975) nos resultados antigos; LDA/QDA são sensíveis à imputação.
- Fluxo antigo: dados em `data/raw/` → modelos em `models_optimized/` e `models/models_ensemble_v2/` →
  relatórios em `reports_refactored/`. Guia de deploy no Raspberry Pi em `raspberry_deploy.md`.
- O `CLAUDE.md` descrevia um pacote `mqtt_under_attack/` que não existe no repositório; ignore essa referência.

## Active Branch

`inference` — all work happens here.

## Python

Pinned to `==3.13.9` (`pyproject.toml`). Conda env: `mqtt` (`miniconda3/envs/mqtt`).
Use `make requirements` or `pip install -r requirements.txt`.

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

Best Pareto combination: `lowvariance_decisiontree` — 12 features, 7 KB, F1=0.9754, 95.8 ms batch inference (Raspberry Pi). Offers near-optimal F1 at 7× faster inference than GradientBoosting.

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

## Benchmark data

- Each `/benchmark/{model_id}` request loads the full test CSV (18925 data rows) and calls `model.predict()` on the entire batch.
- Test datasets: `api_inference/datasets/test/test_optuna_by_selector_lowvariance_*.csv` (18926 lines = 1 header + 18925 rows).
- Primary stress test run with all 5 lowvariance models: `api_inference/results_inference/t16_workers4_concurrency15_allmodels.csv` (n=50 per model, concurrency=15).
- Aggregated CI95% stats: `api_inference/results_inference/inference_time_ci95_lowvariance.csv`.
- Per-run stats: `api_inference/results_inference/inference_stats_by_run_lowvariance.csv`.
- Optuna F1 scores: `reports_refactored/optuna_by_selector_results.csv` (seletor=LowVariance).

## Pareto frontier scripts (`paretto/`)

| Script | Time metric | Source |
|---|---|---|
| `plot_pareto_frontier_lowvariance.py` | mean batch time (ms) | aggregated CI95 CSV |
| `plot_pareto_frontier_per_record_lowvariance.py` | mean / 18925 (ms/row) | aggregated CI95 CSV |
| `plot_pareto_frontier_ci95_lowvariance.py` | CI95 lower + upper (ms) | t16 single run |
| `plot_pareto_frontier_median_lowvariance.py` | median p50 (ms) | t16 single run |
| `plot_pareto_frontier_median_per_line_lowvariance.py` | median p50 / 18925 (ms/row) | t16 single run |

All use the same Pareto dominance logic: maximize combined score `(acc + F1) / 2`, minimize time.
SVM has no F1 in optuna results — uses accuracy as proxy.

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

## Convenções do curso

- O curso vem antes do código: cada ticket ganha uma aula `docs/NN-slug.md` escrita com
  `/mkdocs-project-course <ticket>` (uma por ticket, dividida quando houver conceitos demais); o progresso
  da aprendiz é registrado com `/mkdocs-project-course progresso`.
- `course/` guarda o estado da aprendiz (missão, preferências, registros de aprendizado, histórico).
  Antes de mexer no curso, qualquer agente ou ferramenta lê `course/MISSION.md`, as últimas entradas e as
  pendências abertas de `course/LOG.md`, `course/learning-records/` e `course/NOTES.md`; cada aula escrita
  ou revisada e cada check-in entra como nova entrada no fim de `course/LOG.md`.
- `src/` e `tests/` são escritos pela usuária seguindo as aulas; um agente só escreve código real a pedido explícito.
- Site: `uv run mkdocs serve` (ambiente do projeto criado na aula 01-1; o `.venv` antigo está em `.venv-legacy`).
