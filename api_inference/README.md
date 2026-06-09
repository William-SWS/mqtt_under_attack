# MQTT Inference Benchmark API

API HTTP assíncrona para medir tempo de inferencia dos modelos treinados do pipeline
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

## Referencia dos Arquivos da API

### `app/main.py`

Este arquivo define a aplicacao FastAPI e os endpoints HTTP expostos para o
usuario. Nenhum endpoint exige autenticacao ou corpo JSON.

| Metodo | Rota | Entrada | Retorno esperado |
|---|---|---|---|---|
| `health()` | `GET /health` | Nenhuma. | Dicionario com `status`, caminhos configurados e flags indicando se `models/`, `datasets/test/` e `results_inference/` existem. |
| `models()` | `GET /models` | Nenhuma. | Dicionario com `count`, `compatible_count` e `models`, onde cada item descreve um modelo, dataset pareado, quantidade de features, linhas e compatibilidade. |
| `benchmark_all()` | `POST /benchmark` | Nenhuma. | Executa todos os modelos compativeis, sobrescreve `results_inference/iinference.csv` e retorna `count`, `results_csv` e a lista `results`. |
| `benchmark_one(model_id)` | `POST /benchmark/{model_id}` | `model_id` no path, exemplo: `lowvariance_gradientboosting`. | Executa um unico modelo, atualiza o CSV preservando os outros resultados e retorna `results_csv` e `result`. Se o modelo nao existir ou estiver incompativel, retorna HTTP `404` com detalhes do erro. |

> Todos os endpoints sao assincronos (`async def`). Operacoes CPU-bound
> rodam na thread pool via `asyncio.to_thread()`, permitindo que o event
> loop atenda outras requisicoes durante inferencias longas.

Exemplo de resposta resumida de `POST /benchmark/{model_id}`:

```json
{
  "results_csv": "/app/results_inference/iinference.csv",
  "result": {
    "model_id": "lowvariance_gradientboosting",
    "rows": 18925,
    "n_features": 12,
    "inference_time_sec": 0.056,
    "accuracy": 0.9753,
    "status": "success"
  }
}
```

### `app/benchmark.py`

Este arquivo contem a logica de descoberta de modelos, validacao dos datasets,
execucao da inferencia, calculo dos tempos e escrita do CSV final.

#### Estruturas de dados

| Estrutura | Entrada/Campos | Retorno/Uso |
|---|---|---|
| `Paths` | `root`, `models_dir`, `datasets_test_dir`, `results_dir`, `results_csv`. | Agrupa todos os caminhos usados pela API. |
| `ModelInfo` | Metadados de um par modelo/dataset: `model_id`, arquivos, caminhos, features, linhas, compatibilidade e erro. | Usado por `/models` e pela selecao de quais modelos podem rodar benchmark. |
| `BenchmarkResult` | Resultado de uma execucao: tempos, linhas, features, accuracy, status e erro. | Usado para resposta JSON e para escrever `iinference.csv`. |

#### Funcoes de configuracao e saude

| Funcao | Entrada | Retorno esperado |
|---|---|---|
| `get_paths()` | Nenhuma entrada obrigatoria. Le variaveis de ambiente opcionais: `API_INFERENCE_ROOT`, `MODELS_DIR`, `DATASETS_TEST_DIR`, `RESULTS_DIR`, `RESULTS_CSV`. | Um `Paths` com os caminhos efetivos. Por padrao usa `api_inference/models`, `api_inference/datasets/test` e `api_inference/results_inference/iinference.csv`. |
| `health_status(paths=None)` | `paths` opcional. Se omitido, chama `get_paths()`. | Dicionario com status `ok`, caminhos usados e booleanos indicando existencia dos diretorios principais. |

#### Funcoes de pareamento e leitura

