# Briefing: análise metodológica e reestruturação dos tickets do curso

Você vai trabalhar num projeto de pesquisa em detecção de ataques DoS em redes MQTT, com modelos clássicos de
aprendizado de máquina implantados num Raspberry Pi. O projeto está sendo refatorado em três níveis ao mesmo
tempo: **estrutura** (pastas e pacote), **arquitetura** (treino, artefatos, API de inferência) e
**metodologia** (split, validação, métricas, medição no dispositivo). A refatoração é documentada como um
**curso** em MkDocs: cada ticket em `docs/issues/` vira uma aula, e a autora implementa o código digitando-o
ela mesma, aula por aula.

Seu papel tem duas etapas:

- **Etapa A: análise.** Responder às quatro perguntas abaixo com diagnóstico, opções, recomendação e o
  experimento que confirma cada uma.
- **Etapa B: reestruturação.** Transformar as recomendações aceitas em **tickets, spec e decisões**, no
  formato que o curso usa, para que o projeto passe a seguir essas recomendações. Você é o reestruturador
  do plano de trabalho, não o implementador: o código continua sendo escrito pela autora.

Entre as duas etapas há um **ponto de parada** (seção 0): você entrega o relatório e o mapa de
reestruturação e espera a aprovação da autora antes de editar os tickets.

As quatro perguntas da Etapa A:

1. **Treino sem vazamento.** O que ainda vaza, ou pode vazar, no esquema de treino que está sendo refatorado?
   Como corrigir sem perder a comparabilidade com o artigo, quando isso for possível?
2. **Seleção de modelos para inferência.** O treino gera 42 configurações seletor × modelo (mais 7 de
   baseline; a autora fala em "mais de 50" contando variações). Só algumas cabem na bateria de testes de
   estresse no Raspberry Pi. Qual critério, e qual procedimento estatístico, escolhe as que vão para a
   inferência?
3. **Dados de teste na API de inferência.** Qual é a melhor forma de levar os dados de teste até a API, de
   modo que a medição de latência e de recursos meça o que deve medir e os dados sejam exatamente os do
   teste do treino?
4. **Medição de recursos no dispositivo.** Como medir, no próprio Raspberry Pi, o pico de memória, o uso de
   CPU e (quando houver) o uso de GPU de cada modelo durante a inferência, de forma que o número seja
   atribuível ao modelo, não seja contaminado pela própria instrumentação e possa entrar no Pareto?

Escreva em português do Brasil. Separe sempre **fato** (com o arquivo e, se possível, o número que o
sustenta) de **hipótese** (o que precisa de experimento). Quando puder verificar uma afirmação rodando
código só de leitura sobre os dados do repositório, verifique e diga como. Quando uma afirmação depender do
Raspberry Pi e você não tiver acesso a ele, **não presuma**: escreva o comando que a autora deve rodar no Pi
e o que cada resultado possível muda na proposta.

---

## 0. Papel, permissões e ponto de parada

### O que você pode alterar

- **`docs/issues/`**: criar, reescrever, dividir, fundir e marcar como substituídos os tickets, incluindo a
  spec `0000-spec-treino-unificado.md` (ou criar specs novas por fase, se for o caso).
- **`docs/decisions.md`**: só **acrescentar** decisões ao final. O log é append-only: nunca edite nem
  apague uma decisão existente. Quando uma decisão nova mudar uma antiga, escreva na nova
  "substitui a decisão N" e o porquê.
- **`docs/adr/`**: criar ADRs novos para decisões grandes (por exemplo, a unidade do split), no formato do
  `0001-gaps-sem-rotulo.md`.
- **`GLOSSARY.md`**: acrescentar termos novos que os tickets passarem a usar.
- **O seu relatório** da Etapa A (onde, ver seção 7).

### O que você não pode alterar

- Código: `src/`, `tests/`, `notebooks/`, `pyproject.toml`. Quem digita o código é a autora; um ticket pode
  conter a assinatura de uma função ou o nome de um teste, mas não a implementação.
