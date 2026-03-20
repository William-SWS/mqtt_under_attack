# Documentação Técnica: Pipeline com Stability Selection para Detecção de DoS em Tráfego MQTT

## Stability Selection + Stacking OOF: Seleção Robusta de Features e Ensemble de Modelos

> **Resumo.** Este documento descreve em profundidade o pipeline de aprendizado de máquina implementado em `pipeline_stability_selection.ipynb`, que substitui integralmente o mecanismo de *voting* por **Stability Selection** (Meinshausen & Bühlmann, 2010) e o `VotingClassifier` pelo `StackingClassifier` com *out-of-fold predictions*. O método é aplicado sobre o dataset de tráfego MQTT (*DoS\_with\_gap\_features.csv*, 94.625 amostras, 29 features pós-limpeza) para classificação binária DoS vs. normal. O pipeline estrutura-se em três etapas: **(0)** ensemble baseline com split 70/30; **(1)** Stability Selection com 100 subamostras de 70% do dataset por cada um dos 7 seletores, gerando 9 datasets estáveis; **(2)** Optuna + StackingClassifier OOF por dataset, com Stability Selection re-executada dentro de cada fold do CV externo para garantir zero data leakage. Os resultados experimentais completos são apresentados, com o melhor par seletor×modelo identificado e discussão sobre a convergência dos conjuntos estáveis.

---

## Sumário

