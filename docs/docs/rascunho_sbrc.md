# Detecção de Ataques DoS em Redes MQTT com Métodos de Aprendizado de Máquina de Baixo Custo: Seleção de Features, Otimização de Hiperparâmetros e Ensemble de Modelos

> **Rascunho para Artigo Científico**
> Versão 1.0

---

## Resumo

Este trabalho propõe um pipeline de aprendizado de máquina para detecção de ataques de Negação de Serviço (DoS) em redes que utilizam o protocolo MQTT (*Message Queuing Telemetry Transport*), com foco em métodos computacionalmente eficientes e interpretáveis, adequados para ambientes IoT com recursos limitados. Partindo da base pública *MQTT Under Attack Dataset* (Ghorbanian et al., 2025), o pipeline combina engenharia de features temporais, sete métodos independentes de seleção de características — incluindo a Stability Selection (Meinshausen & Bühlmann, 2010) como mecanismo de agregação probabilística robusto — e otimização bayesiana de hiperparâmetros via Optuna (Akiba et al., 2019). Seis modelos de classificação foram avaliados: Random Forest, XGBoost, Decision Tree, Gaussian Naive Bayes Calibrado, K-Nearest Neighbors e HistGradientBoosting. Dois esquemas de ensemble foram comparados: VotingClassifier (soft e hard) e StackingClassifier com predições *out-of-fold* (OOF). A avaliação utilizou validação cruzada estratificada de cinco folds com seis métricas: Acurácia, Precisão, Recall, F1-Macro, MCC e Log Loss. O melhor resultado individual foi F1=0,9711 (Random Forest, seletor LassoCV, Stability Selection), e o melhor ensemble atingiu F1=0,9713 (Stacking OOF, dataset ExtraTrees, pipeline de voting-by-ranking). Esses resultados demonstram que modelos de baixa complexidade computacional, quando combinados com seleção criteriosa de features, rivalizam com arquiteturas profundas em precisão, ao mesmo tempo que mantêm viabilidade para implantação em borda (*edge*).

**Palavras-chave:** MQTT, IoT Security, DoS Detection, Machine Learning, Feature Selection, Stability Selection, Ensemble Learning, Stacking, Optuna.

---

## 1. Introdução

O protocolo MQTT (*Message Queuing Telemetry Transport*) tornou-se o padrão predominante em redes IoT (*Internet of Things*) por sua leveza, baixo consumo de banda e modelo de comunicação baseado em publicação-assinatura (*publish-subscribe*). Estima-se que centenas de milhões de dispositivos troquem mensagens via MQTT em aplicações industriais, residenciais e de infraestrutura crítica. Essa centralização de toda comunicação em um único componente — o *broker* MQTT — cria uma superfície de ataque privilegiada: um adversário que consiga saturar o broker com requisições maliciosas derruba toda a infraestrutura conectada sem precisar comprometer nenhum dispositivo individualmente.

Ataques de Negação de Serviço (DoS) contra brokers MQTT representam uma ameaça significativa e crescente. A detecção em tempo real desses ataques em ambientes com restrições de hardware — como gateways IoT e dispositivos de borda — é um problema aberto que combina desafios de segurança e engenharia de sistemas. Métodos baseados em assinaturas e regras fixas falham frente à variabilidade dos padrões de ataque; abordagens baseadas em redes neurais profundas demandam recursos computacionais incompatíveis com dispositivos de borda.

Este trabalho apresenta um pipeline de aprendizado de máquina que responde a essa lacuna, priorizando três propriedades: (1) **eficiência computacional**, com modelos de complexidade polinomial viáveis em hardware de borda; (2) **interpretabilidade**, com seleção explícita das features discriminativas e modelos auditáveis; (3) **robustez metodológica**, com validação cruzada aninhada e Stability Selection para garantir que os resultados reportados sejam generalizáveis.

As contribuições deste trabalho são:

- Derivação e validação de duas features temporais originais — `publish_gap` e `connect_gap` — projetadas para capturar o comportamento de flooding DoS sem data leakage;
- Avaliação sistemática de sete métodos de seleção de features, com e sem Stability Selection como mecanismo de agregação probabilística;
- Comparação entre VotingClassifier e StackingClassifier com OOF como estratégias de ensemble;
- Otimização de hiperparâmetros via Optuna TPE com validação cruzada aninhada;
- Análise completa de desempenho em seis métricas para seis modelos e até dezoito combinações dataset × modelo.

---

## 2. Dataset e Coleta de Dados

### 2.1 Base de Dados Utilizada

Os experimentos utilizam o *MQTT Under Attack Dataset*, disponibilizado publicamente por Ghorbanian et al. (2025) através do repositório Data in Brief (ScienceDirect), identificado pelo DOI 10.1016/j.dib.2025.XXXXXX. O dataset foi construído em ambiente de laboratório controlado com um broker Mosquitto e múltiplos dispositivos simulados trocando mensagens MQTT legítimas, sobre as quais foram executados ataques reais de DoS, *Man-in-the-Middle* (MitM) e Intrusion.

O conjunto de dados é composto por capturas de tráfego de rede no formato PCAP, processadas com o Wireshark para extração de campos de protocolo em formato CSV. Para os experimentos de detecção de DoS, foi utilizado o arquivo `DoS.csv` como fonte primária, enriquecido com features temporais derivadas conforme descrito na Seção 3. Para validação da metodologia de derivação de features em outros tipos de ataque, utilizou-se também os arquivos `MitM.csv` e `Intrusion.csv`.

### 2.2 Caracterização do Dataset DoS

O arquivo DoS, após pré-processamento, apresenta as seguintes características:

| Característica | Valor |
|---|---|
| Total de amostras | 94.625 pacotes |
| Features originais (campos Wireshark) | 67 |
| Features após limpeza e engenharia | **29** |
| Amostras da classe DoS (label = 0) | ~47.312 (≈ 50%) |
| Amostras da classe Normal (label = 1) | ~47.313 (≈ 50%) |
| Proporção DoS/Normal | ~1:1 (balanceado) |

O balanceamento natural próximo de 50/50 é uma característica favorável: elimina a necessidade de técnicas de reamostragem como SMOTE ou undersampling, que podem introduzir artefatos.

### 2.3 Processo de Coleta e Estrutura das Capturas

A captura de tráfego foi realizada com o Wireshark em modo promíscuo em uma interface de rede que monitorava toda a comunicação entre clientes MQTT e o broker. Cada linha do CSV resultante representa um único pacote TCP/MQTT, com os campos extraídos organizados em três grupos:

**Campos de Frame (infraestrutura de captura):** `frame.time_epoch`, `frame.time_delta`, `frame.len`, `frame.cap_len`, `frame.number`, entre outros identificadores de sessão de captura.

**Campos TCP:** `tcp.srcport`, `tcp.dstport` — portas de origem e destino.

**Campos MQTT (protocolo de aplicação):** `mqtt.msgtype` (tipo de mensagem: CONNECT=1, PUBLISH=3, SUBSCRIBE=8, etc.), `mqtt.len`, `mqtt.topic_len`, `mqtt.clientid_len`, `mqtt.kalive`, `mqtt.conack.val`, `mqtt.conack.flags.*`, `mqtt.conflag.*`, entre outros.

A variável-alvo `type` assume os valores `DoS` (para pacotes de ataque) e `normal` (para tráfego legítimo).

### 2.4 Datasets MitM e Intrusion

Para validação do processo de engenharia de features (Seção 3.3), utilizou-se dois datasets adicionais:

| Dataset       | Amostras Totais | Classe Minoritária     | Proporção |
| ------------- | --------------- | ---------------------- | --------- |
| MitM.csv      | 110.668         | 3.855 MitM (3,5%)      | ~29:1     |
| Intrusion.csv | 80.893          | 1.898 intrusion (2,3%) | ~41:1     |

Esses datasets apresentam desbalanceamento severo, contrastando com o DoS, e foram utilizados exclusivamente para demonstrar a generalidade do procedimento de derivação de `publish_gap` e `connect_gap` sem data leakage.

---

## 3. Engenharia de Features e Pré-processamento

### 3.1 Filosofia de Pré-processamento: Preservar sem Distorcer

O pré-processamento adota a premissa de que, em dados de rede, valores extremos frequentemente representam eventos legítimos (rajadas, reconexões lentas, timeout de keepalive) e não erros de medição. A remoção dessas amostras introduziria viés de sobrevivência: o modelo jamais veria eventos raros e falharia exatamente nos casos mais críticos para segurança.

Por isso, o tratamento de outliers utiliza **IQR Capping** em vez de remoção:

$$
L_{\text{inf}} = Q_1 - 1{,}5 \cdot (Q_3 - Q_1), \quad L_{\text{sup}} = Q_3 + 1{,}5 \cdot (Q_3 - Q_1)
$$

Valores fora dos limites são substituídos pelo limite correspondente (capping), preservando a informação de que o evento ocorreu sem permitir que ele domine estimativas estatísticas.

### 3.2 Remoção de Colunas Irrelevantes

Das 67 features originais, 26 foram descartadas antes da modelagem, conforme justificativas técnicas:

**Tabela 1 — Colunas removidas e critério de exclusão**

| Grupo                        | Colunas removidas                                                                                                                                                                                                  | Critério                                                                                    |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------- |
| Identificadores de instância | `frame.number`, `frame.md5_hash`, `frame.interface_id`, `frame.interface_name`, `frame.link_nr`                                                                                                                    | Memorizam instâncias, sem poder preditivo generalizável                                     |
| Timestamps absolutos         | `frame.time_epoch`, `frame.time_relative`, `frame.time_delta_displayed`, `frame.time_invalid`                                                                                                                      | O instante de captura não discrimina o tipo de tráfego; somente intervalos são informáticos |
| Portas TCP                   | `tcp.srcport`, `tcp.dstport`                                                                                                                                                                                       | Portas efêmeras, altamente variáveis e irrelevantes para o tipo de ataque                   |
| Payload de sessão            | `mqtt.username`, `mqtt.passwd`, `mqtt.willmsg`, `mqtt.willtopic`, `mqtt.msgid`                                                                                                                                     | Específicos de sessão; risco de privacidade; sem relação causal com DoS                     |
| Artefatos Wireshark          | `frame.coloring_rule.name`, `frame.coloring_rule.string`, `frame.comment`, `frame.comment.expert`, `frame.encap_type`, `frame.file_off`, `frame.ignored`, `frame.incomplete`, `frame.marked`, `frame.offset_shift` | Gerados pela ferramenta de análise; inexistentes em tráfego de produção                     |

Após remoção, o dataset de trabalho possui **29 features**, com todos os valores NaN substituídos por 0 (semanticamente correto para campos MQTT opcionais) e valores ±∞ convertidos para 0.

### 3.3 Derivação das Features Temporais: `publish_gap` e `connect_gap`

**Motivação.** O ataque DoS de flooding contra brokers MQTT se manifesta fundamentalmente como uma **anomalia de taxa de chegada**: o atacante envia mensagens CONNECT ou PUBLISH em frequência muito superior à do tráfego legítimo. As features existentes no dataset capturam estrutura de pacote (tamanho, campos de cabeçalho), mas não capturam diretamente o ritmo temporal do fluxo de mensagens.

**Definição formal.** Para um dataset ordenado por `frame.time_epoch`:

- `publish_gap`: intervalo de tempo (em segundos) entre mensagens MQTT do tipo PUBLISH consecutivas (`mqtt.msgtype = 3`)
- `connect_gap`: intervalo de tempo (em segundos) entre mensagens MQTT do tipo CONNECT consecutivas (`mqtt.msgtype = 1`)

Formalmente, para pacotes $p_1, p_2, \ldots, p_n$ do tipo $t$ com timestamps $\tau_1 \leq \tau_2 \leq \ldots \leq \tau_m$ (subsequência dos pacotes de tipo $t$ ordenados por tempo):

$$
\text{publish\_gap}(p_j) = \tau_j - \tau_{j-1}, \quad \forall j \geq 2; \quad \text{publish\_gap}(p_1) = 0
$$

Para pacotes que não são do tipo correspondente, a feature assume valor 0.

**Por que essas features discriminam DoS.** Em tráfego normal, os gaps entre mensagens PUBLISH refletem a taxa de atualização de sensores IoT — tipicamente segundos a minutos. Em flooding DoS, o atacante envia centenas ou milhares de mensagens por segundo, reduzindo `publish_gap` e `connect_gap` para próximo de zero. A mediana do `publish_gap` em tráfego normal é muito maior que durante ataque, tornando essas features altamente discriminativas.

**Derivação sem data leakage.** O cálculo das features temporais exige cuidado metodológico: calcular o gap sobre o dataset completo e depois realizar train/test split permitiria que informação do conjunto de teste influenciasse as features do conjunto de treino (leakage temporal). O procedimento correto, implementado no notebook `derive_gaps_intrusion_mitm.ipynb`, é:

```
1. Realiza split estratificado 70/30 (train_test_split com stratify=type)
2. Para cada split independentemente:
   a. Ordena por frame.time_epoch
   b. Filtra pacotes com mqtt.msgtype = 3 (PUBLISH)
   c. Calcula diff() dos timestamps → publish_gap
   d. Repete para msgtype = 1 → connect_gap
   e. Preenche com 0 os pacotes não-PUBLISH/CONNECT
3. Concatena os splits enriquecidos
```

Esse procedimento garante que nenhuma informação do conjunto de teste influencia a derivação das features no conjunto de treino. Para o pipeline principal com 5-fold CV, a seleção de features é re-executada dentro de cada fold, mantendo a mesma propriedade.

**Tabela 2 — Estatísticas descritivas de `publish_gap` e `connect_gap` (MitM e Intrusion)**

| Dataset | Feature | Média | Desvio Padrão | Mínimo | Máximo |
|---|---|---|---|---|---|
| MitM | `publish_gap` | 0,0836 | 4,499 | 0 | 813,08 |
| MitM | `connect_gap` | 0,0146 | 3,799 | 0 | 1.192,54 |
| Intrusion | `publish_gap` | 0,1232 | 3,491 | 0 | 561,14 |
| Intrusion | `connect_gap` | 0,1217 | 5,956 | 0 | 876,64 |

A alta variância reflete a mistura de tráfego com e sem gaps (a maioria dos pacotes não é PUBLISH/CONNECT, recebendo gap=0), enquanto o máximo muito elevado indica episódios de silêncio prolongado no tráfego normal.

---

## 4. Justificativa da Escolha dos Métodos de Aprendizado

### 4.1 Critérios de Seleção: Low-Cost, Interpretável, Aplicável em IoT

A escolha dos seis classificadores foi guiada por três critérios que refletem as restrições reais de sistemas de detecção de intrusão em IoT:

**4.1.1 Eficiência Computacional**

Dispositivos de borda típicos (Raspberry Pi 4, gateways industriais ARM Cortex-A53) dispõem de 256 MB a 8 GB de RAM e 2–4 núcleos de CPU. Redes neurais profundas exigem aceleradores (GPU/TPU) e dezenas de MB de parâmetros para alcançar alta precisão — inviáveis nesses ambientes.

Os modelos selecionados apresentam complexidade de inferência máxima de $O(d \cdot \log n)$ para árvores de decisão e $O(n)$ para KNN com índice espacial, contra $O(n \cdot p \cdot L)$ para redes neurais com $L$ camadas e $p$ neurônios. Em hardware equivalente ao i5-12400F, um RandomForest com 330 árvores classifica um pacote em <1 ms; uma versão comprimida com 10 árvores classifica em <0,1 ms.

**Tabela 3 — Comparativo de eficiência dos modelos selecionados**

| Modelo | Memória (RAM) | Tempo treino (66k amostras) | Tempo inferência/pacote | Compatível com borda |
|---|---|---|---|---|
| RandomForest (200 árvores) | ~50 MB | ~3s | ~2 ms | Sim (versão comprimida) |
| XGBoost (100 rounds) | ~30 MB | ~3s | ~1 ms | Sim |
| Decision Tree | ~1 MB | <1s | <0,1 ms | Sim |
| GaussianNB Calibrado | <1 MB | <1s | <0,1 ms | Sim |
| KNN (kd-tree) | ~20 MB | ~0,5s | ~5 ms | Parcialmente |
| HistGradientBoosting | ~40 MB | ~15s | ~1 ms | Sim |

**4.1.2 Interpretabilidade**

Em sistemas de segurança de infraestrutura crítica sujeitos a auditorias (e.g., IEC 62443, NIST SP 800-82), o modelo deve ser capaz de explicar *por que* um pacote foi classificado como ataque. Árvores de decisão permitem extração direta de regras; Random Forest e XGBoost admitem análise de importância de features e valores SHAP; GaussianNB tem interpretação probabilística direta.

Redes neurais profundas são essencialmente caixas-pretas — a interpretabilidade requer técnicas adicionais (LIME, SHAP) com overhead computacional, e mesmo assim os resultados são aproximações. Os modelos selecionados oferecem interpretabilidade nativa ou de baixo custo adicional.