- As aulas já escritas (`docs/02-carga-e-limpeza.md`, `docs/03-gaps-sem-vazamento.md` e qualquer outra
  aula existente). Se uma recomendação as tornar desatualizadas, **liste o que muda em cada uma**; a
  autora regera a aula com a skill do curso.
- Os notebooks antigos, `scripts/`, `api_inference/`, `data/` e `outputs/`. Eles ficam intactos.
- `mkdocs.yml` e a própria skill do curso.

### Git

Trabalhe num branch novo a partir do branch atual da refatoração. Faça commits pequenos, um por mudança
lógica (um ticket reescrito, uma decisão acrescentada), com mensagens em português. Não faça push nem merge.

### Ponto de parada

Ao fim da Etapa A, **pare** e entregue à autora o relatório e o **mapa de reestruturação** (seção 7). Só
comece a Etapa B depois que ela aprovar o mapa, com ou sem ajustes. Se ela rejeitar uma recomendação, o
ticket correspondente não é criado, e a recomendação fica registrada no relatório como "não adotada", com o
motivo que ela der.

---

## 1. Onde estão as coisas

- **Repositório do projeto:** `/home/william/Projetos/mqtt_under_attack`
- **Skill que gera o curso:** `/home/william/.claude/skills/mkdocs-project-course/`. Leia o `SKILL.md` e os
  arquivos de referência dela **antes** de propor qualquer ticket: o formato dos tickets, a relação
  ticket → aula, a ordem das aulas e as convenções de escrita vêm dela, não de você.
- **Configuração do site do curso:** `mkdocs.yml` na raiz do repositório (navegação e o que é publicado).
- **Pesquisa inicial sobre a nova API de inferência:** `/home/william/Documentos/inference/`
  (`plano_metodologico_edge.md`, `dicionario_metricas_inferencia.csv` e o esboço de código `edge_bench/`)
- **Instrumentação de memória já escrita:** `<CAMINHO_DO_PROFILER>` (classe `PeakMemoryProfiler` e funções
  `_isolated_worker` / `run_isolated_inference`; descrição na seção 2)

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
- Verifique no código da API e nos resultados **se e como a memória e a CPU foram medidas** no t01–t16
  (qual biblioteca, qual escopo, qual frequência). Se nada foi medido, diga isso; se foi, diga se o número
  pertence ao processo, ao container ou à máquina.

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
- O `dicionario_metricas_inferencia.csv` define as métricas de inferência. Toda métrica de recurso que você
  propuser na pergunta 4 deve casar com uma linha desse dicionário ou vir como proposta de linha nova.

### Instrumentação de recursos já escrita (`PeakMemoryProfiler`)

Existe um profiler de memória pronto, escrito para outro contexto: ele carrega o modelo com `torch.load` e
chama `model.inference(pyg_data)`, ou seja, foi feito para um modelo PyTorch / PyTorch Geometric. Os modelos
deste projeto são `sklearn.Pipeline` executados em CPU. A ideia de medição pode ser reaproveitada, o código
como está não. O que ele faz:

- **`PeakMemoryProfiler`** é um context manager (também usável como decorador). Na entrada, roda
  `gc.collect()`; em CUDA, também `torch.cuda.empty_cache()`, `reset_peak_memory_stats()` e `synchronize()`;
  depois tira um snapshot de RAM. Na saída, lê o pico de RAM, calcula `incremento = pico − snapshot` e, em
  CUDA, lê `max_memory_allocated()` (pico alocado) e `max_memory_reserved()` (pico reservado), alertando se a
  diferença (fragmentação) passa de 200 MB.
- **RAM:** tenta o cgroup v2 em caminhos fixos (`/sys/fs/cgroup/memory.current` e `/sys/fs/cgroup/memory.peak`)
  e cai para o USS do processo via `psutil` se os arquivos não existirem.
- **`run_isolated_inference`:** salva modelo e dados em arquivos temporários, cria um processo filho com
  contexto `spawn`, roda a inferência dentro do profiler e devolve métricas e saídas por uma `Queue`
  (o pai faz `queue.get()` antes do `join()`, o que evita deadlock com cargas grandes).
- **Ele mede memória, não CPU.** Não há tempo de CPU, utilização por núcleo, pressão de CPU, temperatura
  nem frequência.

