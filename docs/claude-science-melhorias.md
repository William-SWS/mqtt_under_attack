# Briefing para análise: treino sem vazamento, seleção de modelos e dados de teste na inferência

Você vai analisar um projeto de pesquisa em detecção de ataques DoS em redes MQTT, com modelos clássicos de
aprendizado de máquina implantados num Raspberry Pi. Seu trabalho é **propor melhorias** em três frentes,
com justificativa, alternativas e o experimento que confirmaria cada proposta. **Não altere nenhum arquivo**:
este é um trabalho de análise e proposta. A autora implementa as mudanças depois, digitando o código ela
mesma (o repositório é organizado como um curso).

As três perguntas:

1. **Treino sem vazamento.** O que ainda vaza, ou pode vazar, no esquema de treino que está sendo refatorado?
   Como corrigir sem perder a comparabilidade com o artigo, quando isso for possível?
2. **Seleção de modelos para inferência.** O treino gera 42 configurações seletor × modelo (mais 7 de
   baseline; a autora fala em "mais de 50" contando variações). Só algumas cabem na bateria de testes de
   estresse no Raspberry Pi. Qual critério, e qual procedimento estatístico, escolhe as que vão para a
   inferência?
3. **Dados de teste na API de inferência.** Qual é a melhor forma de levar os dados de teste até a API, de
   modo que a medição de latência e de recursos meça o que deve medir e os dados sejam exatamente os do
   teste do treino?

Escreva em português do Brasil. Separe sempre **fato** (com o arquivo e, se possível, o número que o
sustenta) de **hipótese** (o que precisa de experimento). Quando puder verificar uma afirmação rodando
código só de leitura sobre os dados do repositório, verifique e diga como. Quando uma proposta mudar uma
decisão já registrada, diga qual (pelo número em `docs/decisions.md`) e por quê.

---

## 1. Onde estão as coisas

- **Repositório do projeto:** `/home/william/Projetos/mqtt_under_attack`
- **Pesquisa inicial sobre a nova API de inferência:** `/home/william/Documentos/inference/`
  (`plano_metodologico_edge.md`, `dicionario_metricas_inferencia.csv` e o esboço de código `edge_bench/`)

## 2. O projeto hoje

### Dataset

- *MQTT Under Attack Dataset*, subconjunto DoS: `data/raw/MQTT Under Attack Dataset/DoS.csv`.
  94.625 pacotes capturados no Wireshark, 67 colunas, rótulo `type` com 49.111 `normal` e 45.514 `DoS`.
  O CSV vem ordenado por `frame.time_epoch`.
- A limpeza remove 46 colunas (identificadores, timestamps absolutos, IP/MAC, portas TCP, campos MQTT
  textuais, de sessão, compostos ou quase vazios) e deixa **20 preditoras**. Somadas a dois gaps temporais
  (`publish_gap`, `connect_gap`), formam as **22 features candidatas**.
- Fatos medidos na refatoração, que importam para as suas perguntas:
  - Os nulos são **estruturais**: o campo não existe naquele pacote. `mqtt.msgtype` falta em **99,0% do
    `normal`** e em **14,2% do `DoS`**. Só 491 dos 49.111 pacotes normais são MQTT. Uma parte grande da
    separação pode vir de "o pacote é MQTT?". A autora registrou isso como pergunta de pesquisa em aberto.
  - `frame.cap_len` é idêntico a `frame.len` em 100% das linhas, e o seletor LowVariance mantém as duas.
  - `mqtt.dupflag` está entre os "quase vazios", mas tem 59,4% de nulos, a mesma taxa de `mqtt.qos`, que fica.

### Artigos

Há **dois artigos diferentes**. Não misture os dois. Se a relação entre eles importar para uma proposta,
pergunte à autora.