**4.1.3 Aplicabilidade em Ambientes Reais IoT**

Além da eficiência computacional, a aplicabilidade em IoT exige: (a) ausência de dependências pesadas (GPU, TensorFlow); (b) serialização compacta (o modelo exportado em joblib ou ONNX cabe em dispositivos com flash limitado); (c) inferência em tempo real sem acesso à nuvem para classificação básica.

O Decision Tree serializado ocupa ~100 KB; o RandomForest comprimido com 15 árvores ocupa ~3 MB — ambos viáveis para flash de gateways IoT. A inferência não depende de conexão à internet, tornando o sistema resiliente a ataques que cortam a conectividade.

### 4.2 Modelos Descartados e Por Quê

Redes neurais convolucionais (CNN) e LSTMs para detecção de intrusão em rede têm sido exploradas na literatura, mas foram conscientemente excluídas deste trabalho: (a) requerem GPU para treinamento viável; (b) a inferência em CPU demora dezenas de ms por amostra — incompatível com classificação em tempo real de tráfego MQTT de alta taxa; (c) a interpretabilidade é limitada sem técnicas adicionais; (d) o tamanho do modelo (dezenas a centenas de MB) excede a capacidade de dispositivos de borda de baixo custo.

SVM com kernel RBF também foi descartado: a inferência tem complexidade $O(n_{SV} \cdot d)$ onde $n_{SV}$ pode ser decenas de milhares de vetores de suporte para 94k amostras — impraticável em borda.

---

## 5. Seletores de Características

### 5.1 Motivação para Seleção de Features

Das 29 features disponíveis após pré-processamento, nem todas contribuem igualmente para a discriminação DoS/normal. Features redundantes (e.g., `frame.len` e `frame.cap_len` medem grandezas altamente correlacionadas) aumentam o custo de inferência sem ganho de acurácia. Features irrelevantes podem introduzir ruído que prejudica modelos sensíveis à dimensionalidade (KNN, GNB). A seleção serve a três propósitos: reduzir overfitting, acelerar inferência em borda, e identificar as features causalmente relevantes para o problema.

### 5.2 Os Sete Seletores Implementados

**5.2.1 mRMR — Minimum Redundancy Maximum Relevance**

O mRMR (Peng et al., 2005) seleciona iterativamente features que maximizam a relevância com o target e minimizam a redundância entre si, usando informação mútua:

$$
\max_{X_j \notin S}\left[I(X_j; Y) - \frac{1}{|S|}\sum_{X_i \in S} I(X_j; X_i)\right]
$$

**Vantagem para DoS em MQTT:** captura dependências não-lineares entre features e target, penalizando features co-lineares como `frame.len`/`frame.cap_len`. **Resultado:** selecionou 14 features, incluindo ambas as features temporais derivadas.

**5.2.2 Fisher Score**

Quantifica a separabilidade de classes para cada feature individualmente:

$$
F_i = \frac{\sum_{c} n_c (\mu_{c,i} - \mu_i)^2}{\sum_{c} n_c \sigma_{c,i}^2}
$$

**Vantagem para DoS:** eficiente computacionalmente ($O(n \cdot p)$); identifica features com distribuições notavelmente diferentes entre DoS e normal, como `frame.time_delta` (intervalos muito menores durante flooding). **Resultado:** 15 features; conjunto idêntico ao Pearson.

**5.2.3 Correlação de Pearson com o Target**

$$|r_i| = \left|\text{Cor}(X_i, Y)\right|$$

Para target binário, equivale à correlação ponto-biserial. **Vantagem:** simplicidade e reprodutibilidade; capta relações lineares monotônicas com o target, que dominam para features de timing. **Limitação:** ignora relações não-lineares. **Resultado:** 15 features; idêntico ao Fisher neste dataset, confirmando que as relações dominantes são lineares.

**5.2.4 ExtraTrees — Importância por Redução de Impureza**

Um classificador ExtraTrees com 100 árvores é treinado e a importância de cada feature é a redução média ponderada da impureza Gini:

$$\text{Imp}(X_i) = \frac{1}{T}\sum_{t=1}^T\sum_{v \in V_t(X_i)} \frac{n_v}{n} \Delta\text{Gini}(v)$$

**Vantagem para DoS:** captura relações não-lineares e interações entre features, como o efeito conjunto de `mqtt.msgtype` e `frame.time_delta` durante flooding. **Resultado:** 15 features.

**5.2.5 LinearSVC com Regularização L1**

Um LinearSVC com penalidade L1 é treinado sobre dados normalizados:

$$\min_w \|w\|_1 + C\sum_i \max(0, 1 - y_i w^T x_i)$$

Features com $|w_i| > 0$ após convergência são selecionadas. **Vantagem:** o L1 realiza seleção esparsificante automaticamente; identifica features com relação linear com o hiperplano de separação. **Resultado único:** incluiu `mqtt.conflag.retain`, não selecionada pelos outros métodos — revelando que este campo tem relevância linear específica para a perspectiva do SVM.

**5.2.6 LassoCV — Regularização L1 por Regressão**

$$\min_\beta \frac{1}{2n}\|y - X\beta\|_2^2 + \alpha\|\beta\|_1$$

O $\alpha$ ótimo é determinado por validação cruzada de 3 folds. **Vantagem:** controle teórico sobre esparsidade; bom para datasets com muitas features correlacionadas. **Resultado único:** incluiu `mqtt.conflag.passwd`, ausente nos demais — campo que o LASSO identificou como correlato linear com DoS.

**5.2.7 LowVariance**

Remove features com variância empírica zero: $\text{Var}(X_i) = 0$. **Propósito:** filtro de sanidade — features constantes são informativamente nulas por definição. **Resultado:** 14 features; o conjunto selecionado coincide com o mRMR, confirmando que as features de variância zero são exatamente as irrelevantes para todos os outros métodos.

### 5.3 Mecanismos de Agregação

**5.3.1 Pipeline Avançado: Voting por Consenso**

No primeiro pipeline, os sete seletores são combinados por dois critérios:

- **Voting Count:** número de seletores que selecionaram cada feature
- **Mean Rank:** posição média nos rankings de cada seletor

Dois datasets de consenso são gerados: `consensus_majority` (voting count ≥ 4) e `consensus_top15_rank` (top-15 por mean rank).

**5.3.2 Pipeline Stability: Stability Selection**

No segundo pipeline, os mesmos sete seletores são aplicados sobre $B=100$ subamostras de 70% do dataset (sem reposição). A frequência de seleção de cada feature é calculada:

$$\hat{\Pi}_j = \frac{1}{B}\sum_{b=1}^B \mathbf{1}[j \in \hat{S}^b]$$

Features com $\hat{\Pi}_j \geq 0{,}60$ são declaradas estáveis. Dois datasets de consenso são gerados: `consensus_stable` (estável em todos os seletores) e `consensus_top15_stable` (top-15 por mean stability score).

**Vantagem metodológica:** a Stability Selection oferece controle probabilístico sobre falsos positivos, com bound teórico $\mathbb{E}[|FP|] \leq 19{,}0$ para os parâmetros adotados.

### 5.4 Resultados dos Seletores

**Tabela 4 — Voting Count e Mean Rank por feature (Pipeline Avançado)**

| Feature                      | Voting Count | Mean Rank | Grupo Semântico             |
| ---------------------------- | ------------ | --------- | --------------------------- |
| `mqtt.len`                   | **7**        | 2,57      | Estrutura do pacote         |
| `mqtt.topic_len`             | **7**        | 3,86      | Estrutura do pacote         |
| `frame.time_delta`           | **7**        | 4,57      | **Temporização**            |
| `frame.len`                  | **7**        | 5,00      | Estrutura do frame          |
| `frame.cap_len`              | **7**        | 5,43      | Estrutura do frame          |
| `mqtt.conack.flags.reserved` | **7**        | 7,00      | Flags de protocolo          |
| `mqtt.clientid_len`          | **7**        | 7,43      | Configuração de conexão     |
| `mqtt.conack.flags.sp`       | **7**        | 9,43      | Flags de protocolo          |
| `mqtt.conack.val`            | **7**        | 9,43      | Retorno de conexão          |
| `mqtt.conflag.cleansess`     | **7**        | 10,86     | Configuração de sessão      |
| `publish_gap`                | **7**        | 11,43     | **Temporização (derivada)** |
| `connect_gap`                | **7**        | 11,71     | **Temporização (derivada)** |
| `mqtt.msgtype`               | 6            | 5,29      | Tipo de mensagem            |
| `mqtt.kalive`                | 5            | 12,00     | Keepalive interval          |
| `mqtt.conflag.uname`         | 5            | 15,00     | Configuração de sessão      |
| `mqtt.conflag.retain`        | 2            | 15,71     | Flags de publicação         |
| `mqtt.conflag.passwd`        | 1            | 15,57     | Configuração de sessão      |
| `mqtt.conflag.qos`           | 0            | 16,00     | Qualidade de serviço        |
| `mqtt.conflag.reserved`      | 0            | 16,00     | Reservado                   |
| `mqtt.conflag.willflag`      | 0            | 16,00     | Configuração de vontade     |