Defeitos conhecidos, a confirmar no código:

1. **Efeito sombra.** `memory.peak` é o pico histórico do cgroup inteiro desde a sua criação, não o pico do
   bloco. Se o pico maior aconteceu antes (carga do modelo, outro modelo), o incremento sai 0; se o pico
   antigo foi alto e a memória já baixou, o incremento sai superestimado.
2. **Caminhos fixos de cgroup.** `/sys/fs/cgroup/memory.current` só existe dentro de um container com
   namespace de cgroup próprio; o cgroup raiz de um host não tem esse arquivo. Fora de Docker, o profiler
   provavelmente cai no fallback **em silêncio** (hipótese a verificar no Pi).
3. **Page cache.** `memory.current` inclui páginas de arquivo; ler um CSV ou `.pkl` infla o número.
4. **Fallback de pico quebrado.** Sem cgroup, `_get_cpu_ram_mb(use_peak=True)` devolve o USS atual (não 0),
   então o ramo com `ru_maxrss` quase nunca roda: mede-se o uso no fim do bloco, não o pico.
5. **Efeito do observador.** `gc.collect()`, `empty_cache()`, `synchronize()` e leituras em `/sys` custam
   tempo; dentro do caminho cronometrado, distorcem a latência, e mais ainda em B = 1.
6. **`device="cuda:0"` desliga as métricas de GPU** (a checagem é `== "cuda"`).
7. **Processo filho morto por OOM trava o pai** (`queue.get()` sem timeout) e deixa os temporários no disco
   (não há `try/finally`).
8. **No mesmo container, o cgroup do filho é o do pai**: o isolamento por `spawn` limpa a VRAM, mas a RAM
   medida via cgroup ainda inclui o processo pai.

### O dispositivo

- Fato (plano, §0.1): o Pi tem 4 vCPUs.
- Não está neste briefing, e a autora precisa informar: modelo do Raspberry Pi e quantidade de RAM, sistema
  operacional e versão do kernel, se a API roda em Docker ou direto no host, se o controlador `memory` do
  cgroup v2 está ativo e qual BLAS o NumPy usa no ARM. Não presuma nenhum desses.
- **GPU:** os modelos são scikit-learn e rodam só em CPU; o Raspberry Pi não tem GPU CUDA. A GPU integrada
  (VideoCore) compartilha a RAM do sistema e não é usada pelo scikit-learn. Trate GPU como "não usada" até
  prova em contrário, e diga como registrar isso no manifesto. O ramo CUDA do profiler só faz sentido num
  hospedeiro de treino com GPU ou num dispositivo futuro com GPU (por exemplo, um Jetson).

## 3. A refatoração em curso (o plano que você vai reestruturar)

Leia `AGENTS.md`, `docs/decisions.md` (log append-only, decisões 1–43), `GLOSSARY.md`, a spec
`docs/issues/0000-spec-treino-unificado.md` e os tickets `docs/issues/01`–`08`. Esse conjunto é o plano
atual; a Etapa B o reescreve.

Em resumo, o plano atual prevê:

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
- **Artefatos:** em `outputs/<run_name>/`. Nada é escrito em `api_inference/`.
- **Estado do código:** o ticket 01 (ambiente com uv, `RunConfig`, testes, notebook vazio) está pronto e
  implementado. As aulas dos tickets 02 (carga e limpeza) e 03 (gaps) estão escritas, mas a autora ainda não
  digitou esse código. Os tickets 04–08 (split e Pipeline, registro de modelos e baseline, seleção, Optuna,
  artefatos) ainda não têm aula.
- **O plano atual cobre só o treino.** Não há tickets para seleção estatística das configurações, para a
  nova API de inferência nem para a medição de recursos no Pi. Essas frentes entram agora no escopo da
  refatoração, como tickets de fases posteriores (seção 6).

## 4. O que ler, e quanto confiar

A autora indicou o que está **atualizado**. Leia nesta ordem:

| # | Arquivo | Status | Por quê |
|---|---|---|---|
| 1 | `/home/william/.claude/skills/mkdocs-project-course/` (`SKILL.md` e referências) | atualizado | formato dos tickets, relação ticket → aula, convenções do curso |
| 2 | `AGENTS.md` (seções "Refatoração em curso" e "Convenções do curso") | atualizado | regras e estado da refatoração; as seções "Active Branch", "Python" e "Pipeline entrypoints" são antigas |
| 3 | `docs/decisions.md`, `docs/adr/0001-gaps-sem-rotulo.md` | atualizado | todas as decisões, com o porquê |
| 4 | `docs/issues/0000-spec-treino-unificado.md` e `01`–`08` | atualizado | o plano que você vai reestruturar; também o modelo concreto do formato de ticket |
| 5 | `GLOSSARY.md` | atualizado | vocabulário do domínio |
| 6 | `docs/02-carga-e-limpeza.md`, `docs/03-gaps-sem-vazamento.md`, `mkdocs.yml` | atualizado | as aulas já escritas (e os achados de dados, com números) e a navegação do curso |
| 7 | `/home/william/Documentos/inference/plano_metodologico_edge.md`, `dicionario_metricas_inferencia.csv`, `edge_bench/` | atualizado | a pesquisa da nova inferência |
| 8 | `<CAMINHO_DO_PROFILER>` | atualizado, outro contexto | a ideia de medição de pico; escrito para PyTorch, não para scikit-learn |
| 9 | `reports_refactored/` (`RELATORIO_FINAL.md`, `optuna_by_selector_results.csv`, `selected_features.json`, `best_optuna_model_by_selector.csv`, `PIPELINE_REVIEW.md`) | atualizado | resultados de treino que alimentam a API atual |
| 10 | `api_inference/models/`, `api_inference/datasets/test/` | atualizado | os 43 modelos e os CSVs de teste em uso |
| 11 | `api_inference/results_inference/`, `paretto/` | atualizado | estresse t01–t16 e a fronteira de Pareto |
| 12 | `docs/docs/dicionario_de_dados.md` | atualizado | significado de cada coluna do Wireshark |
| 13 | `docs/docs/gaps_with_split.md`, `docs/docs/publish_and_connect_gap.md` | atualizado | derivação dos gaps e do split; quando divergir do ADR 0001 ou da decisão 2, a decisão mais nova vale, e aponte a divergência |
| 14 | `WPMC_2026_rasp__v1_ok_-2.pdf` (seção III) | artigo | o protocolo que a refatoração reproduz |
| 15 | `notebooks_refactored/04_pipeline.ipynb`, `04_svm.ipynb` | código antigo | de onde vêm os resultados atuais; use para entender, não como referência de método |

**Histórico, não confie sem conferir no código:** `api_inference/README.md`, `api_inference/STRESS_README.md`,
`api_inference/docs/stress_api.md`, `raspberry_deploy.md`, `results_new_pipeline.md`, `results_pipeline.md`,
`scripts_pipeline.md`, `docs/pipeline_refactored.md`, `docs/model_training*.md`, `README.md` (seções de
resultados) e a pasta `notebooks/`. O `raspberry_deploy.md` pode ajudar a responder às perguntas sobre o
dispositivo (seção 2), mas confirme com a autora antes de usar o que ele disser.

Um alerta de proveniência: o `04_pipeline.ipynb` grava em `../reports/reports_ensemble_v2/`, uma pasta que
não existe no repositório, e várias saídas de `reports_refactored/` são de abril. Antes de usar um número de
`reports_refactored/`, confira de qual notebook e de qual protocolo ele saiu. Se não for possível saber,
diga isso.

## 5. Etapa A: o que se espera em cada pergunta

Em cada pergunta, além do diagnóstico e da recomendação, diga **como a recomendação vira trabalho**: qual
ticket atual ela altera, qual ticket novo ela exige, qual decisão nova ela gera e qual aula já escrita ela
desatualiza. Isso alimenta o mapa de reestruturação (seção 7).

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
- **Comparabilidade com o artigo.** Se o protocolo mudar (split por grupo, seletor dentro da CV), proponha
  como o `RunConfig` mantém um modo que reproduz o artigo e um modo corrigido, e como os dois aparecem no
  curso (por exemplo, o modo do artigo primeiro e a correção como aula própria, mostrando a diferença).