| Funcao | Entrada | Retorno esperado |
|---|---|---|
| `model_id_from_path(model_path)` | `Path` de um arquivo `.pkl`, exemplo `optuna_by_selector_lowvariance_lda.pkl`. | String sem o prefixo `optuna_by_selector_`, exemplo `lowvariance_lda`. |
| `expected_dataset_name(model_path)` | `Path` de um arquivo `.pkl`. | Nome esperado do CSV de teste, exemplo `test_optuna_by_selector_lowvariance_lda.csv`. |
| `_model_feature_names(model)` | Objeto de modelo carregado via `joblib`. | Lista com `model.feature_names_in_` convertida para string, ou `None` se o modelo nao expuser essa informacao. |
| `_read_dataset_header(dataset_path)` | `Path` de um CSV de teste. | Tupla `(columns, rows)`, com a lista de colunas e numero de linhas de dados. |

#### Funcoes de descoberta e validacao

| Funcao | Entrada | Retorno esperado |
|---|---|---|
| `discover_models(paths=None)` | `paths` opcional. | Lista de `ModelInfo`. Para cada `.pkl`, tenta carregar o modelo, encontra o CSV esperado, compara features do modelo com as colunas do dataset sem `type`, e marca como `compatible` ou `incompatible`. |
| `_empty_result(model_id, model_file, dataset_file, error)` | Identificadores do modelo/dataset e uma mensagem de erro. | Um `BenchmarkResult` com `status="error"` e campos numericos vazios. |

#### Funcoes de benchmark

| Funcao | Entrada | Retorno esperado |
|---|---|---|
| `run_benchmark(model_id, paths=None)` | `model_id`, exemplo `lowvariance_randomforest`; `paths` opcional. | Um `BenchmarkResult`. Carrega o `.pkl`, le o CSV, separa `X` e `y`, valida `feature_names_in_`, faz warm-up com uma linha, mede apenas `model.predict(X)` no dataset completo, calcula `accuracy` e tempos. |
| `run_all_benchmarks(paths=None)` | `paths` opcional. | Lista de `BenchmarkResult` para todos os modelos marcados como compativeis por `discover_models()`. |

O tempo principal salvo em `inference_time_sec` mede apenas esta etapa:

```python
predictions = model.predict(x_test)
```

Tempo de carregamento do modelo e tempo de leitura do dataset sao medidos em
campos separados: `load_time_sec` e `dataset_read_time_sec`.

#### Funcoes de escrita e serializacao

| Funcao | Entrada | Retorno esperado |
|---|---|---|
| `_results_to_frame(results)` | Lista de `BenchmarkResult`. | `pandas.DataFrame` com as colunas padronizadas em `CSV_COLUMNS`. |
| `write_results(results, paths=None)` | Lista de `BenchmarkResult`; `paths` opcional. | Cria `results_inference/` se necessario, sobrescreve `iinference.csv` e retorna o `Path` do CSV. |
| `update_single_result(result, paths=None)` | Um `BenchmarkResult`; `paths` opcional. | Atualiza ou cria `iinference.csv`. Se ja existir resultado para o mesmo `model_id`, substitui essa linha e preserva os demais modelos. |
| `public_model_info(paths=None)` | `paths` opcional. | Lista de dicionarios serializaveis para JSON a partir de `ModelInfo`. Usado por `GET /models`. |
| `public_result(result)` | Um `BenchmarkResult`. | Dicionario serializavel para JSON. Usado pelas respostas de benchmark. |

#### Colunas do CSV `iinference.csv`

| Coluna | Significado |
|---|---|
| `model_id` | Identificador curto do modelo, como `lowvariance_lda`. |
| `model_file` | Arquivo `.pkl` usado. |
| `dataset_file` | CSV de teste usado. |
| `rows` | Numero de amostras inferidas. |
| `n_features` | Numero de features usadas em `X`. |
| `load_time_sec` | Tempo para carregar o modelo com `joblib.load`. |
| `dataset_read_time_sec` | Tempo para ler o CSV com `pandas.read_csv`. |
| `inference_time_sec` | Tempo medido somente para `model.predict(X)`. |
| `inference_time_ms` | Mesmo tempo de inferencia convertido para milissegundos. |
| `avg_inference_ms_per_row` | Tempo medio por linha/amostra. |
| `predictions_per_sec` | Vazao aproximada de predicoes por segundo. |
| `accuracy` | Proporcao de predicoes iguais a coluna `type`. |
| `status` | `success` ou `error`. |
| `error` | Mensagem de erro quando houver falha. |
| `created_at` | Timestamp UTC da execucao. |