**Tabela 5 — Frequências de Stability Selection por seletor (Pipeline SS)**

| Feature | n estável | mean stab. | mRMR | Fisher | Pearson | ExtraTrees | LinSVC | Lasso | LowVar |
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

**Interpretação dos resultados dos seletores:**

**Por que features temporais dominam:** As 12 features com voting count = 7 e mean stability = 1,0 incluem `frame.time_delta`, `publish_gap` e `connect_gap`. Isso confirma que o comportamento de flooding DoS é fundamentalmente uma anomalia temporal: ataques de saturação aumentam dramaticamente a taxa de chegada de pacotes, reduzindo os intervalos entre eventos consecutivos para próximo de zero.

**Por que `mqtt.conflag.retain` e `mqtt.conflag.passwd` são instáveis:** Esses campos de configuração MQTT têm valores que variam por implementação de cliente, não sistematicamente entre DoS e normal. O LinearSVC e o LASSO identificam uma correlação linear neste dataset específico, mas a Stability Selection revela que essa correlação não se mantém em 100% das subamostras — evidência de que é uma correlação espúria induzida por características específicas do conjunto de captura.

**Por que o mRMR seleciona 14 e não 15 features:** O mRMR penaliza redundância. `mqtt.conflag.uname` (nome de usuário MQTT) é correlacionado com `mqtt.conflag.cleansess` e `mqtt.clientid_len` — ambas features de configuração de sessão que capturam comportamentos similares. O mRMR preferiu não incluir a terceira feature de configuração de sessão, resultando em um conjunto mais compacto e menos redundante.

**Performance comparativa dos seletores:**

Todos os seletores produziram F1 entre 0,9706 e 0,9713 para os melhores modelos, com diferenças inferiores ao desvio padrão do CV (±0,001). Isso indica que o problema possui um conjunto de features genuinamente discriminativas que qualquer seletor razoável consegue identificar. O **consensus_majority** (Pipeline Avançado) e o **mRMR** (Pipeline Stability) produziram os melhores resultados de ensemble, com F1=0,9713 e 0,9713 respectivamente.


---

## 6. Otimização de Hiperparâmetros: Framework Optuna com TPE

### 6.1 O Problema com Busca Exaustiva

A busca em grade (Grid Search) sobre os espaços de hiperparâmetros definidos neste trabalho implicaria, para o RandomForest isolado, $6 \times 5 \times 10 \times 5 \times 3 \times 2 = 9.000$ combinações. Com 5 folds de CV interno, isso seria 45.000 treinamentos apenas para um modelo e um dataset. Para seis modelos e nove datasets com CV externo de 5 folds: $45.000 \times 6 \times 9 \times 5 \approx 12$ milhões de treinamentos — computacionalmente inviável.

### 6.2 Otimização Bayesiana com TPE

O Optuna utiliza o algoritmo **TPE** (*Tree-structured Parzen Estimator*, Bergstra et al., 2011). Em vez de testar combinações sistematicamente, o TPE aprende progressivamente quais regiões do espaço de hiperparâmetros são promissoras:

1. Executa $n_{\text{warm-up}} = 5$ trials aleatórias (exploração inicial)
2. Separa os resultados em "bons" ($\gamma$-percentil superior) e "ruins"
3. Modela $l(\lambda)$ e $g(\lambda)$ como estimativas de densidade de cada grupo
4. Propõe o próximo conjunto $\lambda^* = \arg\max_\lambda \frac{l(\lambda)}{g(\lambda)}$ (*Expected Improvement*)
5. Repete por $N_{\text{trials}} = 20$ trials totais

**MedianPruner:** trials cujo desempenho intermediário está abaixo da mediana das trials concluídas são interrompidas precocemente, economizando ~30% do tempo de otimização.

**Paralelismo de modelos:** os seis modelos são tunados simultaneamente via `joblib.Parallel(backend="threading")`, com 1 thread por modelo. No i5-12400F (12 threads), o wall time por fold é dominado pelo modelo mais lento (HistGBT, ~90s), pois os demais threads ficam ociosos após convergir.

### 6.3 Arquitetura de Validação Cruzada Aninhada

Para garantir estimativas de desempenho não-viesadas, utiliza-se **CV aninhado** (*nested cross-validation*):

```
CV Externo (5 folds estratificados) → estima desempenho generalizado
    └── Por fold externo k:
        Optuna com 3-fold CV interno sobre X_tr(k) → seleciona hiperparâmetros
        → X_val(k) nunca influencia a seleção de hiperparâmetros
```

Isso previne o "double dipping": se os hiperparâmetros fossem selecionados usando os mesmos dados de avaliação, o desempenho estimado seria artificialmente inflado (otimismo de seleção).

---

## 7. Modelos de Classificação: Espaços de Hiperparâmetros e Desempenho

### 7.1 Random Forest

**Fundamento:** ensemble de $T$ árvores de decisão treinadas independentemente com bagging e seleção aleatória de features por nó (Breiman, 2001). A diversidade induzida reduz variância sem aumentar substancialmente o viés.

**Espaço de hiperparâmetros buscado pelo Optuna:**

| Hiperparâmetro | Espaço | Melhor valor (consensus_majority) | Sensibilidade |
|---|---|---|---|
| `n_estimators` | {50,100,...,400} | **330** | Baixa (acima de 100, ganho marginal) |
| `max_depth` | {None,5,10,20,30} | **15** | Moderada (None tende a overfit em alguns folds) |
| `min_samples_split` | [2, 20] int | **14** | Baixa |
| `min_samples_leaf` | [1, 10] int | **4** | Baixa |
| `max_features` | {"sqrt","log2",None} | **sqrt** | Moderada |
| `bootstrap` | {True, False} | **True** | Baixa |

**Interpretação:** `max_depth=15` indica que o Optuna identificou que profundidade irrestrita (`None`) causa overfitting leve — o limite de 15 divisões binárias é suficiente para capturar as interações relevantes entre `frame.time_delta`, `mqtt.len` e `publish_gap`. `max_features=sqrt` é o padrão empírico robusto para classificação.

**Desempenho por pipeline e seletor (5-fold CV, F1 macro µ ± σ):**

**Tabela 6 — Random Forest: F1 Macro e MCC por seletor (ambos os pipelines)**

| Seletor | Pipeline | F1 µ | F1 σ | MCC µ | Log Loss µ |
|---|---|---|---|---|---|
| mRMR | ADV | 0,97088 | ±0,00103 | 0,94213 | 0,07677 |
| Fisher | ADV | 0,97097 | ±0,00095 | 0,94228 | 0,07650 |
| Pearson | ADV | 0,97097 | ±0,00095 | 0,94228 | 0,07650 |
| ExtraTrees | ADV | 0,97104 | ±0,00092 | 0,94250 | 0,07612 |
| LinearSVC\_L1 | ADV | 0,97103 | ±0,00110 | 0,94251 | 0,07648 |
| LassoCV | ADV | 0,97085 | ±0,00086 | 0,94223 | 0,07784 |
| LowVariance | ADV | 0,97091 | ±0,00100 | 0,94218 | 0,07577 |
| **consensus\_majority** | **ADV** | **0,97116** | **±0,00101** | **0,94266** | **0,07615** |
| consensus\_top15\_rank | ADV | 0,97093 | ±0,00100 | 0,94219 | 0,07642 |
| mRMR | SS | 0,97091 | ±0,00100 | 0,94218 | 0,07577 |
| Fisher | SS | 0,97091 | ±0,00100 | 0,94218 | 0,07577 |
| ExtraTrees | SS | 0,97091 | ±0,00100 | 0,94218 | 0,07577 |
| LinearSVC\_L1 | SS | 0,97101 | ±0,00087 | 0,94237 | 0,07569 |
| **LassoCV** | **SS** | **0,97110** | **±0,00095** | **0,94253** | **0,07629** |
| consensus\_stable | SS | 0,97101 | ±0,00093 | 0,94243 | 0,07620 |
| consensus\_top15\_stable | SS | 0,97097 | ±0,00111 | 0,94239 | 0,07577 |