### 5.2 Seleção das configurações para inferência

- Proponha o critério de qualidade: MCC, F1 macro, recall e FPR por classe, com a justificativa do §0.3 do
  plano e do desbalanceamento real dentro dos pacotes MQTT.
- Proponha como incluir custo antes do Raspberry Pi: tempo de `predict` isolado medido offline com
  threads fixadas, tamanho do modelo serializado, **pico de memória e tempo de CPU** de cada configuração
  (com o protocolo da pergunta 4, rodado na máquina de desenvolvimento), para fazer uma triagem barata das
  42 configurações. Diga o que dessa triagem se transfere para o Pi e o que não se transfere (arquitetura
  ARM vs x86, BLAS diferente, tamanho de página do kernel, quantidade de RAM), e como verificar a
  transferência com poucas configurações medidas nas duas máquinas (por exemplo, correlação de postos).
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

Para cada opção, avalie: o que a latência medida inclui; **o que a medição de memória e CPU inclui** (por
exemplo: o DataFrame de 18.925 linhas e o page cache do CSV na opção 1, os buffers de desserialização nas
opções 2 e 3, o broker e o extrator de features na opção 4, se rodarem no mesmo cgroup); a fidelidade ao
cenário de IDS (B = 1); como garantir que os dados sejam exatamente o teste do treino (hash do arquivo,
`feature_names_in_`, ordem das colunas, dtype); o custo de serialização em B = 1 e B = 18.925; e como
encaixar no contrato novo, em que o Pipeline aceita features brutas com NaN. Proponha também **o que o
treino deve exportar** para a API (formato, metadados, manifesto do run) para que essa ligação seja
verificável, e **o que a API deve gravar junto de cada resultado** para que o ambiente de medição também
seja verificável (modelo do Pi, kernel, versão e controladores do cgroup, governor de CPU, número de
threads de BLAS/OpenMP, versões de NumPy, scikit-learn e BLAS, temperatura e estado de throttling no
início e no fim). O que o treino exporta afeta o ticket atual de artefatos (08): diga como.

### 5.4 Pico de CPU, memória e GPU no dispositivo

O objetivo é que cada configuração levada ao Pi tenha números de recurso **atribuíveis a ela**,
comparáveis entre configurações e utilizáveis no Pareto. Use o `PeakMemoryProfiler` (seção 2) como ponto de
partida: diga o que dele se aproveita, o que precisa mudar e o que precisa ser escrito do zero. Avalie, no
mínimo:

- **Quais grandezas medir, e para quê.** Separe:
  - *memória de pico* (o que provoca OOM no Pi) e *memória em regime* (PSS depois de carregar o modelo, o
    que limita quantos modelos ou workers cabem); diga qual delas é o eixo de memória do Pareto 3D do plano
    (§1.4) e se as duas devem ser reportadas;
  - *tempo de CPU por inferência* (user + sys, por exemplo via `time.thread_time()` ou
    `resource.getrusage`), que é menos sensível à contenção do que a latência de parede;
  - *utilização de pico por núcleo* e *pressão de CPU* (`cpu.pressure`, PSI), como medida direta da
    contenção que o §0.1 do plano estima indiretamente (2,57×);
  - *GPU*: confirme que não é usada e diga como registrar isso; se a autora disser que algum modelo usa
    GPU, adapte o ramo CUDA do profiler (pico alocado vs reservado, `startswith("cuda")`).
- **Escopo da medição.** Processo, cgroup do container, cgroup dedicado por experimento (por exemplo, cada
  execução dentro de um `systemd-run --scope`, que nasce com `memory.peak` zerado), ou sistema inteiro. Diga
  o que cada escopo inclui (workers do uvicorn, cliente de carga, broker, page cache) e qual responde à
  pergunta "quanto este modelo custa no Pi".
- **Efeito sombra e reset do pico.** Compare as saídas: um processo novo por configuração (em que
  `ru_maxrss` do processo é um pico limpo, incluindo a carga do modelo), um cgroup novo por configuração,
  zerar o pico escrevendo em `memory.peak` (só em kernel recente; diga qual versão e como verificar no Pi)
  ou amostragem contínua. Diga qual combina com cada etapa do plano (§6.1).