## Rodar Localmente

```bash
cd api_inference
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

> Dica: Ajuste `--workers` para o numero de CPUs da maquina. Em ambiente Docker,
> a variavel `UVICORN_WORKERS` controla esse valor.

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

## Stress Test

O script `stress_test.py` simula multiplas requisicoes concorrentes de uma
maquina remota, ideal para validar o comportamento da API sob carga.

### Requisito

```bash
pip install httpx
```

(ja incluido no `requirements.txt`)

### Uso basico

Testar o endpoint `/health` com 10 requisicoes simultaneas:

```bash
python stress_test.py --url http://localhost:8000 --endpoint /health --concurrency 10 --requests 100
```

### Opcoes

| Argumento | Padrao | Descricao |
|---|---|---|
| `--url` | `http://localhost:8000` | URL base da API |
| `--endpoint` | `/health` | Caminho do endpoint: `/health`, `/models`, `/benchmark` ou `/benchmark/lowvariance_gradientboosting` |
| `-c` / `--concurrency` | `10` | Numero de requisicoes simultaneas |
| `-n` / `--requests` | `100` | Total de requisicoes a enviar |
| `-t` / `--timeout` | `300` | Timeout por requisicao em segundos (modelos podem demorar) |

### Exemplos

Teste rapido de health check com 50 requisicoes concorrentes:

```bash
python stress_test.py --endpoint /health --concurrency 50 --requests 500
```

Teste de benchmark com 5 requisicoes simultaneas (cada uma roda todos os modelos):

```bash
python stress_test.py --endpoint /benchmark --concurrency 5 --requests 20 --timeout 600
```

De outra maquina na mesma rede:

```bash
python stress_test.py --url http://192.168.1.100:8000 --endpoint /models --concurrency 20 --requests 200
```

### Relatorio de saida

O script exibe ao final:

```
=== Stress Test Results ===
Target URL:       http://localhost:8000/health
Concurrency:      100 total
Total duration:   2.34s

--- Results ---
Successful:       100
Failed:           0
Timeouts:         0
Error rate:       0.0%

--- Throughput ---
Requests/sec:     42.7

--- Latency (ms) ---
Average:          233.5
Min:              45.2
Max:              512.8
P50 (median):     198.3
P95:              481.2
P99:              508.9
```

### Arquitetura assincrona e concorrencia

A API usa FastAPI com `async def` em todos os endpoints. As operacoes
CPU-bound (carregamento de modelo, inferencia, leitura de CSV) sao
executadas na thread pool do Python via `asyncio.to_thread()`, liberando
o event loop para atender outras requisicoes enquanto a inferencia roda.

O Uvicorn pode ser executado com multiplos workers (`--workers N`), cada
um em um processo separado, permitindo paralelismo real em maquinas
multi-core. Cada worker tem sua propria thread pool e event loop.

Para ambientes conteinerizados, a variavel `UVICORN_WORKERS` controla o
numero de workers (padrao: 4). Ajuste conforme a CPU disponivel:

```yaml
environment:
  UVICORN_WORKERS: 4
```

## Raspberry Pi

A imagem base `python:3.13-slim-bookworm` e multi-arch, entao funciona em desktop
x86_64 e Raspberry Pi OS 64-bit/arm64. Para melhores resultados, use Raspberry Pi
OS 64-bit, pois `pandas`, `numpy` e `scikit-learn` dependem de wheels compativeis
com a arquitetura.

### Passo a Passo Para Replicar no Raspberry Pi

Use preferencialmente Raspberry Pi OS 64-bit. Em Raspberry Pi OS 32-bit, algumas
dependencias cientificas podem nao ter wheels prontas e o build pode ficar lento
ou falhar.

