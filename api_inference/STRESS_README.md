# Stress Test API

Servidor FastAPI que dispara requisições HTTP concorrentes contra a API de
inferência de modelos MQTT rodando no **Raspberry Pi**, medindo latência,
throughput e consumo de recursos sob carga.

## Pré-requisitos

```bash
pip install uvicorn httpx fastapi
```

Python 3.13+.

## Como rodar

```bash
cd api_inference
uvicorn stress_api.main:app --host 0.0.0.0 --port 8001
```

O servidor fica disponível em `http://localhost:8001`.

## Endpoints

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/health` | Health check do servidor de stress |
| `POST` | `/run` | Executa um teste de estresse completo |

## Parâmetros do `POST /run`

| Campo | Tipo | Padrão | Obrigatório | Descrição |
|---|---|---|---|---|
| `target_url` | string | — | **sim** | URL base da API alvo (ex: `http://192.168.20.83:8000`) |
| `endpoint` | string | `/benchmark` | não | Endpoint a testar: `/benchmark` (todos os modelos), `/benchmark/lowvariance_gradientboosting`, `/health`, `/models` |
| `concurrency` | int | `5` | não | Número de requisições simultâneas |
| `requests` | int | `20` | não | Total de requisições a enviar |
| `timeout` | float | `600.0` | não | Timeout por requisição em segundos |
| `output_dir` | string | `results_inference` | não | Diretório para salvar o JSON de resultados |

## Exemplos

### Mínimo (testa todos os modelos com defaults)

```bash
curl -X POST http://localhost:8001/run \
  -H "Content-Type: application/json" \
  -d '{"target_url": "http://192.168.20.83:8000"}'
```

### Teste pesado (alta concorrência)

```bash
curl -X POST http://localhost:8001/run \
  -H "Content-Type: application/json" \
  -d '{
    "target_url": "http://192.168.20.83:8000",
    "endpoint": "/benchmark",
    "concurrency": 10,
    "requests": 50,
    "timeout": 600
  }'
```

### Testar apenas um modelo específico

```bash
curl -X POST http://localhost:8001/run \
  -H "Content-Type: application/json" \
  -d '{
    "target_url": "http://192.168.20.83:8000",
    "endpoint": "/benchmark/lowvariance_gradientboosting",
    "concurrency": 5,
    "requests": 20
  }'
```

### Apenas health check (teste leve)

```bash
curl -X POST http://localhost:8001/run \
  -H "Content-Type: application/json" \
  -d '{
    "target_url": "http://192.168.20.83:8000",
    "endpoint": "/health",
    "concurrency": 50,
    "requests": 500
  }'
```

## Threads e concorrência — Como aumentar

Há **3 níveis** de paralelismo que podem ser ajustados:

### 1. Concorrência do stress test (`concurrency`)

Controla quantas requisições HTTP são disparadas simultaneamente contra
o Pi. Implementado via `asyncio.Semaphore`.

```json
{"concurrency": 20, "requests": 200}
```

### 2. Workers do Uvicorn no Pi (`UVICORN_WORKERS`)

No `docker-compose.yml` do Pi:

```yaml
environment:
  UVICORN_WORKERS: 4
```

Cada worker é um **processo separado** com seu próprio event loop e thread
pool. No Raspberry Pi 4 (4 CPUs), valores recomendados:

| `UVICORN_WORKERS` | Cenário |
|---|---|
| `2` | Estável, menor uso de RAM |
| `4` | Máximo throughput, 1 worker por CPU |
| `6+` | Oversubscription — mais processos que CPUs |

#### Como alterar os workers no Pi

**Não precisa rebuildar a imagem Docker** — a env var é lida em runtime.
Basta editar o `docker-compose.yml` no Pi e reiniciar o container:

```bash
ssh pi@192.168.20.83
cd ~/api_inference
# Altere o valor no docker-compose.yml com seu editor, ou via sed:
sed -i 's/UVICORN_WORKERS: 4/UVICORN_WORKERS: 2/' docker-compose.yml
# Só reinicia o container, sem rebuild:
docker compose up -d
```

O `docker compose up -d` recria o container com a nova variável de ambiente
sem rebuildar a imagem, porque o `Dockerfile` não mudou — só a configuração
em runtime.

### 3. Threads do scikit-learn (`OMP_NUM_THREADS`)

O scikit-learn usa OpenMP internamente para paralelizar operações. Com
`UVICORN_WORKERS > 1`, múltiplos workers podem competir pelas CPUs.

Para evitar **oversubscription**, adicione no `docker-compose.yml` do Pi:

```yaml
environment:
  OMP_NUM_THREADS: 1
  OPENBLAS_NUM_THREADS: 1
```

Isso força cada predict a usar apenas 1 thread, deixando o escalonamento
para o UVICORN_WORKERS.

### Tabela de configurações recomendadas

| Cenário | `concurrency` | `UVICORN_WORKERS` | `OMP_NUM_THREADS` |
|---|---|---|---|
| Teste leve | 5 | 2 | 1 |
| Teste moderado | 10 | 4 | 1 |
| Estresse máximo | 20 | 4 | 1 |

## O que o JSON retornado contém

```jsonc
{
  "test_info": {            // metadados do teste
    "target_url": "...",
    "concurrency": 5,
    "requests": 20,
    "duration_sec": 45.2
  },
  "results": {              // resumo global
    "successful": 20,       // requisições OK
    "failed": 0,            // requisições com erro
    "throughput_req_per_sec": 8.5  // requisições por segundo
  },
  "latency_ms": {           // latência HTTP
    "average": 587.3,
    "p50": 550.2,
    "p95": 1100.8,
    "p99": 1200.3,
    "all": [201.7, ...]     // todas as latências individuais
  },
  "per_model": {            // só aparece em /benchmark
    "lowvariance_gradientboosting": {
      "requests": 20,
      "inference_time_ms_avg": 252.6,
      "inference_time_ms_ci95_lower": 233.5,
      "inference_time_ms_ci95_upper": 271.7,
      "inference_times_ms": [297.2, ...]
    }
  },
  "system_before": {        // estado do Pi antes do teste
    "uvicorn_workers": 4,
    "memory_used_mb": 2894,
    "load_avg_1min": 0.5
  },
  "system_after": { ... }   // estado do Pi depois do teste
}
```

## CLI standalone (alternativa sem servidor)

```bash
python stress_test.py --url http://192.168.20.83:8000 --endpoint /benchmark -c 5 -n 20
```

O JSON também é salvo em `results_inference/stress_test_*.json`.