- **Efeito do observador.** A instrumentação não pode estar dentro do trecho cronometrado em B = 1.
  Proponha: execuções separadas para latência e para recursos, ou um amostrador externo (outro processo,
  idealmente fixado em outro núcleo) lendo cgroup, `/proc` e sensores; e um experimento que meça o custo da
  instrumentação (p95 em B = 1 com e sem ela, no `/ping` e num modelo real).
- **Granularidade.** Um `predict` em B = 1 de um modelo rápido dura microssegundos; um amostrador a 10–100 Hz
  não vê o pico de uma requisição. Diga quais grandezas exigem contador acumulado (`ru_maxrss`,
  `memory.peak`, `cpu.stat`, tempo de CPU por thread) e quais podem ser amostradas, e compare, num
  experimento, o máximo amostrado com o pico do contador.
- **Threads.** O número de threads de BLAS/OpenMP muda tanto a CPU quanto a memória e é parte da inflação
  não uniforme do §0.1. Proponha como fixá-lo (variáveis de ambiente ou `threadpoolctl`) e se ele deve ser
  um fator experimental ou uma constante registrada.
- **Condições do dispositivo.** Temperatura, frequência, throttling (`vcgencmd get_throttled`,
  `vcgencmd measure_temp`), governor de CPU e outros processos ativos. Proponha critérios para descartar ou
  repetir uma execução e o tempo de aquecimento e de resfriamento entre configurações.
- **Os defeitos conhecidos do profiler** (seção 2, itens 1–8): diga quais invalidam a medição no Pi, quais
  só importam em outros cenários e quais precisam ser corrigidos antes de qualquer número ir para o artigo.
- **Ligação com o dicionário.** Para cada grandeza proposta, dê nome, unidade, fonte (arquivo do kernel ou
  função), escopo, momento da leitura e linha correspondente no `dicionario_metricas_inferencia.csv` (ou a
  linha nova a acrescentar).

Entregue um **protocolo de medição de recursos** em forma de tabela (grandeza, unidade, fonte, escopo,
contador ou amostragem, em qual execução é medida), e o experimento que o valida no Pi: por exemplo,
carregar duas configurações no mesmo processo e comparar o pico da segunda com o pico medido num processo
novo; ou medir o p95 em B = 1 com e sem o amostrador. Diga qual resultado mudaria a recomendação.

## 6. Etapa B: como reestruturar os tickets

### Formato

- O formato de um ticket é o que a skill `mkdocs-project-course` define e o que os tickets 01–08 já
  seguem. Não invente um formato novo. Se a skill e os tickets existentes divergirem, siga a skill e aponte
  a divergência no relatório.
- Cada ticket precisa conter, no formato da skill: objetivo, contexto (com as decisões que o sustentam,
  pelo número), dependências, arquivos que a autora vai criar ou mudar, critérios de aceite **verificáveis**
  (de preferência como nomes de testes ou comandos com resultado esperado) e o que a aula correspondente
  precisa ensinar (conceitos, a pergunta que a aula responde, o erro comum que ela previne).
- Um ticket é um passo de curso: pequeno o bastante para uma aula, com um entregável que roda. Se uma
  recomendação for grande demais para isso (por exemplo, o split por grupo com CV aninhada), divida.

### Ordem e numeração

- A ordem dos tickets é a ordem das aulas. Cada ticket só pode usar conceitos e código de tickets
  anteriores. Verifique isso explicitamente para cada ticket novo ou reescrito.
- **Não renumere os tickets 01–03**: o 01 já foi implementado e o 02 e o 03 têm aula escrita. Se uma
  recomendação mudar o 02 ou o 03, reescreva o ticket mantendo o número e liste, no relatório, o que muda
  na aula correspondente.
- Os tickets 04 em diante não têm aula e podem ser renumerados, divididos ou fundidos, se isso deixar a
  sequência do curso mais clara. Nesse caso, atualize todas as referências nos tickets e na spec e registre o
  mapeamento antigo → novo numa decisão nova (as decisões antigas não são editadas).