- `WPMC_2026_rasp__v1_ok_-2.pdf`, na raiz: *Deployment-Aware Machine Learning for DoS Detection in Edge-Based
  IoT Networks*. Ele descreve o protocolo de treino que a refatoração reproduz: split estratificado 80/20 com
  seed 42 (75.700 / 18.925), seis seletores, seis modelos mais um SVM de referência em LowVariance
  (12 features), Optuna com TPE, 30 trials, `StratifiedKFold(5)` e objetivo F1 macro. As métricas são
  accuracy, precision weighted, F1 weighted, F1 macro e log loss, e o Pareto usa `S = (Acc + F1w)/2` contra
  a latência por registro do teste de estresse t16.
- O `plano_metodologico_edge.md` cita *Edge-Based Machine Learning for MQTT Intrusion Detection: A Pareto
  Analysis of Accuracy and Latency on Raspberry Pi* (WPMC 2026) e propõe a metodologia v2 de medição.

### Código antigo (fonte dos resultados atuais)

- `notebooks_refactored/04_pipeline.ipynb`: 6 modelos (LDA, QDA, GaussianNB, DecisionTree, RandomForest,
  GradientBoosting) × 7 seletores, mais baseline, Optuna global por consenso, ensembles e Optuna por seletor.
- `notebooks_refactored/04_svm.ipynb`: SVM só em LowVariance, com protocolo próprio (hold-out, 12 trials).
- Problemas já identificados nesse código, e que a refatoração corrige:
  - **Contrato de entrada divergente.** LDA e QDA foram salvos sem scaler, esperando um CSV já
    escalonado com um scaler ajustado nas 21 colunas e depois fatiado. O SVM foi salvo como
    `Pipeline(scaler + SVC)`, recebendo dados brutos. As listas de features eram as mesmas.
  - **Vazamento de rótulo nos gaps:** eles eram calculados separadamente para cada `type`. O efeito
    medido neste dataset é pequeno: 6150 → 6151 gaps de PUBLISH não nulos, e uma árvore treinada só com
    os gaps tem acurácia igual (0,5874) nas duas versões. O método, porém, não é reproduzível em produção.
    Ver `docs/adr/0001-gaps-sem-rotulo.md`.
  - **Smart Soft Voting com pesos otimizados no conjunto de teste.**
  - **Seletores duplicados ou mal nomeados:** Pearson e Fisher são o mesmo `f_classif`, "mRMR" é
    informação mútua e "ExtraTrees" era um `RandomForestClassifier`.
  - **Protocolo do Optuna diferente do paper:** 10–12 trials, 3 folds e F1 weighted.
  - **Calibração cara:** QDA e GaussianNB usavam `CalibratedClassifierCV(cv=3)` com `ensemble=True`, que
    guarda 3 cópias do modelo e custa cerca de 3× na inferência.

### API de inferência atual (`api_inference/`)

- FastAPI. `discover_models` carrega `api_inference/models/*.pkl` (43 modelos `optuna_by_selector_*`, de
  ago/2026) e casa cada um com `api_inference/datasets/test/test_<model_id>.csv`. A cada `POST /benchmark`,
  o servidor lê o CSV inteiro de teste (18.925 linhas) **do disco do próprio servidor** e chama `predict` no
  lote todo. O cliente não envia dados.
- Os CSVs de LDA e QDA estão escalonados e os dos demais modelos estão brutos, um reflexo do contrato
  divergente.
- Resultados de estresse: `api_inference/results_inference/` (t01–t16, CI95, `stress_report.md`).
  Fronteira de Pareto: `paretto/` e `paretto/paretto.md`.

### Pesquisa da nova API (`/home/william/Documentos/inference/`)

Leia o `plano_metodologico_edge.md` inteiro. Pontos que tocam diretamente as suas perguntas:

- **§0.1:** as medianas do t16 embutem pelo menos 2,57× de contenção (concorrência aparente de 10,28× em
  4 vCPUs), e a inflação não é uniforme entre modelos (threads de BLAS).