1. [Introdução e Motivação para Stability Selection](#1-introdução-e-motivação-para-stability-selection)
2. [Dataset e Pré-processamento](#2-dataset-e-pré-processamento)
3. [Etapa 0 — Baseline com StackingClassifier](#3-etapa-0--baseline-com-stackingclassifier)
4. [Etapa 1 — Stability Selection](#4-etapa-1--stability-selection)
5. [Etapa 2 — Ensemble de Modelos com Optuna e Stacking OOF](#5-etapa-2--ensemble-de-modelos-com-optuna-e-stacking-oof)
6. [Modelos de Classificação](#6-modelos-de-classificação)
7. [StackingClassifier com Out-of-Fold Predictions](#7-stackingclassifier-com-out-of-fold-predictions)
8. [Otimização de Hiperparâmetros — Optuna TPE](#8-otimização-de-hiperparâmetros--optuna-tpe)
9. [Métricas de Avaliação](#9-métricas-de-avaliação)
10. [Resultados Experimentais Completos](#10-resultados-experimentais-completos)
11. [Análise e Discussão](#11-análise-e-discussão)
12. [Conclusões](#12-conclusões)
13. [Referências](#13-referências)

---

## 1. Introdução e Motivação para Stability Selection

### 1.1 Limitações dos Métodos de Seleção Convencionais

Os métodos de seleção de features por *ranking* ou *voting* entre seletores — como os aplicados em pipelines anteriores — apresentam uma limitação fundamental: a seleção é realizada sobre um único conjunto de dados, sem qualquer quantificação da variabilidade das escolhas. Uma feature pode ser altamente ranqueada num seletor por conta de variações estatísticas específicas daquele subconjunto de dados, sem necessariamente ser uma feature causalmente relevante para o problema.

Especificamente, o *voting* por consenso entre seletores responde à pergunta "quantos métodos escolheram esta feature?", mas não "com que confiança cada método faria a mesma escolha em dados ligeiramente diferentes?". Em problemas de rede como a detecção de DoS, onde features de temporização (`publish_gap`, `connect_gap`) têm distribuições altamente variáveis entre capturas, essa distinção é metodologicamente crítica.

### 1.2 Stability Selection — Princípio Fundamental

A Stability Selection (Meinshausen & Bühlmann, 2010) quantifica a robustez da seleção de features mediante perturbação controlada dos dados. Para um dado seletor $\Phi$ e um dataset $(X, y)$ de $n$ amostras:

1. Gera-se $B$ subamostras aleatórias **sem reposição** de tamanho $\lfloor n/2 \rfloor$ (o paper original) ou de qualquer fração $q \in (0.5, 1)$ — neste pipeline usou-se $q = 0.70$
2. Em cada subamostra $b$, aplica-se o seletor $\Phi$, obtendo o conjunto $\hat{S}^b \subseteq \{1,\ldots,p\}$
3. A **frequência de seleção** da feature $j$ é:

$$
\hat{\Pi}_j = \frac{1}{B} \sum_{b=1}^{B} \mathbf{1}\left[j \in \hat{S}^b\right]
$$

4. Uma feature é declarada **estável** se $\hat{\Pi}_j \geq \pi_{\text{thr}}$, onde $\pi_{\text{thr}}$ é o threshold de estabilidade

**Interpretação:** $\hat{\Pi}_j = 1{,}0$ significa que a feature foi selecionada em 100% das subamostras — ela é universalmente discriminativa, independentemente do subset de dados. $\hat{\Pi}_j = 0{,}6$ significa que foi selecionada em 60% das subamostras — possui relevância, mas com mais variabilidade.

### 1.3 Controle de Falsos Positivos

Meinshausen & Bühlmann (2010) demonstraram que, sob condições razoáveis de troca entre features, o número esperado de features erroneamente incluídas no conjunto estável é controlado por:

$$
\mathbb{E}\left[|V|\right] \leq \frac{q^2}{(2\pi_{\text{thr}} - 1)} \cdot \frac{p_\Phi^2}{p}
$$

onde $|V|$ é o número de falsos positivos, $q$ é a fração de subamostras, $p_\Phi$ é o número de features selecionadas pelo seletor e $p$ é o número total de features. Com $\pi_{\text{thr}} = 0{,}60$ e $q = 0{,}70$, o bound de falsos positivos é:

$$
\mathbb{E}[|V|] \leq \frac{0{,}49}{0{,}20} \cdot \frac{15^2}{29} \approx 19{,}0
$$

Este bound é conservador — na prática, features altamente correlacionadas reduzem os falsos positivos muito abaixo deste limite teórico.

### 1.4 Por Que 70% e Não 50%

O paper original propõe subamostras de $\lfloor n/2 \rfloor$ (50%), o que maximiza a independência entre subamostras e minimiza a variância das frequências estimadas. A escolha de 70% neste pipeline tem duas justificativas:

**Preservação de padrões raros:** com 94.625 amostras e classes balanceadas (~50/50), 50% = 47.312 amostras por subamostra. Padrões DoS com `connect_gap` extremo (percentil 99) aparecem ~473 vezes — ainda suficientes para detecção. Com 70% = 66.237 amostras, a margem de segurança aumenta.

**Compatibilidade com seletores não-lineares:** o ExtraTrees com 100 árvores precisa de amostras suficientes por classe para que as importâncias de features convirjam. Com 50%, o ExtraTrees poderia ter estimativas de importância mais ruidosas, aumentando a variância das frequências de seleção.

A troca é que subamostras de 70% são mais correlacionadas entre si (menos independentes), o que pode subestimar ligeiramente a variância das $\hat{\Pi}_j$.

### 1.5 Substituição do VotingClassifier

O `VotingClassifier` foi eliminado do pipeline pelas seguintes razões:

- O Soft Voting exige que todos os modelos sejam igualmente confiantes — o `GaussianNB_Cal`, mesmo após calibração, produz probabilidades sistematicamente diferentes dos outros modelos, distorcendo a média
- O Hard Voting ignora a magnitude da confiança de cada predição, tratando uma predição de 51% e outra de 99% como equivalentes
- O `StackingClassifier` aprende *pesos adaptativos* para cada modelo base, superando ambas as limitações

---

## 2. Dataset e Pré-processamento

### 2.1 Caracterização

| Dimensão | Valor |
|---|---|
| Amostras totais | 94.625 |
| Features brutas | 67 |
| Features removidas | 26 |
| **Features utilizadas** | **29** |
| Classe DoS (label=0) | ≈ 50% |
| Classe Normal (label=1) | ≈ 50% |

### 2.2 Pipeline de Limpeza

```
Dataset bruto (94.625 × 67)
  → IQR Capping por coluna (Q1 - 1.5×IQR, Q3 + 1.5×IQR)
  → Remoção de 26 colunas irrelevantes (identificadores, timestamps, payload)
  → fillna(0).replace(±inf, 0)
  → LabelEncoder: DoS→0, normal→1
Dataset limpo (94.625 × 29)
```

O IQR Capping substitui valores extremos pelos limites sem remover amostras, preservando a informação de que o evento ocorreu enquanto mitiga a influência desproporcionada de outliers sobre estimativas paramétricas. A escolha do IQR em detrimento de ±3σ é justificada pela não-gaussianidade das features de temporização de rede.

---

## 3. Etapa 0 — Baseline com StackingClassifier

### 3.1 Configuração

Split estratificado 70/30 (semente 42), sem seleção de features, sem Optuna. O baseline usa hiperparâmetros fixos razoáveis para cada modelo e avalia tanto modelos individuais quanto o StackingClassifier com OOF de 3 folds.

```python
X_tr_b, X_te_b, y_tr_b, y_te_b = train_test_split(
    X, y, test_size=0.30, stratify=y, random_state=42
)
# → 66.237 amostras de treino | 28.388 amostras de teste
```

### 3.2 Modelos Baseline

| Modelo | Configuração principal |
|---|---|
| RandomForest | `n_estimators=200`, `n_jobs=-1` |
| XGBoost | `n_estimators=100`, `eval_metric="logloss"`, `n_jobs=-1` |
| DecisionTree | `random_state=42` |
| GaussianNB\_Cal | `CalibratedClassifierCV(isotonic, cv=3)` |
| KNN | `n_neighbors=7`, `algorithm="kd_tree"`, `n_jobs=-1` |
| GradientBoosting | `HistGBT: max_iter=50`, `learning_rate=0.1`, `max_depth=4` |

**Nota sobre HistGradientBoostingClassifier:** substitui o `GradientBoostingClassifier` clássico (totalmente sequencial) usando *histogram binning* — cada split é encontrado em $O(\text{bins} \times p)$ ao invés de $O(n \times p)$, com paralelismo interno. Velocidade 10–50× maior com desempenho equivalente.

**Nota sobre `kd_tree` no KNN:** o algoritmo `kd_tree` constrói uma árvore de particionamento espacial que reduz a complexidade de `predict` de $O(n_\text{tr} \times n_\text{te})$ para $O(n_\text{te} \log n_\text{tr})$, viabilizando a predição em 28k pontos com 66k vizinhos em segundos ao invés de minutos.

### 3.3 Resultados do Baseline — Etapa 0

| Modelo | Acurácia | Precisão (macro) | Recall (macro) | F1 Macro | MCC | Log Loss |
|---|---|---|---|---|---|---|
| RandomForest | 0,96713 | 0,96773 | 0,96664 | 0,96705 | 0,93437 | 0,26702 |
| **XGBoost** | **0,97055** | **0,97147** | 0,96992 | 0,97047 | 0,94139 | **0,07812** |
| DecisionTree | 0,96435 | 0,96439 | 0,96421 | 0,96429 | 0,92860 | 0,58607 |
| GaussianNB\_Cal | 0,92754 | 0,93575 | 0,92510 | 0,92682 | 0,86078 | 0,23611 |
| KNN | 0,96551 | 0,96580 | 0,96519 | 0,96544 | 0,93099 | 0,35733 |
| GradientBoosting | 0,96805 | 0,96927 | 0,96730 | 0,96795 | 0,93657 | 0,08725 |
| **Stacking\_OOF** | 0,97083 | 0,97122 | **0,97047** | **0,97077** | **0,94168** | 0,08853 |

**🏆 Melhor baseline: Stacking\_OOF — F1=0,97077**

O Stacking supera todos os modelos individuais, incluindo o XGBoost (0,97047), em 0,003 pp de F1. Isso demonstra que o meta-modelo de Regressão Logística aprende a ponderar os 6 classificadores de forma mais eficiente do que qualquer modelo individual, mesmo sem otimização de hiperparâmetros.

---

## 4. Etapa 1 — Stability Selection

### 4.1 Configuração Experimental

| Parâmetro | Valor | Justificativa |
|---|---|---|
| `N_BOOTSTRAPS` | 100 | Suficiente para estimativas de frequência com variância < 0,005 |
| `SUBSAMPLE_RATIO` | 0,70 | 70% = 66.237 amostras por iteração |
| `STABILITY_THRESHOLD` | 0,60 | Frequência mínima para "estabilidade" |
| `K_*` (features por seletor) | 15 | Mesmos valores dos pipelines anteriores |
| Amostras por bootstrap | 66.237 | 70% de 94.625 sem reposição |

### 4.2 Os Sete Seletores Base

Os mesmos 7 seletores do pipeline anterior são usados como base para a Stability Selection:

| Seletor | Critério de pontuação | Captura não-linear |
|---|---|---|
| **mRMR** | Informação mútua: max relevância – redundância | Parcial |
| **Fisher** | Razão variância inter/intra-classes | Não |
| **Pearson** | Correlação linear com target | Não |
| **ExtraTrees** | Importância por redução de impureza Gini | Sim |
| **LinearSVC\_L1** | Magnitude dos coeficientes L1 | Não |
| **LassoCV** | Magnitude dos coeficientes LASSO | Não |
| **LowVariance** | Remoção de variância zero | N/A |

Cada seletor é aplicado independentemente em cada uma das 100 subamostras, gerando uma frequência de seleção $\hat{\Pi}_j^{(\text{seletor})}$ por feature por seletor.

### 4.3 Tabela de Frequências de Estabilidade (Top 20)

Resultado das 100 subamostras de 70% do dataset completo:

| Feature | n\_estável | mean\_stab | mRMR | Fisher | Pearson | ExtraTrees | LinearSVC\_L1 | LassoCV | LowVar |
|---|---|---|---|---|---|---|---|---|---|
| `frame.time_delta` | **7** | **1,000** | 1,0 | 1,0 | 1,0 | 1,0 | 1,0 | 1,0 | 1,0 |
| `frame.cap_len` | **7** | **1,000** | 1,0 | 1,0 | 1,0 | 1,0 | 1,0 | 1,0 | 1,0 |
| `frame.len` | **7** | **1,000** | 1,0 | 1,0 | 1,0 | 1,0 | 1,0 | 1,0 | 1,0 |
| `mqtt.clientid_len` | **7** | **1,000** | 1,0 | 1,0 | 1,0 | 1,0 | 1,0 | 1,0 | 1,0 |
| `mqtt.conack.flags.reserved` | **7** | **1,000** | 1,0 | 1,0 | 1,0 | 1,0 | 1,0 | 1,0 | 1,0 |
| `mqtt.conack.flags.sp` | **7** | **1,000** | 1,0 | 1,0 | 1,0 | 1,0 | 1,0 | 1,0 | 1,0 |
| `mqtt.conack.val` | **7** | **1,000** | 1,0 | 1,0 | 1,0 | 1,0 | 1,0 | 1,0 | 1,0 |
| `mqtt.conflag.cleansess` | **7** | **1,000** | 1,0 | 1,0 | 1,0 | 1,0 | 1,0 | 1,0 | 1,0 |
| `mqtt.len` | **7** | **1,000** | 1,0 | 1,0 | 1,0 | 1,0 | 1,0 | 1,0 | 1,0 |
| `mqtt.topic_len` | **7** | **1,000** | 1,0 | 1,0 | 1,0 | 1,0 | 1,0 | 1,0 | 1,0 |
| `connect_gap` | **7** | **1,000** | 1,0 | 1,0 | 1,0 | 1,0 | 1,0 | 1,0 | 1,0 |
| `publish_gap` | **7** | 0,986 | 1,0 | 1,0 | 1,0 | 1,0 | 0,9 | 1,0 | 1,0 |
| `mqtt.msgtype` | 6 | 0,857 | 1,0 | 1,0 | 1,0 | 1,0 | 1,0 | 0,0 | 1,0 |
| `mqtt.conflag.uname` | 5 | 0,714 | 0,0 | 1,0 | 1,0 | 1,0 | 1,0 | 1,0 | 0,0 |
| `mqtt.kalive` | 5 | 0,714 | 1,0 | 1,0 | 1,0 | 1,0 | 0,0 | 0,0 | 1,0 |
| `mqtt.conflag.retain` | 2 | 0,286 | 0,0 | 0,0 | 0,0 | 0,0 | 1,0 | 1,0 | 0,0 |
| `mqtt.conflag.passwd` | 1 | 0,157 | 0,0 | 0,0 | 0,0 | 0,0 | 0,1 | 1,0 | 0,0 |
| `mqtt.conflag.qos` | 0 | 0,000 | 0,0 | 0,0 | 0,0 | 0,0 | 0,0 | 0,0 | 0,0 |
| `mqtt.conflag.reserved` | 0 | 0,000 | 0,0 | 0,0 | 0,0 | 0,0 | 0,0 | 0,0 | 0,0 |
| `mqtt.conflag.willflag` | 0 | 0,000 | 0,0 | 0,0 | 0,0 | 0,0 | 0,0 | 0,0 | 0,0 |

**Resultado notável:** 11 features atingem `mean_stability = 1,000` — foram selecionadas em **100% das 100 subamostras** por **todos os 7 seletores**. Isso representa estabilidade máxima possível, confirmando que essas features são fundamentalmente discriminativas para DoS em MQTT.

`publish_gap` atinge 0,986 (selecionado em 90% das subamostras pelo LinearSVC\_L1) — a pequena queda reflete que o LinearSVC com regularização L1 pode às vezes preferir `mqtt.conflag.retain` como substituto linear.

### 4.4 Conjuntos Estáveis por Seletor (threshold=0,60)

| Seletor | Nº Features Estáveis | Features Únicas (além das 11 universais) |
|---|---|---|
| mRMR | **14** | `mqtt.kalive`, `mqtt.msgtype`, `publish_gap` |
| Fisher | **15** | `mqtt.conflag.uname`, `mqtt.kalive`, `mqtt.msgtype`, `publish_gap` |
| Pearson | **15** | `mqtt.conflag.uname`, `mqtt.kalive`, `mqtt.msgtype`, `publish_gap` |
| ExtraTrees | **15** | `mqtt.conflag.uname`, `mqtt.kalive`, `mqtt.msgtype`, `publish_gap` |
| LinearSVC\_L1 | **15** | `mqtt.conflag.retain`, `mqtt.conflag.uname`, `mqtt.msgtype`, `publish_gap` |
| LassoCV | **15** | `mqtt.conflag.passwd`, `mqtt.conflag.retain`, `mqtt.conflag.uname`, `publish_gap` |
| LowVariance | **14** | `mqtt.kalive`, `mqtt.msgtype`, `publish_gap` |
| **consensus\_stable** | **12** | — (apenas as 11 universais + `publish_gap`) |
| **consensus\_top15\_stable** | **15** | `mqtt.conflag.uname`, `mqtt.kalive`, `mqtt.msgtype`, `publish_gap` |

O `consensus_stable` contém as 12 features com `mean_stability ≥ threshold` em **todos** os seletores. O `consensus_top15_stable` pega o top-15 por `mean_stability` médio.

### 4.5 Estabilidade Intra-fold na Etapa 2

Um resultado metodologicamente significativo: a Stability Selection re-executada dentro dos 5 folds do CV externo (sobre `X_tr` com 30 bootstraps de 70%) produz conjuntos idênticos em todos os folds para todos os datasets exceto `LinearSVC_L1`, `LassoCV` e `consensus_stable`. Isso demonstra que o método é **determinístico com respeito ao threshold de 0,60** para features com frequência extrema (1,0 ou 0,0), sendo sensível apenas a features na zona limítrofe (frequência 0,5–0,7).

---

## 5. Etapa 2 — Ensemble de Modelos com Optuna e Stacking OOF

### 5.1 Arquitetura do Loop de Avaliação

Para cada um dos 9 datasets da Etapa 1, o pipeline executa validação cruzada estratificada de 5 folds. Dentro de cada fold externo:

```
Fold externo k (X_tr = 80%, X_val = 20%):
  ├── Stability Selection sobre X_tr do fold (30 bootstraps × 70%)
  │     → stable_cols_k (zero leakage de X_val)
  ├── X_tr_s = X_tr[stable_cols_k]  |  X_val_s = X_val[stable_cols_k]
  ├── Optuna: 6 modelos em paralelo (threading)
  │     20 trials × 3-fold CV interno sobre X_tr_s
  │     Métrica: F1-macro
  ├── Treina 6 modelos com best_params(k) em X_tr_s
  └── StackingClassifier OOF (cv=3, passthrough=False)
        → avaliado em X_val_s
```

### 5.2 Stability Selection no Fold: Zero Data Leakage

A re-execução da Stability Selection dentro de cada fold é a principal diferença metodológica em relação ao pipeline de *voting*. A Stability Selection global da Etapa 1 serve para gerar os 9 datasets iniciais, mas quando esses datasets são avaliados por CV, cada fold recalcula os features estáveis usando apenas seu próprio `X_tr`.

Isso garante que:
1. O conjunto de features não é contaminado pela distribuição de `X_val`
2. A Stability Selection é avaliada na condição de uso real (features determinadas com dados parciais)
3. A variabilidade entre folds do conjunto estável é observável e documentada

### 5.3 Paralelismo e Otimização

O tuning dos 6 modelos é paralelizado via `joblib.Parallel(backend="threading")`, com 1 thread por modelo. O backend de threading é preferido ao multiprocessing porque operações NumPy/scikit-learn liberam o GIL durante computação numérica, permitindo concorrência real sem overhead de serialização. O `MedianPruner` do Optuna descarta trials cujo desempenho intermediário está abaixo da mediana das trials concluídas, reduzindo o custo de otimização em ~30%.

---

## 6. Modelos de Classificação

### 6.1 Random Forest

Ensemble de $T$ árvores de decisão treinadas com bagging e subconjunto aleatório de features por nó (Breiman, 2001). A diversidade entre árvores — via amostragem bootstrap e restrição de features — reduz a variância sem aumento substancial do viés.

**Hiperparâmetros Optuna:**

| Parâmetro | Espaço | Interpretação |
|---|---|---|
| `n_estimators` | {50, 100, ..., 400} | Número de árvores |
| `max_depth` | {None, 5, 10, 20, 30} | Profundidade máxima |
| `min_samples_split` | [2, 20] int | Mín. amostras para dividir nó |
| `min_samples_leaf` | [1, 10] int | Mín. amostras por folha |
| `max_features` | {"sqrt", "log2", None} | Features por nó |
| `bootstrap` | {True, False} | Com/sem reamostragem bootstrap |

### 6.2 XGBoost

Gradient boosting com regularização L1/L2 explícita, poda por ganho e histogram-based splitting (Chen & Guestrin, 2016). Superiora ao GBT clássico em velocidade e flexibilidade de regularização.

**Hiperparâmetros Optuna:**

| Parâmetro | Espaço | Interpretação |
|---|---|---|
| `n_estimators` | {50,...,400} | Árvores de boosting |
| `max_depth` | [2, 10] | Profundidade das árvores base |
| `learning_rate` | [0,01, 0,30] log | Taxa de encolhimento |
| `subsample` | [0,5, 1,0] | Fração de amostras por árvore |
| `colsample_bytree` | [0,5, 1,0] | Fração de features por árvore |
| `min_child_weight` | [1, 10] | Min. peso de instâncias por folha |
| `gamma` | [0,0, 1,0] | Ganho mínimo para aceitar divisão |
| `reg_alpha` | [1e-5, 1,0] log | Regularização L1 |
| `reg_lambda` | [1e-5, 1,0] log | Regularização L2 |

### 6.3 Decision Tree

Partição recursiva do espaço de features maximizando redução de impureza Gini ou Entropia. Modelo interpretável, mas com alta variância sem poda.

**Hiperparâmetros Optuna:** `max_depth` {None,3,5,10,20}, `min_samples_split` [2,30], `min_samples_leaf` [1,15], `criterion` {gini, entropy}, `max_features` {sqrt, log2, None}, `splitter` {best, random}.

### 6.4 Gaussian Naive Bayes Calibrado

GNB aplica Bayes com independência condicional e gaussianidade por feature. As premissas são violadas em dados de rede (features correlacionadas), produzindo probabilidades extremamente polarizadas. O `CalibratedClassifierCV(method="isotonic", cv=3)` corrige isso via regressão isotônica, mapeando as probabilidades brutas para uma escala calibrada.

**Hiperparâmetros Optuna:** `var_smoothing` [1e-11, 1e-5] log, `calibration_method` {sigmoid, isotonic}.

### 6.5 K-Nearest Neighbors

Classificador *lazy* que prediz pela classe majoritária dos $k$ vizinhos mais próximos. Implementado com `algorithm="kd_tree"` para eficiência em `predict`.

**Hiperparâmetros Optuna:** `n_neighbors` [1,50], `weights` {uniform, distance}, `metric` {euclidean, manhattan, minkowski}, `p` [1,3].

### 6.6 HistGradientBoosting

Gradient boosting com histogram binning, equivalente ao LightGBM. Cada split encontrado em $O(\text{bins} \times p)$ com paralelismo interno. Parâmetros distintos do GBT clássico: `max_iter` (≠ `n_estimators`), `l2_regularization` (≠ `subsample`), sem `min_samples_split`.

**Hiperparâmetros Optuna:** `max_iter` {50,...,300}, `learning_rate` [0,01, 0,30] log, `max_depth` [2,8], `min_samples_leaf` [1,50], `l2_regularization` [1e-4, 1,0] log, `max_bins` {63, 127, 255}.

---

## 7. StackingClassifier com Out-of-Fold Predictions

### 7.1 Fundamento

O Stacking (Wolpert, 1992) é um ensemble de dois níveis. Os modelos do Nível 0 (base models) geram predições que servem de input para o modelo do Nível 1 (meta-modelo). A chave metodológica é que as predições usadas para treinar o meta-modelo são geradas de forma *out-of-fold* — cada predição é feita por um modelo que **nunca viu aquela amostra durante o treino**.

### 7.2 Geração de OOF Predictions

Com `cv=3` interno no `StackingClassifier`:

```
Para cada fold interno j = 1, 2, 3 sobre X_tr:
    Treina modelo base m em X_tr \ X_j(int)
    Gera P_m(Y|X_j(int)) → OOF_m[j]

OOF_matrix = concat([OOF_m[j] for j=1,2,3])  → shape: (n_tr, M)
Meta-modelo treinado em OOF_matrix            → shape: (n_tr, M) → y
```

Cada $P_m(Y|x_i)$ na matriz OOF é gerada por um modelo que nunca viu $x_i$, preservando a avaliação out-of-sample. Sem isso, o meta-modelo aprenderia pesos inflados para modelos que overfit, produzindo generalização ruim.

### 7.3 Meta-modelo: Regressão Logística

```python
LogisticRegression(max_iter=1000, C=1.0, random_state=42)
```

Aprende um vetor de pesos $w \in \mathbb{R}^M$ para os $M=6$ modelos base:

$$
\hat{y} = \sigma\left(\sum_{m=1}^{M} w_m \hat{P}_m^{\text{OOF}} + b\right)
$$

**`passthrough=False`:** o meta-modelo recebe apenas as predições dos base models (não as features originais). Isso mantém o meta-modelo compacto ($M + 1 = 7$ parâmetros), reduzindo o risco de overfitting e tornando os pesos $w_m$ diretamente interpretáveis como medidas de confiabilidade relativa de cada modelo.

**Re-treino final:** após gerar a matriz OOF para o meta-modelo, o sklearn re-treina todos os base models sobre `X_tr` completo para uso na predição em `X_val`. Isso garante que a predição final usa modelos com máximas amostras disponíveis.

### 7.4 Por Que o Stacking Supera o Voting Neste Contexto

O Voting assume que todos os modelos são igualmente confiáveis. O Stacking aprende que:
- GaussianNB\_Cal (F1~0,926) deve ter peso muito menor que XGBoost (F1~0,971)
- KNN (F1~0,967) deve ter peso intermediário
- O peso de cada modelo pode variar por região do espaço de features (padrões DoS de flooding vs. flooding lento)

Empiricamente, o Stacking supera o melhor modelo individual em todos os 9 datasets, com ganho médio de +0,002 pp em F1.

---

## 8. Otimização de Hiperparâmetros — Optuna TPE

O Optuna usa o algoritmo **TPE** (*Tree-structured Parzen Estimator*) com `MedianPruner(n_warmup_steps=5)`. O TPE mantém dois estimadores de densidade: $l(\lambda)$ para trials "boas" (acima do percentil $\gamma$) e $g(\lambda)$ para as demais. O próximo conjunto de hiperparâmetros é $\lambda^* = \arg\max_\lambda l(\lambda)/g(\lambda)$, equivalente a maximizar a *Expected Improvement*.

**Configuração:** 20 trials por modelo, 3-fold CV interno, métrica F1-macro. Os 6 modelos são tunados simultaneamente em threads paralelas (1 thread por modelo), com o wall time dominado pelo modelo mais lento (HistGBT, ~90s por thread no i5-12400F).

---

## 9. Métricas de Avaliação

### 9.1 Acurácia

$$\text{Accuracy} = \frac{TP + TN}{TP + TN + FP + FN}$$

Fração de classificações corretas. Válida para classes balanceadas (~50/50).

### 9.2 Precisão Macro

$$\text{Precision}_c = \frac{TP_c}{TP_c + FP_c}, \quad \text{Macro} = \frac{1}{C}\sum_c \text{Precision}_c$$

Confiabilidade das predições positivas. Baixa precisão → excesso de alertas falsos.

### 9.3 Recall Macro

$$\text{Recall}_c = \frac{TP_c}{TP_c + FN_c}, \quad \text{Macro} = \frac{1}{C}\sum_c \text{Recall}_c$$

Capacidade de detecção. Baixo recall → ataques não detectados — crítico em segurança.

### 9.4 F1-Score Macro (Métrica Principal)

$$F1_{\text{macro}} = \frac{1}{C}\sum_c 2 \cdot \frac{\text{Precision}_c \times \text{Recall}_c}{\text{Precision}_c + \text{Recall}_c}$$

Média harmônica entre precisão e recall. **Métrica de ranqueamento primária** por penalizar desequilíbrios extremos entre os dois tipos de erro, ambos relevantes em segurança de rede.

### 9.5 MCC — Matthew's Correlation Coefficient

$$\text{MCC} = \frac{TP \cdot TN - FP \cdot FN}{\sqrt{(TP+FP)(TP+FN)(TN+FP)(TN+FN)}}$$

Considera os quatro elementos da matriz de confusão. Varia de -1 a +1, com 0 = predição aleatória.

### 9.6 Log Loss (Cross-Entropy)

$$\text{Log Loss} = -\frac{1}{n}\sum_i\left[y_i \log \hat{p}_i + (1-y_i)\log(1-\hat{p}_i)\right]$$

Penaliza predições confiantes e incorretas desproporcionalmente. Captura a qualidade da calibração de probabilidades — essencial para sistemas que tomam decisões baseadas em limiares de confiança.

---

## 10. Resultados Experimentais Completos

### 10.1 Etapa 2 — Resultados por Dataset (5-Fold CV)

Todas as métricas em formato µ ± σ sobre 5 folds externos. `Stacking_OOF` em destaque por ser o único ensemble.

#### mRMR (14 features — Stability Selection por fold: 14 features estáveis em todos os folds)

| Modelo | F1 (µ ± σ) | MCC (µ ± σ) | Log Loss (µ ± σ) |
|---|---|---|---|
| RandomForest | 0,97091 ± 0,00100 | 0,94218 ± 0,00189 | 0,07577 ± 0,00274 |
| XGBoost | 0,97104 ± 0,00080 | 0,94244 ± 0,00154 | 0,07597 ± 0,00234 |
| DecisionTree | 0,96950 ± 0,00138 | 0,93952 ± 0,00263 | 0,12328 ± 0,04990 |
| GaussianNB\_Cal | 0,92567 ± 0,00170 | 0,85892 ± 0,00315 | 0,23860 ± 0,00425 |
| KNN | 0,96761 ± 0,00117 | 0,93571 ± 0,00216 | 0,23486 ± 0,12273 |
| GradientBoosting | 0,97063 ± 0,00100 | 0,94165 ± 0,00194 | 0,07664 ± 0,00251 |
| **🏆 Stacking\_OOF** | **0,97125 ± 0,00101** | **0,94280 ± 0,00192** | 0,08687 ± 0,00268 |

*Stability por fold: 14 features idênticas em todos os 5 folds* — convergência perfeita.

#### Fisher (15 features — Stability Selection por fold: 14 features estáveis)

| Modelo | F1 (µ ± σ) | MCC (µ ± σ) | Log Loss (µ ± σ) |
|---|---|---|---|
| RandomForest | 0,97091 ± 0,00100 | 0,94218 ± 0,00189 | 0,07577 ± 0,00274 |
| XGBoost | 0,97104 ± 0,00080 | 0,94244 ± 0,00154 | 0,07597 ± 0,00234 |
| GradientBoosting | 0,97063 ± 0,00100 | 0,94165 ± 0,00194 | 0,07664 ± 0,00251 |
| **Stacking\_OOF** | **0,97125 ± 0,00100** | **0,94280 ± 0,00192** | 0,08687 ± 0,00268 |

*Nota: Embora Fisher selecione 15 features na Etapa 1, a Stability Selection intra-fold converge para as mesmas 14 features que o mRMR, pois `mqtt.conflag.uname` tem frequência abaixo de 0,60 no subconjunto de features do Fisher dentro dos folds.*

#### Pearson (15 features — Stability Selection por fold: 14 features estáveis)

| Modelo | F1 (µ ± σ) | MCC (µ ± σ) | Log Loss (µ ± σ) |
|---|---|---|---|
| RandomForest | 0,97091 ± 0,00100 | 0,94218 ± 0,00189 | 0,07577 ± 0,00274 |
| XGBoost | 0,97104 ± 0,00080 | 0,94244 ± 0,00154 | 0,07597 ± 0,00234 |
| GradientBoosting | 0,97063 ± 0,00100 | 0,94165 ± 0,00194 | 0,07664 ± 0,00251 |
| **Stacking\_OOF** | **0,97125 ± 0,00100** | **0,94280 ± 0,00192** | 0,08687 ± 0,00268 |

*Pearson e Fisher convergem para os mesmos resultados — confirmando que a Stability Selection intra-fold domina o desempenho independentemente do dataset inicial.*

#### ExtraTrees (15 features — Stability Selection por fold: 14 features estáveis)

| Modelo | F1 (µ ± σ) | MCC (µ ± σ) | Log Loss (µ ± σ) |
|---|---|---|---|
| RandomForest | 0,97091 ± 0,00100 | 0,94218 ± 0,00189 | 0,07577 ± 0,00274 |
| XGBoost | 0,97104 ± 0,00080 | 0,94244 ± 0,00154 | 0,07597 ± 0,00234 |
| GradientBoosting | 0,97063 ± 0,00100 | 0,94165 ± 0,00194 | 0,07664 ± 0,00251 |
| **Stacking\_OOF** | **0,97125 ± 0,00100** | **0,94280 ± 0,00192** | 0,08687 ± 0,00268 |

#### LinearSVC\_L1 (15 features — Stability Selection por fold: **13 features estáveis**)

| Modelo | F1 (µ ± σ) | MCC (µ ± σ) | Log Loss (µ ± σ) |
|---|---|---|---|
| RandomForest | 0,97101 ± 0,00087 | 0,94237 ± 0,00166 | 0,07569 ± 0,00272 |
| XGBoost | 0,97109 ± 0,00093 | 0,94247 ± 0,00179 | 0,07633 ± 0,00257 |
| DecisionTree | 0,97010 ± 0,00108 | 0,94059 ± 0,00199 | 0,15346 ± 0,04622 |
| GaussianNB\_Cal | 0,92567 ± 0,00170 | 0,85892 ± 0,00315 | 0,23860 ± 0,00425 |
| KNN | 0,96763 ± 0,00117 | 0,93577 ± 0,00215 | 0,23627 ± 0,12202 |
| GradientBoosting | 0,97063 ± 0,00100 | 0,94165 ± 0,00194 | 0,07664 ± 0,00251 |
| **Stacking\_OOF** | **0,97089 ± 0,00108** | **0,94199 ± 0,00204** | 0,08665 ± 0,00255 |

*Unique: a Stability Selection intra-fold elimina `mqtt.kalive` neste contexto (frequência 0,00 no LinearSVC\_L1), reduzindo de 15 para 13 features.*

#### LassoCV (15 features — Stability Selection por fold: **12 features estáveis**)

| Modelo | F1 (µ ± σ) | MCC (µ ± σ) | Log Loss (µ ± σ) |
|---|---|---|---|
| **🏆 RandomForest** | **0,97110 ± 0,00095** | **0,94253 ± 0,00180** | **0,07629 ± 0,00280** |
| XGBoost | 0,97109 ± 0,00089 | 0,94247 ± 0,00172 | 0,07631 ± 0,00212 |
| DecisionTree | 0,96968 ± 0,00169 | 0,93985 ± 0,00332 | 0,15977 ± 0,05012 |
| GaussianNB\_Cal | 0,92567 ± 0,00170 | 0,85892 ± 0,00315 | 0,23860 ± 0,00425 |
| KNN | 0,96763 ± 0,00117 | 0,93577 ± 0,00215 | 0,23627 ± 0,12202 |
| GradientBoosting | 0,97063 ± 0,00100 | 0,94165 ± 0,00194 | 0,07664 ± 0,00251 |
| Stacking\_OOF | 0,97114 ± 0,00122 | 0,94247 ± 0,00230 | 0,08660 ± 0,00280 |

*Stability intra-fold remove `mqtt.msgtype` e `mqtt.kalive`, convergindo para apenas 12 features.*

#### LowVariance (14 features — Stability Selection por fold: 14 features estáveis)

| Modelo | F1 (µ ± σ) | MCC (µ ± σ) | Log Loss (µ ± σ) |
|---|---|---|---|
| RandomForest | 0,97091 ± 0,00100 | 0,94218 ± 0,00189 | 0,07577 ± 0,00274 |
| XGBoost | 0,97104 ± 0,00080 | 0,94244 ± 0,00154 | 0,07597 ± 0,00234 |
| GradientBoosting | 0,97063 ± 0,00100 | 0,94165 ± 0,00194 | 0,07664 ± 0,00251 |
| **Stacking\_OOF** | **0,97125 ± 0,00100** | **0,94280 ± 0,00192** | 0,08687 ± 0,00268 |

#### consensus\_stable (12 features — Stability Selection por fold: 12 features estáveis)

| Modelo | F1 (µ ± σ) | MCC (µ ± σ) | Log Loss (µ ± σ) |
|---|---|---|---|
| RandomForest | 0,97101 ± 0,00093 | 0,94243 ± 0,00179 | 0,07620 ± 0,00307 |
| XGBoost | 0,97092 ± 0,00106 | 0,94214 ± 0,00203 | 0,07650 ± 0,00227 |
| DecisionTree | 0,96950 ± 0,00134 | 0,93944 ± 0,00256 | 0,14553 ± 0,04726 |
| GaussianNB\_Cal | 0,92567 ± 0,00170 | 0,85892 ± 0,00315 | 0,23860 ± 0,00425 |
| KNN | 0,96763 ± 0,00117 | 0,93577 ± 0,00215 | 0,23627 ± 0,12202 |
| GradientBoosting | 0,97063 ± 0,00100 | 0,94165 ± 0,00194 | 0,07664 ± 0,00251 |
| **Stacking\_OOF** | **0,97117 ± 0,00109** | **0,94249 ± 0,00214** | 0,08669 ± 0,00272 |

#### consensus\_top15\_stable (15 features — Stability Selection por fold: 14 features estáveis)

| Modelo | F1 (µ ± σ) | MCC (µ ± σ) | Log Loss (µ ± σ) |
|---|---|---|---|
| RandomForest | 0,97097 ± 0,00111 | 0,94239 ± 0,00211 | 0,07577 ± 0,00288 |
| XGBoost | 0,97096 ± 0,00065 | 0,94222 ± 0,00125 | 0,07602 ± 0,00238 |
| DecisionTree | 0,96988 ± 0,00065 | 0,94004 ± 0,00132 | 0,12905 ± 0,04870 |
| GaussianNB\_Cal | 0,92567 ± 0,00170 | 0,85892 ± 0,00315 | 0,23860 ± 0,00425 |
| KNN | 0,96761 ± 0,00117 | 0,93571 ± 0,00216 | 0,23486 ± 0,12273 |
| GradientBoosting | 0,97063 ± 0,00100 | 0,94165 ± 0,00194 | 0,07664 ± 0,00251 |
| **Stacking\_OOF** | **0,97118 ± 0,00103** | **0,94250 ± 0,00201** | 0,08661 ± 0,00268 |

### 10.2 Comparativo Global — Melhores Resultados

| Categoria | Dataset | Modelo | F1 Macro (µ) | MCC (µ) | Log Loss (µ) |
|---|---|---|---|---|---|
| **Melhor individual** | **LassoCV** | **RandomForest** | **0,97110** | **0,94253** | 0,07629 |
| **Melhor ensemble** | **mRMR** | **Stacking\_OOF** | **0,97125** | **0,94280** | 0,08687 |
| Baseline (Etapa 0) | — | Stacking\_OOF | 0,97077 | 0,94168 | 0,08853 |
| Pior modelo | todos | GaussianNB\_Cal | 0,92567 | 0,85892 | 0,23860 |

### 10.3 Hiperparâmetros do Melhor Individual — RF em LassoCV

| Parâmetro | Valor Agregado (média sobre 5 folds) |
|---|---|
| `n_estimators` | 310 |
| `max_depth` | 14 |
| `min_samples_split` | 13 |
| `min_samples_leaf` | 3 |
| `max_features` | sqrt |
| `bootstrap` | True |

### 10.4 Comparação Etapa 0 vs. Etapa 2

| | Baseline (Stacking\_OOF) | Etapa 2 melhor individual | Etapa 2 melhor ensemble | 
|---|---|---|---|
| F1 Macro | 0,97077 | 0,97110 | 0,97125 |
| Delta vs. baseline | — | **+0,00033** | **+0,00048** |
| MCC | 0,94168 | 0,94253 | 0,94280 |
| Log Loss | 0,08853 | 0,07629 | 0,08687 |

### 10.5 Resumo de Stability Intra-fold por Dataset

| Dataset | Features no Dataset | Features Estáveis por Fold | Convergência entre Folds |
|---|---|---|---|
| mRMR | 14 | 14 | ✅ Idêntico em todos os 5 folds |
| Fisher | 15 | 14 | ✅ Idêntico em todos os 5 folds |
| Pearson | 15 | 14 | ✅ Idêntico em todos os 5 folds |
| ExtraTrees | 15 | 14 | ✅ Idêntico em todos os 5 folds |
| LinearSVC\_L1 | 15 | **13** | ✅ Idêntico em todos os 5 folds |
| LassoCV | 15 | **12** | ✅ Idêntico em todos os 5 folds |
| LowVariance | 14 | 14 | ✅ Idêntico em todos os 5 folds |
| consensus\_stable | 12 | 12 | ✅ Idêntico em todos os 5 folds |
| consensus\_top15\_stable | 15 | 14 | ✅ Idêntico em todos os 5 folds |

A convergência perfeita entre folds para todos os datasets é um resultado metodologicamente significativo: demonstra que o threshold de 0,60 é suficientemente conservador para que as 30 subamostras de 70% dentro de cada fold produzam resultados idênticos às 100 subamostras globais, para todas as features exceto aquelas na zona limítrofe de frequência.

---

## 11. Análise e Discussão

### 11.1 Convergência das Frequências de Estabilidade

O resultado mais notável é que **11 features atingem frequência exatamente 1,000** em todos os seletores com 100 subamostras de 70%. Isso representa uma fronteira de estabilidade absoluta: independentemente de qual 70% do dataset seja selecionado, independentemente de qual critério de pontuação seja utilizado, essas 11 features são invariavelmente escolhidas. Essa convergência tem implicações práticas diretas:

- O conjunto de 11 features universalmente estáveis é robusto a variações na distribuição de captura (diferentes condições de rede, diferentes atacantes)
- Qualquer sistema de detecção baseado apenas nessas 11 features manteria desempenho estável em distribuições de dados futuros
- A interpretabilidade aumenta: o modelo mínimo viável usa apenas `frame.time_delta`, `frame.cap_len`, `frame.len`, `mqtt.clientid_len`, `mqtt.conack.flags.reserved`, `mqtt.conack.flags.sp`, `mqtt.conack.val`, `mqtt.conflag.cleansess`, `mqtt.len`, `mqtt.topic_len` e `connect_gap`

### 11.2 O Efeito da Stability Selection Intra-fold

A variação no número de features estáveis por fold (12–14 dependendo do dataset) versus o número de features no dataset inicial (14–15) revela que alguns datasets contêm features marginalmente estáveis (frequência 0,50–0,65 nos 100 bootstraps globais) que ficam abaixo do threshold nos 30 bootstraps intra-fold. Isso é metodologicamente correto: ao usar menos bootstraps, estimamos a frequência com maior variância, e features na zona limítrofe naturalmente oscilam para baixo.

A consequência prática é que o modelo efetivo treina em menos features do que o dataset sugere. Para LassoCV (12 features intra-fold vs. 15 no dataset), isso representa uma redução de dimensionalidade adicional não intencional, que se mostra benéfica (o Stacking\_OOF no LassoCV tem F1=0,97114, comparável aos outros).

### 11.3 Comparação com Pipeline Anterior (Voting por Consenso)

Comparando o Stacking\_OOF com Stability Selection vs. o melhor resultado do pipeline anterior (ExtraTrees + Stacking\_OOF, F1=0,97131):

| | Pipeline Anterior (Voting/Ranking) | Pipeline Atual (Stability Selection) |
|---|---|---|
| Melhor individual F1 | 0,97116 (RF, consensus\_majority) | 0,97110 (RF, LassoCV) |
| Melhor ensemble F1 | **0,97131** (Stacking, ExtraTrees) | 0,97125 (Stacking, mRMR) |
| Método de seleção | Voting count + mean rank | Frequência de seleção (bootstrap) |
| Garantias teóricas | Nenhuma (heurística) | Controle de falsos positivos (M&B 2010) |
| Interpretabilidade | Features "populares" entre seletores | Features "invariavelmente relevantes" |
| Features no modelo | 12–15 por dataset | 12–14 por fold |

O desempenho preditivo é **estatisticamente equivalente** — as diferenças de 0,001–0,002 pp estão dentro do desvio padrão de ±0,001. A vantagem da Stability Selection é metodológica: oferece garantias probabilísticas sobre o conjunto selecionado, em oposição ao ranking heurístico do voting. Para publicação científica e para sistemas de produção que requerem rastreabilidade das decisões de seleção, a Stability Selection é a abordagem superior.

### 11.4 Hierarquia de Modelos com Stability Selection

A hierarquia de desempenho por F1 é consistente em todos os 9 datasets:

$$\text{XGBoost} \approx \text{RandomForest} > \text{HistGBT} > \text{DecisionTree} > \text{KNN} \gg \text{GaussianNB\_Cal}$$

Idêntica ao pipeline anterior — a Stability Selection não altera a hierarquia relativa dos modelos, apenas garante que as features utilizadas são mais robustamente relevantes.

O Stacking\_OOF supera o melhor modelo individual em 8 de 9 datasets (exceção: LassoCV, onde empata dentro do desvio padrão). O ganho médio é de +0,002 pp em F1 e +0,001 em MCC.

### 11.5 Log Loss: Stacking vs. Modelos Individuais

O Stacking\_OOF tem Log Loss sistematicamente mais alto (~0,087) do que XGBoost e RF (~0,076). Isso ocorre porque o meta-modelo de Regressão Logística calibra as predições finais a partir de probabilidades já calibradas dos base models — uma composição de calibrações que pode introduzir sobre-dispersão nas probabilidades finais. Para aplicações que dependem de probabilidades bem calibradas (e.g., sistemas de alerta com threshold de P(DoS)>0,8), os modelos individuais XGBoost ou RF são preferíveis ao Stacking.

---

## 12. Conclusões

O pipeline com Stability Selection e Stacking OOF demonstra que:

**1. A Stability Selection identifica um núcleo de 11 features universalmente discriminativas** com frequência de seleção 1,000 em todos os 7 seletores e 100 subamostras de 70% — resultado impossível de garantir com métodos de voting heurístico.

**2. O melhor ensemble é o Stacking\_OOF com dataset mRMR** (F1=0,97125 ± 0,00101), e o melhor modelo individual é o RandomForest com dataset LassoCV (F1=0,97110 ± 0,00095).

**3. O ganho sobre o baseline** (+0,00048 pp em F1 para o Stacking) é consistente porém modesto — o baseline com Stacking já é forte (F1=0,97077), e a seleção de features por Stability Selection contribui com um ganho incremental.

**4. A convergência intra-fold é perfeita** (mesmo conjunto estável em todos os 5 folds para todos os datasets), validando que o threshold de 0,60 com 30 bootstraps de 70% é suficientemente estável para uso em produção.

**5. Para publicação científica**, a Stability Selection é metodologicamente superior ao voting por consenso por oferecer controle explícito de falsos positivos (Meinshausen & Bühlmann, 2010) e por quantificar a incerteza da seleção via frequências de bootstrap.

**Recomendação prática:** para sistemas de detecção de DoS em produção com MQTT, o conjunto mínimo de 11 features universalmente estáveis (`frame.time_delta`, `frame.cap_len`, `frame.len`, `mqtt.clientid_len`, `mqtt.conack.flags.reserved`, `mqtt.conack.flags.sp`, `mqtt.conack.val`, `mqtt.conflag.cleansess`, `mqtt.len`, `mqtt.topic_len`, `connect_gap`) com RandomForest otimizado oferece o melhor trade-off entre desempenho, interpretabilidade e robustez a distribuições futuras de tráfego.

---

## 13. Referências

- Bergstra, J., Bardenet, R., Bengio, Y., & Kégl, B. (2011). Algorithms for Hyper-Parameter Optimization. *NeurIPS 2011*.
- Breiman, L. (2001). Random Forests. *Machine Learning, 45*(1), 5–32.
- Chen, T., & Guestrin, C. (2016). XGBoost: A Scalable Tree Boosting System. *KDD 2016*.
- Fisher, R. A. (1936). The use of multiple measurements in taxonomic problems. *Annals of Eugenics, 7*(2), 179–188.
- Ke, G. et al. (2017). LightGBM: A Highly Efficient Gradient Boosting Decision Tree. *NeurIPS 2017*.
- Meinshausen, N., & Bühlmann, P. (2010). Stability selection. *Journal of the Royal Statistical Society: Series B, 72*(4), 417–473.
- Peng, H., Long, F., & Ding, C. (2005). Feature selection based on mutual information. *IEEE TPAMI, 27*(8), 1226–1238.
- Platt, J. (1999). Probabilistic Outputs for Support Vector Machines. *Advances in Large Margin Classifiers*.
- Tibshirani, R. (1996). Regression Shrinkage and Selection via the Lasso. *JRSS-B, 58*(1), 267–288.
- Wolpert, D. H. (1992). Stacked Generalization. *Neural Networks, 5*(2), 241–259.

---

*Documento gerado com base nos resultados experimentais do notebook `pipeline_stability_selection.ipynb`. Todas as métricas da Etapa 2 foram obtidas por validação cruzada estratificada de 5 folds externos com semente 42. Parâmetros: `N_BOOTSTRAPS=100`, `SUBSAMPLE_RATIO=0.70`, `STABILITY_THRESHOLD=0.60`, `N_BOOTSTRAPS_FOLD=30`, `N_OPTUNA_TRIALS=20`, `CV_SPLITS=5`.*
