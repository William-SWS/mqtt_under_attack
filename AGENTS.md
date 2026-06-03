# AGENTS.md — MQTT Under Attack: Detecção de Ataques DoS via Machine Learning

> Documento de contexto para agentes de IA. Leia este arquivo antes de qualquer ação no repositório.

---

## 1. Visão Geral do Projeto

Pipeline de Machine Learning para classificação de ataques **DoS (Denial of Service)** em redes **MQTT** (protocolo IoT). O sistema treina, otimiza e avalia múltiplos algoritmos de classificação com o objetivo final de rodar inferência em tempo real num **Raspberry Pi** (edge computing).

**Domínio:** Segurança de Redes IoT / Intrusion Detection System (IDS)
**Dataset:** `data/raw/DoS.csv` — tráfego MQTT rotulado (normal vs. ataques DoS)
**Branch ativa:** `refactor-pipeline`

---

## 2. Arquitetura do Pipeline (Versão Atual — Ensemble V2)

O pipeline foi refatorado em 3 fases sequenciais. O notebook principal é `notebooks_refactored/03_pipeline_05_05.ipynb`.

```
Fase 1: Baseline + Seleção de Features
  ├── Carregamento do DoS.csv
  ├── Limpeza (remoção de NaN, cálculo de gap features)
  ├── Split Train/Test (80/20, stratified)
  ├── StandardScaler (para modelos que requerem normalização)
  ├── Treino de 6 modelos baseline (sem otimização)
  └── Seleção de features via 7 seletores → Features de Consenso

Fase 2: Otimização com Optuna
  ├── Optuna Global — otimiza os 6 modelos usando as features de consenso
  └── Optuna por Seletor — otimiza 6 modelos × 7 seletores = 42 combinações

Fase 3: Super Ensemble (sobre os modelos já otimizados)
  ├── Averaging (média simples das probabilidades)
  ├── Hard Voting (voto majoritário das predições)
  └── Smart Soft Voting (Optuna otimiza os pesos do ensemble)
```

### 2.1. O Que Mudou em Relação ao Pipeline Antigo

O pipeline anterior (`02_dos_complete_pipeline.ipynb`) executava o Ensemble **antes** do Optuna, usando modelos baseline sem otimização. Isso causava perda de performance porque modelos fracos (LDA, QDA, GaussianNB com F1 ~0.92) "puxavam para baixo" os modelos fortes (GradientBoosting com F1 ~0.975).

A refatoração moveu o Ensemble para **depois** do Optuna, garantindo que apenas modelos de elite participem da votação.

### 2.2. Os 6 Algoritmos de Classificação

| Algoritmo | Tipo | Requer Scaling | Performance (F1) |
|---|---|---|---|
| GradientBoosting | Ensemble de árvores | Não | **0.9754** (Campeão) |
| RandomForest | Ensemble de árvores | Não | 0.9734 |
| DecisionTree | Árvore única | Não | 0.9688 |
| LDA | Discriminante linear | Sim | 0.9232 |
| QDA | Discriminante quadrático | Sim | 0.9224 |
| GaussianNB | Bayesiano ingênuo | Sim | 0.9198 |

> **Conclusão confirmada:** LDA, QDA e GaussianNB atingem um teto algorítmico de ~0.923. A limitação é da família de modelos (incapazes de traçar fronteiras não-lineares complexas), não dos hiperparâmetros.

### 2.3. Os 7 Seletores de Features

| Seletor | Nº Features Selecionadas |
|---|---|
| LowVariance | **12** (menor, ideal para edge) |
| Pearson | 15 |
| Fisher | 15 |
| mRMR | 15 |
| LassoCV | 15 |
| LinearSVC_L1 | 15 |
| ExtraTrees | 15 |

As **features de consenso** são a interseção dos resultados de todos os 7 seletores. O seletor **LowVariance** é o mais econômico (12 features), reduzindo a carga computacional no Raspberry Pi.

---

## 3. Estrutura de Diretórios