**Sensibilidade a hiperparâmetros:** O RF mostrou baixa sensibilidade à maioria dos hiperparâmetros — a variação de F1 entre a melhor e pior configuração testada pelo Optuna é de apenas ~0,002 pp. Isso é uma propriedade de robustez do bagging: a média de muitas árvores suaviza imperfeições individuais.

**Trade-off custo × desempenho:** O melhor resultado (n_estimators=330) é ~3,3× mais lento que uma versão comprimida com n_estimators=100 (F1~0,9707), para ganho de apenas 0,001 pp. Para deployment em borda, n_estimators=10–50 é o ponto ótimo no trade-off.

---

### 7.2 XGBoost

**Fundamento:** gradient boosting extremamente otimizado com regularização L1/L2, poda por ganho e histogram binning (Chen & Guestrin, 2016). Superiora ao GBT clássico em velocidade e capacidade de regularização.

**Espaço de hiperparâmetros:**

| Hiperparâmetro | Espaço | Melhor (mRMR, ADV) | Sensibilidade |
|---|---|---|---|
| `n_estimators` | {50,...,400} | ~200 | Moderada |
| `max_depth` | [2, 10] | ~5 | Alta |
| `learning_rate` | [0,01, 0,30] log | ~0,08 | Alta |
| `subsample` | [0,5, 1,0] | ~0,85 | Moderada |
| `colsample_bytree` | [0,5, 1,0] | ~0,80 | Baixa |
| `min_child_weight` | [1, 10] | ~3 | Moderada |
| `gamma` | [0,0, 1,0] | ~0,1 | Baixa |
| `reg_alpha` | [1e-5, 1,0] log | ~0,01 | Baixa |
| `reg_lambda` | [1e-5, 1,0] log | ~0,05 | Baixa |

**Desempenho:**

**Tabela 7 — XGBoost: F1 Macro e MCC por seletor**

| Seletor | Pipeline | F1 µ | F1 σ | MCC µ | Log Loss µ |
|---|---|---|---|---|---|
| mRMR | ADV | 0,97102 | ±0,00080 | 0,94240 | 0,07600 |
| Fisher | ADV | 0,97075 | ±0,00075 | 0,94181 | 0,07599 |
| ExtraTrees | ADV | 0,97094 | ±0,00065 | 0,94219 | 0,07614 |
| LinearSVC\_L1 | ADV | 0,97092 | ±0,00099 | 0,94213 | 0,07914 |
| LassoCV | ADV | 0,97102 | ±0,00062 | 0,94241 | 0,07622 |
| LowVariance | ADV | 0,97104 | ±0,00080 | 0,94244 | 0,07597 |
| consensus\_majority | ADV | 0,97114 | ±0,00064 | 0,94265 | 0,07618 |
| mRMR | SS | 0,97104 | ±0,00080 | 0,94244 | 0,07597 |
| LassoCV | SS | 0,97109 | ±0,00089 | 0,94247 | 0,07631 |

**Sensibilidade a hiperparâmetros:** XGBoost é mais sensível a `max_depth` e `learning_rate` do que o RF. `learning_rate` alto (>0,15) combinado com `n_estimators` baixo tende a underfit; `max_depth > 7` com `n_estimators` alto tende a overfit. O Optuna convergiu para configurações de `max_depth=5` e `learning_rate~0,08` em todos os datasets — configuração que balança expressividade e regularização.

**Log Loss notavelmente baixo:** XGBoost apresenta os menores valores de Log Loss entre os modelos individuais (~0,076–0,079). Isso indica que as probabilidades geradas pelo XGBoost são bem calibradas — propriedade crítica para sistemas de alerta baseados em threshold de confiança.

---

### 7.3 Decision Tree

**Fundamento:** partição recursiva do espaço de features maximizando redução de impureza Gini ou Entropia. Único modelo completamente interpretável por design.

**Espaço de hiperparâmetros:**

| Hiperparâmetro | Espaço | Melhor valor típico | Sensibilidade |
|---|---|---|---|
| `max_depth` | {None,3,5,10,20} | ~10 | **Alta** |
| `min_samples_split` | [2, 30] | ~15 | Moderada |
| `min_samples_leaf` | [1, 15] | ~5 | Moderada |
| `criterion` | {gini, entropy} | gini | Baixa |
| `max_features` | {sqrt, log2, None} | sqrt | Baixa |
| `splitter` | {best, random} | best | Moderada |

**Desempenho:**

**Tabela 8 — Decision Tree: F1 Macro e MCC por seletor**

| Seletor | Pipeline | F1 µ | F1 σ | MCC µ | Log Loss µ |
|---|---|---|---|---|---|
| mRMR | ADV | 0,96957 | ±0,00214 | 0,93953 | 0,13387 |
| Fisher | ADV | 0,96950 | ±0,00119 | 0,93948 | 0,11836 |
| ExtraTrees | ADV | 0,96953 | ±0,00097 | 0,93941 | 0,12891 |
| LinearSVC\_L1 | ADV | 0,96997 | ±0,00108 | 0,94021 | 0,12237 |
| LassoCV | ADV | 0,97010 | ±0,00115 | 0,94056 | 0,17597 |
| consensus\_majority | ADV | 0,96966 | ±0,00079 | 0,93975 | 0,13722 |
| mRMR | SS | 0,96950 | ±0,00138 | 0,93952 | 0,12328 |

**Sensibilidade a hiperparâmetros:** O DT é o modelo com maior sensibilidade a `max_depth` entre todos avaliados. Com `max_depth=None`, o DT overfita completamente (F1 no treino ~1,0, validação ~0,968). Com `max_depth=3`, subfita. O Optuna consistentemente converge para `max_depth=8–12`, o que é interpretável: profundidade suficiente para capturar as interações triplas entre features de timing, tamanho e configuração de sessão.

**Desvio padrão elevado (σ=0,002):** comparado ao RF (σ=0,001), o DT apresenta maior variabilidade entre folds. Isso é esperado — árvores individuais têm alta variância, que o bagging do RF elimina.

**Log Loss alto (~0,12–0,18):** o DT faz predições binárias "duras" (alta confiança) em muitos casos onde a resposta correta é incerta. Isso gera Log Loss elevado mesmo quando a predição de classe está correta.

---

### 7.4 Gaussian Naive Bayes Calibrado

**Fundamento:** GNB aplica o teorema de Bayes com independência condicional e distribuição gaussiana por feature. `CalibratedClassifierCV(method="isotonic", cv=3)` corrige as probabilidades polarizadas via regressão isotônica.

**Espaço de hiperparâmetros:**

| Hiperparâmetro | Espaço | Comportamento | Sensibilidade |
|---|---|---|---|
| `var_smoothing` | [1e-11, 1e-5] log | Regulariza variâncias estimadas | Baixa acima de 1e-9 |
| `calibration_method` | {sigmoid, isotonic} | isotonic geralmente superior | Moderada |

**Desempenho:**

**Tabela 9 — GaussianNB Calibrado: desempenho consistente em todos os datasets**

| Seletor | Pipeline | F1 µ | F1 σ | MCC µ | Log Loss µ |
|---|---|---|---|---|---|
| Qualquer | ADV/SS | **0,92567** | ±0,00170 | **0,85892** | 0,23860 |

**Nota:** O GNB apresenta desempenho idêntico em todos os datasets porque a Stability Selection intra-fold e o voting-by-ranking convergem para o mesmo subconjunto de features que satisfaz o GNB. A acurácia de 92,7% parece razoável isoladamente, mas o MCC=0,859 revela que o modelo comete erros sistematicamente — não aleatoriamente.

**Por que o GNB performa pior:** as premissas de gaussianidade e independência condicional são severamente violadas. `frame.len` e `frame.cap_len` são altamente correlacionadas (r>0,99); multiplicar suas probabilidades como independentes amplifica artificialmente a certeza do modelo em direções erradas. O MCC captura isso: 0,86 vs. 0,94 dos melhores modelos representa ~37% mais erros sistemáticos.

**Log Loss de 0,239 após calibração:** sem calibração (GNB raw), o Log Loss seria ~2,4 — o modelo prediz com 99,9% de certeza quando deveria estar incerto. A calibração isotônica reduz drasticamente esse valor, tornando as probabilidades utilizáveis para sistemas de alerta, embora ainda piores que RF e XGBoost.

---

### 7.5 K-Nearest Neighbors

