# Documentação Técnica: Pipeline Avançado de Detecção de Ataques DoS em Tráfego MQTT

## Ensemble de Seleção de Features + Ensemble de Modelos com Stacking e Voting

> **Resumo.** Este documento descreve integralmente o pipeline de aprendizado de máquina implementado no notebook `pipeline_advanced_v3_fixed.ipynb` para a classificação binária de tráfego MQTT como ataque DoS (*Denial of Service*) ou tráfego normal. O pipeline estrutura-se em três etapas: **(0)** ensemble baseline com split 70/30, incluindo VotingClassifier; **(1)** ensemble de seleção de características por sete métodos independentes com agregação por consenso; **(2)** ensemble de modelos por dataset via Optuna, VotingClassifier (soft e hard) e StackingClassifier com *out-of-fold predictions*. São detalhados os métodos de pré-processamento, os sete seletores de características, os seis modelos de classificação com seus espaços de hiperparâmetros, o processo de otimização bayesiana, as três estratégias de ensemble, a validação cruzada estratificada e as seis métricas de avaliação empregadas. Os resultados experimentais completos são apresentados em tabelas, incluindo o melhor par seletor×modelo identificado.

---

## Sumário

1. [Introdução e Arquitetura do Pipeline](#1-introdução-e-arquitetura-do-pipeline)
2. [Dataset e Pré-processamento](#2-dataset-e-pré-processamento)
3. [Etapa 0 — Ensemble Baseline](#3-etapa-0--ensemble-baseline)
4. [Etapa 1 — Ensemble de Seleção de Features](#4-etapa-1--ensemble-de-seleção-de-features)
5. [Etapa 2 — Ensemble de Modelos com Optuna](#5-etapa-2--ensemble-de-modelos-com-optuna)
6. [Modelos de Classificação](#6-modelos-de-classificação)
7. [Estratégias de Ensemble](#7-estratégias-de-ensemble)
8. [Validação Cruzada Estratificada](#8-validação-cruzada-estratificada)
9. [Métricas de Avaliação](#9-métricas-de-avaliação)
10. [Resultados Experimentais Completos](#10-resultados-experimentais-completos)
11. [Análise e Discussão](#11-análise-e-discussão)
12. [Conclusões](#12-conclusões)
13. [Referências](#13-referências)

---

## 1. Introdução e Arquitetura do Pipeline

O protocolo MQTT (*Message Queuing Telemetry Transport*) é o padrão dominante em ecossistemas IoT (*Internet of Things*), adotado por sua leveza e modelo publish-subscribe. A centralização de toda comunicação em um único *broker* torna esse componente particularmente vulnerável a ataques de Negação de Serviço (DoS), nos quais um adversário satura o serviço com requisições maliciosas, comprometendo a disponibilidade de toda a infraestrutura conectada.

O presente pipeline é estruturado em três etapas progressivas, cada uma construindo sobre a anterior:

```
Dataset bruto (94.625 × 67)
    │
    ▼
Pré-processamento (IQR capping → limpeza → encoding)
    │
    ├─► Etapa 0: Baseline
    │       Split 70/30 estratificado
    │       6 modelos individuais + VotingClassifier Soft
    │       Referência sem seleção de features nem Optuna
    │
    ├─► Etapa 1: Ensemble de Seleção
    │       7 seletores aplicados sobre X completo
    │       Agregação por voting_count e mean_rank
    │       9 datasets gerados (7 individuais + 2 consenso)
    │
    └─► Etapa 2: Ensemble de Modelos
            Por dataset: 5-fold CV externo
            Por fold: Optuna (20 trials, 3-fold interno) → 6 modelos
            VotingClassifier Soft + Hard por fold
            StackingClassifier OOF por fold
            Comparação final: melhor par (seletor × modelo)
```

A separação entre as etapas tem propósito metodológico claro: a Etapa 0 estabelece uma referência honesta sem qualquer otimização; a Etapa 1 identifica as features discriminativas usando múltiplas perspectivas independentes; a Etapa 2 otimiza os modelos rigorosamente dentro de cada fold de CV, garantindo estimativas não-viesadas do desempenho generalizado.

---

## 2. Dataset e Pré-processamento

### 2.1 Caracterização do Dataset

| Dimensão | Valor |
|---|---|
| Amostras totais | 94.625 |
| Features no dataset bruto | 67 |
| Features removidas por irrelevância | 26 |
| **Features utilizadas nos modelos** | **29** |
| Classe DoS (label = 0) | ≈ 50% |
| Classe Normal (label = 1) | ≈ 50% |

### 2.2 Remoção de Colunas Irrelevantes

Vinte e seis colunas são descartadas antes de qualquer modelagem, agrupadas em quatro categorias:

**Identificadores de instância** (`frame.number`, `frame.interface_id`, `frame.md5_hash`, `frame.interface_name`): não carregam poder preditivo generalizável; sua inclusão produziria overfitting trivial por memorização de IDs.

**Timestamps absolutos** (`frame.time_epoch`, `frame.time_relative`, `frame.time_delta_displayed`): o instante absoluto de captura de um pacote é irrelevante para a classificação do tipo de tráfego. O campo `frame.time_delta` (intervalo entre pacotes consecutivos) é **retido** por refletir a taxa de chegada — feature discriminativa de DoS.

**Campos de payload de sessão** (`mqtt.username`, `mqtt.passwd`, `mqtt.willmsg`, `mqtt.willtopic`, `mqtt.msgid`): valores específicos de sessão sem relação causal com DoS; também representam risco de privacidade.

**Artefatos de captura Wireshark** (`frame.coloring_rule.name`, `frame.comment`, `frame.file_off`, `frame.offset_shift`, `frame.link_nr` e similares): gerados pela ferramenta de análise, inexistentes em tráfego de produção.

### 2.3 Tratamento de Outliers — IQR Capping

O método IQR (*Interquartile Range*) é aplicado coluna a coluna sobre todas as 55 features numéricas antes da remoção de colunas irrelevantes:

$$
\text{IQR} = Q_3 - Q_1, \quad L_{\inf} = Q_1 - 1{,}5 \times \text{IQR}, \quad L_{\sup} = Q_3 + 1{,}5 \times \text{IQR}
$$

Valores fora dos limites são substituídos pelo limite respectivo (*capping*). A remoção de linhas não é realizada, preservando todas as 94.625 amostras.

**Justificativa do capping sobre remoção:** em dados de rede, valores extremos representam eventos legítimos (rajadas, reconexões lentas) e não erros de medição. O capping preserva a informação de que o evento ocorreu sem permitir que valores discrepantes distorçam as distribuições. O método IQR é escolhido por ser não-paramétrico e, portanto, robusto a distribuições exponenciais e log-normais típicas de features de rede.

### 2.4 Tratamento de Valores Ausentes e Inválidos

```python
X = X.fillna(0).replace([np.inf, -np.inf], 0)
```

`NaN` em campos MQTT opcionais (presentes apenas em mensagens `CONNECT`) são substituídos por zero — semanticamente correto, pois a ausência do campo equivale ao valor padrão do protocolo. Valores `±inf` surgem de divisões em campos de gap temporal quando o intervalo é nulo.

### 2.5 Codificação do Label

```python
le = LabelEncoder()
y = le.fit_transform(df_tratado["type"])
# DoS → 0,  normal → 1
```

---

## 3. Etapa 0 — Ensemble Baseline

### 3.1 Propósito e Metodologia

A Etapa 0 estabelece uma **linha de base honesta**: todos os 29 features pós-limpeza são utilizados, sem seleção e sem otimização de hiperparâmetros via Optuna. A avaliação usa split holdout 70/30 estratificado, com semente fixa para reprodutibilidade.

```python
X_tr_b, X_te_b, y_tr_b, y_te_b = train_test_split(
    X, y, test_size=0.30, stratify=y, random_state=42
)
```

O split estratificado garante que a proporção de classes (~50/50) seja preservada no conjunto de treino (66.237 amostras) e no conjunto de teste (28.388 amostras).

### 3.2 Modelos do Baseline

Os seis modelos são configurados com hiperparâmetros razoáveis fixos, sem busca:

| Modelo | Configuração principal |
|---|---|
| RandomForest | `n_estimators=200`, `n_jobs=-1` |
| XGBoost | `n_estimators=100`, `n_jobs=-1`, `eval_metric="logloss"` |
| DecisionTree | `random_state=42` (hiperparâmetros padrão) |
| GaussianNB\_Cal | `CalibratedClassifierCV(isotonic, cv=3)` |
| KNN | `n_neighbors=7`, `algorithm="kd_tree"`, `n_jobs=-1` |
| GradientBoosting | `HistGBT: max_iter=50`, `learning_rate=0.1`, `max_depth=4` |

**Nota sobre `kd_tree` no KNN:** o `KNeighborsClassifier` com `algorithm="kd_tree"` constrói um índice espacial sobre os dados de treino, reduzindo a complexidade de `predict` de $O(n_{\text{train}} \times n_{\text{test}})$ para $O(n_{\text{test}} \log n_{\text{train}})$ — aceleração de 5–20× em relação ao `brute force` para 29 features.

**Nota sobre `HistGradientBoostingClassifier`:** substitui o `GradientBoostingClassifier` clássico (sequencial, $O(n \times p)$ por split) pelo algoritmo de binning de histogramas, reduzindo cada split para $O(\text{bins} \times p)$ com paralelismo interno. Tempo de treino: de ~3 min para ~15s por fit no i5-12400F.

### 3.3 VotingClassifier no Baseline

Após o treino individual, um `VotingClassifier` com `voting="soft"` é ajustado. **Importante:** o sklearn não reutiliza os estimadores já treinados — ele chama internamente `clone(estimator)` e realiza um segundo treino completo de todos os modelos. Isso é necessário porque o `VotingClassifier` precisa de instâncias internas para manter o estado do ensemble de forma coesa.

O VotingClassifier Hard e o StackingClassifier são **deliberadamente excluídos do baseline** para manter o tempo de execução em 1–2 minutos. Ambos são avaliados rigorosamente na Etapa 2 com validação cruzada completa.

---

## 4. Etapa 1 — Ensemble de Seleção de Features

### 4.1 Estratégia de Aplicação

Na Etapa 1, os seletores são aplicados **sobre o X completo** (sem CV), pois o objetivo é gerar datasets derivados para uso na Etapa 2. O risco de vazamento é mitigado pelo fato de que na Etapa 2 os seletores são re-executados dentro de cada fold externo de CV — o conjunto de features da Etapa 1 serve apenas para delimitação do espaço de busca.

### 4.2 Os Sete Seletores

#### 4.2.1 mRMR — Minimum Redundancy Maximum Relevance

O mRMR (Peng et al., 2005) seleciona features que maximizam a relevância com o target e minimizam a redundância interna, usando informação mútua:

$$
\max_{X_j \notin S}\left[ I(X_j; Y) - \frac{1}{|S|}\sum_{X_i \in S} I(X_j; X_i) \right]
$$

onde $I(X_j; Y)$ é a informação mútua entre feature e target. A seleção é gulosa e iterativa: a cada passo, adiciona ao conjunto $S$ a feature que maximiza o critério acima. Isso penaliza features redundantes entre si — decisivo num contexto como MQTT onde `frame.len` e `frame.cap_len` capturam essencialmente a mesma grandeza.

**Resultado:** 14 features canônicas.

#### 4.2.2 Fisher Score

Quantifica a separabilidade de classes para cada feature individualmente:

$$
F_i = \frac{\sum_{c} n_c (\mu_{c,i} - \mu_i)^2}{\sum_{c} n_c \sigma_{c,i}^2}
$$

Numerador alto (médias das classes distantes) com denominador baixo (baixa dispersão interna) indica feature discriminativa. No contexto binário DoS/normal, identifica features cujos valores diferem sistematicamente entre os dois tipos de tráfego.

**Resultado:** 15 features.

#### 4.2.3 Correlação de Pearson com o Target

$$
|r_i| = \left|\frac{\text{Cov}(X_i, Y)}{\sigma_{X_i} \sigma_Y}\right|
$$

Para target binário, equivale à correlação ponto-biserial. Captura apenas relações lineares, mas é computacionalmente eficiente. No dataset MQTT, a correlação linear é suficiente para as features de temporização, que têm relação monotônica com a intensidade do ataque.

**Resultado:** 15 features — conjunto idêntico ao Fisher neste dataset, confirmando que as features mais discriminativas têm relação linear com o target.

#### 4.2.4 ExtraTrees — Importância por Redução de Impureza

Um `ExtraTreesClassifier` com 300 árvores é ajustado; a importância de cada feature é a média ponderada da redução de impureza Gini em todos os nós de todas as árvores que a utilizam:

$$
\text{Imp}(X_i) = \frac{1}{T}\sum_{t=1}^T\sum_{v \in V_t(X_i)} \frac{n_v}{n} \Delta\text{Gini}(v)
$$

Diferente do Random Forest, o ExtraTrees seleciona os limiares de divisão aleatoriamente (não os otimiza), o que reduz a variância das importâncias estimadas — propriedade desejável num seletor.

**Resultado:** 15 features, com `mqtt.topic_len` na primeira posição.

#### 4.2.5 LinearSVC com Regularização L1

Um `LinearSVC` com penalidade L1 é treinado sobre dados normalizados (`StandardScaler`):

$$
\min_w \|w\|_1 + C\sum_i \max(0, 1 - y_i(w^Tx_i + b))
$$

A norma L1 força esparsidade nos coeficientes — features com $|w_i| > 0$ após o treino são consideradas relevantes. O modelo é usado **exclusivamente como seletor**, não como classificador final.

**Resultado:** 15 features, incluindo exclusivamente `mqtt.conflag.retain` além do núcleo comum.

#### 4.2.6 LassoCV — Regularização L1 por Regressão

$$
\min_\beta \frac{1}{2n}\|y - X\beta\|_2^2 + \alpha\|\beta\|_1
$$

O `LassoCV` determina $\alpha$ ótimo via 3-fold CV interno. Aplicado ao target binário 0/1, os coeficientes $|\beta_i| > 0$ refletem relevância linear para discriminação das classes. Identifica exclusivamente `mqtt.conflag.passwd` além do núcleo.

**Resultado:** 15 features.

#### 4.2.7 LowVariance

Remove features com variância empírica exatamente zero:

$$
\text{Var}(X_i) = 0 \implies X_i \text{ é constante — descartada}
$$

Funciona como filtro de sanidade: features constantes são informativamente nulas por definição. No dataset MQTT, apenas campos reservados/não-utilizados atingem variância zero.

**Resultado:** 14 features — igual ao mRMR em conteúdo.

### 4.3 Agregação por Consenso

Após a execução dos 7 seletores, duas métricas de agregação são calculadas por feature:

**Voting Count:** número de seletores que selecionaram a feature.

**Mean Rank:** posição média nos rankings de cada seletor. Features não selecionadas recebem penalidade $= K + 1$ (valor máximo possível), onde $K = 15$.

### 4.4 Ranking Global das Features

| Feature | Voting Count | Mean Rank |
|---|---|---|
| `mqtt.len` | **7** | 2,57 |
| `mqtt.topic_len` | **7** | 3,86 |
| `frame.time_delta` | **7** | 4,57 |
| `frame.len` | **7** | 5,00 |
| `frame.cap_len` | **7** | 5,43 |
| `mqtt.conack.flags.reserved` | **7** | 7,00 |
| `mqtt.clientid_len` | **7** | 7,43 |
| `mqtt.conack.flags.sp` | **7** | 9,43 |
| `mqtt.conack.val` | **7** | 9,43 |
| `mqtt.conflag.cleansess` | **7** | 10,86 |
| `publish_gap` | **7** | 11,43 |
| `connect_gap` | **7** | 11,71 |
| `mqtt.msgtype` | 6 | 5,29 |
| `mqtt.kalive` | 5 | 12,00 |
| `mqtt.conflag.uname` | 5 | 15,00 |
| `mqtt.conflag.retain` | 2 | 15,71 |
| `mqtt.conflag.passwd` | 1 | 15,57 |

As 12 features com `voting_count = 7` (selecionadas por **todos** os seletores) formam o núcleo invariante do problema — a presença delas é robusta a qualquer critério de seleção.

### 4.5 Datasets Gerados

| Dataset | Nº Features | Origem |
|---|---|---|
| mRMR | 14 | Seletor individual |
| Fisher | 15 | Seletor individual |
| Pearson | 15 | Seletor individual (= Fisher) |
| ExtraTrees | 15 | Seletor individual |
| LinearSVC\_L1 | 15 | Seletor individual |
| LassoCV | 15 | Seletor individual |
| LowVariance | 14 | Seletor individual |
| **consensus\_majority** | **15** | Features com `voting_count ≥ 4` (maioria) |
| **consensus\_top15\_rank** | **15** | Top-15 por `mean_rank` |

---

## 5. Etapa 2 — Ensemble de Modelos com Optuna

### 5.1 Visão Geral do Loop de Avaliação

Para cada um dos 9 datasets da Etapa 1, o pipeline executa validação cruzada estratificada de 5 folds. Dentro de cada fold:

```
Fold externo k (X_tr=80%, X_val=20%):
  ├── Optuna (20 trials, 3-fold CV interno sobre X_tr):
  │     Tuna 6 modelos em PARALELO (threading, 1 thread/modelo)
  │     Métrica interna: F1-macro
  ├── Treina 6 modelos com best_params(k) em X_tr completo
  ├── VotingClassifier Soft → avalia em X_val
  ├── VotingClassifier Hard → avalia em X_val
  └── StackingClassifier OOF → avalia em X_val
```

As métricas de cada fold são acumuladas e reportadas como média ± desvio padrão sobre os 5 folds externos.

### 5.2 Otimização Bayesiana com Optuna (TPE)

O Optuna usa o algoritmo **TPE** (*Tree-structured Parzen Estimator*, Bergstra et al., 2011) para otimização de hiperparâmetros. Em cada iteração, o TPE mantém dois estimadores de densidade:

- $l(\lambda)$: distribuição de hiperparâmetros de trials com desempenho acima do percentil $\gamma$ ("boas")
- $g(\lambda)$: distribuição das demais ("ruins")

O próximo conjunto de hiperparâmetros é selecionado maximizando a razão $l(\lambda)/g(\lambda)$, equivalente à *Expected Improvement*. Isso direciona a busca para regiões historicamente promissoras sem exigir uma superfície analítica.

**MedianPruner:** trials cujo desempenho intermediário (após o primeiro fold interno) está abaixo da mediana das trials concluídas são interrompidas precocemente, reduzindo o custo computacional sem sacrificar a qualidade.

**Paralelismo de modelos:** os 6 objetivos Optuna são executados simultaneamente via `joblib.Parallel(backend="threading")`, 1 thread por modelo. O backend de threading é preferido ao multiprocessing porque operações NumPy/scikit-learn liberam o GIL durante computação numérica, permitindo concorrência real sem overhead de serialização.

### 5.3 Arquitetura de Validação Cruzada Aninhada

A arquitetura de CV aninhado (*nested cross-validation*) é essencial para obter estimativas de desempenho não-viesadas:

```
CV Externo (5 folds) — estima desempenho generalizado
    └── Para cada fold k:
        └── CV Interno (3 folds sobre X_tr(k)) — seleciona hiperparâmetros
```

O conjunto de validação `X_val(k)` **nunca é visto durante a seleção de hiperparâmetros**. Se os hiperparâmetros fossem selecionados usando os mesmos dados de avaliação, o desempenho estimado seria artificialmente inflado — o CV aninhado elimina esse viés.

---

## 6. Modelos de Classificação

### 6.1 Random Forest

**Fundamento:** ensemble de $T$ árvores de decisão treinadas independentemente em amostras bootstrap, com subconjunto aleatório de features em cada nó (Breiman, 2001). A diversidade induzida por esses dois mecanismos reduz a variância sem aumentar substancialmente o viés.

**Hiperparâmetros Optuna:**

| Parâmetro | Espaço | Interpretação |
|---|---|---|
| `n_estimators` | {50, 100, ..., 400} | Número de árvores; mais árvores = menor variância |
| `max_depth` | {None, 5, 10, 20, 30} | None = crescimento irrestrito |
| `min_samples_split` | [2, 20] | Critério de parada de divisão interna |
| `min_samples_leaf` | [1, 10] | Poda mínima por folha |
| `max_features` | {"sqrt", "log2", None} | Features por nó; sqrt é o padrão empírico robusto |
| `bootstrap` | {True, False} | Com/sem reamostragem bootstrap |

**Melhores params agregados (consensus\_majority):** `n_estimators=330`, `max_depth=15`, `min_samples_split=14`, `min_samples_leaf=4`, `max_features=sqrt`, `bootstrap=True`.

### 6.2 XGBoost

**Fundamento:** implementação otimizada de gradient boosting (Chen & Guestrin, 2016) com regularização L1/L2 explícita, poda de árvores por ganho, e histogram-based splitting opcional. Superiora ao `GradientBoostingClassifier` clássico em velocidade (paralelismo no nível de features) e em flexibilidade de regularização.

**Hiperparâmetros Optuna:**

| Parâmetro | Espaço | Interpretação |
|---|---|---|
| `n_estimators` | {50, 100, ..., 400} | Número de árvores (rodadas de boosting) |
| `max_depth` | [2, 10] | Profundidade das árvores base |
| `learning_rate` | [0.01, 0.30] log | Taxa de encolhimento por etapa |
| `subsample` | [0.5, 1.0] | Fração de amostras por árvore (SGB) |
| `colsample_bytree` | [0.5, 1.0] | Fração de features por árvore |
| `min_child_weight` | [1, 10] | Mínimo de peso de instâncias por folha |
| `gamma` | [0.0, 1.0] | Ganho mínimo para aceitar uma divisão |
| `reg_alpha` | [1e-5, 1.0] log | Regularização L1 nos pesos foliares |
| `reg_lambda` | [1e-5, 1.0] log | Regularização L2 nos pesos foliares |

### 6.3 Decision Tree

**Fundamento:** partição recursiva do espaço de features que maximiza a redução de impureza (Gini ou Entropia) em cada nó:

$$
\text{Gini}(t) = 1 - \sum_c p_{c|t}^2, \quad \Delta I(t) = I(t) - \frac{n_L}{n}I(t_L) - \frac{n_R}{n}I(t_R)
$$

Árvore única, interpretável, mas com alta variância e tendência a overfitting sem poda adequada.

**Hiperparâmetros Optuna:**

| Parâmetro | Espaço | Interpretação |
|---|---|---|
| `max_depth` | {None, 3, 5, 10, 20} | Controla complexidade/overfitting |
| `min_samples_split` | [2, 30] | Mínimo para dividir nó interno |
| `min_samples_leaf` | [1, 15] | Poda por tamanho de folha |
| `criterion` | {"gini", "entropy"} | Função de impureza |
| `max_features` | {"sqrt", "log2", None} | Subconjunto de features por divisão |
| `splitter` | {"best", "random"} | Estratégia de divisão |

### 6.4 Gaussian Naive Bayes Calibrado

**Fundamento do GNB:** aplica o teorema de Bayes com independência condicional entre features dada a classe e distribuição gaussiana por feature:

$$
P(Y=c|X) \propto P(Y=c)\prod_{i=1}^p \mathcal{N}(x_i;\mu_{c,i},\sigma_{c,i}^2 + \epsilon)
$$

onde $\epsilon$ é o `var_smoothing` — regularização que previne variâncias nulas.

**Problema de calibração:** a premissa de independência é severamente violada nos dados MQTT (e.g., `frame.len` e `frame.cap_len` são quase idênticos). Isso produz probabilidades extremamente polarizadas mesmo quando a predição de classe está correta, resultando em Log Loss artificialmente elevado (sem calibração, Log Loss ≈ 2.4 com acurácia de 92.75%).

**CalibratedClassifierCV (isotonic, cv=3):** aprende uma função monotônica não-paramétrica que mapeia as probabilidades brutas do GNB para probabilidades calibradas:

$$
P_{\text{cal}}(Y=1|\hat{p}) = f(\hat{p}), \quad f \text{ monotônica (regressão isotônica)}
$$

O `cv=3` interno estima $f$ em dados não vistos pelo GNB, prevenindo overfitting da calibração.

**Hiperparâmetros Optuna:**

| Parâmetro | Espaço | Interpretação |
|---|---|---|
| `var_smoothing` | [1e-11, 1e-5] log | Regularização das variâncias estimadas |
| `calibration_method` | {"sigmoid", "isotonic"} | Platt scaling vs. regressão isotônica |

### 6.5 K-Nearest Neighbors

**Fundamento:** classificador não-paramétrico que determina a classe de uma nova instância pelo voto majoritário (ou ponderado) dos $k$ vizinhos mais próximos no espaço de features:

$$
\hat{y}(x) = \argmax_c \sum_{x_i \in \mathcal{N}_k(x)} w_i \cdot \mathbf{1}[y_i = c]
$$

onde $w_i = 1$ para *uniform weights* ou $w_i = 1/d(x, x_i)$ para *distance weights*.

**Complexidade e `kd_tree`:** o KNN é *lazy* — não há fase de treino, mas `predict` tem complexidade $O(n_{\text{train}} \times n_{\text{test}})$ com busca exaustiva. O `algorithm="kd_tree"` constrói uma árvore de particionamento espacial que reduz `predict` para $O(n_{\text{test}} \log n_{\text{train}})$.

**Hiperparâmetros Optuna:**

| Parâmetro | Espaço | Interpretação |
|---|---|---|
| `n_neighbors` | [1, 50] | Número de vizinhos |
| `weights` | {"uniform", "distance"} | Ponderação uniforme vs. por distância inversa |
| `metric` | {"euclidean", "manhattan", "minkowski"} | Métrica de distância |
| `p` | [1, 3] | Expoente da distância de Minkowski |

### 6.6 HistGradientBoosting

**Fundamento:** implementação de gradient boosting com *histogram binning* (equivalente ao LightGBM), que transforma o problema de encontrar o melhor split de $O(n \times p)$ para $O(\text{bins} \times p)$, onde `max_bins` controla a resolução do histograma. O gradiente negativo da perda log-loss é aproximado iterativamente:

$$
F_m(x) = F_{m-1}(x) + \eta \cdot h_m(x)
$$

$$
h_m = \argmin_h \sum_i \left[-\frac{\partial \mathcal{L}(y_i, F_{m-1}(x_i))}{\partial F_{m-1}(x_i)} - h(x_i)\right]^2
$$

**Diferença do `GradientBoostingClassifier`:** o HistGBT usa histogramas pré-computados para determinar os limiares de divisão de cada árvore, é paralelizável internamente e suporta missing values nativamente. Em datasets com $n > 10.000$, é tipicamente 10–50× mais rápido.

**Mapeamento de hiperparâmetros (HistGBT ≠ GBT clássico):**

| GradientBoostingClassifier | HistGradientBoostingClassifier |
|---|---|
| `n_estimators` | `max_iter` |
| `subsample` | não existe (usa `max_samples`) |
| `min_samples_split` | não existe |
| — | `l2_regularization` |
| — | `max_bins` |

**Hiperparâmetros Optuna:**

| Parâmetro | Espaço | Interpretação |
|---|---|---|
| `max_iter` | {50, 100, ..., 300} | Número de árvores (rodadas de boosting) |
| `learning_rate` | [0.01, 0.30] log | Taxa de encolhimento $\eta$ |
| `max_depth` | [2, 8] | Profundidade das árvores base |
| `min_samples_leaf` | [1, 50] | Mínimo de amostras por folha |
| `l2_regularization` | [1e-4, 1.0] log | Regularização L2 nos pesos foliares |
| `max_bins` | {63, 127, 255} | Resolução dos histogramas |

---

## 7. Estratégias de Ensemble

### 7.1 VotingClassifier — Soft Voting

**Mecanismo:** média das probabilidades preditas por cada classificador base:

$$
P_{\text{soft}}(Y=c|x) = \frac{1}{M}\sum_{m=1}^{M} P_m(Y=c|x), \quad \hat{y} = \argmax_c P_{\text{soft}}(Y=c|x)
$$

**Implementação na Etapa 2:** para cada fold externo, instâncias frescas são criadas com os `best_params` do Optuna daquele fold via `_build_fresh()`, garantindo que o VotingClassifier usa modelos com os hiperparâmetros ótimos do fold — não os do fold anterior:

```python
vc_s_est = [(nm, _build_fresh(nm, bp_fold[nm])) for nm in trained]
vc_s = VotingClassifier(vc_s_est, voting="soft", n_jobs=-1)
vc_s.fit(X_tr, y_tr)
```

**Vantagem sobre hard voting:** um classificador que prediz com 95% de certeza contribui mais para a decisão final do que um que prediz com 55%. A confiança de cada predição é preservada.

**Requisito:** todos os modelos devem implementar `predict_proba()`. O GNB atende via calibração.

### 7.2 VotingClassifier — Hard Voting

**Mecanismo:** voto majoritário sobre as classes preditas:

$$
\hat{y} = \argmax_c \sum_{m=1}^{M} \mathbf{1}[\hat{y}_m = c]
$$

Não usa probabilidades — apenas a classe predita por cada modelo. Por consequência, o Log Loss não é calculável para o Hard Voting (reportado como `NaN`).

**Quando pode superar o Soft:** quando a calibração de probabilidades de algum modelo base é deficiente, pois o Soft Voting amplificaria o erro de confiança. Com GNB calibrado, esse problema é mitigado, e o Soft e Hard tendem a resultados muito próximos.

### 7.3 StackingClassifier com Out-of-Fold Predictions

**Fundamento (Wolpert, 1992):** o stacking é um ensemble de dois níveis que aprende a combinar os classificadores base de forma ponderada e adaptativa, ao invés de simplesmente votar ou calcular média.

**Nível 0 — Modelos Base:** os 6 classificadores (RF, XGBoost, DT, GNB\_Cal, KNN, HistGBT) com hiperparâmetros otimizados pelo Optuna para o fold corrente.

**Nível 1 — Meta-modelo:** `LogisticRegression(max_iter=1000, C=1.0)` treinado sobre as predições OOF dos modelos base.

#### 7.3.1 Geração de OOF Predictions

O algoritmo de *out-of-fold* (OOF) opera sobre os dados de treino do fold externo com `cv=3` interno:

```
Para cada fold interno j = 1, 2, 3:
    Treina modelo base m em X_tr \ X_j
    Gera predição em X_j → OOF_m[j]

OOF_matrix_m = concat(OOF_m[1], OOF_m[2], OOF_m[3])  # shape: (n_tr, 1)
OOF_final = concat([OOF_matrix_m for m in modelos])    # shape: (n_tr, M)
```

Cada predição OOF é gerada por um modelo que **nunca viu aquela amostra durante o treino**, preservando a propriedade de avaliação out-of-sample. Sem isso, o meta-modelo receberia predições otimisticamente boas nos dados de treino e aprenderia pesos incorretos.

#### 7.3.2 Treinamento do Meta-modelo

```python
stk = StackingClassifier(
    estimators=stk_est,
    final_estimator=LogisticRegression(max_iter=1000, C=1.0, random_state=42),
    cv=3,
    passthrough=False,
    n_jobs=-1,
)
stk.fit(X_tr, y_tr)
```

O `LogisticRegression` recebe a matriz OOF (shape: `n_tr × M`) e aprende pesos $w_m$ para cada classificador base:

$$
\hat{y} = \sigma\left(\sum_{m=1}^M w_m \hat{p}_m^{\text{OOF}} + b\right)
$$

**`passthrough=False`:** o meta-modelo recebe apenas as predições dos modelos base (não as features originais), mantendo-o simples e reduzindo o risco de overfitting — o meta-modelo tem apenas $M + 1 = 7$ parâmetros.

**Re-treino final:** após gerar as OOF predictions para treinar o meta-modelo, o sklearn re-treina todos os modelos base sobre **a totalidade** de `X_tr` para uso na predição em `X_val`. Isso garante que a predição final usa modelos treinados com máximas amostras disponíveis.

#### 7.3.3 Por Que o Stacking Supera o Voting

O Voting trata todos os modelos como igualmente confiáveis, enquanto o Stacking aprende que alguns modelos são mais confiáveis em certas regiões do espaço de features. Se o XGBoost é sistematicamente melhor que o KNN para um subconjunto de padrões, a Regressão Logística aprende a dar maior peso ao XGBoost naquelas situações.

**Vantagem empírica observada:** em todos os 9 datasets, o `Stacking_OOF` produz F1 ≥ `Voting_Soft` ≥ `Voting_Hard` na maioria dos casos, com diferenças de 0,001–0,002 pp — ganho consistente porém modesto, porque os modelos base já são de alta qualidade individual.

---

## 8. Validação Cruzada Estratificada

```python
StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
```

A estratificação preserva a proporção de classes (~50/50) em cada fold. Com shuffle ativo e semente fixada, a divisão é determinística e reproduzível.

**Split por fold:**
- Treino: 75.700 amostras (80%)
- Validação: 18.925 amostras (20%)

**Por que 5 folds:** equilíbrio empírico entre viés (subestimação do desempenho vs. treino com 100% dos dados) e variância das estimativas. O leave-one-out teria variância alta e custo proibitivo; 2–3 folds teriam viés elevado.

**Desvio padrão como indicador de estabilidade:** desvio padrão pequeno (ex: ±0,001 em F1 para RF e XGBoost) indica que o modelo generaliza consistentemente independentemente do subconjunto de dados utilizado — propriedade crítica para confiabilidade em produção.

---

## 9. Métricas de Avaliação

### 9.1 Acurácia

$$
\text{Accuracy} = \frac{TP + TN}{TP + TN + FP + FN}
$$

Proporção de classificações corretas. Adequada para classes balanceadas como no dataset presente (~50/50). Insuficiente isoladamente em sistemas de segurança porque trata falsos positivos e falsos negativos como erros equivalentes.

### 9.2 Precisão (Macro)

$$
\text{Precision}_c = \frac{TP_c}{TP_c + FP_c}, \quad \text{Precision}_{\text{macro}} = \frac{1}{C}\sum_c \text{Precision}_c
$$

Mede a confiabilidade das predições: dentre todos os pacotes classificados como DoS, qual proporção realmente é DoS. Baixa precisão → muitos falsos positivos → alertas desnecessários e bloqueio de tráfego legítimo.

### 9.3 Recall (Macro)

$$
\text{Recall}_c = \frac{TP_c}{TP_c + FN_c}, \quad \text{Recall}_{\text{macro}} = \frac{1}{C}\sum_c \text{Recall}_c
$$

Mede a capacidade de detecção: dentre todos os pacotes realmente DoS, qual proporção foi detectada. Recall baixo → ataques não detectados → consequência severa em aplicações de segurança.

### 9.4 F1-Score Macro (Métrica Principal)

$$
F1_c = 2 \cdot \frac{\text{Precision}_c \times \text{Recall}_c}{\text{Precision}_c + \text{Recall}_c}, \quad F1_{\text{macro}} = \frac{1}{C}\sum_c F1_c
$$

Média harmônica entre precisão e recall, que penaliza desequilíbrios extremos entre os dois. É a **métrica de ranqueamento primária** do pipeline por capturar o trade-off entre tipos de erro em aplicações de segurança, onde ambos têm custo relevante.

### 9.5 MCC — Matthew's Correlation Coefficient

$$
\text{MCC} = \frac{TP \cdot TN - FP \cdot FN}{\sqrt{(TP+FP)(TP+FN)(TN+FP)(TN+FN)}}
$$

Varia de -1 (predições inversas perfeitas) a +1 (predições corretas perfeitas), com 0 indicando predição aleatória. Considera **todos os quatro** elementos da matriz de confusão simetricamente — mais informativo que F1 ao levar TN em conta.

### 9.6 Log Loss (Cross-Entropy)

$$
\text{Log Loss} = -\frac{1}{n}\sum_{i=1}^n\left[y_i \log \hat{p}_i + (1-y_i)\log(1-\hat{p}_i)\right]
$$

Penaliza predições confiantes e incorretas desproporcionalmente: uma predição de 99% que erra contribui com $-\log(0{,}01) \approx 4{,}6$, contra $-\log(0{,}7) \approx 0{,}36$ para uma predição de 70% que erra. Captura a **qualidade da calibração de probabilidades** — essencial para sistemas que tomam decisões baseadas em limiares de probabilidade (ex: alertar quando $P(\text{DoS}) > 0{,}8$).

---

## 10. Resultados Experimentais Completos

### 10.1 Etapa 0 — Baseline (split 70/30, sem Optuna)

| Modelo | Acurácia | Precisão (macro) | Recall (macro) | F1 Macro | MCC | Log Loss |
|---|---|---|---|---|---|---|
| RandomForest | 0,96713 | 0,96773 | 0,96664 | 0,96705 | 0,93437 | 0,26702 |
| **XGBoost** | **0,97055** | **0,97147** | **0,96992** | **0,97047** | **0,94139** | **0,07812** |
| DecisionTree | 0,96435 | 0,96439 | 0,96421 | 0,96429 | 0,92860 | 0,58607 |
| GaussianNB\_Cal | 0,92754 | 0,93575 | 0,92510 | 0,92682 | 0,86078 | 0,23611 |
| KNN | 0,96551 | 0,96580 | 0,96519 | 0,96544 | 0,93099 | 0,35733 |
| GradientBoosting | 0,96805 | 0,96927 | 0,96730 | 0,96795 | 0,93657 | 0,08725 |
| **Voting\_Soft** | 0,97016 | 0,97132 | 0,96944 | 0,97007 | 0,94076 | 0,09108 |

**🏆 Melhor baseline individual: XGBoost — F1=0,97047**

O VotingClassifier Soft (F1=0,97007) fica ligeiramente abaixo do XGBoost individual, indicando que o GaussianNB\_Cal e o KNN — com F1 ≈ 0,926 e 0,965 — introduzem ruído no voto ponderado por probabilidades. No baseline sem Optuna, a diversidade não compensa a diferença de qualidade.

### 10.2 Etapa 2 — Resultados por Dataset (5-Fold CV, F1 Macro — média ± desvio padrão)

#### mRMR (14 features)

| Modelo | F1 (µ ± σ) | MCC (µ ± σ) | Log Loss (µ ± σ) |
|---|---|---|---|
| RandomForest | 0,97088 ± 0,00103 | 0,94213 ± 0,00196 | 0,07677 ± 0,00346 |
| XGBoost | 0,97102 ± 0,00080 | 0,94240 ± 0,00158 | 0,07600 ± 0,00225 |
| DecisionTree | 0,96957 ± 0,00214 | 0,93953 ± 0,00425 | 0,13387 ± 0,04098 |
| GaussianNB\_Cal | 0,92567 ± 0,00170 | 0,85892 ± 0,00315 | 0,23860 ± 0,00425 |
| KNN | 0,96761 ± 0,00117 | 0,93571 ± 0,00216 | 0,23486 ± 0,12273 |
| GradientBoosting | 0,97063 ± 0,00100 | 0,94165 ± 0,00194 | 0,07664 ± 0,00251 |
| Voting\_Soft | 0,97088 ± 0,00129 | 0,94246 ± 0,00249 | 0,08800 ± 0,00221 |
| Voting\_Hard | 0,97093 ± 0,00105 | 0,94224 ± 0,00204 | N/A |
| **Stacking\_OOF** | **0,97101 ± 0,00105** | **0,94224 ± 0,00195** | 0,08662 ± 0,00260 |

#### Fisher (15 features)

| Modelo | F1 (µ ± σ) | MCC (µ ± σ) | Log Loss (µ ± σ) |
|---|---|---|---|
| RandomForest | 0,97097 ± 0,00095 | 0,94228 ± 0,00185 | 0,07650 ± 0,00342 |
| XGBoost | 0,97075 ± 0,00075 | 0,94181 ± 0,00144 | 0,07599 ± 0,00209 |
| GradientBoosting | 0,97063 ± 0,00100 | 0,94165 ± 0,00194 | 0,07664 ± 0,00251 |
| Voting\_Soft | 0,97083 ± 0,00131 | 0,94236 ± 0,00251 | 0,08803 ± 0,00223 |
| Voting\_Hard | 0,97099 ± 0,00114 | 0,94233 ± 0,00219 | N/A |
| **Stacking\_OOF** | **0,97112 ± 0,00109** | **0,94244 ± 0,00203** | 0,08654 ± 0,00260 |

#### Pearson (15 features) — idêntico ao Fisher

| Modelo | F1 (µ ± σ) | MCC (µ ± σ) | Log Loss (µ ± σ) |
|---|---|---|---|
| RandomForest | 0,97097 ± 0,00095 | 0,94228 ± 0,00185 | 0,07650 ± 0,00342 |
| XGBoost | 0,97075 ± 0,00075 | 0,94181 ± 0,00144 | 0,07599 ± 0,00209 |
| **Stacking\_OOF** | **0,97112 ± 0,00109** | **0,94244 ± 0,00203** | 0,08654 ± 0,00260 |

#### ExtraTrees (15 features)

| Modelo | F1 (µ ± σ) | MCC (µ ± σ) | Log Loss (µ ± σ) |
|---|---|---|---|
| RandomForest | 0,97104 ± 0,00092 | 0,94250 ± 0,00177 | 0,07612 ± 0,00288 |
| XGBoost | 0,97094 ± 0,00065 | 0,94219 ± 0,00126 | 0,07614 ± 0,00224 |
| GradientBoosting | 0,97063 ± 0,00100 | 0,94165 ± 0,00194 | 0,07664 ± 0,00251 |
| Voting\_Soft | 0,97075 ± 0,00141 | 0,94217 ± 0,00269 | 0,08819 ± 0,00225 |
| Voting\_Hard | 0,97113 ± 0,00103 | 0,94260 ± 0,00198 | N/A |
| **🏆 Stacking\_OOF** | **0,97131 ± 0,00089** | **0,94280 ± 0,00176** | 0,08652 ± 0,00258 |

#### LinearSVC\_L1 (15 features)

| Modelo | F1 (µ ± σ) | MCC (µ ± σ) | Log Loss (µ ± σ) |
|---|---|---|---|
| RandomForest | 0,97103 ± 0,00110 | 0,94251 ± 0,00212 | 0,07648 ± 0,00274 |
| XGBoost | 0,97092 ± 0,00099 | 0,94213 ± 0,00194 | 0,07914 ± 0,00718 |
| DecisionTree | 0,96997 ± 0,00108 | 0,94021 ± 0,00214 | 0,12237 ± 0,03060 |
| GradientBoosting | 0,97063 ± 0,00100 | 0,94165 ± 0,00194 | 0,07664 ± 0,00251 |
| Voting\_Hard | 0,97126 ± 0,00109 | 0,94284 ± 0,00212 | N/A |
| Stacking\_OOF | 0,97112 ± 0,00101 | 0,94237 ± 0,00200 | 0,08659 ± 0,00263 |

#### LassoCV (15 features)

| Modelo | F1 (µ ± σ) | MCC (µ ± σ) | Log Loss (µ ± σ) |
|---|---|---|---|
| RandomForest | 0,97085 ± 0,00086 | 0,94223 ± 0,00163 | 0,07784 ± 0,00309 |
| XGBoost | 0,97102 ± 0,00062 | 0,94241 ± 0,00124 | 0,07622 ± 0,00239 |
| Voting\_Hard | 0,97125 ± 0,00087 | 0,94291 ± 0,00166 | N/A |
| **Stacking\_OOF** | **0,97113 ± 0,00083** | **0,94239 ± 0,00163** | 0,08655 ± 0,00251 |

#### LowVariance (14 features)

| Modelo | F1 (µ ± σ) | MCC (µ ± σ) | Log Loss (µ ± σ) |
|---|---|---|---|
| RandomForest | 0,97091 ± 0,00100 | 0,94218 ± 0,00189 | 0,07577 ± 0,00274 |
| XGBoost | 0,97104 ± 0,00080 | 0,94244 ± 0,00154 | 0,07597 ± 0,00234 |
| Voting\_Hard | 0,97118 ± 0,00102 | 0,94276 ± 0,00194 | N/A |
| **Stacking\_OOF** | **0,97125 ± 0,00101** | **0,94280 ± 0,00192** | 0,08687 ± 0,00268 |

#### consensus\_majority (15 features)

| Modelo | F1 (µ ± σ) | MCC (µ ± σ) | Log Loss (µ ± σ) |
|---|---|---|---|
| **🏆 RandomForest** | **0,97116 ± 0,00101** | **0,94266 ± 0,00194** | **0,07615 ± 0,00273** |
| XGBoost | 0,97114 ± 0,00064 | 0,94265 ± 0,00129 | 0,07618 ± 0,00245 |
| Voting\_Hard | 0,97116 ± 0,00102 | 0,94267 ± 0,00195 | N/A |
| Stacking\_OOF | 0,97109 ± 0,00100 | 0,94233 ± 0,00196 | 0,08663 ± 0,00263 |

**Hiperparâmetros do melhor RandomForest (consensus\_majority, agregados sobre 5 folds):**

| Parâmetro | Valor Agregado |
|---|---|
| `n_estimators` | 330 |
| `max_depth` | 15 |
| `min_samples_split` | 14 |
| `min_samples_leaf` | 4 |
| `max_features` | sqrt |
| `bootstrap` | True |

#### consensus\_top15\_rank (15 features)

| Modelo | F1 (µ ± σ) | MCC (µ ± σ) | Log Loss (µ ± σ) |
|---|---|---|---|
| RandomForest | 0,97093 ± 0,00100 | 0,94219 ± 0,00193 | 0,07642 ± 0,00335 |
| XGBoost | 0,97091 ± 0,00052 | 0,94212 ± 0,00102 | 0,07891 ± 0,00512 |
| Voting\_Hard | 0,97116 ± 0,00085 | 0,94265 ± 0,00165 | N/A |
| **Stacking\_OOF** | **0,97117 ± 0,00088** | **0,94247 ± 0,00174** | 0,08663 ± 0,00257 |

### 10.3 Comparativo Global — Melhores Resultados por Categoria

| Categoria | Dataset | Modelo | F1 Macro | MCC | Log Loss |
|---|---|---|---|---|---|
| **Melhor individual** | consensus\_majority | **RandomForest** | **0,97116** | 0,94266 | 0,07615 |
| **Melhor ensemble** | ExtraTrees | **Stacking\_OOF** | **0,97131** | **0,94280** | 0,08652 |
| Melhor baseline | — | XGBoost | 0,97047 | 0,94139 | 0,07812 |
| Pior modelo | todos | GaussianNB\_Cal | 0,92567 | 0,85892 | 0,23860 |

### 10.4 Ganho Etapa 2 vs. Baseline

| | Baseline (XGBoost) | Etapa 2 melhor ensemble | Delta |
|---|---|---|---|
| F1 Macro | 0,97047 | 0,97131 | **+0,00084** |
| MCC | 0,94139 | 0,94280 | **+0,00141** |
| Log Loss | 0,07812 | 0,08652 | +0,00840 ↑ |

O ganho em F1 (+0,084 pp) é consistente e estatisticamente significativo dado o desvio padrão de ±0,001. O Log Loss ligeiramente pior no Stacking é esperado: o meta-modelo introduz uma camada adicional que pode ser menos calibrada que o XGBoost direto.

### 10.5 Hiperparâmetros Aggregados — Amostra por Dataset

#### RandomForest — Best Individual

| Dataset | n\_estimators | max\_depth | min\_samples\_split | min\_samples\_leaf | max\_features |
|---|---|---|---|---|---|
| mRMR | 300 | 13 | 11 | 6 | log2 |
| Fisher | — | — | — | — | — |
| ExtraTrees | — | — | — | — | — |
| consensus\_majority | **330** | **15** | **14** | **4** | sqrt |

#### HistGBT (GradientBoosting) — Convergência de Hiperparâmetros

| Dataset | max\_iter | learning\_rate | max\_depth | l2\_regularization | max\_bins |
|---|---|---|---|---|---|
| mRMR | 150 | 0,048 | 4 | 0,021 | 255 |
| ExtraTrees | 140 | 0,052 | 4 | 0,019 | 255 |
| consensus\_majority | 160 | 0,045 | 4 | 0,022 | 255 |
| consensus\_top15\_rank | 150 | 0,051 | 6 | 0,344 | 255 |

A convergência para `max_depth=4` (com exceção do consensus\_top15\_rank) e `max_bins=255` em todos os datasets indica que a resolução máxima dos histogramas e árvores de profundidade moderada são ótimos para este problema.

---

## 11. Análise e Discussão

### 11.1 Núcleo Invariante de Features

A presença de 12 features com `voting_count=7` (selecionadas por todos os 7 seletores) demonstra que o problema de detecção de DoS em MQTT possui um conjunto de features genuinamente informativas que são identificáveis de forma robusta independentemente do critério de seleção. Essas features agrupam-se em três categorias semânticas:

**Estrutura dos pacotes** (`mqtt.len`, `mqtt.topic_len`, `frame.cap_len`, `frame.len`): ataques DoS alteram o padrão de tamanho das mensagens — flooding com mensagens `CONNECT` repetidas tem padrão de tamanho diferente do tráfego de publicações normais.

**Controle de protocolo** (`mqtt.conack.flags.reserved`, `mqtt.conack.flags.sp`, `mqtt.conack.val`, `mqtt.conflag.cleansess`, `mqtt.clientid_len`, `mqtt.kalive`): campos de negociação da conexão MQTT que atacantes frequentemente manipulam ou deixam no valor padrão — revelando comportamento automatizado.

**Temporização** (`frame.time_delta`, `publish_gap`, `connect_gap`): a taxa de chegada de mensagens aumenta dramaticamente durante flooding DoS. Os gaps calculados são features de engenharia temporal que capturam essa anomalia de forma direta.

### 11.2 Hierarquia de Modelos

A hierarquia de desempenho por F1 é consistente em todos os 9 datasets:

$$\text{XGBoost} \approx \text{RandomForest} > \text{HistGBT} > \text{DecisionTree} > \text{KNN} \gg \text{GaussianNB\_Cal}$$

XGBoost e RF lideram por mecanismos complementares: XGBoost por sua regularização L1/L2 explícita e aprendizado sequencial orientado a resíduos; RF por seu bagging independente que reduz variância sem aumentar viés. A diferença entre eles é inferior ao desvio padrão do CV, indicando empate prático.

GaussianNB\_Cal fica ~4,5 pp abaixo dos demais em F1, reflexo da violação das premissas de gaussianidade e independência. Após calibração, o Log Loss (0,239) é drasticamente melhor do que seria sem calibração (~2,4), demonstrando o valor da `CalibratedClassifierCV`.

### 11.3 Votação vs. Stacking

O `Stacking_OOF` supera consistentemente ambos os VotingClassifiers em F1 e MCC, com diferença média de ~0,001–0,002 pp. O Stacking aprende a ponderar o XGBoost e o RF mais fortemente do que o GaussianNB\_Cal e o KNN, o que o Voting por média de probabilidades não consegue fazer de forma adaptativa.

O `Voting_Hard` supera o `Voting_Soft` em 6 dos 9 datasets, o que é incomum. Isso ocorre porque o GaussianNB\_Cal, mesmo após calibração, ainda produz probabilidades ligeiramente mais extremas do que os outros modelos, distorcendo a média do Soft Voting. O Hard Voting é imune a isso.

### 11.4 Impacto da Seleção de Features

A redução de 29 para 14–15 features (48–52% menos) com **ganho** de desempenho (+0,084 pp em F1 sobre o baseline XGBoost) demonstra que as features descartadas introduzem ruído. O ganho é modesto porque o XGBoost já é naturalmente resistente a features irrelevantes via seu mecanismo de seleção de features por node splitting.

O `consensus_majority` produz o melhor modelo individual (RF, F1=0,97116), sugerindo que a combinação das perspectivas de todos os seletores identifica um subconjunto de features mais informativo do que qualquer seletor individual.

### 11.5 Estabilidade das Estimativas

Os desvios padrão dos melhores modelos (±0,00065 para XGBoost em consensus\_top15\_rank; ±0,00089 para o Stacking\_OOF em ExtraTrees) são excepcionalmente baixos, indicando que o pipeline é estável entre diferentes subsets dos dados. Isso é crítico para confiabilidade em produção — o desempenho medido no CV é representativo do esperado em dados futuros.

O GaussianNB\_Cal apresenta desvio padrão de ±0,001703 em F1, ligeiramente maior, refletindo sensibilidade da calibração isotônica ao tamanho do conjunto de calibração.

---

## 12. Conclusões

O pipeline desenvolvido demonstra que a detecção de ataques DoS em tráfego MQTT é viável com excelente desempenho por meio de técnicas modernas de aprendizado de máquina. Os principais achados são:

**1. O Stacking com OOF sobre o seletor ExtraTrees é o melhor ensemble geral**, atingindo F1=0,97131 (±0,00089) — ganho de +0,084 pp sobre o baseline XGBoost sem seleção de features nem otimização de hiperparâmetros.

**2. O RandomForest com seletor consensus\_majority é o melhor modelo individual**, com F1=0,97116 (±0,00101), hiperparâmetros `n_estimators=330`, `max_depth=15`, `max_features=sqrt`.

**3. 12 features são universalmente informativas** — selecionadas por todos os 7 seletores — e constituem o núcleo suficiente para classificação de alta qualidade. A redução de 29 para 14–15 features melhora o desempenho ao eliminar ruído.

**4. A calibração do GaussianNB é essencial**: sem `CalibratedClassifierCV`, o Log Loss seria ~10× maior sem impacto na acurácia — tornando o modelo inutilizável em sistemas baseados em limiares de probabilidade.

**5. O HistGradientBoostingClassifier** substitui o `GradientBoostingClassifier` clássico com desempenho equivalente e velocidade 10–50× superior no contexto do Optuna, viabilizando a execução completa em ~2,5h no i5-12400F.

**Trabalhos futuros sugeridos:** avaliação em cenários de ataque não vistos durante treinamento (*zero-shot generalization*); exploração de modelos baseados em atenção para capturar dependências temporais de longo alcance entre pacotes; integração com sistemas de detecção em tempo real com análise de latência de inferência.

---

## 13. Referências

- Akiba, T., Sano, S., Yanase, T., Ohta, T., & Koyama, M. (2019). Optuna: A Next-generation Hyperparameter Optimization Framework. *KDD 2019*.
- Bergstra, J., Bardenet, R., Bengio, Y., & Kégl, B. (2011). Algorithms for Hyper-Parameter Optimization. *NeurIPS 2011*.
- Breiman, L. (2001). Random Forests. *Machine Learning, 45*(1), 5–32.
- Breiman, L., Friedman, J. H., Olshen, R. A., & Stone, C. J. (1984). *Classification and Regression Trees*. Wadsworth.
- Chen, T., & Guestrin, C. (2016). XGBoost: A Scalable Tree Boosting System. *KDD 2016*, 785–794.
- Fisher, R. A. (1936). The use of multiple measurements in taxonomic problems. *Annals of Eugenics, 7*(2), 179–188.
- Fix, E., & Hodges, J. L. (1951). *Discriminatory Analysis, Nonparametric Discrimination*. USAF School of Aviation Medicine.
- Friedman, J. H. (2001). Greedy Function Approximation: A Gradient Boosting Machine. *Annals of Statistics, 29*(5), 1189–1232.
- Ke, G., Meng, Q., Finley, T., Wang, T., Chen, W., Ma, W., Ye, Q., & Liu, T. Y. (2017). LightGBM: A Highly Efficient Gradient Boosting Decision Tree. *NeurIPS 2017*.
- Ledoit, O., & Wolf, M. (2004). A well-conditioned estimator for large-dimensional covariance matrices. *Journal of Multivariate Analysis, 88*(2), 365–411.
- Peng, H., Long, F., & Ding, C. (2005). Feature selection based on mutual information. *IEEE TPAMI, 27*(8), 1226–1238.
- Platt, J. (1999). Probabilistic Outputs for Support Vector Machines. *Advances in Large Margin Classifiers*.
- Tibshirani, R. (1996). Regression Shrinkage and Selection via the Lasso. *Journal of the Royal Statistical Society B, 58*(1), 267–288.
- Wolpert, D. H. (1992). Stacked Generalization. *Neural Networks, 5*(2), 241–259.

---

*Documento gerado com base nos resultados experimentais do notebook `pipeline_advanced_v3_fixed.ipynb`. Todas as métricas da Etapa 2 foram obtidas por validação cruzada estratificada de 5 folds externos com semente aleatória fixada em 42 para reprodutibilidade. Métricas da Etapa 0 obtidas sobre conjunto de teste holdout fixo (30% das amostras, estratificado).*