- **§0.2:** para os modelos rápidos, o t16 mediu principalmente o framework (`check_array`, Pydantic,
  serialização), não o `predict`.
- **§0.3 e §1.4:** o `S` é colinear com a acurácia (Pearson 0,999997). O plano propõe MCC ou F1 macro e um
  Pareto em 3 eixos: qualidade, p95 com B = 1 isolado e PSS.
- **§1.3:** o tamanho de lote vira fator experimental, com B = 1 como caso primário de IDS.
- **§5, E10:** o split aleatório 80/20 sobre *pacotes* vaza entre pacotes do mesmo fluxo ou sessão. O plano
  propõe split por fluxo (5-tupla) ou temporal.
- `edge_bench/api.py` tem `POST /predict` recebendo lotes de features, `/ping` (linha de base sem modelo) e
  `/canary`. `edge_bench/loadgen.py` envia lotes de um `X_test.npy`, em regime fechado ou aberto (Poisson).
  Esse desenho contrasta com o servidor atual, que lê o CSV no disco.

## 3. A refatoração em curso (o que vai existir)

Leia `AGENTS.md`, `docs/decisions.md` (log append-only, decisões 1–43), `GLOSSARY.md`, a spec
`docs/issues/0000-spec-treino-unificado.md` e os tickets `docs/issues/01`–`08`.

Em resumo:

- **Pacote `src/mqtt_dos/`** e um notebook de narrativa (`notebooks/training.ipynb`). O `RunConfig`, uma
  dataclass congelada, guarda o protocolo do paper como padrão.
- **Sem ensemble, sem Optuna global por consenso, sem etapa de "seleção com parâmetros default".** O
  pipeline tem só:
  1. baseline: 7 modelos com hiperparâmetros default nas 22 features;
  2. **Optuna por seletor:** 6 seletores (LowVariance, ANOVA, MutualInformation, Lasso, LinearSVC,
     ExtraTrees) × 7 modelos (os 6 acima mais o SVM, agora no mesmo protocolo), com TPE seed 42, 30 trials,
     `StratifiedKFold(5)` e F1 macro. O SVM pode ser ajustado numa subamostra estratificada de 15k linhas;
     o fit final usa o treino completo.
- **Ordem de dados:** `load_raw → add_gaps → drop_unused_columns → split estratificado 80/20 (seed 42)`.
  Os gaps são calculados sobre o fluxo inteiro, ordenado por tempo, sem o rótulo e antes do split.
- **Contrato único:** cada modelo é salvo como um `sklearn.Pipeline` (imputer constante 0 → [StandardScaler
  para LDA, QDA e SVM] → [calibração sigmoide com `ensemble=False` para QDA e GaussianNB] → modelo) que
  aceita as features **brutas** do seletor. Há um CSV de teste bruto por configuração.
- **Seleção de features:** ajustada uma única vez no treino imputado. Lasso e LinearSVC usam um scaler
  interno; LowVariance usa threshold 0.01 sem truncar (dá 12 features); os demais pegam o top-15.
- **Artefatos:** em `outputs/<run_name>/`. Nada é escrito em `api_inference/` nesta fase; a API fica para
  depois.
- **Estado do código:** o ticket 01 (ambiente com uv, `RunConfig`, testes, notebook vazio) está pronto. As
  aulas dos tickets 02 (carga e limpeza) e 03 (gaps) estão escritas, mas a autora ainda não digitou esse
  código. Os tickets 04–08 (split e Pipeline, registro de modelos e baseline, seleção, Optuna, artefatos)
  ainda não têm aula.

## 4. O que ler, e quanto confiar

A autora indicou o que está **atualizado**. Leia nesta ordem:

| # | Arquivo | Status | Por quê |
|---|---|---|---|
| 1 | `AGENTS.md` (seções "Refatoração em curso" e "Convenções do curso") | atualizado | regras e estado da refatoração; as seções "Active Branch", "Python" e "Pipeline entrypoints" são antigas |
| 2 | `docs/decisions.md`, `docs/adr/0001-gaps-sem-rotulo.md` | atualizado | todas as decisões, com o porquê |
| 3 | `docs/issues/0000-spec-treino-unificado.md` e `01`–`08` | atualizado | o que será construído |
| 4 | `GLOSSARY.md` | atualizado | vocabulário do domínio |
| 5 | `docs/02-carga-e-limpeza.md`, `docs/03-gaps-sem-vazamento.md` | atualizado | os achados de dados descritos acima, com números |
| 6 | `/home/william/Documentos/inference/plano_metodologico_edge.md`, `dicionario_metricas_inferencia.csv`, `edge_bench/` | atualizado | a pesquisa da nova inferência |
| 7 | `reports_refactored/` (`RELATORIO_FINAL.md`, `optuna_by_selector_results.csv`, `selected_features.json`, `best_optuna_model_by_selector.csv`, `PIPELINE_REVIEW.md`) | atualizado | resultados de treino que alimentam a API atual |
| 8 | `api_inference/models/`, `api_inference/datasets/test/` | atualizado | os 43 modelos e os CSVs de teste em uso |
| 9 | `api_inference/results_inference/`, `paretto/` | atualizado | estresse t01–t16 e a fronteira de Pareto |
| 10 | `docs/docs/dicionario_de_dados.md` | atualizado | significado de cada coluna do Wireshark |
| 11 | `docs/docs/gaps_with_split.md`, `docs/docs/publish_and_connect_gap.md` | atualizado | derivação dos gaps e do split; quando divergir do ADR 0001 ou da decisão 2, a decisão mais nova vale, e aponte a divergência |
| 12 | `WPMC_2026_rasp__v1_ok_-2.pdf` (seção III) | artigo | o protocolo que a refatoração reproduz |
| 13 | `notebooks_refactored/04_pipeline.ipynb`, `04_svm.ipynb` | código antigo | de onde vêm os resultados atuais; use para entender, não como referência de método |

**Histórico, não confie sem conferir no código:** `api_inference/README.md`, `api_inference/STRESS_README.md`,
`api_inference/docs/stress_api.md`, `raspberry_deploy.md`, `results_new_pipeline.md`, `results_pipeline.md`,
`scripts_pipeline.md`, `docs/pipeline_refactored.md`, `docs/model_training*.md`, `README.md` (seções de
resultados) e a pasta `notebooks/`.

Um alerta de proveniência: o `04_pipeline.ipynb` grava em `../reports/reports_ensemble_v2/`, uma pasta que
não existe no repositório, e várias saídas de `reports_refactored/` são de abril. Antes de usar um número de
`reports_refactored/`, confira de qual notebook e de qual protocolo ele saiu. Se não for possível saber,
diga isso.

## 5. O que se espera em cada pergunta

### 5.1 Treino sem vazamento

Avalie, no mínimo, os pontos abaixo. Para cada um, diga se é vazamento de fato, qual o impacto provável na
métrica reportada e como medir esse impacto:

- **Unidade do split.** Pacotes do mesmo fluxo ou da mesma rajada de ataque caem no treino e no teste (E10
  do plano). As colunas `ip.src`, `ip.dst`, `tcp.srcport`, `tcp.dstport` e `frame.time_epoch` saem das
  features, mas continuam no CSV bruto e podem servir para **agrupar**: `GroupKFold`/`StratifiedGroupKFold`
  por 5-tupla ou sessão, ou um split temporal. Mostre como ficam as classes em cada opção, sabendo que os
  dois tráfegos se sobrepõem no tempo (DoS cobre cerca de 564 s de uma captura de cerca de 942 s).
- **Seleção de features fora da validação cruzada.** Os seletores são ajustados uma vez no treino inteiro,
  e o Optuna faz a CV com essas features fixas. A CV do tuning fica otimista. Vale colocar o seletor dentro
  do `Pipeline` avaliado em cada fold? Qual o custo?