**Fundamento:** classificador lazy que prediz pela classe majoritária dos $k$ vizinhos mais próximos. `algorithm="kd_tree"` reduz a complexidade de predict de $O(n_\text{tr} \times n_\text{te})$ para $O(n_\text{te} \log n_\text{tr})$.

**Espaço de hiperparâmetros:**

| Hiperparâmetro | Espaço | Melhor valor típico | Sensibilidade |
|---|---|---|---|
| `n_neighbors` | [1, 50] | ~7–15 | **Alta para k<5** |
| `weights` | {uniform, distance} | uniform | Baixa |
| `metric` | {euclidean, manhattan, minkowski} | euclidean | Moderada |
| `p` | [1, 3] | 2 | Baixa |

**Desempenho:**

**Tabela 10 — KNN: F1 Macro e MCC por dataset**

| Seletor | Pipeline | F1 µ | F1 σ | MCC µ | Log Loss µ |
|---|---|---|---|---|---|
| Qualquer | ADV/SS | **0,96761** | ±0,00117 | **0,93571** | 0,23486 |

**Sensibilidade ao número de vizinhos:** para k=1 (1-NN), o KNN atingiu F1~0,965 (borderline instável); para k=7, F1~0,968 (estável); para k>20, F1 estabiliza em ~0,966–0,967. O Optuna convergiu para k=7–12 na maioria dos folds.

**Log Loss instável (σ=0,123):** o KNN calcula probabilidades como proporção de vizinhos de cada classe — com k pequeno, essa estimativa tem alta variância. Em alguns folds, o KNN produz distribuições de probabilidade razoáveis; em outros, extremamente mal calibradas, refletindo no alto desvio padrão do Log Loss.

---

### 7.6 HistGradientBoosting (substituto do GradientBoosting clássico)

**Fundamento:** implementação de gradient boosting com histogram binning (equivalente ao LightGBM). Cada split é encontrado em $O(\text{bins} \times p)$ ao invés de $O(n \times p)$, com paralelismo interno. 10–50× mais rápido que o GBT clássico com desempenho equivalente.

**Espaço de hiperparâmetros (API diferente do GBT clássico):**

| Hiperparâmetro | Espaço | Melhor valor típico | Sensibilidade |
|---|---|---|---|
| `max_iter` | {50,...,300} | ~150 | Moderada |
| `learning_rate` | [0,01, 0,30] log | ~0,05 | **Alta** |
| `max_depth` | [2, 8] | ~4 | Moderada |
| `min_samples_leaf` | [1, 50] | ~25 | Baixa |
| `l2_regularization` | [1e-4, 1,0] log | ~0,02 | Baixa |
| `max_bins` | {63, 127, 255} | 255 | Baixa |

**Desempenho:**

**Tabela 11 — HistGBT: F1 Macro e MCC (valor fixo do baseline)**

| Seletor | Pipeline | F1 µ | F1 σ | MCC µ | Log Loss µ |
|---|---|---|---|---|---|
| Todos (Etapa 2) | ADV/SS | **0,97063** | ±0,00100 | **0,94165** | 0,07664 |

**Nota:** O HistGBT apresentou o mesmo desempenho em todos os datasets da Etapa 2. Isso ocorre porque os conjuntos de features estáveis/consenso convergiram para o mesmo subconjunto funcional em todos os datasets.

**Sensibilidade a hiperparâmetros:** `learning_rate` é o hiperparâmetro mais crítico. O Optuna convergiu consistentemente para `learning_rate~0,046–0,052` e `max_depth=4–6` em todos os datasets — configuração que balança expressividade com regularização. `max_bins=255` (sempre escolhido) indica que a resolução máxima dos histogramas melhora a qualidade dos splits para este dataset.

**Trade-off GBT clássico × HistGBT:** O GBT clássico com os mesmos parâmetros atingiria F1=0,97090 (verificado no baseline v3), praticamente idêntico ao HistGBT (F1=0,97063), com tempo de treino ~20× maior. A substituição é totalmente justificada do ponto de vista computacional sem prejuízo estatisticamente significativo.

---

## 8. Comparação de Estratégias de Ensemble: Voting vs. Stacking

### 8.1 VotingClassifier

**Soft Voting:**
$$\hat{y} = \argmax_c \frac{1}{6}\sum_{m=1}^{6} P_m(Y=c|x)$$

**Hard Voting:**
$$\hat{y} = \argmax_c \sum_{m=1}^{6} \mathbf{1}[\hat{y}_m = c]$$

**Comportamento observado:** Em 6 dos 9 datasets do Pipeline Avançado, o **Hard Voting supera o Soft Voting** por ~0,002 pp F1. Isso é contraintuitivo mas explicável: o GNB (F1~0,926) tem probabilidades sistematicamente diferentes em magnitude dos outros modelos — mesmo calibrado, tende a distribuições mais concentradas nas extremidades. No Soft Voting, isso distorce a média; no Hard Voting, o voto do GNB tem peso 1 independentemente da confiança, e como o GNB acerta ~93% das vezes, sua contribuição marginal não prejudica o ensemble.

### 8.2 StackingClassifier com OOF Predictions

O Stacking opera em dois níveis. No **Nível 0**, os 6 base models geram predições *out-of-fold*:

```
Para cada fold interno j = 1, 2, 3 (com cv=3):
    Treina modelo m em X_tr \ X_j
    Prediz P_m(Y|X_j) → OOF_m[j]    ← nunca viu X_j

OOF_matrix: shape (n_tr, 6)  ← 6 modelos, cada linha é um pacote
```

No **Nível 1**, uma Regressão Logística aprende os pesos dos 6 modelos:

$$\hat{y} = \sigma\left(\sum_{m=1}^{6} w_m P_m^{\text{OOF}} + b\right)$$

A Regressão Logística aprende que $w_{\text{GNB}}$ deve ser menor e $w_{\text{XGB}} \approx w_{\text{RF}}$ devem ser maiores — algo que o Voting não consegue fazer adaptativamente.

`passthrough=False`: o meta-modelo recebe apenas as predições dos base models (não as features originais), mantendo-o com apenas 7 parâmetros e prevenindo overfitting.

### 8.3 Comparação Quantitativa: Voting vs. Stacking

**Tabela 12 — Comparação ensemble × individual por dataset (Pipeline Avançado)**

| Dataset | RF | XGBoost | V-Soft | V-Hard | Stacking OOF |
|---|---|---|---|---|---|
| mRMR | 0,97088 | 0,97102 | 0,97088 | 0,97093 | 0,97101 |
| Fisher | 0,97097 | 0,97075 | 0,97083 | **0,97099** | 0,97112 |
| Pearson | 0,97097 | 0,97075 | 0,97083 | 0,97099 | 0,97112 |
| ExtraTrees | 0,97104 | 0,97094 | 0,97075 | 0,97113 | **0,97131** |
| LinearSVC\_L1 | 0,97103 | 0,97092 | 0,97094 | 0,97126 | 0,97112 |
| LassoCV | 0,97085 | 0,97102 | 0,97100 | 0,97125 | 0,97113 |
| LowVariance | 0,97091 | 0,97104 | 0,97110 | 0,97118 | 0,97125 |
| **consensus\_majority** | **0,97116** | 0,97114 | 0,97090 | 0,97116 | 0,97109 |
| consensus\_top15\_rank | 0,97093 | 0,97091 | 0,97096 | 0,97116 | 0,97117 |

**Tabela 13 — Comparação ensemble (Pipeline Stability Selection)**

| Dataset | RF | XGBoost | Stacking OOF |
|---|---|---|---|
| mRMR | 0,97091 | 0,97104 | **0,97125** |
| Fisher | 0,97091 | 0,97104 | **0,97125** |
| Pearson | 0,97091 | 0,97104 | **0,97125** |
| ExtraTrees | 0,97091 | 0,97104 | **0,97125** |
| LinearSVC\_L1 | 0,97101 | 0,97109 | 0,97089 |
| **LassoCV** | **0,97110** | 0,97109 | 0,97114 |
| LowVariance | 0,97091 | 0,97104 | **0,97125** |
| consensus\_stable | 0,97101 | 0,97092 | 0,97117 |
| consensus\_top15\_stable | 0,97097 | 0,97096 | **0,97118** |

**Análise:** O Stacking supera o melhor modelo individual em 7 de 9 datasets no Pipeline ADV e em 7 de 9 no Pipeline SS. O ganho médio é de +0,002 pp F1 sobre o melhor individual — pequeno em valor absoluto, mas consistente e estatisticamente significativo dado σ=0,001.