```
mqtt_under_attack/
├── AGENTS.md                          ← ESTE ARQUIVO
├── CLAUDE.md                          ← Contexto para Claude Code (legado)
├── raspberry_deploy.md                ← Guia de deploy no Raspberry Pi
├── new_pipeline_proposal.md           ← Proposta arquitetural da refatoração
├── results_new_pipeline.md            ← Rankings e métricas dos modelos finais
│
├── data/raw/                          ← Dataset bruto (DoS.csv)
├── data_refactored/                   ← Dados processados
│
├── notebooks_refactored/
│   ├── 01_dos_complete_pipeline.ipynb  ← Pipeline v1 (fillna global — leakage)
│   ├── 02_dos_complete_pipeline.ipynb  ← Pipeline v2 (SimpleImputer constant)
│   ├── 03_dos_complete_pipeline.ipynb  ← Pipeline v3 (SimpleImputer median)
│   └── 03_pipeline_05_05.ipynb        ← ★ PIPELINE ATUAL (Ensemble V2 + Optuna)
│
├── models/
│   ├── models_ensemble_v2/
│   │   ├── base/                       ← Modelos baseline (sem Optuna)
│   │   └── optuna/                     ← ★ Modelos otimizados (deploy)
│   ├── models_refactored/              ← Modelos do pipeline antigo
│   └── models_optuna/                  ← Modelos Optuna do pipeline antigo
│
├── reports/
│   └── reports_ensemble_v2/            ← ★ Relatórios do pipeline atual
│       ├── RELATORIO_FINAL.md          ← Relatório consolidado
│       ├── RELATORIO_DETALHADO.md      ← Relatório com análise profunda
│       ├── optuna_by_selector_best_params.json  ← Hiperparâmetros otimizados
│       ├── optuna_by_selector_results.csv       ← Métricas por seletor×modelo
│       ├── timing_results.csv          ← Tempos detalhados de cada etapa
│       └── ensemble_results.csv        ← Resultados do Averaging/Voting
│
├── scripts/
│   ├── data_loader.py                  ← Carregamento e pré-processamento
│   ├── train.py                        ← Treino com Optuna
│   ├── evaluate.py                     ← Avaliação e relatórios
│   └── pi_inference.py                 ← Script de inferência para o Raspberry Pi
│
├── mqtt_under_attack/                  ← Pacote Python principal
│   ├── dataset.py                      ← Utilitários de dados
│   ├── features.py                     ← Engenharia de features
│   ├── modeling/train.py               ← Lógica de treino
│   ├── modeling/predict.py             ← Inferência
│   ├── plots.py                        ← Visualizações
│   └── config.py                       ← Configurações
│
└── main.py                             ← Orquestrador do pipeline via scripts/
```

---

## 4. Modelos Selecionados para Deploy (Raspberry Pi)

Todos localizados em `models/models_ensemble_v2/optuna/`. Formato: `.pkl` (pickle/joblib).

| # | Arquivo | Tamanho | F1-Score | Log Loss | Tempo de Inferência* | Perfil |
|---|---|---|---|---|---|---|
| 1 | `optuna_by_selector_lowvariance_gradientboosting.pkl` | 995 KB | **0.9754** | **0.0714** | 0.056 s | Campeão geral (12 features) |
| 2 | `optuna_by_selector_lowvariance_decisiontree.pkl` | 6.7 KB | 0.9688 | 0.0891 | **0.001 s** | Ultra-rápido para ataques volumétricos |
| 3 | `optuna_by_selector_lowvariance_randomforest.pkl` | 2.4 MB | 0.9734 | 0.0848 | 0.155 s | Multicore (`n_jobs=-1`) |
| 4 | `optuna_by_selector_extratrees_gradientboosting.pkl` | 994 KB | **0.9754** | **0.0714** | 0.055 s | Benchmark (15 features) |
| 5 | `optuna_by_selector_lowvariance_lda.pkl` | 1.9 KB | 0.9232 | 0.3764 | **0.001 s** | Fallback de emergência |

*\*Tempo para predição sobre ~18.900 amostras de teste. Inferência por pacote individual: microsegundos.*

### 4.1. Hiperparâmetros Otimizados dos Modelos de Deploy

**GradientBoosting (LowVariance / ExtraTrees):**
```json
{"n_estimators": 191, "max_depth": 6, "learning_rate": 0.035, "min_samples_split": 11}
```

**DecisionTree (LowVariance):**
```json
{"max_depth": 6, "min_samples_split": 94, "min_samples_leaf": 27, "max_features": "log2"}
```

**RandomForest (LowVariance):**
```json
{"n_estimators": 298, "max_depth": 10, "min_samples_split": 97, "min_samples_leaf": 10, "max_features": "log2", "max_samples": 0.7157}
```

**LDA (LowVariance):**
```json
{"solver": "svd", "tol": 1.49e-06}
```

