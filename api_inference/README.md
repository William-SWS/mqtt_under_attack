# MQTT Inference Benchmark API

API HTTP simples para medir tempo de inferencia dos modelos treinados do pipeline
`03_pipeline_05_05.ipynb`.

## Estrutura

```text
api_inference/
├── app/
├── datasets/test/
├── models/
└── results_inference/
```

O resultado do benchmark e salvo em:

```text
results_inference/iinference.csv
```

## Endpoints

- `GET /health`: status da API e dos diretorios.
- `GET /models`: lista os modelos, datasets pareados e compatibilidade.
- `POST /benchmark`: executa todos os modelos compativeis e sobrescreve o CSV.
- `POST /benchmark/{model_id}`: executa um modelo e atualiza o CSV.

Model IDs esperados:

- `lowvariance_gradientboosting`
- `lowvariance_decisiontree`
- `lowvariance_randomforest`
- `extratrees_gradientboosting`
- `lowvariance_lda`

## Rodar Localmente

```bash
cd api_inference
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Em outro terminal:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/models
curl -X POST http://localhost:8000/benchmark
```

## Rodar Com Docker

```bash
cd api_inference
docker compose build
docker compose up
```

O `docker-compose.yml` monta os modelos e datasets como leitura e permite escrita
em `results_inference/`.

## Raspberry Pi

A imagem base `python:3.13-slim-bookworm` e multi-arch, entao funciona em desktop
x86_64 e Raspberry Pi OS 64-bit/arm64. Para melhores resultados, use Raspberry Pi
OS 64-bit, pois `pandas`, `numpy` e `scikit-learn` dependem de wheels compativeis
com a arquitetura.
