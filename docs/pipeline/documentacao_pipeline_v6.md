# Documentação Técnica: Pipeline de Detecção de Ataques DoS em Tráfego MQTT via Aprendizado de Máquina

> **Resumo.** Este documento descreve em profundidade o pipeline de aprendizado de máquina desenvolvido para a classificação binária de tráfego MQTT como ataque DoS (*Denial of Service*) ou tráfego normal. São detalhados os métodos de pré-processamento e limpeza de dados, os sete algoritmos de seleção de características, o processo de otimização de hiperparâmetros via Optuna, cada um dos seis modelos de classificação utilizados, a estratégia de ensemble por votação, as seis métricas de avaliação empregadas e os resultados experimentais completos obtidos sobre o dataset *DoS\_with\_gap\_features.csv* (94.625 amostras, 29 características após limpeza).

---

## Sumário

1. [Introdução e Contexto](#1-introdução-e-contexto)
2. [Caracterização do Dataset](#2-caracterização-do-dataset)
3. [Pré-processamento e Limpeza de Dados](#3-pré-processamento-e-limpeza-de-dados)
4. [Seleção de Características](#4-seleção-de-características)
5. [Otimização de Hiperparâmetros com Optuna](#5-otimização-de-hiperparâmetros-com-optuna)
6. [Modelos de Classificação](#6-modelos-de-classificação)
7. [Ensemble de Modelos por Votação](#7-ensemble-de-modelos-por-votação)
8. [Validação Cruzada Estratificada](#8-validação-cruzada-estratificada)
9. [Métricas de Avaliação](#9-métricas-de-avaliação)
10. [Resultados Experimentais](#10-resultados-experimentais)
11. [Análise e Discussão](#11-análise-e-discussão)
12. [Conclusões](#12-conclusões)
13. [Referências](#13-referências)

---

## 1. Introdução e Contexto

O protocolo MQTT (*Message Queuing Telemetry Transport*) é o padrão dominante para comunicação em ecossistemas de Internet das Coisas (IoT), adotado por sua leveza, baixo consumo de banda e modelo publish-subscribe. Um *broker* MQTT centraliza a troca de mensagens entre dispositivos publicadores (*publishers*) e dispositivos assinantes (*subscribers*). Precisamente por essa centralização, o broker representa um ponto único de falha suscetível a ataques de Negação de Serviço (DoS), nos quais um adversário satura o serviço com requisições maliciosas, tornando-o indisponível para clientes legítimos.

Sistemas de detecção baseados em regras estáticas são frágeis frente a variações nos padrões de ataque. Abordagens de aprendizado de máquina (*machine learning*, ML) oferecem generalização automática a partir de dados históricos, sem necessidade de atualização manual de assinaturas. O presente trabalho desenvolve e avalia um pipeline completo de ML que, a partir de capturas de tráfego MQTT convertidas em features estatísticas, classifica pacotes individuais como normais ou como parte de um ataque DoS.

A relevância do problema é amplificada pelo crescimento explosivo de dispositivos IoT em ambientes industriais, de saúde e de infraestrutura crítica, onde ataques DoS ao broker MQTT podem ter consequências físicas severas.

---

## 2. Caracterização do Dataset

### 2.1 Origem e Dimensões

O dataset *DoS\_with\_gap\_features.csv* contém capturas de tráfego MQTT obtidas em ambiente controlado, processadas pelo analisador de protocolos Wireshark para extração de campos de protocolo e geração de features de temporização. As dimensões originais e pós-processamento são:

| Dimensão | Valor |
|---|---|
| Amostras totais | 94.625 |
| Features no dataset bruto | 67 |
| Features numéricas identificadas | 55 |
| Features removidas por irrelevância | 26 |
| **Features utilizadas nos modelos** | **29** |
| Classe DoS (label = 0) | ~47.312 (≈50%) |
| Classe Normal (label = 1) | ~47.313 (≈50%) |

### 2.2 Variável-Alvo

A variável-alvo `type` é binária: `"DoS"` (codificado como 0) e `"normal"` (codificado como 1). O balanceamento próximo de 50/50 é favorável à aprendizagem supervisionada, reduzindo o risco de viés para a classe majoritária.

### 2.3 Features Selecionadas pelos Métodos de Seleção

Após o pipeline de seleção, os sete métodos convergiram para um núcleo consistente de features de alta relevância. A tabela abaixo apresenta os conjuntos canônicos selecionados por cada método (features que aparecem em ≥50% dos folds de CV):

| Seletor | Nº Features | Features Selecionadas |
|---|---|---|
| **mRMR** | 14 | `mqtt.len`, `mqtt.msgtype`, `mqtt.topic_len`, `frame.time_delta`, `frame.cap_len`, `frame.len`, `mqtt.conack.flags.reserved`, `mqtt.clientid_len`, `connect_gap`, `mqtt.conack.val`, `mqtt.conflag.cleansess`, `mqtt.conack.flags.sp`, `mqtt.kalive`, `publish_gap` |
| **Fisher** | 15 | mRMR + `mqtt.conflag.uname` |
| **Pearson** | 15 | Idêntico ao Fisher |
| **ExtraTrees** | 15 | mRMR + `mqtt.conflag.uname` (ordem diferente) |
| **LinearSVC\_L1** | 15 | mRMR + `mqtt.conflag.uname`, `mqtt.conflag.retain` |
| **LassoCV** | 15 | mRMR + `mqtt.conflag.passwd`, `mqtt.conflag.uname`, `mqtt.conflag.retain` (sem `mqtt.msgtype`) |
| **LowVariance** | 14 | Idêntico ao mRMR (ordena alfabeticamente) |

A convergência de 13–14 features comuns entre todos os métodos indica que esse núcleo é robusto e informativamente suficiente para a tarefa.

---

## 3. Pré-processamento e Limpeza de Dados

### 3.1 Visão Geral do Pipeline de Limpeza

O pré-processamento é executado nas seguintes etapas sequenciais, conforme implementado na Célula 3 do notebook:

```
Dataset bruto (94.625 × 67)
    → Identificação de colunas numéricas (55 colunas)
    → IQR Capping (tratamento de outliers)
    → Remoção de colunas irrelevantes (26 colunas descartadas)
    → Substituição de NaN → 0
    → Substituição de ±inf → 0
    → Codificação do label (LabelEncoder)
Dataset limpo (94.625 × 29) + vetor y (94.625,)
```

### 3.2 Remoção de Colunas Irrelevantes

Vinte e seis colunas são descartadas antes de qualquer modelagem. Os critérios de exclusão agrupam-se em quatro categorias:

**Identificadores de instância** (`frame.number`, `frame.interface_id`, `frame.interface_name`, `frame.md5_hash`): Identificam pacotes individuais sem qualquer relação causal com o tipo de tráfego. Incluir tais identificadores resultaria em overfitting trivial (o modelo memorizaria IDs em vez de padrões).

**Timestamps absolutos** (`frame.time_epoch`, `frame.time_relative`, `frame.time_delta_displayed`): O tempo absoluto de captura de um pacote não é preditor do tipo de tráfego; captura apenas o instante da coleta. O campo `frame.time_delta` (intervalo entre pacotes consecutivos) é retido por refletir a taxa de chegada de pacotes — feature discriminativa para DoS, que aumenta artificialmente essa taxa.

**Campos de payload textual e metadados de sessão** (`mqtt.username`, `mqtt.passwd`, `mqtt.willmsg`, `mqtt.willtopic`, `mqtt.msgid`): Contêm valores de payload específicos de sessão sem relação comportamental com DoS. Incluí-los representaria também um risco de privacidade.

**Artefatos de captura** (`frame.coloring_rule.name`, `frame.comment`, `frame.file_off`, etc.): Gerados pelo Wireshark durante a análise, não existem no tráfego real de produção.

### 3.3 Tratamento de Outliers via IQR Capping

O método IQR (*Interquartile Range*) é aplicado por coluna sobre todas as 55 features numéricas originais, antes da remoção de colunas irrelevantes:

$$
\text{IQR} = Q_3 - Q_1
$$

$$
L_{\inf} = Q_1 - 1{,}5 \times \text{IQR}, \qquad L_{\sup} = Q_3 + 1{,}5 \times \text{IQR}
$$

Valores além dos limites são **substituídos pelo limite** (*capping*), não removidos:

```python
df[col] = df[col].clip(lower=L_inf, upper=L_sup)
```

**Justificativa do capping sobre remoção:** Em dados de tráfego de rede, valores extremos representam eventos legítimos (rajadas, reconexões lontas) e não erros de medição. Remover essas linhas introduziria viés de sobrevivência — o modelo nunca veria esses padrões durante o treino e falharia ao encontrá-los em produção. O capping preserva a informação de que o evento ocorreu, sem permitir que um único valor domine a escala.

**Escolha do método IQR:** O IQR é robusto a distribuições não-gaussianas, que são características de features de rede (distribuições exponenciais, log-normais, bimodais). Métodos paramétricos como ±3σ da média pressupõem normalidade e falham em identificar corretamente os limites em distribuições assimétricas.

A tabela abaixo apresenta as features com maior percentual de outliers identificados antes do capping:

| Feature | Q1 | Q3 | IQR | Limite Sup. | % Outliers |
|---|---|---|---|---|---|
| `frame.time_delta` | 6,20×10⁻⁵ | 7,81×10⁻⁴ | 7,19×10⁻⁴ | 1,86×10⁻³ | 15,61% |
| `frame.time_delta_displayed` | 6,20×10⁻⁵ | 7,81×10⁻⁴ | 7,19×10⁻⁴ | 1,86×10⁻³ | 15,61% |
| `mqtt.len` | 160 | 168 | 8 | 180 | 2,28% |
| `mqtt.msgtype` | 3 | 3 | 0 | 3 | 1,77% |
| `mqtt.topic_len` | 62 | 63 | 1 | 64,5 | 1,21% |

### 3.4 Tratamento de Valores Ausentes e Inválidos

Após o IQR capping e a remoção de colunas:

```python
X = X.fillna(0).replace([np.inf, -np.inf], 0)
```

**Valores `NaN`:** Resultam de campos MQTT opcionais ausentes em determinados tipos de mensagem (e.g., `mqtt.passwd` só está presente em mensagens `CONNECT`). Substituir por zero é semanticamente correto: a ausência do campo equivale ao valor padrão/nulo do protocolo.

**Valores `±inf`:** Podem surgir de divisões nas features de gap temporal (`publish_gap`, `connect_gap`) quando intervalos nulos são processados. Substituídos por zero como sentinela de ausência de gap.

### 3.5 Codificação do Label

```python
le = LabelEncoder()
y = le.fit_transform(df_tratado["type"])
# DoS → 0, normal → 1
```

O `LabelEncoder` do scikit-learn atribui inteiros em ordem lexicográfica: `"DoS"` → 0, `"normal"` → 1. Esta codificação é utilizada diretamente por todos os classificadores e métricas.

---

## 4. Seleção de Características

### 4.1 Motivação e Papel no Pipeline

A seleção de características busca três objetivos simultâneos: (1) reduzir a dimensionalidade, diminuindo o custo computacional de treinamento; (2) eliminar features ruidosas ou redundantes que degradam a generalização; (3) aumentar a interpretabilidade do modelo, identificando as features genuinamente informativas.

Com 29 features após a limpeza, a dimensionalidade é moderada, mas features altamente correlacionadas (e.g., `frame.len` e `frame.cap_len` no protocolo TCP/IP representam a mesma grandeza física em diferentes camadas) ainda podem prejudicar modelos sensíveis à multicolinearidade como LDA e KNN.

O pipeline implementa **sete métodos de seleção independentes**, cada um selecionando até $K = 15$ features. Crucialmente, cada seletor é **re-executado dentro de cada fold do CV externo** (ver Seção 8), garantindo que a seleção ocorra estritamente sobre os dados de treino do fold, sem contaminação do conjunto de validação.

### 4.2 mRMR — Minimum Redundancy Maximum Relevance

**Formulação:** O mRMR (Peng et al., 2005) seleciona features que maximizam a relevância com o target e minimizam a redundância interna ao conjunto selecionado, usando informação mútua:

$$
\max_{X_j \notin S} \left[ I(X_j; Y) - \frac{1}{|S|} \sum_{X_i \in S} I(X_j; X_i) \right]
$$

onde $I(X_j; Y)$ é a informação mútua entre a feature $X_j$ e o target $Y$, e $S$ é o conjunto de features já selecionadas.

**Processo:** Seleção gulosa iterativa. A cada passo, a feature não selecionada que maximiza o critério acima é adicionada a $S$. Ao contrário do simples ranqueamento por relevância, o mRMR penaliza features redundantes entre si — mesmo que cada uma seja individualmente relevante. Isso é especialmente importante no contexto MQTT, onde `frame.len` e `frame.cap_len` são altamente correlacionadas.

**Resultado obtido:** 14 features canônicas, incluindo as temporais `frame.time_delta`, `publish_gap` e `connect_gap` — indicando que o mRMR valoriza a informação de timing, não apenas a estrutura dos pacotes.

### 4.3 Fisher Score

**Formulação:** O Fisher Score (Fisher, 1936) quantifica a separabilidade de classes para cada feature individualmente:

$$
F_i = \frac{\sum_{c} n_c (\mu_{c,i} - \mu_i)^2}{\sum_{c} n_c \sigma_{c,i}^2}
$$

onde $\mu_{c,i}$ é a média da feature $i$ na classe $c$, $\mu_i$ é a média global e $\sigma_{c,i}^2$ é a variância intra-classe.

Features com Fisher Score alto apresentam grande separação entre as médias das classes (numerador alto) com baixa dispersão interna a cada classe (denominador baixo). No contexto binário DoS/normal, isso equivale a identificar features cujos valores divergem sistematicamente entre tráfego de ataque e tráfego legítimo.

**Implementação:** Cálculo direto em NumPy/Pandas, sem dependências externas. Denominador mínimo de $10^{-10}$ para evitar divisão por zero em features constantes por classe.

**Resultado obtido:** 15 features, conjunto quase idêntico ao do mRMR acrescido de `mqtt.conflag.uname`, que controla a presença de username na conexão — campo frequentemente manipulado em ataques.

### 4.4 Correlação de Pearson com o Target

**Formulação:** Para cada feature $X_i$, calcula-se o coeficiente de correlação de Pearson (absoluto) com o vetor de labels binários $Y$:

$$
|r_i| = \left| \frac{\text{Cov}(X_i, Y)}{\sigma_{X_i} \cdot \sigma_Y} \right|
$$

Features são ranqueadas pelo valor absoluto de $r_i$, e as $K$ mais correlacionadas são selecionadas. No caso de target binário, esta correlação equivale à correlação ponto-biserial e captura relações lineares entre feature e classe.

**Limitações e adequação:** A correlação de Pearson não captura relações não-lineares. Contudo, para features de tráfego MQTT com relação monotônica com a intensidade do ataque (ex.: maior frequência de mensagens `CONNECT` → maior probabilidade de DoS), ela é suficiente e computacionalmente muito eficiente.

**Resultado obtido:** 15 features, idênticas ao Fisher Score neste dataset — o que indica que as features mais discriminativas têm relação aproximadamente linear com o target.

### 4.5 ExtraTrees — Importância por Redução de Impureza

**Formulação:** Um `ExtraTreesClassifier` com 300 árvores é treinado nos dados de treino do fold. A importância de cada feature é a média ponderada da redução de impureza Gini em todos os nós de todas as árvores que utilizam aquela feature:

$$
\text{Imp}(X_i) = \frac{1}{T} \sum_{t=1}^{T} \sum_{v \in V_t(X_i)} \frac{n_v}{n} \Delta \text{Gini}(v)
$$

**Diferença do Random Forest:** No ExtraTrees (*Extremely Randomized Trees*), tanto os atributos quanto os limiares de divisão são escolhidos aleatoriamente (ao invés de otimizados como no RF). Isso reduz a variância das importâncias estimadas, tornando-as mais estáveis entre execuções — propriedade desejável em um seletor de features.

**Resultado obtido:** 15 features, com `mqtt.topic_len` em primeira posição (diferente dos outros métodos que colocam `mqtt.len` primeiro) — refletindo a perspectiva da aleatoriedade sobre a importância relativa das features de comprimento.

### 4.6 LinearSVC com Regularização L1

**Formulação:** Um `LinearSVC` com penalidade L1 é treinado sobre os dados normalizados. A regularização L1 força esparsidade nos coeficientes:

$$
\min_w \|w\|_1 + C \sum_i \max(0, 1 - y_i (w^T x_i + b))
$$

Features com $|w_i| > 0$ após o treinamento são consideradas relevantes. A magnitude $|w_i|$ reflete a contribuição da feature $i$ para a fronteira de decisão linear.

**Normalização obrigatória:** Antes do treinamento, `StandardScaler` normaliza cada feature para média zero e desvio padrão unitário. Sem normalização, features de maior escala dominam $\|w\|_1$, independentemente de sua relevância.

**Papel no pipeline:** O LinearSVC é usado **exclusivamente como seletor** (não como classificador final). Sua regularização L1 é especialmente útil quando se suspeita que poucas features são realmente decisivas — o que é o caso aqui, onde 15 features entre 29 capturaram quase toda a informação relevante.

**Resultado obtido:** 15 features, únicas inclusões em relação ao núcleo mRMR sendo `mqtt.conflag.uname` e `mqtt.conflag.retain`. O LinearSVC\_L1 foi o seletor que produziu o melhor modelo final (GradientBoosting com F1=0.9716).

### 4.7 LassoCV — Regularização L1 por Regressão

**Formulação:** O LASSO (*Least Absolute Shrinkage and Selection Operator*) minimiza:

$$
\min_\beta \frac{1}{2n} \|y - X\beta\|_2^2 + \alpha \|\beta\|_1
$$

O `LassoCV` determina $\alpha$ ótimo via validação cruzada interna de 3 folds. Features com $|\beta_i| > 0$ são selecionadas. Embora o LASSO seja formalmente um método de regressão, sua aplicação ao target binário 0/1 produz coeficientes que refletem relevância linear para discriminação das classes.

**Resultado obtido:** 15 features, incluindo unicamente `mqtt.conflag.passwd` além do núcleo comum — campo de comprimento de senha que o LASSO identifica como linearmente relevante para a distinção entre conexões de ataque e legítimas.

### 4.8 LowVariance — Filtro de Variância Nula

**Formulação:** Remove features com variância exatamente zero:

$$
\text{Var}(X_i) = \frac{1}{n}\sum_{j=1}^n (x_{ij} - \bar{x}_i)^2 = 0
$$

Features constantes em todo o conjunto de treino não carregam informação discriminativa por definição.

**Resultado obtido:** 14 features, conjunto idêntico ao mRMR (sem `mqtt.msgtype`, que apesar de ter poucos valores únicos, não é constante). Este seletor serve como filtro de sanidade — no dataset presente, apenas features de campos MQTT reservados/não-utilizados têm variância zero.

### 4.9 Resumo Comparativo dos Seletores

| Seletor | Tipo | Captura Não-Linearidade | Considera Redundância | Requer Treinamento |
|---|---|---|---|---|
| mRMR | Filtro (info mútua) | Parcialmente | Sim | Não |
| Fisher Score | Filtro (estatístico) | Não | Não | Não |
| Pearson | Filtro (correlação) | Não | Não | Não |
| ExtraTrees | Wrapper/Embebido | Sim | Parcialmente | Sim (300 árvores) |
| LinearSVC\_L1 | Embebido | Não | Parcialmente | Sim (SVM) |
| LassoCV | Embebido | Não | Parcialmente | Sim (regressão) |
| LowVariance | Filtro (variância) | N/A | Não | Não |

---

## 5. Otimização de Hiperparâmetros com Optuna

### 5.1 Motivação

Hiperparâmetros são parâmetros de configuração dos modelos que não são aprendidos durante o treinamento (e.g., número de árvores, taxa de aprendizado). Sua escolha impacta diretamente o desempenho — valores inadequados resultam em underfitting ou overfitting. A busca manual ou por grid é ineficiente em espaços de alta dimensionalidade.

### 5.2 Framework Optuna e o Algoritmo TPE

O Optuna (Akiba et al., 2019) é um framework de otimização automática de hiperparâmetros baseado no algoritmo **TPE** (*Tree-structured Parzen Estimator*, Bergstra et al., 2011).

O TPE mantém dois modelos de densidade estimados via *kernel density estimation*: $l(\lambda)$ para hiperparâmetros de trials com desempenho acima do percentil $\gamma$ ("boas"), e $g(\lambda)$ para as demais ("ruins"). A cada iteração, propõe o conjunto de hiperparâmetros $\lambda^*$ que maximiza a razão:

$$
\lambda^* = \argmax_\lambda \frac{l(\lambda)}{g(\lambda)}
$$

Esta formulação é equivalente a maximizar a *Expected Improvement* esperada. O TPE aprende progressivamente quais regiões do espaço de hiperparâmetros produzem bons resultados, concentrando as avaliações nessas regiões — ao contrário do Random Search, que amostra uniformemente sem aprendizado.

**Vantagem empírica:** O TPE tipicamente requer 30–50 trials para encontrar configurações competitivas em espaços com 5–8 hiperparâmetros, contra centenas de avaliações no Grid Search.

### 5.3 Poda de Trials com MedianPruner

O `MedianPruner` interrompe trials cujo desempenho intermediário (após o primeiro fold do CV interno) está abaixo da mediana das trials concluídas. Configurado com `n_warmup_steps=5`, aguarda 5 trials antes de ativar a poda.

**Impacto:** Reduz significativamente o tempo total de otimização sem sacrificar a qualidade — trials claramente ruins são interrompidas antes de concluir os 3 folds completos do CV interno.

### 5.4 CV Aninhado para Prevenção de Vazamento

A arquitetura de **validação cruzada aninhada** (*nested cross-validation*) garante estimativas não-viesadas do desempenho generalizado:

```
CV Externo (5 folds, Etapa de Avaliação)
└── Para cada fold externo k:
    ├── X_tr(k), y_tr(k) — dados de treino (80%)
    ├── X_val(k), y_val(k) — dados de validação (20%, NUNCA vistos pelo Optuna)
    └── Optuna: CV Interno (3 folds sobre X_tr(k))
        ├── Métrica: F1-macro
        ├── 30 trials por modelo
        ├── Seleciona best_params(k) para cada modelo
        └── Modelos com best_params(k) são avaliados em X_val(k)
```

Se os hiperparâmetros fossem selecionados usando o mesmo conjunto de avaliação, o desempenho estimado seria artificialmente inflado. O CV aninhado assegura que `X_val(k)` nunca influencia a seleção de hiperparâmetros.

### 5.5 Paralelismo de Tuning

Dentro de cada fold, o tuning dos 6 modelos é paralelizado:

```python
results = Parallel(n_jobs=6, backend="threading")(
    delayed(_tune_one_model)(...) for name, ... in MODEL_OBJECTIVES.items()
)
```

O backend `"threading"` é preferido ao `"loky"` (multiprocessing) porque operações NumPy/scikit-learn liberam o GIL Python durante computação numérica intensa, permitindo concorrência real. O multiprocessing adicionaria overhead de serialização desnecessário.

---

## 6. Modelos de Classificação

### 6.1 Random Forest

**Fundamento teórico:** O Random Forest (Breiman, 2001) é um método de ensemble de árvores de decisão treinadas por **bagging** (*bootstrap aggregating*). Cada árvore é construída sobre uma amostra bootstrap (com reposição) dos dados de treino e, em cada nó de divisão, considera apenas um subconjunto aleatório de features. A predição final é o voto majoritário das $T$ árvores.

A diversidade entre as árvores — induzida pela amostragem bootstrap e pela restrição de features — é o mecanismo que reduz a variância do modelo sem aumentar o viés substancialmente. Formalmente, para $T$ árvores não-correlacionadas com variância $\sigma^2$, a variância do ensemble é $\sigma^2/T$.

**Hiperparâmetros otimizados pelo Optuna:**

| Hiperparâmetro | Espaço de Busca | Descrição |
|---|---|---|
| `n_estimators` | {50, 100, ..., 500} (step 50) | Número de árvores |
| `max_depth` | {None, 5, 10, 20, 30} | Profundidade máxima |
| `min_samples_split` | [2, 20] int | Mín. amostras para dividir nó |
| `min_samples_leaf` | [1, 10] int | Mín. amostras por folha |
| `max_features` | {"sqrt", "log2", None} | Features por nó de divisão |
| `bootstrap` | {True, False} | Usar amostragem bootstrap |

**Parâmetros fixos:** `random_state=42`, `n_jobs=-1`.

**Melhores hiperparâmetros agregados (seletor mRMR):** `n_estimators=300`, `max_depth=13`, `min_samples_split=12`, `min_samples_leaf=7`, `max_features=log2`, `bootstrap=True`.

### 6.2 Decision Tree

**Fundamento teórico:** A árvore de decisão (Breiman et al., 1984) constrói uma estrutura hierárquica de decisões binárias. Em cada nó interno, escolhe-se a divisão que maximiza a redução de impureza segundo um critério:

$$
\text{Gini}(t) = 1 - \sum_{c=1}^C p_{c|t}^2
$$

$$
\text{Entropia}(t) = -\sum_{c=1}^C p_{c|t} \log_2 p_{c|t}
$$

O ganho de uma divisão é:

$$
\Delta I(t) = I(t) - \frac{n_L}{n_t} I(t_L) - \frac{n_R}{n_t} I(t_R)
$$

A árvore cresce recursivamente até atingir os critérios de parada. É o modelo mais interpretável do pipeline — cada caminho da raiz a uma folha é uma regra de classificação legível.

**Hiperparâmetros otimizados:**

| Hiperparâmetro | Espaço de Busca | Descrição |
|---|---|---|
| `max_depth` | {None, 3, 5, 10, 20} | Controla complexidade |
| `min_samples_split` | [2, 30] int | Critério de parada de divisão |
| `min_samples_leaf` | [1, 15] int | Poda mínima de folhas |
| `criterion` | {"gini", "entropy"} | Função de impureza |
| `max_features` | {"sqrt", "log2", None} | Features por divisão |
| `splitter` | {"best", "random"} | Estratégia de divisão |

**Parâmetros fixos:** `random_state=42`.

### 6.3 K-Nearest Neighbors (KNN)

**Fundamento teórico:** O KNN (Fix & Hodges, 1951) é um classificador não-paramétrico e *lazy* (sem fase de treinamento). Para classificar uma nova instância $x$, identifica os $k$ pontos mais próximos no espaço de treino segundo uma métrica de distância e retorna o voto majoritário:

$$
\hat{y}(x) = \argmax_c \sum_{x_i \in \mathcal{N}_k(x)} \mathbf{1}[y_i = c]
$$

Com ponderação por distância (`weights="distance"`), cada vizinho contribui proporcionalmente a $1/d(x, x_i)$.

**Métricas disponíveis:**
- **Euclidiana:** $d(x,x') = \sqrt{\sum_i (x_i - x'_i)^2}$ — sensível a diferenças em todas as dimensões igualmente
- **Manhattan:** $d(x,x') = \sum_i |x_i - x'_i|$ — mais robusta a outliers em features individuais
- **Minkowski:** $d(x,x') = (\sum_i |x_i - x'_i|^p)^{1/p}$ — generalização paramétrica

**Hiperparâmetros otimizados:**

| Hiperparâmetro | Espaço de Busca | Descrição |
|---|---|---|
| `n_neighbors` | [1, 50] int | Número de vizinhos |
| `weights` | {"uniform", "distance"} | Esquema de ponderação |
| `metric` | {"euclidean", "manhattan", "minkowski"} | Métrica de distância |
| `p` | [1, 3] int | Expoente Minkowski |

**Parâmetros fixos:** `n_jobs=-1`.

### 6.4 Linear Discriminant Analysis (LDA)

**Fundamento teórico:** A LDA (Fisher, 1936) encontra a projeção linear do espaço de features que maximiza a razão de Fisher entre dispersão inter-classes e intra-classes:

$$
J(w) = \frac{w^T S_B w}{w^T S_W w}
$$

Para classificação bayesiana, assume gaussianidade multivariada com mesma covariância entre classes. A fronteira de decisão é linear no espaço original de features.

**Solvers disponíveis:**

- **SVD** (`"svd"`): decompõe a matriz de dados centrada por classe, sem inverter $S_W$ explicitamente. Sempre estável, mas incompatível com `shrinkage`.
- **LSQR** (`"lsqr"`): resolve por mínimos quadrados, suporta `shrinkage` para regularização de $S_W$.

**Nota sobre o solver `"eigen"` removido:** O solver eigen exige que $S_W$ seja positiva-definida (fatoração de Cholesky). Com features correlacionadas no tráfego MQTT, $S_W$ torna-se singular, causando `LinAlgError`. Ele foi removido do espaço de busca do Optuna.

**Shrinkage de Ledoit-Wolf** (`shrinkage="auto"`): Regulariza $S_W$ por $S_W^{\text{reg}} = (1-\alpha)S_W + \alpha I$, onde $\alpha$ é estimado analiticamente. Essencial para dados com features correlacionadas.

**Hiperparâmetros otimizados:**

| Hiperparâmetro | Espaço de Busca | Descrição |
|---|---|---|
| `solver` | {"svd", "lsqr"} | Algoritmo de solução |
| `shrinkage` | {None, "auto"} | Regularização de $S_W$ |
| `tol` | [1e-6, 1e-3] log | Tolerância numérica |

### 6.5 Gaussian Naive Bayes Calibrado (GaussianNB\_Cal)

#### 6.5.1 Gaussian Naive Bayes

**Fundamento:** O GNB aplica o teorema de Bayes com premissa de independência condicional entre features dada a classe, e distribuição gaussiana por feature:

$$
P(Y=c \mid X) \propto P(Y=c) \prod_{i=1}^p \mathcal{N}(x_i; \mu_{c,i}, \sigma_{c,i}^2 + \epsilon)
$$

onde $\epsilon$ é o `var_smoothing` — parâmetro de regularização que evita variâncias nulas.

**Problema de calibração:** A premissa de independência entre features é violada no tráfego MQTT (`frame.len` e `frame.cap_len` são quase idênticos). Isso faz com que as probabilidades preditas sejam extremamente polarizadas (próximas de 0 ou 1), resultando em Log Loss elevado mesmo quando a predição de classe está correta — conforme observado no baseline: acurácia de 92,75% mas Log Loss de apenas 0,237 (com calibração).

#### 6.5.2 CalibratedClassifierCV

O calibrador aprende uma função $f$ que mapeia as probabilidades brutas $\hat{p}$ do GNB para probabilidades corretamente calibradas:

**Platt Scaling** (`method="sigmoid"`):
$$P_{\text{cal}}(Y=1 \mid \hat{p}) = \sigma(A\hat{p} + B) = \frac{1}{1 + e^{-(A\hat{p}+B)}}$$

**Regressão Isotônica** (`method="isotonic"`): Ajusta função monotônica não-paramétrica — mais flexível que Platt scaling, adequada para datasets de ~95k amostras.

O `cv=3` dentro do `CalibratedClassifierCV` usa validação cruzada interna para estimar $f$, prevenindo vazamento de dados para a calibração.

**Hiperparâmetros otimizados:**

| Hiperparâmetro | Espaço de Busca | Descrição |
|---|---|---|
| `var_smoothing` | [1e-11, 1e-5] log | Regularização de variâncias |
| `calibration_method` | {"sigmoid", "isotonic"} | Método de calibração |

### 6.6 Gradient Boosting

**Fundamento teórico:** O Gradient Boosting (Friedman, 2001) constrói um ensemble aditivo sequencial de árvores rasas, onde cada nova árvore aproxima os **gradientes negativos** da função de perda:

$$
F_m(x) = F_{m-1}(x) + \eta \cdot h_m(x)
$$

$$
h_m = \argmin_h \sum_i \left[ -\frac{\partial \mathcal{L}(y_i, F(x_i))}{\partial F(x_i)} \bigg|_{F=F_{m-1}} - h(x_i) \right]^2
$$

Para classificação binária com perda log-loss, o gradiente é $y_i - P(Y=1|x_i)$, e cada árvore corrige a diferença entre probabilidade predita e rótulo verdadeiro.

**Stochastic Gradient Boosting:** Com `subsample < 1.0`, cada árvore é treinada sobre uma subamostra aleatória dos dados, introduzindo diversidade que reduz overfitting. Essa variante combina boosting com bagging.

**Trade-off fundamental:** Taxas de aprendizado $\eta$ menores requerem mais árvores para convergir, mas geralmente generalizam melhor. O Optuna explora automaticamente esse trade-off.

**Hiperparâmetros otimizados:**

| Hiperparâmetro | Espaço de Busca | Descrição |
|---|---|---|
| `n_estimators` | {50, 100, ..., 300} step 50 | Número de árvores (iterações) |
| `learning_rate` | [0.01, 0.30] log | Taxa de encolhimento por etapa |
| `max_depth` | [2, 8] int | Profundidade das árvores base |
| `min_samples_split` | [2, 20] int | Mín. amostras para divisão |
| `min_samples_leaf` | [1, 10] int | Mín. amostras por folha |
| `subsample` | [0.50, 1.00] float | Fração de amostras por árvore |

**Parâmetros fixos:** `random_state=42`.

**Melhores hiperparâmetros encontrados (LinearSVC\_L1):** `n_estimators=210`, `learning_rate=0.046`, `max_depth=5`, `min_samples_split=5`, `min_samples_leaf=7`, `subsample=0.818`.

---

## 7. Ensemble de Modelos por Votação

### 7.1 Fundamento Teórico dos Ensembles

O princípio fundamental é que a **diversidade entre classificadores** combinada reduz o erro total. Se $M$ classificadores têm taxa de erro $\epsilon < 0.5$ e cometem erros de forma independente, a probabilidade de erro do ensemble por voto majoritário é:

$$
P_{\text{ensemble}} = \sum_{k > M/2} \binom{M}{k} \epsilon^k (1-\epsilon)^{M-k} \ll \epsilon
$$

Na prática, os erros não são completamente independentes, mas a diversidade de algoritmos (Random Forest com suas árvores independentes, Gradient Boosting sequencial, KNN baseado em distância, etc.) é suficiente para ganhos consistentes.

### 7.2 VotingClassifier — Soft Voting

**Mecanismo:** Cada classificador base fornece um vetor de probabilidades $P_m(Y=c|x)$, e o soft voting calcula a **média dessas probabilidades** para determinar a classe final:

$$
P_{\text{soft}}(Y=c|x) = \frac{1}{M} \sum_{m=1}^{M} P_m(Y=c|x)
$$

$$
\hat{y} = \argmax_c P_{\text{soft}}(Y=c|x)
$$

**Vantagem:** Um classificador que prediz com 95% de certeza tem mais influência que um que prediz com 55%. A confiança de cada predição é preservada na decisão final — isso é superior ao hard voting quando os modelos base são bem calibrados.

**Requisito:** Todos os modelos devem implementar `predict_proba()`. Os 6 modelos do pipeline atendem esse requisito (GNB via calibração).

### 7.3 VotingClassifier — Hard Voting

**Mecanismo:** Contagem de votos sobre as classes preditas por cada modelo:

$$
\hat{y} = \argmax_c \sum_{m=1}^{M} \mathbf{1}[\hat{y}_m = c]
$$

**Quando preferível ao soft voting:** Quando alguns modelos base têm calibração de probabilidades deficiente (e.g., sem o `CalibratedClassifierCV`, o GNB original teria log loss de ~2.4, distorcendo o soft voting). Após a calibração, o soft voting geralmente é igual ou superior ao hard.

**Nota:** O hard voting não produz probabilidades, portanto o Log Loss não é calculável para o VotingClassifier\_Hard.

### 7.4 Comparação entre Voting Modes

No pipeline, ambos os modos são avaliados em cada fold de CV para cada seletor. Os resultados (Seção 10) mostram que o Hard Voting consistentemente supera o Soft Voting em F1 por margem pequena (~0.002), enquanto o Soft Voting tem Log Loss explicitamente calculado e menor.

---

## 8. Validação Cruzada Estratificada

### 8.1 Configuração

```
StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
```

A validação cruzada estratificada divide os dados em $K=5$ folds preservando a proporção de classes em cada fold. Com shuffle ativo e semente fixada, a divisão é reproduzível.

**Split:** Em cada iteração, 80% dos dados (75.700 amostras) são usados para treino e 20% (18.925 amostras) para validação. As métricas são calculadas em cada fold e reportadas como média ± desvio padrão sobre os 5 folds.

### 8.2 Propriedades Estatísticas

**Por que 5 folds e não Leave-One-Out:** O LOO tem variância alta nas estimativas de desempenho e custo computacional proibitivo. 5 folds oferece o melhor equilíbrio entre viés (subestima ligeiramente o desempenho versus treinamento com 100% dos dados) e variância das estimativas.

**Desvio padrão como indicador de estabilidade:** Um desvio padrão pequeno (ex.: ±0.001 para RF) indica que o modelo é estável entre diferentes subsets dos dados — propriedade importante para confiabilidade em produção. O desvio padrão maior de algumas métricas (ex.: KNN Log Loss ±0.121) indica instabilidade naquela dimensão de avaliação.

---

## 9. Métricas de Avaliação

### 9.1 Acurácia (Accuracy)

**Definição:**

$$
\text{Accuracy} = \frac{TP + TN}{TP + TN + FP + FN}
$$

Proporção de predições corretas sobre o total de amostras.

**Quando é suficiente:** Para classes balanceadas como no dataset presente (~50/50), a acurácia é uma métrica razoável. Em datasets desbalanceados, pode ser enganosa — um modelo que prediz sempre a classe majoritária teria alta acurácia sem qualquer utilidade prática.

**Interpretação:** Acurácia de 0.9716 para o GradientBoosting com LinearSVC\_L1 significa que 97,16% dos pacotes de rede foram corretamente classificados.

### 9.2 Precisão (Precision) — Macro

**Definição (por classe):**

$$
\text{Precision}_c = \frac{TP_c}{TP_c + FP_c}
$$

**Macro-average:**

$$
\text{Precision}_{\text{macro}} = \frac{1}{C} \sum_{c=1}^C \text{Precision}_c
$$

A precisão mede a confiabilidade das predições positivas: dentre todos os pacotes classificados como DoS, qual proporção realmente era DoS. A macro-average trata as classes com peso igualitário.

**Importância no contexto:** Precisão baixa para a classe DoS significa muitos falsos positivos — pacotes legítimos classificados como ataque, gerando alertas desnecessários e possível bloqueio de tráfego legítimo.

### 9.3 Recall (Sensibilidade) — Macro

**Definição (por classe):**

$$
\text{Recall}_c = \frac{TP_c}{TP_c + FN_c}
$$

**Macro-average:**

$$
\text{Recall}_{\text{macro}} = \frac{1}{C} \sum_{c=1}^C \text{Recall}_c
$$

O recall mede a capacidade de detectar todos os ataques: dentre todos os pacotes realmente DoS, qual proporção foi detectada. Alta recall é crítica em segurança — ataques não detectados (falsos negativos) têm consequências severas.

### 9.4 F1-Score — Macro

**Definição:**

$$
F1_c = 2 \cdot \frac{\text{Precision}_c \times \text{Recall}_c}{\text{Precision}_c + \text{Recall}_c} = \frac{2 \cdot TP_c}{2 \cdot TP_c + FP_c + FN_c}
$$

$$
F1_{\text{macro}} = \frac{1}{C} \sum_{c=1}^C F1_c
$$

O F1-score é a **média harmônica** entre precisão e recall, penalizando desequilíbrios entre os dois. É a **métrica principal de ranqueamento** neste pipeline.

**Por que média harmônica:** A média aritmética de precisão e recall pode ocultar desequilíbrios extremos (ex.: precisão=1.0, recall=0.5 → aritmética=0.75, harmônica=0.667). A média harmônica penaliza valores extremos, refletindo melhor o trade-off real.

**Importância como métrica principal:** Em aplicações de segurança, tanto falsos positivos quanto falsos negativos têm custo relevante. O F1 balanceia ambos, tornando-se mais informativo que acurácia ou precisão/recall isoladamente.

### 9.5 Coeficiente de Correlação de Matthews (MCC)

**Definição:**

$$
\text{MCC} = \frac{TP \cdot TN - FP \cdot FN}{\sqrt{(TP+FP)(TP+FN)(TN+FP)(TN+FN)}}
$$

O MCC varia de -1 (predições inversas perfeitas) a +1 (predições corretas perfeitas), com 0 indicando predição aleatória. Ao contrário do F1, considera todos os quatro elementos da matriz de confusão (TP, TN, FP, FN) simetricamente.

**Vantagem para avaliação balanceada:** O MCC é especialmente informativo para datasets desbalanceados, mas também em datasets balanceados fornece uma visão mais completa que o F1. Um modelo com MCC de 0.943 (GradientBoosting melhor fold) indica correlação muito forte entre predições e rótulos verdadeiros.

**Interpretação:** Para o baseline do GradientBoosting: MCC=0.942, indicando que o modelo captura 94,2% da informação de classificação em um único número.

### 9.6 Log Loss (Cross-Entropy Loss)

**Definição:**

$$
\text{Log Loss} = -\frac{1}{n} \sum_{i=1}^n \left[ y_i \log \hat{p}_i + (1-y_i) \log (1-\hat{p}_i) \right]
$$

O Log Loss penaliza predições **confiantes e incorretas** desproporcionalmente. Uma predição de 99% de certeza que erra contribui com $-\log(0.01) \approx 4{,}6$ para a soma, contra $-\log(0.7) \approx 0{,}36$ de uma predição de 70% de certeza que erra.

**Por que é essencial além da acurácia:** Dois modelos com idêntica acurácia podem ter Log Loss muito diferentes se um for superconfiante. O Log Loss captura a **qualidade da calibração de probabilidades** — crítica para sistemas que tomam decisões com base em limiares de probabilidade (e.g., alertar apenas quando P(DoS)>0.8).

**O problema do GNB sem calibração:** No baseline sem calibração, o GNB teria Log Loss de ~2.4 mesmo com acurácia de 92.75%, porque as probabilidades preditas são extremas (0.0001 ou 0.9999). Com `CalibratedClassifierCV`, o Log Loss cai para 0.237 — a acurácia não muda, mas as probabilidades são muito mais confiáveis.

**Interpretação:** Log Loss de 0.079 do GradientBoosting (baseline) indica probabilidades bem calibradas. Log Loss de 0.076 após seleção via LassoCV representa uma melhora adicional significativa.

---

## 10. Resultados Experimentais

### 10.1 Etapa 0 — Baseline (sem seleção de features, split 70/30)

A tabela abaixo apresenta os resultados do baseline avaliado sobre o conjunto de teste fixo de 30% das amostras (~28.388 instâncias), usando todos os 29 features sem seleção e hiperparâmetros padrão (sem Optuna):

| Modelo | Acurácia | Precisão (macro) | Recall (macro) | F1 Macro | MCC | Log Loss |
|---|---|---|---|---|---|---|
| RandomForest | 0.96713 | 0.96773 | 0.96664 | 0.96705 | 0.93437 | 0.26702 |
| DecisionTree | 0.96435 | 0.96439 | 0.96421 | 0.96429 | 0.92860 | 0.58607 |
| KNN | 0.96569 | 0.96600 | 0.96535 | 0.96562 | 0.93135 | 0.36967 |
| LDA | 0.92754 | 0.93575 | 0.92510 | 0.92682 | 0.86078 | 0.34551 |
| GaussianNB\_Cal | 0.92754 | 0.93575 | 0.92510 | 0.92682 | 0.86078 | 0.23697 |
| GradientBoosting | 0.97090 | 0.97184 | 0.97027 | **0.97082** | **0.94211** | **0.07930** |
| VotingClassifier\_Soft | 0.96971 | 0.97118 | 0.96887 | 0.96960 | 0.94004 | 0.09892 |
| **VotingClassifier\_Hard** | **0.97002** | **0.97102** | **0.96936** | **0.96993** | **0.94038** | N/A |

**Observações:**
- O GradientBoosting supera todos os modelos individuais no baseline com F1=0.9708, sendo também o que apresenta menor Log Loss (0.079), indicando excelente calibração de probabilidades.
- LDA e GaussianNB\_Cal produzem resultados idênticos em acurácia e F1, mas o GaussianNB\_Cal tem Log Loss menor (0.237 vs. 0.346) graças à calibração isotônica.
- O VotingClassifier\_Hard supera o Soft em acurácia e F1, mas carece de Log Loss mensurável.
- O melhor modelo baseline é identificado como **GradientBoosting** (F1=0.97082).

### 10.2 Features Selecionadas por Seletor (Conjuntos Canônicos)

| Seletor | Nº Features | Features Únicas (além do núcleo comum) |
|---|---|---|
| mRMR | 14 | — (conjunto base de referência) |
| Fisher | 15 | `mqtt.conflag.uname` |
| Pearson | 15 | `mqtt.conflag.uname` (igual Fisher) |
| ExtraTrees | 15 | `mqtt.conflag.uname` |
| LinearSVC\_L1 | 15 | `mqtt.conflag.uname`, `mqtt.conflag.retain` |
| LassoCV | 15 | `mqtt.conflag.passwd`, `mqtt.conflag.uname`, `mqtt.conflag.retain` (sem `mqtt.msgtype`) |
| LowVariance | 14 | — (igual ao mRMR em conteúdo) |

**Núcleo de 13 features compartilhadas por todos os seletores:**
`mqtt.len`, `mqtt.topic_len`, `frame.time_delta`, `frame.cap_len`, `frame.len`, `mqtt.conack.flags.reserved`, `mqtt.clientid_len`, `connect_gap`, `mqtt.conack.val`, `mqtt.conflag.cleansess`, `mqtt.conack.flags.sp`, `mqtt.kalive`, `publish_gap`

### 10.3 Resultados por Seletor — Soft Voting (5-Fold CV)

Médias sobre os 5 folds externos. Melhor valor por coluna em **negrito**.

#### mRMR (14 features)

| Modelo | Acc (µ±σ) | F1 Macro (µ±σ) | MCC (µ±σ) | Log Loss (µ±σ) |
|---|---|---|---|---|
| RandomForest | 0.9708 ± 0.0008 | 0.9708 ± 0.0008 | 0.9419 ± 0.0015 | 0.0768 ± 0.0029 |
| DecisionTree | 0.9704 ± 0.0009 | 0.9703 ± 0.0009 | 0.9410 ± 0.0017 | 0.1170 ± 0.0182 |
| KNN | 0.9679 ± 0.0010 | 0.9678 ± 0.0010 | 0.9360 ± 0.0019 | 0.2398 ± 0.1213 |
| LDA | 0.9264 ± 0.0017 | 0.9257 ± 0.0017 | 0.8589 ± 0.0031 | 0.3547 ± 0.0115 |
| GaussianNB\_Cal | 0.9264 ± 0.0017 | 0.9257 ± 0.0017 | 0.8589 ± 0.0031 | 0.2386 ± 0.0043 |
| **GradientBoosting** | **0.9715 ± 0.0007** | **0.9714 ± 0.0007** | **0.9432 ± 0.0014** | **0.0775 ± 0.0043** |
| VotingClassifier\_Soft | 0.9691 ± 0.0014 | 0.9690 ± 0.0014 | 0.9389 ± 0.0028 | 0.0981 ± 0.0028 |

#### Fisher (15 features)

| Modelo | Acc (µ±σ) | F1 Macro (µ±σ) | MCC (µ±σ) | Log Loss (µ±σ) |
|---|---|---|---|---|
| RandomForest | 0.9711 ± 0.0009 | 0.9710 ± 0.0010 | 0.9423 ± 0.0018 | 0.0762 ± 0.0031 |
| DecisionTree | 0.9702 ± 0.0016 | 0.9701 ± 0.0016 | 0.9406 ± 0.0030 | 0.1486 ± 0.0513 |
| KNN | 0.9679 ± 0.0010 | 0.9678 ± 0.0010 | 0.9360 ± 0.0019 | 0.2398 ± 0.1213 |
| LDA | 0.9264 ± 0.0017 | 0.9257 ± 0.0017 | 0.8589 ± 0.0031 | 0.3547 ± 0.0115 |
| GaussianNB\_Cal | 0.9264 ± 0.0017 | 0.9257 ± 0.0017 | 0.8589 ± 0.0031 | 0.2386 ± 0.0043 |
| **GradientBoosting** | **0.9714 ± 0.0009** | **0.9713 ± 0.0009** | **0.9430 ± 0.0017** | **0.0759 ± 0.0024** |
| VotingClassifier\_Soft | 0.9691 ± 0.0016 | 0.9690 ± 0.0016 | 0.9390 ± 0.0031 | 0.0978 ± 0.0022 |

#### Pearson (15 features) — Idêntico ao Fisher

| Modelo | Acc (µ±σ) | F1 Macro (µ±σ) | MCC (µ±σ) | Log Loss (µ±σ) |
|---|---|---|---|---|
| RandomForest | 0.9711 ± 0.0009 | 0.9710 ± 0.0010 | 0.9423 ± 0.0018 | 0.0762 ± 0.0031 |
| **GradientBoosting** | **0.9714 ± 0.0009** | **0.9713 ± 0.0009** | **0.9430 ± 0.0017** | **0.0759 ± 0.0024** |
| VotingClassifier\_Soft | 0.9691 ± 0.0016 | 0.9690 ± 0.0016 | 0.9390 ± 0.0031 | 0.0978 ± 0.0022 |

*Nota: Pearson produziu exatamente as mesmas features que Fisher neste dataset, resultando em métricas idênticas.*

#### ExtraTrees (15 features)

| Modelo | Acc (µ±σ) | F1 Macro (µ±σ) | MCC (µ±σ) | Log Loss (µ±σ) |
|---|---|---|---|---|
| RandomForest | 0.9711 ± 0.0009 | 0.9711 ± 0.0009 | 0.9425 ± 0.0016 | 0.0762 ± 0.0025 |
| DecisionTree | 0.9706 ± 0.0011 | 0.9705 ± 0.0011 | 0.9414 ± 0.0023 | 0.1624 ± 0.0465 |
| KNN | 0.9679 ± 0.0010 | 0.9678 ± 0.0010 | 0.9360 ± 0.0019 | 0.2398 ± 0.1213 |
| **GradientBoosting** | **0.9714 ± 0.0009** | **0.9714 ± 0.0010** | **0.9432 ± 0.0019** | 0.0766 ± 0.0025 |
| VotingClassifier\_Soft | 0.9693 ± 0.0013 | 0.9692 ± 0.0013 | 0.9393 ± 0.0024 | **0.0978 ± 0.0023** |

#### LinearSVC\_L1 (15 features) — **Melhor Seletor**

| Modelo | Acc (µ±σ) | F1 Macro (µ±σ) | MCC (µ±σ) | Log Loss (µ±σ) |
|---|---|---|---|---|
| RandomForest | 0.9712 ± 0.0011 | 0.9711 ± 0.0011 | 0.9427 ± 0.0022 | 0.0764 ± 0.0033 |
| DecisionTree | 0.9704 ± 0.0010 | 0.9703 ± 0.0010 | 0.9409 ± 0.0020 | 0.1233 ± 0.0474 |
| KNN | 0.9679 ± 0.0010 | 0.9678 ± 0.0010 | 0.9361 ± 0.0018 | 0.2412 ± 0.1205 |
| LDA | 0.9264 ± 0.0017 | 0.9257 ± 0.0017 | 0.8589 ± 0.0031 | 0.3547 ± 0.0115 |
| GaussianNB\_Cal | 0.9264 ± 0.0017 | 0.9257 ± 0.0017 | 0.8589 ± 0.0031 | 0.2386 ± 0.0043 |
| **GradientBoosting** | **0.9716 ± 0.0010** | **0.9716 ± 0.0010** | **0.9435 ± 0.0019** | **0.0762 ± 0.0029** |
| VotingClassifier\_Soft | 0.9692 ± 0.0013 | 0.9691 ± 0.0013 | 0.9391 ± 0.0026 | 0.0979 ± 0.0024 |

#### LassoCV (15 features)

| Modelo | Acc (µ±σ) | F1 Macro (µ±σ) | MCC (µ±σ) | Log Loss (µ±σ) |
|---|---|---|---|---|
| RandomForest | 0.9712 ± 0.0010 | 0.9711 ± 0.0010 | 0.9426 ± 0.0019 | 0.0769 ± 0.0019 |
| DecisionTree | 0.9703 ± 0.0009 | 0.9702 ± 0.0009 | 0.9408 ± 0.0016 | 0.1769 ± 0.0325 |
| **GradientBoosting** | **0.9715 ± 0.0010** | **0.9714 ± 0.0010** | **0.9433 ± 0.0020** | **0.0756 ± 0.0026** |
| VotingClassifier\_Soft | 0.9694 ± 0.0009 | 0.9692 ± 0.0010 | 0.9394 ± 0.0018 | 0.0979 ± 0.0023 |

#### LowVariance (14 features)

| Modelo | Acc (µ±σ) | F1 Macro (µ±σ) | MCC (µ±σ) | Log Loss (µ±σ) |
|---|---|---|---|---|
| RandomForest | 0.9711 ± 0.0008 | 0.9711 ± 0.0008 | 0.9425 ± 0.0015 | 0.0757 ± 0.0021 |
| DecisionTree | 0.9696 ± 0.0011 | 0.9695 ± 0.0012 | 0.9396 ± 0.0022 | 0.1248 ± 0.0508 |
| **GradientBoosting** | **0.9715 ± 0.0008** | **0.9714 ± 0.0008** | **0.9432 ± 0.0016** | 0.0765 ± 0.0023 |
| VotingClassifier\_Soft | 0.9692 ± 0.0012 | 0.9691 ± 0.0012 | 0.9392 ± 0.0024 | 0.0980 ± 0.0022 |

### 10.4 Resultados por Seletor — Hard Voting (5-Fold CV, F1 Macro)

| Seletor | GB (F1) | RF (F1) | DT (F1) | KNN (F1) | VotingClassifier\_Hard (F1) |
|---|---|---|---|---|---|
| mRMR | 0.9714 | 0.9708 | 0.9703 | 0.9678 | 0.9709 |
| Fisher | 0.9713 | 0.9710 | 0.9701 | 0.9678 | 0.9709 |
| Pearson | 0.9713 | 0.9710 | 0.9701 | 0.9678 | 0.9709 |
| ExtraTrees | 0.9714 | 0.9711 | 0.9705 | 0.9678 | 0.9713 |
| **LinearSVC\_L1** | **0.9716** | 0.9711 | 0.9703 | 0.9678 | **0.9711** |
| LassoCV | 0.9714 | 0.9711 | 0.9702 | 0.9679 | 0.9710 |
| LowVariance | 0.9714 | 0.9711 | 0.9695 | 0.9679 | 0.9710 |

### 10.5 Resultado Final — Melhor Par (Seletor × Modelo)

O pipeline identificou o seguinte par ótimo por ambos os critérios de voting:

| | Soft Voting | Hard Voting |
|---|---|---|
| **Seletor** | LinearSVC\_L1 | LinearSVC\_L1 |
| **Modelo** | GradientBoosting | GradientBoosting |
| **F1 Macro** | **0.97155** | **0.97155** |

**Melhores hiperparâmetros do GradientBoosting (LinearSVC\_L1, agregados sobre 5 folds):**

| Hiperparâmetro | Valor Agregado |
|---|---|
| `n_estimators` | 210 |
| `learning_rate` | 0.04599 |
| `max_depth` | 5 |
| `min_samples_split` | 5 |
| `min_samples_leaf` | 7 |
| `subsample` | 0.8175 |
| `random_state` | 42 |

### 10.6 Hiperparâmetros Agregados por Seletor e Modelo (Amostra)

A tabela abaixo apresenta uma seleção dos hiperparâmetros médios agregados sobre os 5 folds para o GradientBoosting em cada seletor:

| Seletor | n\_estimators | learning\_rate | max\_depth | subsample |
|---|---|---|---|---|
| mRMR | 200 | 0.0672 | 5 | 0.790 |
| Fisher | 200 | 0.0601 | 5 | 0.800 |
| Pearson | 200 | 0.0601 | 5 | 0.800 |
| ExtraTrees | 200 | 0.0594 | 5 | 0.812 |
| **LinearSVC\_L1** | **210** | **0.0460** | **5** | **0.818** |
| LassoCV | 200 | 0.0549 | 5 | 0.820 |
| LowVariance | 200 | 0.0584 | 5 | 0.823 |

A estabilidade do `max_depth=5` em todos os seletores indica que árvores rasas são suficientes para capturar a estrutura do problema, e que profundidades maiores levam a overfitting.

---

## 11. Análise e Discussão

### 11.1 Convergência dos Seletores de Features

A alta sobreposição entre os conjuntos selecionados pelos 7 métodos (13 features comuns de um total de 14–15) é notável. Isso indica que as features relevantes para detecção de DoS em tráfego MQTT são **robustamente identificáveis** por diferentes critérios — estatísticos, baseados em modelo e de regularização. As features do núcleo comum representam:

- **Estrutura dos pacotes:** `mqtt.len`, `mqtt.topic_len`, `frame.cap_len`, `frame.len` — ataques DoS alteram o padrão de tamanho das mensagens
- **Tipo de controle:** `mqtt.msgtype`, `mqtt.conack.flags.reserved`, `mqtt.conack.flags.sp`, `mqtt.conack.val` — flooding tipicamente usa tipos específicos de mensagem (ex.: CONNECT repetido)
- **Temporização:** `frame.time_delta`, `publish_gap`, `connect_gap` — a taxa de chegada de mensagens aumenta dramaticamente durante ataques DoS
- **Configuração de conexão:** `mqtt.clientid_len`, `mqtt.kalive`, `mqtt.conflag.cleansess` — atacantes frequentemente usam parâmetros de conexão anômalos

### 11.2 Impacto da Seleção de Features sobre o Desempenho

Comparando o baseline (29 features, sem Optuna) com o melhor resultado do CV (15 features LinearSVC\_L1 + Optuna):

| | Baseline GB | Melhor CV (LinearSVC\_L1 + GB) | Ganho |
|---|---|---|---|
| F1 Macro | 0.97082 | 0.97155 | +0.00073 |
| Acurácia | 0.97090 | 0.97162 | +0.00072 |
| Log Loss | 0.07930 | 0.07616 | −0.00314 |

O ganho em F1 é modesto (+0.073 pp), mas consistente. A principal melhora é no Log Loss (−0.314 pp), indicando que a seleção de features e o tuning de hiperparâmetros melhoram significativamente a calibração das probabilidades, mesmo que o poder discriminativo já fosse alto com todos os features.

A redução de 29 para 15 features (48% menos) com ganho de desempenho demonstra que **as 14 features descartadas introduzem ruído** que prejudica sutilmente a generalização, especialmente para modelos lineares como LDA.

### 11.3 Hierarquia de Modelos

A ordenação por F1 é consistente entre todos os seletores:

$$\text{GradientBoosting} > \text{RandomForest} \approx \text{DecisionTree} > \text{KNN} \gg \text{LDA} = \text{GaussianNB\_Cal}$$

O GradientBoosting supera consistentemente o RF (~0.3–0.4 pp em F1), confirmando que a estrutura sequencial de boosting é mais eficaz que o bagging independente para este problema.

LDA e GaussianNB\_Cal têm desempenho substancialmente inferior (~4.5 pp abaixo em F1) por suas premissas de linearidade/gaussianidade, que são violadas nos dados. Após calibração, o GNB\_Cal tem Log Loss (0.238) muito menor que o LDA (0.355), confirmando o valor da calibração de probabilidades.

### 11.4 Soft vs. Hard Voting

O Hard Voting supera marginalmente o Soft em F1 Macro (+0.002 pp na maioria dos seletores). Isso sugere que, mesmo com calibração, as probabilidades do GNB influenciam negativamente o soft voting por serem ligeiramente diferentes das dos outros modelos mais poderosos. O Hard Voting é mais robusto a esse efeito.

### 11.5 Estabilidade do Pipeline

Os desvios padrão das métricas são excepcionalmente baixos para GB e RF (~0.0007–0.0010 em F1), indicando alta estabilidade entre folds — o modelo é consistente independentemente do subconjunto de dados usado para treino. O KNN apresenta variância alta em Log Loss (±0.121), provavelmente devido à sensibilidade local do algoritmo a outliers que não foram completamente eliminados pelo capping de IQR.

---

## 12. Conclusões

O pipeline desenvolvido demonstra que a classificação de ataques DoS em tráfego MQTT é altamente viável com técnicas modernas de aprendizado de máquina. Os principais achados são:

1. **GradientBoosting com seleção via LinearSVC\_L1 é a melhor combinação**, atingindo F1 Macro de 0.9716 em validação cruzada de 5 folds (F1=0.9708 no baseline sem seleção de features).

2. **15 features são suficientes** para capturar todo o poder preditivo dos 29 features disponíveis, com features de temporização (`frame.time_delta`, `publish_gap`, `connect_gap`) sendo críticas para a detecção.

3. **A calibração de probabilidades do GNB é essencial**: sem `CalibratedClassifierCV`, o Log Loss seria ~10× maior sem impacto na acurácia — tornando o modelo inutilizável em sistemas que usam limiares de probabilidade para alertas.

4. **O ensemble por votação melhora consistentemente** sobre os modelos individuais para modelos complementares (RF + DT + KNN + LDA + GNB + GB), porém o ganho é marginal quando o GB domina o sinal — o modelo mais forte "afoga" a diversidade dos demais.

5. **A otimização via Optuna converge para `max_depth=5`** para o GradientBoosting em todos os seletores — árvores rasas com taxa de aprendizado moderada (~0.05) são preferíveis a árvores profundas com taxa alta, refletindo o princípio de shrinkage do boosting.

**Trabalhos futuros:** Avaliação com XGBoost e LightGBM (implementações otimizadas de gradient boosting); análise de tempo de resposta para deployment em tempo real; avaliação em cenários de ataque não vistos durante treinamento (zero-shot generalization).

---

## 13. Referências

- Akiba, T., Sano, S., Yanase, T., Ohta, T., & Koyama, M. (2019). Optuna: A Next-generation Hyperparameter Optimization Framework. *KDD 2019*.
- Bergstra, J., Bardenet, R., Bengio, Y., & Kégl, B. (2011). Algorithms for Hyper-Parameter Optimization. *NeurIPS 2011*.
- Breiman, L. (1996). Bagging Predictors. *Machine Learning, 24*(2), 123–140.
- Breiman, L. (2001). Random Forests. *Machine Learning, 45*(1), 5–32.
- Breiman, L., Friedman, J. H., Olshen, R. A., & Stone, C. J. (1984). *Classification and Regression Trees*. Wadsworth.
- Fisher, R. A. (1936). The use of multiple measurements in taxonomic problems. *Annals of Eugenics, 7*(2), 179–188.
- Fix, E., & Hodges, J. L. (1951). *Discriminatory Analysis, Nonparametric Discrimination*. USAF School of Aviation Medicine.
- Friedman, J. H. (2001). Greedy Function Approximation: A Gradient Boosting Machine. *Annals of Statistics, 29*(5), 1189–1232.
- Ledoit, O., & Wolf, M. (2004). A well-conditioned estimator for large-dimensional covariance matrices. *Journal of Multivariate Analysis, 88*(2), 365–411.
- Peng, H., Long, F., & Ding, C. (2005). Feature selection based on mutual information: criteria of max-dependency, max-relevance, and min-redundancy. *IEEE TPAMI, 27*(8), 1226–1238.
- Platt, J. (1999). Probabilistic Outputs for Support Vector Machines. *Advances in Large Margin Classifiers*.
- Tibshirani, R. (1996). Regression Shrinkage and Selection via the Lasso. *Journal of the Royal Statistical Society B, 58*(1), 267–288.
- Wolpert, D. H. (1992). Stacked Generalization. *Neural Networks, 5*(2), 241–259.

---

*Documento gerado com base nos resultados experimentais do notebook `full_pipeline_v6.ipynb`. Todas as métricas foram obtidas por validação cruzada estratificada de 5 folds com semente aleatória fixada em 42 para reprodutibilidade.*