---

## 5. Resultados do Ensemble

O Ensemble opera exclusivamente sobre os modelos **já otimizados** pelo Optuna. Os 3 métodos implementados:

| Método | F1-Score | Observação |
|---|---|---|
| **Smart Soft Voting** (Optuna-weighted) | **0.9742** | Silencia modelos fracos automaticamente |
| **Hard Voting** (Majoritário) | 0.9742 | Robusto contra overconfidence |
| **Averaging** (Média simples) | 0.9251 | Diluído pelos modelos fracos — não recomendado |

> **Conclusão:** O Ensemble não superou o GradientBoosting individual (0.9754 vs 0.9742), mas **aumenta a robustez** do sistema. No Raspberry Pi, recomenda-se rodar o GradientBoosting individualmente (máxima precisão) ou um Top-3 Voting (GB + RF + DT) para máxima segurança.

---

## 6. Correções Técnicas Aplicadas na Refatoração

Problemas resolvidos durante a implementação do Ensemble V2:

1. **`NameError: X_train_cons`** — A variável de features de consenso não era criada antes do Optuna Global. Corrigido injetando o setup de `X_train_cons` e `X_test_cons` antes da célula de otimização.
2. **`ValueError: need at least one array to stack`** — Adicionadas guard clauses em todas as células de Ensemble para pular graciosamente caso `optuna_trained_models` esteja vazio.
3. **`TypeError` no `scipy.stats.mode`** — Versões recentes do SciPy rejeitam arrays de strings. Migrado para `pandas.DataFrame().mode()` no Hard Voting.

---

## 7. Estratégia de Tratamento de Valores Ausentes

O projeto avalia 3 abordagens de imputação em notebooks separados:

| Estratégia | Notebook | Diretório de Artefatos | Status |
|---|---|---|---|
| `fillna(0)` global (pré-split) | `01_dos_complete_pipeline.ipynb` | `reports_refactored/` | ⚠️ Data leakage |
| `SimpleImputer(constant, 0)` post-split | `02_dos_complete_pipeline.ipynb` | `reports/reports_refactored_constant/` | ✅ Recomendada |
| `SimpleImputer(median)` post-split | `03_dos_complete_pipeline.ipynb` | `reports/reports_refactored_median/` | ❌ Degradação |

O pipeline atual (`03_pipeline_05_05.ipynb`) usa a estratégia **Constant** como base.

---

## 8. Como Executar

### Pipeline Completo (Notebook)
```bash
# Abrir o notebook principal e executar "Restart Kernel and Run All Cells"
jupyter notebook notebooks_refactored/03_pipeline_05_05.ipynb
```

### Pipeline via Scripts (Legado)
```bash
python main.py  # Orquestra: data_loader.py → train.py → evaluate.py
```

### Deploy no Raspberry Pi
```bash
# Da máquina local:
scp models/models_ensemble_v2/optuna/optuna_by_selector_lowvariance_gradientboosting.pkl \
    pi@<IP>:~/mqtt_infer/models/
scp scripts/pi_inference.py pi@<IP>:~/mqtt_infer/

# No Raspberry Pi:
source ~/mqtt_env/bin/activate
python pi_inference.py --model models/optuna_by_selector_lowvariance_gradientboosting.pkl \
    --broker localhost --topic "sensor/#"
```

Detalhes completos em `raspberry_deploy.md`.

---

## 9. Dependências Principais

```
python >= 3.10
scikit-learn
numpy
pandas
optuna
scipy
joblib
paho-mqtt (para inferência no Pi)
```

Instalação: `pip install -r requirements.txt`

---

## 10. Próximos Passos Sugeridos

1. **Validar `pi_inference.py`** — Garantir que o script carrega corretamente os modelos `.pkl` do Ensemble V2 e que as 12 features do LowVariance são extraídas em tempo real do tráfego MQTT.
2. **Benchmark no Raspberry Pi** — Executar os 5 modelos de deploy na placa e medir latência real, uso de RAM e temperatura da CPU sob carga.
3. **Monitoramento em Produção** — Adicionar validação de drift (distribuição das features em produção vs. treino) para detectar quando o modelo precisa ser re-treinado.
4. **Pruning do Ensemble no Pi** — Se usar Voting na placa, carregar apenas os 3 modelos com maior peso do Smart Soft Voting (ignorar GaussianNB, LDA, QDA).