- **Escolha da melhor configuração usando o teste.** Escolher a melhor entre 42 pelo F1 no teste é viés de
  seleção. Proponha como escolher na validação e reportar o teste uma única vez (CV aninhada, partição de
  validação separada, ou outra), dentro do orçamento computacional (o fit do SVM baseline levou 123 s
  nas 75,7 mil linhas de treino, no `04_svm.ipynb`).
- **Gaps calculados antes do split.** Eles são causais (só olham para o passado) e calculáveis em
  produção, mas usam pacotes vizinhos que podem estar no teste. Isso é vazamento para a avaliação? Depende
  da unidade do split?
- **A assimetria "o pacote é MQTT?".** É vazamento de artefato de coleta? Que experimento separa "detecta
  DoS" de "detecta tráfego MQTT" (por exemplo, avaliar só nos pacotes MQTT)?
- Qualquer outro ponto que você encontrar: imputação, calibração com `cv=3` dentro do treino, subamostra do
  SVM, `random_state` em comum.

### 5.2 Seleção das configurações para inferência

- Proponha o critério de qualidade: MCC, F1 macro, recall e FPR por classe, com a justificativa do §0.3 do
  plano e do desbalanceamento real dentro dos pacotes MQTT.
- Proponha como incluir custo antes do Raspberry Pi: tempo de `predict` isolado medido offline com
  threads fixadas, tamanho do modelo e memória, para fazer uma triagem barata das 42 configurações.
- Diga como decidir se duas configurações são de fato diferentes (IC bootstrap, McNemar ou teste pareado
  sobre o mesmo teste, tamanho de efeito) e como desempatar a favor da mais simples ou mais barata.
- Diga quantas configurações levar ao Pi e quais, considerando o desenho em duas etapas do plano (§6.1),
  e se o "melhor por seletor" ou o "conjunto não dominado no Pareto 3D" é o critério melhor.
- Considere o caso de um modelo dominar em qualidade em todos os seletores (DecisionTree tinha F1 ≈ 0,975
  nos resultados antigos): vale levar mais de um seletor do mesmo modelo?

### 5.3 Dados de teste na API

Compare, no mínimo:

1. o servidor lê o CSV de teste do disco (como hoje);
2. o cliente envia lotes de features como JSON (como o `edge_bench`);
3. o cliente envia um formato binário (`.npy`, Arrow, msgpack);
4. a reprodução de tráfego: pacotes por um broker MQTT local, com a extração de features no Pi (E9 do
   plano, latência pacote-a-veredito).

Para cada opção, avalie: o que a latência medida inclui; a fidelidade ao cenário de IDS (B = 1); como
garantir que os dados sejam exatamente o teste do treino (hash do arquivo, `feature_names_in_`, ordem das
colunas, dtype); o custo de serialização em B = 1 e B = 18.925; e como encaixar no contrato novo, em que o
Pipeline aceita features brutas com NaN. Proponha também **o que o treino deve exportar** para a API
(formato, metadados, manifesto do run) para que essa ligação seja verificável.

## 6. Forma da resposta

1. Um resumo de uma página com as recomendações principais, ordenadas por impacto na validade dos
   resultados do artigo.
2. Uma seção por pergunta (5.1, 5.2, 5.3) com: diagnóstico (fato + fonte), opções com prós e contras,
   recomendação, e o experimento que a confirma (o que rodar, sobre quais dados, qual resultado mudaria a
   recomendação).
3. Uma lista de **decisões a mudar** em `docs/decisions.md` (pelo número), com a mudança proposta, e de
   **tickets afetados** em `docs/issues/`.
4. Uma lista de **perguntas para a autora**: tudo o que você não conseguiu decidir sem ela.

Não proponha nada que exija apagar os notebooks antigos, `scripts/` ou a `api_inference/` atual: eles ficam
intactos nesta fase.