- Um ticket que deixar de fazer sentido não é apagado: marque-o como "substituído por NN" ou "descartado",
  com o motivo e a decisão que justifica, para o histórico do curso ficar legível.

### Fases

Organize os tickets em fases, com uma spec por fase (a `0000` atual pode virar a spec da fase de treino):

1. **Treino** (o que já existe, corrigido pela Etapa A): dados, gaps, split, Pipeline, seleção, tuning,
   artefatos com manifesto.
2. **Avaliação e seleção das configurações:** métrica de qualidade, testes pareados, triagem offline de
   custo, escolha do que vai ao Pi.
3. **Inferência e medição no dispositivo:** formato de dados para a API, nova API (sem alterar a
   `api_inference/` atual), protocolo de recursos, gerador de carga, Pareto 3D.

Essa divisão é uma sugestão; proponha outra se a análise indicar. Diga onde fica o código das fases 2 e 3
(dentro de `src/mqtt_dos/`, num pacote irmão, ou partindo do `edge_bench/`) e registre isso como decisão.

### Experimentos que decidem

Quando uma recomendação depender de um experimento (por exemplo, "o split por fluxo muda o F1 em mais de X
pontos?"), o próprio experimento vira um ticket que **precede** o ticket que depende dele. Escreva no ticket
do experimento o critério de decisão (o resultado que leva a cada caminho), para que a autora não precise
voltar a você para decidir.

### Rastreabilidade

- Toda recomendação aprovada da Etapa A vira pelo menos um ticket ou uma decisão. Nenhuma fica órfã: se
  não couber agora, registre-a como "fora de escopo" no relatório, com o motivo.
- Todo ticket novo ou reescrito cita a seção do relatório que o originou.
- Termos novos usados nos tickets entram no `GLOSSARY.md`.

## 7. Entregas

### Antes do ponto de parada (Etapa A)

Escreva o relatório num arquivo Markdown dentro do repositório, num lugar que **não** entre na navegação do
curso (confira o `mkdocs.yml` e as convenções da skill; se não houver convenção, use
`docs/analises/claude-science-<AAAA-MM-DD>.md` e diga isso). O relatório tem:

1. Um resumo de uma página com as recomendações principais, ordenadas por impacto na validade dos
   resultados do artigo.
2. Uma seção por pergunta (5.1, 5.2, 5.3, 5.4) com: diagnóstico (fato + fonte), opções com prós e contras,
   recomendação, e o experimento que a confirma (o que rodar, sobre quais dados, qual resultado mudaria a
   recomendação). Na 5.4, inclua o protocolo de medição de recursos em tabela.
3. O **mapa de reestruturação**, em tabela: ticket atual (ou "novo") → ação (manter, reescrever, dividir,
   fundir, substituir, descartar, criar) → número final → fase → motivo (seção do relatório) → decisões
   novas ou substituídas → aula já escrita que fica desatualizada e o que muda nela.
4. O texto das **decisões novas** que serão acrescentadas ao `docs/decisions.md`, já redigido, indicando
   quais decisões antigas cada uma substitui.
5. Uma lista de **comandos para rodar no Raspberry Pi**, com o que cada saída possível muda na proposta
   (versão do kernel, controladores do cgroup, existência de `memory.peak`, tamanho de página, BLAS do
   NumPy, estado de throttling).
6. Uma lista de **perguntas para a autora**: tudo o que você não conseguiu decidir sem ela.

Faça commit do relatório no branch novo e pare.

### Depois da aprovação (Etapa B)

1. Aplique o mapa aprovado: tickets, specs, decisões, ADRs e glossário, em commits pequenos.
2. Releia a sequência final de tickets do início ao fim e confirme que cada um só depende de anteriores e
   que todo critério de aceite é verificável.
3. Atualize o relatório com uma seção final: arquivos alterados, commits, recomendações não adotadas e o que
   ficou para a autora (aulas a regerar com a skill, comandos a rodar no Pi, perguntas pendentes).

Não proponha nada que exija apagar os notebooks antigos, `scripts/` ou a `api_inference/` atual: eles ficam
intactos nesta fase.