#### 1. Preparar o sistema no Raspberry Pi

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y ca-certificates curl git
```

#### 2. Instalar Docker e Docker Compose

Opcao simples, usando o script oficial de instalacao do Docker:

```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo apt-get update
sudo apt-get install -y docker-compose-plugin
```

Permita executar Docker sem `sudo`:

```bash
sudo usermod -aG docker "$USER"
newgrp docker
```

Verifique a instalacao:

```bash
docker --version
docker compose version
docker run --rm hello-world
```

#### 3. Copiar a API para o Raspberry Pi

Na maquina local, a partir da raiz do repositorio:

```bash
rsync -av api_inference/ pi@192.168.20.83:~/api_inference/
```

Se preferir `scp`:

```bash
scp -r api_inference pi@192.168.20.83:~/
```

#### 4. Conferir modelos e datasets no Raspberry Pi

No Raspberry Pi:

```bash
cd ~/api_inference
find models -maxdepth 1 -type f -name "*.pkl" | sort
find datasets/test -maxdepth 1 -type f -name "*.csv" | sort
```

Devem existir estes 5 modelos:

```text
optuna_by_selector_extratrees_gradientboosting.pkl
optuna_by_selector_lowvariance_decisiontree.pkl
optuna_by_selector_lowvariance_gradientboosting.pkl
optuna_by_selector_lowvariance_lda.pkl
optuna_by_selector_lowvariance_randomforest.pkl
```

E estes datasets de teste correspondentes:

```text
test_optuna_by_selector_extratrees_gradientboosting.csv
test_optuna_by_selector_lowvariance_decisiontree.csv
test_optuna_by_selector_lowvariance_gradientboosting.csv
test_optuna_by_selector_lowvariance_lda.csv
test_optuna_by_selector_lowvariance_randomforest.csv
```

#### 5. Construir a imagem Docker

```bash
cd ~/api_inference
docker compose build
```

No primeiro build, o Docker vai baixar a imagem base e instalar `pandas`,
`numpy`, `scikit-learn`, `joblib`, `fastapi` e `uvicorn`.

#### 6. Subir a API

```bash
docker compose up -d
docker compose logs -f
```

A API fica disponivel em:

```text
http://192.168.20.83:8000
```

Se a porta `8000` ja estiver em uso, altere o mapeamento no
`docker-compose.yml`:

```yaml
ports:
  - "8001:8000"
```

Depois rode:

```bash
docker compose up -d
```

#### 7. Testar os endpoints

No Raspberry Pi ou em outra maquina na mesma rede:

```bash
curl http://192.168.20.83:8000/health
curl http://192.168.20.83:8000/models
```

Para executar o benchmark completo:

```bash
curl -X POST http://192.168.20.83:8000/benchmark
```

Para executar apenas um modelo:

```bash
curl -X POST http://192.168.20.83:8000/benchmark/lowvariance_gradientboosting
curl -X POST http://192.168.20.83:8000/benchmark/lowvariance_decisiontree
curl -X POST http://192.168.20.83:8000/benchmark/lowvariance_randomforest
curl -X POST http://192.168.20.83:8000/benchmark/extratrees_gradientboosting
curl -X POST http://192.168.20.83:8000/benchmark/lowvariance_lda
```

#### 8. Conferir o CSV de resultados

O benchmark salva os tempos em:

```text
~/api_inference/results_inference/iinference.csv
```

Confira no Raspberry Pi:

```bash
cat results_inference/iinference.csv
```

Para copiar o CSV de volta para a maquina local:

```bash
scp pi@192.168.20.83:~/api_inference/results_inference/iinference.csv .
```

#### 9. Parar a API

```bash
cd ~/api_inference
docker compose down
```

#### Troubleshooting

- `permission denied while trying to connect to the Docker daemon`: execute
  `sudo usermod -aG docker "$USER"` e abra uma nova sessao SSH.
- `Bind for :::8000 failed: port is already allocated`: troque o mapeamento
  para `8001:8000` no `docker-compose.yml`.
- Build muito lento no Raspberry Pi: confirme que o sistema e 64-bit com
  `uname -m`; o esperado para Raspberry Pi OS 64-bit e `aarch64`.
- Modelo incompatível em `/models`: confira se existe o CSV de teste com o
  mesmo sufixo do `.pkl`, prefixado por `test_`.