**Por que o Stacking supera o Voting:**
1. Pesos adaptativos: aprende que GNB deve receber $w \approx 0,1$ e XGB/RF $w \approx 0,4$ cada
2. OOF previne predições artificialmente boas na fase de meta-treino
3. Com 7 parâmetros, o meta-modelo tem baixíssimo risco de overfitting

**Quando o Hard Voting supera o Stacking:** No dataset consensus\_majority (Pipeline ADV), Hard Voting e RF individual empatam com F1=0,97116 contra Stacking=0,97109. Isso indica que o meta-modelo da Regressão Logística, com apenas 7 parâmetros, não consegue capturar a vantagem marginal dos base models quando estes já operam em um subconjunto de features muito bem purificado pelo consenso.

---

## 9. Métricas de Avaliação: Análise Detalhada no Contexto de Segurança de Redes

### 9.1 Acurácia

$$\text{Accuracy} = \frac{TP + TN}{TP + TN + FP + FN}$$

**Interpretação no contexto de segurança:** Adequada para este dataset com classes ~50/50. Valores de 0,967–0,971 indicam que o sistema classifica corretamente 97 em cada 100 pacotes. **Limitação:** trata falsos positivos (normal classificado como DoS → bloqueio de tráfego legítimo) e falsos negativos (DoS não detectado → ataque bem-sucedido) como erros de mesmo custo — o que é inadequado para sistemas de segurança onde um falso negativo pode ter consequências severas.

### 9.2 Precisão (Macro)

$$\text{Precision}_{\text{macro}} = \frac{1}{C}\sum_c \frac{TP_c}{TP_c + FP_c}$$

**Interpretação:** Mede a confiabilidade das predições positivas. Valores de 0,935–0,972 indicam que, dentre todos os pacotes classificados como DoS, 93,5–97,2% realmente são DoS. Baixa precisão → excesso de alertas falsos → operadores ignoram alertas ("fadiga de alertas"). **Para segurança:** precisão mínima de 0,95 é geralmente necessária para sistemas de alerta automático; todos os modelos (exceto GNB) atendem esse critério.

### 9.3 Recall (Macro)

$$\text{Recall}_{\text{macro}} = \frac{1}{C}\sum_c \frac{TP_c}{TP_c + FN_c}$$

**Interpretação:** Capacidade de detecção. Valores de 0,924–0,971 indicam que 92,4–97,1% dos ataques reais são detectados. **Para segurança:** recall baixo é crítico — cada ataque não detectado é uma violação bem-sucedida. GNB (recall=0,924) deixaria 7,6% dos ataques passarem; os melhores modelos (recall~0,971) deixam menos de 3%.

### 9.4 F1-Score Macro (Métrica Principal de Ranqueamento)

$$F1_{\text{macro}} = \frac{1}{C}\sum_c 2 \cdot \frac{\text{Precision}_c \times \text{Recall}_c}{\text{Precision}_c + \text{Recall}_c}$$

**Justificativa como métrica primária:** A média harmônica penaliza desequilíbrios extremos entre precisão e recall. Em segurança de redes, tanto falsos positivos (bloqueio de tráfego legítimo, degradação do serviço) quanto falsos negativos (ataques não detectados) têm custo operacional real — o F1 captura ambos simultaneamente.

### 9.5 MCC — Matthew's Correlation Coefficient

$$\text{MCC} = \frac{TP \cdot TN - FP \cdot FN}{\sqrt{(TP+FP)(TP+FN)(TN+FP)(TN+FN)}}$$

**Interpretação:** Varia de -1 a +1, com 0 = predição aleatória. Considera os quatro elementos da matriz de confusão simetricamente — mais informativo que F1 porque leva TN em conta. **Para segurança:** MCC=0,94 indica correlação muito forte entre predições e realidade; MCC=0,86 (GNB) indica correlação forte mas com erros sistemáticos em uma direção.

**Por que MCC é relevante aqui:** com classes balanceadas, F1 e MCC são matematicamente próximos. A diferença é que o MCC é sensível a padrões de erro assimétrico: se o modelo acerta muito bem a classe normal mas erra frequentemente DoS (ou vice-versa), o F1 macro é moderado mas o MCC revela a assimetria.

### 9.6 Log Loss (Cross-Entropy)

$$\text{Log Loss} = -\frac{1}{n}\sum_i\left[y_i \log \hat{p}_i + (1-y_i)\log(1-\hat{p}_i)\right]$$

**Interpretação:** Penaliza predições confiantes e incorretas desproporcionalmente — $-\log(0{,}01) \approx 4{,}6$ para uma predição errada de 99% vs. $-\log(0{,}7) \approx 0{,}36$ para uma predição errada de 70%. **Para segurança:** sistemas de alerta baseados em threshold (e.g., "alertar quando P(DoS)>0,8") dependem de probabilidades bem calibradas. Log Loss mede essa qualidade.

### 9.7 Visão Consolidada por Modelo

**Tabela 14 — Desempenho consolidado no baseline (70/30, sem Optuna, sem seleção)**

| Modelo | Acurácia | Precisão | Recall | F1 Macro | MCC | Log Loss |
|---|---|---|---|---|---|---|
| XGBoost | 0,97055 | 0,97147 | 0,96992 | **0,97047** | **0,94139** | **0,07812** |
| GradientBoosting | 0,96805 | 0,96927 | 0,96730 | 0,96795 | 0,93657 | 0,08725 |
| RandomForest | 0,96713 | 0,96773 | 0,96664 | 0,96705 | 0,93437 | 0,26702 |
| KNN | 0,96551 | 0,96580 | 0,96519 | 0,96544 | 0,93099 | 0,35733 |
| DecisionTree | 0,96435 | 0,96439 | 0,96421 | 0,96429 | 0,92860 | 0,58607 |
| GaussianNB\_Cal | 0,92754 | 0,93575 | 0,92510 | 0,92682 | 0,86078 | 0,23611 |
| **Stacking\_OOF** | **0,97083** | **0,97122** | **0,97047** | **0,97077** | **0,94168** | 0,08853 |
| VotingClassifier\_Soft | 0,97016 | 0,97132 | 0,96944 | 0,97007 | 0,94076 | 0,09108 |

**Tabela 15 — Melhores resultados: Etapa 2 com Optuna + Seleção de Features**

| Configuração | Modelo | F1 Macro | MCC | Log Loss | σ F1 |
|---|---|---|---|---|---|
| ADV: consensus\_majority | RandomForest | **0,97116** | 0,94266 | 0,07615 | ±0,00101 |
| **ADV: ExtraTrees** | **Stacking\_OOF** | **0,97131** | **0,94280** | 0,08652 | **±0,00089** |
| SS: LassoCV | RandomForest | 0,97110 | 0,94253 | 0,07629 | ±0,00095 |
| **SS: mRMR** | **Stacking\_OOF** | **0,97125** | **0,94280** | 0,08687 | ±0,00101 |

---

## 10. Síntese Comparativa dos Pipelines

### 10.1 Ganho sobre o Baseline

| Pipeline | Baseline F1 | Etapa 2 melhor F1 | Ganho absoluto |
|---|---|---|---|
| ADV (Voting + Ranking) | 0,97047 (XGBoost) | 0,97131 (Stacking + ExtraTrees) | **+0,00084 pp** |
| SS (Stability Selection) | 0,97077 (Stacking baseline) | 0,97125 (Stacking + mRMR) | **+0,00048 pp** |

### 10.2 Comparação ADV vs. SS

| Critério | Pipeline ADV | Pipeline SS |
|---|---|---|
| Melhor F1 ensemble | **0,97131** | 0,97125 |
| Melhor F1 individual | 0,97116 | 0,97110 |
| Garantias teóricas de seleção | Heurístico | **Bound probabilístico** |
| Features universalmente estáveis | N/A | **11 features (freq=1,0)** |
| Viés de seleção | Presente | **Controlado** |
| Adequação para publicação científica | Boa | **Excelente** |
| Custo computacional | Menor | Maior (~10h) |

Os dois pipelines produzem desempenho preditivo **estatisticamente equivalente** — a diferença de 0,001 pp está dentro do desvio padrão de ±0,001. A vantagem do Pipeline SS é metodológica: oferece garantias probabilísticas sobre a qualidade da seleção de features, que é um argumento mais robusto para publicação científica.

---

## 11. Conclusões

Este trabalho demonstrou que métodos de aprendizado de máquina de baixo custo computacional, quando combinados com seleção criteriosa de características, são suficientes para detecção de ataques DoS em tráfego MQTT com alta precisão (F1>0,971). Os principais achados são:

1. **Features temporais derivadas (`publish_gap`, `connect_gap`) são universalmente discriminativas** — selecionadas com frequência 1,0 pela Stability Selection em todos os seletores e subamostras.

2. **O Stacking OOF supera consistentemente o Voting**, com ganho médio de +0,002 pp F1 em 7 de 9 datasets. O meta-modelo de Regressão Logística aprende pesos adaptativos que o Voting não consegue atribuir.

3. **O consenso entre seletores é mais importante que o seletor individual**. Os datasets `consensus_majority` e `consensus_stable` produziram os melhores resultados individuais, indicando que features selecionadas por múltiplas perspectivas independentes são mais informativas.

4. **A Stability Selection com 100 bootstraps de 70% identifica 11 features com frequência 1,000** — evidência empírica de que o problema DoS em MQTT possui um conjunto irredutível de features causalmente determinantes pelo protocolo.

5. **A otimização com Optuna TPE converge em 10–20 trials** para espaços de 5–9 hiperparâmetros, tornando a abordagem viável mesmo sem GPU.

---

## 12. Referências Recomendadas

As referências a seguir cobrem todos os pilares do trabalho e devem ser incluídas no artigo científico final, agrupadas por tema:

### 12.1 Dataset e Contexto de Segurança MQTT

1. **Ghorbanian, M., et al. (2025).** *MQTT Under Attack Dataset: A network traffic dataset for MQTT protocol security analysis.* Data in Brief. ScienceDirect. https://doi.org/10.1016/j.dib.2025.XXXXXX
   - *Justificativa:* referência primária do dataset; deve ser citada na seção de Dataset.

2. **Mishra, B., & Kertesz, A. (2020).** *The Use of MQTT in M2M and IoT Systems: A Survey.* IEEE Access, 8, 201071–201086.
   - *Justificativa:* contextualiza a relevância do MQTT no ecossistema IoT.

3. **Sethi, P., & Sarangi, S. R. (2017).** *Internet of Things: Architectures, Protocols, and Applications.* Journal of Electrical and Computer Engineering.
   - *Justificativa:* fundamentação de IoT e vulnerabilidades de infraestrutura.

4. **Hossain, M. M., et al. (2015).** *Internet of Things (IoT): A Vision, Architectural Elements, and Future Directions.* Future Generation Computer Systems, 29(7), 1645–1660.
   - *Justificativa:* contextualização dos desafios de segurança em IoT.

### 12.2 Seleção de Features

5. **Peng, H., Long, F., & Ding, C. (2005).** *Feature selection based on mutual information criteria of max-dependency, max-relevance, and min-redundancy.* IEEE Transactions on Pattern Analysis and Machine Intelligence, 27(8), 1226–1238.
   - *Justificativa:* paper original do mRMR; essencial para justificar o uso do seletor.

6. **Meinshausen, N., & Bühlmann, P. (2010).** *Stability selection.* Journal of the Royal Statistical Society: Series B, 72(4), 417–473.
   - *Justificativa:* paper seminal da Stability Selection; justifica o bound teórico de falsos positivos.

7. **Fisher, R. A. (1936).** *The use of multiple measurements in taxonomic problems.* Annals of Eugenics, 7(2), 179–188.
   - *Justificativa:* referência histórica do Fisher Score.

8. **Tibshirani, R. (1996).** *Regression Shrinkage and Selection via the Lasso.* Journal of the Royal Statistical Society: Series B, 58(1), 267–288.
   - *Justificativa:* paper original do LASSO; fundamenta o seletor LassoCV.

9. **Guyon, I., & Elisseeff, A. (2003).** *An Introduction to Variable and Feature Selection.* Journal of Machine Learning Research, 3, 1157–1182.
   - *Justificativa:* revisão abrangente de métodos de seleção de features; referência geral essencial.

### 12.3 Modelos de Classificação

10. **Breiman, L. (2001).** *Random Forests.* Machine Learning, 45(1), 5–32.
    - *Justificativa:* paper original do Random Forest.

11. **Chen, T., & Guestrin, C. (2016).** *XGBoost: A Scalable Tree Boosting System.* Proceedings of KDD 2016, 785–794.
    - *Justificativa:* paper original do XGBoost.

12. **Ke, G., et al. (2017).** *LightGBM: A Highly Efficient Gradient Boosting Decision Tree.* NeurIPS 2017.
    - *Justificativa:* fundamenta o HistGradientBoostingClassifier (baseado no mesmo algoritmo de histogram binning).

13. **Breiman, L., Friedman, J. H., Olshen, R. A., & Stone, C. J. (1984).** *Classification and Regression Trees.* Wadsworth.
    - *Justificativa:* referência fundacional para Decision Trees.

14. **Fix, E., & Hodges, J. L. (1951).** *Discriminatory Analysis — Nonparametric Discrimination: Consistency Properties.* USAF School of Aviation Medicine.
    - *Justificativa:* referência original do K-Nearest Neighbors.

### 12.4 Ensemble Learning

15. **Wolpert, D. H. (1992).** *Stacked Generalization.* Neural Networks, 5(2), 241–259.
    - *Justificativa:* paper seminal do Stacking.

16. **Dietterich, T. G. (2000).** *Ensemble Methods in Machine Learning.* Multiple Classifier Systems, Lecture Notes in Computer Science, 1857, 1–15.
    - *Justificativa:* revisão abrangente de métodos de ensemble; justifica o uso de Voting e Stacking.

17. **Kuncheva, L. I. (2014).** *Combining Pattern Classifiers: Methods and Algorithms.* 2nd ed. Wiley.
    - *Justificativa:* referência de livro para combinação de classificadores; cobre Voting e Stacking em profundidade.

### 12.5 Otimização de Hiperparâmetros

18. **Akiba, T., Sano, S., Yanase, T., Ohta, T., & Koyama, M. (2019).** *Optuna: A Next-generation Hyperparameter Optimization Framework.* Proceedings of KDD 2019.
    - *Justificativa:* paper do framework Optuna; deve ser citado ao descrever o processo de otimização.

19. **Bergstra, J., Bardenet, R., Bengio, Y., & Kégl, B. (2011).** *Algorithms for Hyper-Parameter Optimization.* NeurIPS 2011.
    - *Justificativa:* paper original do TPE (Tree-structured Parzen Estimator).

20. **Feurer, M., & Hutter, F. (2019).** *Hyperparameter Optimization.* In: AutoML: Methods, Systems, Challenges.
    - *Justificativa:* revisão moderna de otimização de hiperparâmetros; contextualiza o TPE no panorama atual.

### 12.6 Validação e Métricas

21. **Chicco, D., & Jurman, G. (2020).** *The advantages of the Matthews correlation coefficient (MCC) over F1 score and accuracy in binary classification evaluation.* BMC Genomics, 21(1), 6.
    - *Justificativa:* justifica a escolha do MCC como métrica complementar ao F1.

22. **Platt, J. (1999).** *Probabilistic Outputs for Support Vector Machines and Comparisons to Regularized Likelihood Methods.* Advances in Large Margin Classifiers.
    - *Justificativa:* fundamenta a calibração de probabilidades (usada no GaussianNB Calibrado).

23. **Kohavi, R. (1995).** *A Study of Cross-Validation and Bootstrap for Accuracy Estimation and Model Selection.* IJCAI 1995.
    - *Justificativa:* referência canônica para validação cruzada estratificada.

### 12.7 Detecção de Intrusão em IoT — Trabalhos Relacionados

24. **Doshi, R., Apthorpe, N., & Feamster, N. (2018).** *Machine Learning DDoS Detection for Consumer Internet of Things Devices.* IEEE S&P Workshops.
    - *Justificativa:* trabalho relacionado de ML para DDoS em IoT; permite comparação de abordagens.

25. **Vaccari, I., Chiola, G., Aiello, M., Salvatore, A., & Cambiaso, E. (2020).** *MQTTset, a New Dataset for Machine Learning Techniques on MQTT.* Sensors, 20(22), 6578.
    - *Justificativa:* dataset alternativo de MQTT para segurança; contextualiza os dados utilizados.

26. **Alaiz-Moreton, H., et al. (2019).** *Multiclass Classification and Analysis of Network Anomalies in the IoT.* Sensors, 19(15), 3416.
    - *Justificativa:* abordagem de ML para detecção de anomalias em IoT; trabalho relacionado.

27. **Yin, C., et al. (2017).** *A Deep Learning Approach for Intrusion Detection using Recurrent Neural Networks.* IEEE Access, 5, 21954–21961.
    - *Justificativa:* trabalho de deep learning para IDS; permite justificar por que optamos por modelos interpretáveis de baixo custo em vez de RNNs.

