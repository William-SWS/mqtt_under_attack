# Análise metodológica e mapa de reestruturação — Etapa A

**Data:** 2026-10-30 · **Briefing:** `docs/claude-science-melhorias.md` (sha256 `3130854f…21e4f`) ·
**Base:** `refact/repository_structure`, commit `51f6861` · **Status:** ponto de parada. A Etapa B só começa
depois da aprovação da autora.

> **Nota (2026-10-30):** o branch `analise/claude-science-2026-10-30` e os commits `29223bb` e `8981a21`
> foram criados pelo agente, seguindo o §0 do briefing. A regra da autora, registrada como decisão 65, é
> que nenhum agente executa operações de git. A partir daqui, toda operação de git é só sugerida.

Este arquivo fica em `docs/analises/` e **não** está na `nav` do `mkdocs.yml`. Não há convenção da skill para
relatórios que eu tenha conseguido ler (ver §0.2), então usei o caminho sugerido no briefing. Caminhos são
citados como código, nunca como link, para que `mkdocs build --strict` não acuse links quebrados.

Pacote de execução para a Etapa B (texto integral dos tickets, specs, ADRs e glossário, e a ordem dos
commits): `docs/analises/claude-science-2026-10-30-etapa-b.md`. Script das verificações e a saída dele:
`docs/analises/claude-science-2026-10-30-verificacoes.py` e `…-verificacoes.out`.

---

## 0. Escopo, fontes e limites desta análise

### 0.1 O que foi lido

`AGENTS.md`, `CLAUDE.md`, `GLOSSARY.md`, `mkdocs.yml`, `docs/decisions.md` (1–43), `docs/adr/0001`, a spec
`0000` e os tickets `01`–`08`, `course/` (MISSION, NOTES, LOG nº 1–26, learning records 0001–0003), o código
de `src/` e `tests/`, os blocos de código das aulas 02 e 03, `api_inference/app/{main,benchmark}.py`,
`Dockerfile`, `docker-compose.yml`, `requirements.txt`, o cabeçalho e o JSON do t16,
`reports_refactored/` (datas e as linhas de `optuna_by_selector_results.csv`), `api_inference/models/` (os 43
nomes; 8 `.pkl` carregados), `/home/william/Documentos/inference/` (plano, dicionário com 53 métricas,
`edge_bench/metrics.py` e `api.py`) e `data/raw/MQTT Under Attack Dataset/DoS.csv`.

### 0.2 O que não foi possível ler (e o que isso muda)

| Item | Situação | Consequência |
|---|---|---|
| Skill `mkdocs-project-course` (`~/.claude/skills/…`) | o diretório não é visível do sandbox (pedido de acesso falhou: "Directory could not be accessed") | o formato dos tickets segue os tickets 01–08 existentes; acrescentei os campos que o briefing exige (Contexto, Arquivos, Aula, Origem) e marquei isso como **divergência a confirmar** (pergunta P6) |
| `PeakMemoryProfiler` (`<CAMINHO_DO_PROFILER>`) | o placeholder não foi preenchido; `grep` nas pastas concedidas não achou a classe | a §2.4 avalia o profiler **pela descrição do briefing**; os 8 defeitos ficam como "a confirmar no código" (P5) |
| PDF do artigo | o briefing cita `WPMC_2026_rasp__v1_ok_-2.pdf`; na raiz existe `WPMC_2026_rasp__v1_ok_.pdf` (não rastreado) | usei a descrição do protocolo que está no briefing e na spec; confirmar se é o mesmo arquivo (P4) |
| Raspberry Pi | sem acesso | nada sobre o Pi é presumido; ver §5 (comandos) |

### 0.3 Como verifiquei

Todas as afirmações marcadas **[medido]** saem do script de verificação, que reproduz a limpeza da aula 02
(46 colunas, extraídas do próprio `.md`) e os gaps da aula 03, só lendo o repositório. Ele roda com
`python docs/analises/claude-science-2026-10-30-verificacoes.py .` (scikit-learn 1.9.1, pandas 2.3.3). As
marcadas **[código]** foram lidas no arquivo citado. As marcadas **[hipótese]** precisam do experimento indicado.

### 0.4 Correções ao meu próprio plano anterior (`plano_metodologico_edge.md` e `edge_bench/`)

A autora precisa saber disso antes de usar aquele material:

1. **`memory.peak` não é zerável a partir do kernel 6.3.** Ele existe, só leitura, desde o 5.19, e passou a
   aceitar escrita no 6.12. O reset vale só para o descritor de arquivo que escreveu: a leitura por outro
   descritor continua devolvendo o pico desde a criação do cgroup (documentação do kernel, `cgroup-v2`,
   `memory.peak`). O plano dizia 6.3.
2. **`edge_bench.metrics.CgroupV2.reset_peak()` não funciona** [código]: ele abre o arquivo, escreve `"0"`,
   fecha e depois `snapshot()` relê por um descritor novo. A leitura devolve o pico desde a criação do
   cgroup. O `ResourceWindow` herda o defeito, que é o mesmo "efeito sombra" do `PeakMemoryProfiler`.
3. **A explicação da inflação não uniforme do t16 por "threads de BLAS do SVM" estava errada em parte.** Os
   RandomForest em uso foram salvos com `n_jobs=1` [medido, `lowvariance_randomforest.pkl` e
   `extratrees_randomforest.pkl`], e `SVC.predict` roda na libsvm, sem BLAS [hipótese, confirmar com o
   experimento V5]. Entre os cinco do t16, só o LDA passa por BLAS. O diagnóstico de contenção (≥ 2,57×)
   continua de pé; o que muda é o mecanismo provável.

---

## 1. Resumo (uma página), ordenado por impacto na validade dos resultados do artigo

1. **Os números de recurso do t16 não são atribuíveis a modelo nenhum.** [código] A memória é
   `MemTotal − MemAvailable` da máquina, lida por `GET /stats` antes e depois da bateria. A CPU é só
   `loadavg`. A latência é o `predict` do lote inteiro (18.925 linhas) sob 4 workers × até 8 threads. →
   Proposta: protocolo novo com execuções separadas para latência (L) e recursos (R), processo novo por
   configuração, cgroup dedicado ao worker e PSS em regime como eixo de memória (§2.4, ADR 0004).
2. **Boa parte da separação vem de "o pacote é MQTT?".** [medido] Na janela do ataque há 39.044 pacotes
   MQTT `DoS` contra 275 `normal`. A regra "é MQTT ⇒ DoS", sozinha, dá F1 macro 0,929 e MCC 0,866 no teste;
   a árvore completa dá 0,969 e 0,939. O FPR sobre tráfego MQTT normal, que é o que importa num gateway
   MQTT, sai de **80 pacotes** no teste: 2/80, IC de Wilson 95% de 0,7% a 8,7%. → A regra entra como
   baseline obrigatória e os resultados passam a ser recortados por `is_mqtt` (ticket 11).
3. **Não dá para garantir que o Pi mediu o modelo e o teste do treino.** [medido] O t16 mediu acurácia
   0,9688 para `lowvariance_decisiontree`; o relatório de treino diz 0,9754. Os caminhos em
   `optuna_by_selector_results.csv` apontam para pastas que não são `api_inference/models/`, e o `.pkl` do
   GradientBoosting não carrega em scikit-learn 1.9.1 (`ModuleNotFoundError: _loss`). → Proposta: manifesto
   com sha256, teste em `.npy`, predições esperadas e verificação de paridade no startup da API (ticket 08 e
   ADR 0003).
4. **A escolha da "melhor configuração" usa o teste e não distingue empates.** [medido] O IC bootstrap de
   95% do F1 macro de uma árvore no teste é [0,9672; 0,9719], com meia largura de cerca de 0,0024. Os três
   modelos de árvore antigos ficam entre 0,9743 e 0,9754, dentro desse ruído. → Proposta: escolher pela CV,
   comparar com testes pareados e margem de equivalência, desempatar pelo menor custo (§2.2).
5. **O vazamento por fluxo (E10) não se confirmou para a árvore.** [medido] O F1 macro foi 0,9692 com CV
   aleatória, 0,9675 com CV agrupada por fluxo e 0,9715 com split temporal por classe; nesse último, só 18,7%
   dos pacotes de teste pertencem a fluxos vistos no treino. Isso apesar de 73,9% das linhas de teste terem
   uma duplicata exata no treino. → Manter o split do artigo como primário e tornar obrigatório o
   experimento com todas as famílias de modelo (ticket 09), que decide por critério escrito.
6. **A seleção de features fora da CV tem efeito nulo, pelo menos no ANOVA.** [medido] O seletor reajustado
   em cada fold escolheu as mesmas 15 features nos 5 folds, e o F1 de CV foi idêntico (0,969 ± 0,0011). →
   Não reestruturar o tuning; o ticket 06 ganha uma checagem de estabilidade por fold.
7. **O `S = (Acc + F1w)/2` sai.** O §0.3 do plano mostra Pearson 0,999997 entre os dois termos. → MCC passa a
   ser o escalar de seleção e do Pareto 3D (MCC × p95 com B = 1 × PSS), com hipervolume.
8. **Estrutura.** As fases 2 e 3 ganham specs próprias. O código de inferência vira um membro de workspace
   uv (`edge/`, pacote `edge_bench`) com dependências mínimas para o Pi e o mesmo `uv.lock` do treino, o que
   resolve o desalinhamento de versão do item 3 por construção.

---

## 2. Análise por pergunta

### 2.1 Treino sem vazamento (pergunta 1)

#### a) Unidade do split

**Fatos [medido]:**

| Medida | Valor |
|---|---|
| Fluxos bidirecionais (IP:porta ordenados; sem IP → par de MAC) | 1.329 |
| Fluxos com rótulo misto / linhas neles | 50 / 4.025 |
| Maior fluxo (HTTP `192.168.1.196 ↔ 91.189.88.148:80`, `normal`) | 7,66% das linhas |
| Hosts de origem do DoS / maior emissor | 14 / `192.168.1.196`, com 40.751 dos 45.514 DoS (e 7.284 normais) |
| Janela do DoS / captura | 225,6–789,5 s / 0–942,1 s |
| Vetores de features distintos (22 features) | 32.359 em 94.625 linhas |
| Teste com duplicata exata no treino (todas / DoS / normal) | 73,9% / 83,1% / 65,4% |
| Teste cujo vetor aparece no treino com o outro rótulo | 8,6% (piso de erro irredutível) |
| Teste cujo fluxo também está no treino (split do artigo) | 99,97% |

DecisionTree default, `SimpleImputer(0)`, 22 features:

| Esquema | F1 macro | MCC | Observação |
|---|---|---|---|
| Hold-out do artigo (estratificado, seed 42) | 0,9694 | 0,9391 | recall DoS 0,957; FPR 0,019 |
| `StratifiedKFold(5)` (média dos folds) | 0,9692 (dp 0,0012) | 0,9385 | |
| `StratifiedGroupKFold(5)` por fluxo (média) | 0,9675 (dp 0,0041) | 0,9352 | folds de 0,9617 a 0,9723 |
| Temporal por classe (80% iniciais de cada classe → treino) | 0,9715 | 0,9430 | só 18,7% dos pacotes de teste em fluxos vistos no treino |
| Temporal global (corte em 748,3 s) | não avaliado | — | treino 34.297 DoS / 41.403 normal; teste 11.217 / 7.708: o teste só cobre os últimos ~41 s do ataque e muda a prevalência (59% contra 48%) |

**Diagnóstico.** O split por pacote coloca o mesmo fluxo nos dois lados, e três em cada quatro linhas de
teste têm gêmea no treino. Mesmo assim, para a árvore, agrupar por fluxo custa 0,0017 de F1 macro, menos que
a meia largura do IC (0,0024), e o split temporal por classe não piora. A leitura mais provável é que as
duplicatas são uma propriedade do ataque (inundação de PUBLISH quase idênticos em muitos fluxos), não de um
fluxo específico. Por isso, separar fluxos não tira do teste os gêmeos que importam. **[hipótese]** Isso pode
não valer para modelos que memorizam a vizinhança (RF profundo, SVM RBF); o ticket 09 mede todas as famílias.

**O que não se consegue medir com este dataset:** generalização para um **atacante novo**. Com 89,5% do DoS
saindo de um host, um "deixa um host de fora" não tem classes suficientes nos folds. Isso entra como
limitação declarada no artigo, não como experimento.

**Opções.**

| Opção | Prós | Contras |
|---|---|---|
| A. Manter só o split do artigo | comparabilidade total | não responde ao revisor que perguntar por vazamento entre fluxos |
| B. Trocar o primário para `StratifiedGroupKFold` por fluxo | metodologicamente mais conservador | muda todos os números do artigo; a CV do Optuna também teria de ser agrupada (custo zero em tempo, mas é refatoração); efeito medido pequeno |
| C. **Primário = artigo, mais um experimento obrigatório de robustez com critério de troca** | comparabilidade e defesa; a decisão fica ancorada em dado | um ticket a mais |

**Recomendação: C.** O `RunConfig` ganha `split_strategy: Literal["stratified_random", "flow_group",
"temporal_per_class"] = "stratified_random"`, e a CV do tuning herda a unidade do split. O ticket 09
(experimento) precede o 10 (modo corrigido).

**Critério de decisão do ticket 09:** para cada família de modelo, compute a diferença de F1 macro e de MCC
entre o split do artigo e o `flow_group`, com 5 sementes.

- Se |ΔMCC| ≤ 0,005 em todas as famílias, o artigo fica primário e a tabela de robustez vai para o apêndice.
- Se ΔMCC > 0,01 em alguma família, o `flow_group` vira primário (ticket 10 roda o grid completo nele) e os
  números do artigo passam a ser reportados como "otimistas (reprodução)".
- Entre 0,005 e 0,01, os dois aparecem lado a lado e o primário é o `flow_group`.

#### b) Seleção de features fora da validação cruzada

**Fato [medido]:** ANOVA top-15 ajustado no treino inteiro contra reajustado dentro de cada fold: o mesmo
conjunto nos 5/5 folds e o mesmo F1 de CV (0,9690 ± 0,0011). Com 22 candidatas e k = 15, o seletor tem pouca
margem para sobreajustar.

**Custo de pôr o seletor no `Pipeline` do tuning:** um reajuste por trial e por fold, ou seja
6 × 7 × 30 × 5 = 6.300 ajustes de seletor. O ANOVA leva milissegundos. MutualInformation e ExtraTrees custam
segundos em 60 mil linhas **[hipótese]**, o que daria horas a mais no grid.

**Recomendação:** não mover. O ticket 06 ganha uma verificação de estabilidade: o Jaccard entre o conjunto
do treino inteiro e o de cada fold, por seletor. Se o Jaccard mínimo de algum seletor ficar abaixo de 0,8, a
melhor configuração desse seletor é reavaliada uma vez com o seletor dentro da CV, e a diferença é reportada.

#### c) Escolha da melhor configuração usando o teste

**Fato [código]:** o ticket 08 pede o "melhor modelo por seletor" sem dizer a fonte; o código antigo escolhia
pelo teste. **Fato [medido]:** o IC do F1 macro no teste tem meia largura de cerca de 0,0024, e
DecisionTree, GB e RF antigos ficam a menos de 0,0011 uns dos outros.

**Opções:** CV aninhada (5 externos × 42 × 30 trials × 5 internos, inviável com o SVM: 123 s por ajuste nas
75,7 mil linhas); partição de validação separada (tira dados do treino); **seleção pela média de CV que o
Optuna já calcula, de custo zero**.

**Recomendação:** escolher pela média de CV (MCC e F1 macro guardados como `user_attrs` de cada trial). O
teste é avaliado uma única vez para as 42 configurações. Entre as configurações a até 1 erro-padrão da
melhor média de CV, fica a de menor custo (§2.2). O viés residual, o de escolher o máximo entre 42 médias de
CV, é reportado como a correlação de postos entre CV e teste.

#### d) Gaps calculados antes do split

**Diagnóstico:** não é vazamento, em nenhuma unidade de split. O gap de um pacote usa só o tempo de pacotes
**anteriores**, sem rótulo (ADR 0001). Em produção o detector também vê todos os pacotes anteriores, sejam eles
"de treino" ou "de teste". No split temporal, o primeiro pacote de teste usa o último do treino, que é
exatamente a condição de produção. A ADR 0001 e a decisão 2 ficam como estão; a decisão nova 45 só registra
esta conclusão.

#### e) A assimetria "o pacote é MQTT?"

**Fatos [medido]:**

| Recorte | DoS | normal |
|---|---|---|
| Pacotes MQTT (`mqtt.msgtype` não nulo) | 39.044 | 491 |
| … dentro da janela do ataque | 39.044 | 275 |
| PUBLISH (msgtype 3) | 37.626 | 237 |
| PINGREQ/PINGRESP (12/13) | 11 | 219 |
| Porta 1883 / HTTP(S) / sem TCP / outro TCP | 45.330 / 32 / 54 / 98 | 969 / 35.538 / 6.111 / 6.493 |

| Avaliação no teste do artigo (DecisionTree) | F1 macro | MCC | recall DoS | FPR |
|---|---|---|---|---|
| Completa | 0,9694 | 0,9391 | 0,957 | 0,019 |
| Regra "é MQTT ⇒ DoS" | 0,9294 | 0,8661 | 0,864 | 0,008 |
| Sem nenhuma feature `mqtt.*` (5 features) | 0,8740 | 0,7485 | 0,886 | 0,137 |
| Só pacotes MQTT (7.861 DoS, 80 normal) | 0,9667 | 0,9343 | 0,999 | 0,025 (2/80; IC 0,7%–8,7%) |
| Só pacotes não MQTT (1.242 DoS, 9.742 normal) | 0,8617 | 0,7272 | 0,692 | 0,019 |

**Diagnóstico:** não é vazamento em sentido estrito, porque `mqtt.msgtype` existe em produção. É um
**artefato de coleta** que ameaça a validade de construto: no cenário normal quase não há tráfego de aplicação
MQTT, e o modelo aprende "tráfego MQTT ≈ ataque". Num gateway MQTT real quase todo o tráfego é MQTT, então o
número decisivo é o FPR em MQTT normal, e ele vem de 80 pacotes.

**Recomendação (ticket 11, experimento):** baseline de regra nas tabelas; métricas recortadas por `is_mqtt` e
por msgtype; FPR em MQTT normal com IC de Wilson. Critério: se o limite superior do IC passar de 5%, o artigo
declara que o FPR em tráfego MQTT legítimo não está estimado com precisão útil e propõe validação externa (P2:
normal das capturas `Intrusion.csv`/`MitM.csv`, se forem do mesmo testbed).

#### f) Outros pontos

- **Imputação constante 0** junta "campo ausente" com zero legítimo (há 22 pacotes DoS com `msgtype = 0`). Para
  árvores, não muda nada que importe; para LDA/QDA, muda. Recomendação: manter no modo do artigo e propor
  `add_indicator=True` como variante no ticket 09, sem trocar o default.
- **Calibração `cv=3` com `ensemble=False`** usa só o treino, então não vaza. A calibração sigmoide pode mudar
  o `argmax` e, portanto, o F1; o tuning tem de otimizar o mesmo Pipeline que é implantado (como já está).
- **Subamostra do SVM (15k):** o `C` ótimo depende de n. Não é vazamento; é ameaça à validade do SVM. Registrar.
- **`random_state` único (42):** os resultados ficam condicionados a um só split. O ticket 09 repete a
  avaliação com 5 sementes para as melhores configurações de cada família (barato fora do SVM).
- **`frame.cap_len ≡ frame.len`** (pendência nº 21 do LOG) torna a matriz de covariância de LDA/QDA singular;
  o tratamento fica no ticket 06.

#### Comparabilidade com o artigo, e como aparece no curso

O modo do artigo (`RunConfig()` default) continua sendo o caminho das aulas 04–08. O modo corrigido é uma
aula própria (ticket 10), depois que o experimento (09) mostra a diferença. Se o critério do 09 mantiver o
artigo como primário, o ticket 10 se reduz à tabela de robustez.

**Vira trabalho:** reescreve os tickets 04 (recortes, MCC, IC), 06 (estabilidade), 07 (métricas de CV,
`cv_splitter`) e 08 (escolha pela CV). Cria os tickets 09, 10 e 11 e o ADR 0002. Gera as decisões 44 a 50.
Aulas desatualizadas: 02 (as colunas de IP e porta continuam no bruto para agrupar) e 03 (a ordem do pipeline
de dados ganha `flow_key`) — ver §3.

### 2.2 Seleção das configurações para inferência (pergunta 2)

**Critério de qualidade.** Proponho o MCC como escalar de seleção e de Pareto. Ele é simétrico, não colinear
com a acurácia e continua informativo dentro do recorte MQTT, onde a proporção é 99% para 1% (§2.1e). O F1
macro continua como objetivo do Optuna, por ser o do artigo. Toda tabela traz também recall de DoS, FPR de
normal e FPR em MQTT normal com IC.

**Triagem de custo antes do Pi (na máquina de desenvolvimento), por configuração:**

1. latência de `predict` em B = 1 e B = 1024, em processo novo, threads = 1, com `perf_counter_ns` e
   `thread_time_ns`, n ≥ 2.000 chamadas após aquecimento;
2. tamanho do `.joblib` e complexidade estrutural (nós totais, número de árvores, vetores de suporte);
3. USS e PSS em regime depois de carregar e aquecer, e `ru_maxrss` do processo novo;
4. CPU-segundos por registro.

| Transfere para o Pi | Não transfere |
|---|---|
| tamanho em disco; complexidade estrutural; ordem de grandeza entre famílias | latência absoluta (Cortex-A72 contra x86, NEON contra AVX2); BLAS (OpenBLAS ARM contra a pilha x86); L2 de 1 MB do A72 (percorrer um RF depende de cache); tamanho de página (4 KiB no Pi 4; o kernel padrão do Pi 5 usa 16 KiB, o que muda RSS/PSS); RAM total |

**Verificação da transferência:** de 6 a 8 configurações que cubram a faixa de custo, medidas nas duas
máquinas. Critério: Spearman ρ ≥ 0,9 entre os postos de p95 (B = 1) e nenhuma inversão entre candidatas ao
Pareto, para confiar na triagem. Abaixo disso, todas as candidatas são medidas no Pi.

**Diferença entre configurações:** sobre o mesmo teste, usar o bootstrap pareado de ΔMCC (reamostrando
índices em conjunto, B = 2.000), o McNemar exato nos pares discordantes e a correção de Holm contra a melhor.
Equivalência prática: o IC 95% de ΔMCC inteiro dentro de ±0,005. Desempate entre equivalentes: menor p95
offline, depois menor PSS, depois menos features, depois família mais simples.

**Quantas levar ao Pi, e quais.** "Melhor por seletor" desperdiça bateria: com a árvore dominando a
qualidade, ele leva seis árvores praticamente idênticas, e o LowVariance-DT e o ExtraTrees-DT antigos têm
acurácia e FP/FN idênticos, [112, 354]. Recomendo:

- a **melhor de cada família de modelo**, pela média de CV com desempate por custo (7);
- mais as **não dominadas do Pareto 3D offline** (MCC de CV × p95 offline × PSS offline);
- com teto de cerca de 10;
- e o **conjunto LowVariance × {LDA, DT, GB, RF, SVM}** garantido, para comparar com o t16 (P8).

Mais de um seletor da mesma família só entra se for não dominado no 3D. A etapa 1 do plano (§6.1, triagem no
Pi) roda sobre esse conjunto; a etapa 2 (confirmação) roda só sobre o Pareto medido no Pi.

**Vira trabalho:** tickets novos 12 (comparação pareada), 13 (pacote `edge_bench` e profiler), 14 (triagem
offline) e 15 (escolha e bundle); decisões 49, 51 e 59.

### 2.3 Dados de teste na API (pergunta 3)

**Fatos [código/medido]:**

- O servidor atual lê o CSV a cada `POST /benchmark`, recarrega o `.pkl` (o `discover_models()` carrega os 43
  só para ler `feature_names_in_`) e cronometra `predict` no lote inteiro.
- Os CSVs de LDA/QDA estão escalonados e os demais não.
- O `requirements.txt` da API fixa `scikit-learn>=1.8,<1.9`, e o treino novo está em 1.9.1.
- O t16 mediu acurácia 0,9688 onde o relatório diz 0,9754.

| | 1. Servidor lê o CSV | 2. Lotes em JSON | 3. Binário (`.npy`/bruto) | 4. Reprodução de tráfego |
|---|---|---|---|---|
| A latência inclui | parsing do CSV (se dentro do cronômetro) e `predict` do lote | HTTP + `json.loads` + Pydantic + `ndarray` + `predict` | HTTP + `np.frombuffer` (µs) + `predict` | broker, captura, extração das features, gaps online, `predict` |
| Memória e CPU incluem | DataFrame de 18.925 linhas, parser do pandas, **page cache do CSV** (conta em `memory.current`) | buffers de JSON e objetos Pydantic (227 mil floats em B = 18.925) | só o buffer, de 1,82 MB em float64 com B = 18.925 | broker e extrator, se no mesmo cgroup |
| Fidelidade a IDS (B = 1) | nenhuma | boa | boa | máxima |
| Identidade dos dados | sha256 do CSV | depende do cliente | sha256 do `.npy` e paridade | exige teste de paridade extrator × CSV |
| Serialização em B = 1 / B = 18.925 | — / leitura do CSV | dezenas de µs / dezenas de ms **[hipótese, medir]** | ~µs / ~µs mais a transferência (~15 ms a 1 Gb/s) | — |
| NaN (contrato novo) | nativo | **JSON não tem NaN**: exige `null` → `float \| None` → `np.nan`, ou o token `NaN` não padrão | nativo | nativo |

**Recomendação:** a opção 3 é o caminho de medição: `POST /predict` com `application/octet-stream`, float64
C-order e cabeçalhos `X-Rows`/`X-Cols`/`X-Dtype`, com B como fator. A opção 2 é medida uma vez como variante
"de produção", para quantificar o custo de JSON e Pydantic (ticket 17). A opção 1 sai do caminho de medição e
vira só a **verificação de paridade** no startup. A opção 4 é o E9, registrado como ticket 22 bloqueado
(depende do pcap original, P2).

**Duas armadilhas do contrato novo, que viram critério de aceite:**

1. `sklearn.set_config(assume_finite=True)`, usado no `edge_bench`, não pode mudar a saída com NaN na entrada.
   Teste: as saídas com e sem a configuração têm de ser iguais.
2. Um Pipeline ajustado com DataFrame emite `UserWarning` ("X does not have valid feature names") a cada
   `predict` com `ndarray`. Isso pesa em B = 1. A API valida `feature_names_in_` contra o manifesto **uma vez**
   no startup e filtra esse aviso; o ticket 17 mede DataFrame × ndarray × ndarray sem o aviso.

**O que o treino exporta (muda o ticket 08), por configuração em `outputs/<run>/configs/<selector>__<model>/`:**

- `pipeline.joblib`
- `X_test.npy` (float64, colunas na ordem de `feature_names_in_`, NaN preservado)
- `y_test.npy` (int8, com o mapa de rótulo no manifesto)
- `test_index.npy` (índices de linha em `DoS.csv`)
- `y_pred_expected.npy` e `proba_expected.npy`
- `test_raw.csv` (mantido como proveniência, decisão 1)
- `config_manifest.json`: features, sha256 de cada arquivo, melhores parâmetros, métricas de CV e de teste,
  tamanho e complexidade estrutural

No nível do run, `manifest.json` registra: `RunConfig` serializado, commit git e flag de árvore suja, sha256
do `DoS.csv`, `split_strategy`, versões (Python, numpy, pandas, scikit-learn, optuna, joblib) e plataforma.

**O que a API grava em `run_meta`:**

- modelo da placa (`/proc/device-tree/model`) e RAM;
- SO, kernel e tamanho de página;
- versão do cgroup, controladores ativos e caminho do cgroup do processo; existência e capacidade de reset
  do `memory.peak`;
- governor e frequências;
- variáveis de thread e `threadpoolctl.threadpool_info()` (biblioteca BLAS, versão, threads, arquitetura);
- versões de numpy, scipy, scikit-learn, joblib, FastAPI e uvicorn;
- temperatura e `get_throttled` no início e no fim;
- runtime de container;
- sha256 do modelo, do `X_test.npy` e do manifesto;
- resultado da paridade.

A maior parte já sai de `host_fingerprint()`; faltam `threadpoolctl`, o tamanho de página, os hashes e a
paridade.

**Vira trabalho:** reescreve o ticket 08; cria os tickets 15, 16 e 17, o ADR 0003 e as decisões 52 a 54 e 62.

### 2.4 Pico de CPU, memória e GPU no dispositivo (pergunta 4)

**O `PeakMemoryProfiler`, pela descrição do briefing:**

- **Aproveita-se:** a forma de context manager; o processo filho com `spawn` por medição; `queue.get()` antes
  de `join()`; a ideia de delta sobre um snapshot.
- **Muda:** sem torch; o escopo deixa de ser fixo e passa a ser resolvido por `/proc/self/cgroup`, com
  registro de qual fonte foi usada; o pico passa a ser `ru_maxrss`/`VmHWM` do filho, e não o USS do fim.
- **Escreve-se do zero:** CPU (`getrusage`, `thread_time_ns`, `schedstat`, `cpu.stat`, PSI), PSS em regime,
  `memory.stat` (anon contra file), escopo dedicado por configuração, timeout e limpeza.

**Grandezas e para que servem:**

- **Memória de pico** (OOM): `ru_maxrss` de um processo novo que carrega e roda a rajada. Entra no RSS só a
  página residente; o page cache de `read()` do `.joblib`/`.npy` não entra, o que torna esse o número mais
  limpo para "custo do modelo".
- **Memória em regime** (quantos modelos e workers cabem): PSS do worker depois do carregamento e do
  aquecimento. **É o eixo de memória do Pareto 3D.** As duas são reportadas.
- **Tempo de CPU por inferência** (`thread_time_ns` em volta do `predict`; `getrusage` por janela): é estável
  sob contenção e é o eixo de custo entre níveis de estresse.
- **Utilização de pico por núcleo e PSI** (`cpu.pressure` do cgroup e `/proc/pressure/cpu`): medem
  diretamente a contenção que o §0.1 estima de forma indireta.
- **GPU:** não usada. O manifesto registra `gpu_backend: "none"` e o `vcgencmd get_mem gpu` (RAM reservada
  à VideoCore, que reduz a RAM útil). O ramo CUDA não é portado; se algum dia houver Jetson, aplica-se
  `device.startswith("cuda")` e pico alocado contra reservado.

**Escopo.** "Quanto este modelo custa no Pi" é respondido pelo **processo worker dentro de um cgroup só dele**,
criado por `systemd-run --scope -p MemoryAccounting=yes -p CPUAccounting=yes` ao redor de `uvicorn --workers 1`,
com o sampler num escopo à parte e o gerador de carga em outro host. As outras opções:

- o cgroup do container soma o master do uvicorn e todos os workers;
- o sistema inteiro soma tudo, inclusive o page cache, que é o que o t16 mediu;
- `memory.current` e `memory.peak` incluem o page cache dos arquivos lidos, então reportam-se `anon` e `file`
  de `memory.stat`.

**Efeito sombra e reset:**

| Mecanismo | Pico limpo? | Requisito | Etapa do plano (§6.1) |
|---|---|---|---|
| Processo novo por configuração (`ru_maxrss`) | sim, inclui a carga do modelo | nenhum | triagem e confirmação (padrão) |
| `/proc/self/clear_refs` ← `5` e depois `VmHWM` | sim, por janela, por processo | kernel ≥ 4.0, mesmo usuário | pico por tamanho de lote dentro de um processo |
| Escopo cgroup novo por configuração | sim, `memory.peak` nasce zerado | cgroup v2 com `memory` (comando C3) | triagem e confirmação (validação cruzada) |
| Reset do `memory.peak` | sim, só no **mesmo descritor** | kernel ≥ 6.12; um único descritor por cgroup | pico por janela no cgroup |
| Amostragem contínua (sampler a 200 Hz) | não (perde picos curtos) | — | só curvas (figura F5), nunca o número da tabela |

O uso de um único descritor por cgroup vem de uma correção de 2026 ainda em revisão para um bug em que o
reset de um descritor rebaixa o pico lido por outros.

**Efeito do observador.** São duas execuções por célula:

- **L (latência):** só `perf_counter_ns` e `thread_time_ns` por fase, sem sampler e sem leituras de `/proc`
  por requisição; `getrusage` uma vez por janela, fora do cronômetro.
- **R (recursos):** com sampler, cgroup e PSS.

Experimento V2 (ticket 19): p95 em B = 1 no `/ping` e na árvore, com e sem o sampler e com e sem leituras por
requisição, n ≥ 10.000, em blocos aleatorizados. Se Δp95 ≤ máx(2%, 5 µs), L e R podem ser fundidas.

**Granularidade.** Algumas grandezas exigem contador acumulado:

- `ru_maxrss`/`VmHWM`, `memory.peak`;
- `cpu.stat`, `thread_time_ns`, `schedstat`, `nivcsw`, `majflt`;
- os totais de PSI.

Outras podem ser amostradas: a curva de RSS, a utilização por núcleo, a temperatura e a frequência.
Experimento V3: numa rajada de 10.000 chamadas B = 1 de RF, comparar o máximo amostrado com o pico do
contador. Se o máximo amostrado subestimar o pico em mais de 5%, só contadores entram nas tabelas, o que é o
esperado.

**Threads.** `OMP/OPENBLAS/MKL/NUMEXPR_NUM_THREADS=1` no ambiente antes do processo, mais
`threadpoolctl.threadpool_limits(1)` e `n_jobs=1` depois do `joblib.load`, e `threadpool_info()` gravado.
Na bateria principal isso é uma **constante registrada**. O fator `{1, 4}` entra só num subexperimento com
LDA e RF no regime operacional.

**Condições do dispositivo.**

- Governor em `performance`.
- `get_throttled` igual a `0x0` antes e depois; qualquer bit de 0 a 3 no fim descarta a célula.
- Temperatura inicial abaixo de 55 °C (espera de resfriamento entre células); temperatura máxima abaixo de
  80 °C, onde começa o limite suave do Pi 4.
- `majflt` = 0 na janela.
- Sampler a pelo menos 90% da taxa nominal.
- Aquecimento fixo de 200 requisições, com o cold start registrado à parte.
- Ordem das células sorteada; até duas repetições por célula descartada, e depois a célula fica marcada.

**Os defeitos do profiler (briefing, itens 1–8):**

| # | Defeito | Invalida no Pi? | Corrigir antes do artigo? |
|---|---|---|---|
| 1 | efeito sombra do `memory.peak` | sim | sim (processo ou escopo novo; ver o bug equivalente no `edge_bench`, §0.4) |
| 2 | caminhos fixos de cgroup e fallback silencioso | sim, fora de Docker | sim (resolver por `/proc/self/cgroup` e falhar alto) |
| 3 | page cache em `memory.current` | sim, para atribuição | sim (`memory.stat` anon/file; pico primário por `ru_maxrss`) |
| 4 | fallback de pico devolve o USS atual | sim | sim |
| 5 | observador no trecho cronometrado | sim, para latência | sim (execuções L/R) |
| 6 | `"cuda:0"` desliga a GPU | não (sem CUDA no Pi) | não; corrigir só se houver hospedeiro com GPU |
| 7 | filho morto por OOM trava o pai | sim, nos perfis D2/D3 com `memory.max` | sim, antes dos perfis D (timeout, `exitcode`, `try/finally`; OOM vira resultado, E11) |
| 8 | filho no mesmo cgroup do pai | sim, para números de cgroup | sim (escopo próprio para o filho, ou só métricas de processo) |

**Protocolo de medição de recursos:**

| Grandeza | Unidade | Fonte | Escopo | Contador / amostra | Execução | Linha do dicionário |
|---|---|---|---|---|---|---|
| Pico de memória do processo | B | `getrusage(RUSAGE_SELF).ru_maxrss` (KiB) ou `VmHWM` com `clear_refs` | processo novo por config | contador | R | `maxrss_b` (existente) |
| Pico de memória do cgroup | B | `memory.peak` (escopo novo, ou reset no mesmo descritor em kernel ≥ 6.12) | escopo do worker | contador | R | `cg_peak_b` (existente) |
| Memória anon / file do cgroup | B | `memory.stat` (`anon`, `file`) no fim da janela | escopo do worker | contador | R | **nova:** `cg_anon_b`, `cg_file_b` |
| PSS / USS em regime | B | `/proc/<pid>/smaps_rollup` após carga e aquecimento, e no fim | worker | leitura pontual | R | `pss_b uss_b` (existente) |
| Footprint de carga do modelo | B | `statm` antes e depois de `joblib.load` | worker | leitura pontual | R | `model_rss_delta_b` (existente) |
| Tamanho em disco | B | `os.stat` | arquivo | — | meta | `model_size_disk_b` (existente) |
| CPU de thread no predict | ns | `time.thread_time_ns()` | thread | contador | L | `predict_cpu_ns` (existente) |
| CPU user / sys por janela | s | `getrusage` em volta da janela | processo | contador | L e R | `cpu_user_s cpu_sys_s` (existente) |
| CPU-segundos por registro | s | derivada | processo | contador | L | `cpu_seconds_per_record` (existente) |
| Uso e throttling do cgroup | µs | `cpu.stat` | escopo | contador | R | `cg_usage_usec`, `cg_throttled_usec` (existentes) |
| Espera em runqueue | ns | `/proc/self/schedstat` [1] | processo | contador | R | `runqueue_wait_ns` (existente) |
| Pressão de CPU (PSI) | µs | `cpu.pressure` (`some total`) do escopo; `/proc/pressure/cpu` | escopo / sistema | contador | R | **nova:** `cg_cpu_psi_some_us`, `sys_cpu_psi_some_us` |
| Utilização por núcleo (pico) | % | `/proc/stat` pelo sampler a 10 Hz | sistema | amostra | R | **nova:** `cpu_core_util_max_pct` |
| Faltas maiores / swap | contagem / B | `getrusage.ru_majflt`, `memory.swap.current` | processo / escopo | contador | L e R | `majflt`, `swap_b` (existentes) |
| Temperatura, frequência, throttling, governor | °C, kHz, máscara | `vcgencmd`, `sysfs` | SoC | início e fim, mais 1 Hz em R | L e R | existentes |
| GPU | — | constante `gpu_backend="none"`; `vcgencmd get_mem gpu` | dispositivo | meta | meta | **nova:** `gpu_backend`, `gpu_mem_split_mb` |
| Tamanho de página e BLAS | B / texto | `getconf PAGESIZE`; `threadpool_info()` | dispositivo / processo | meta | meta | **nova:** `page_size_b`, `blas_info` |

**Experimentos que validam o protocolo no Pi (ticket 19):**

- **V1. Mesmo processo contra processo novo.** Carregar a configuração A e depois a B num processo, e
  comparar o pico e o delta de B com B medida num processo novo. Se diferirem em mais de 5%, o processo novo
  por configuração é obrigatório, o que é o esperado.
- **V2. Custo do observador.** Ver o parágrafo "Efeito do observador".
- **V3. Amostra contra contador.** Ver o parágrafo "Granularidade".
- **V4. Reset do `memory.peak`.** Abrir o arquivo, escrever, alocar 100 MB com numpy e ler pelo mesmo
  descritor. Se a leitura der cerca de 100 MB mais a linha de base, o reset funciona; caso contrário, usar
  escopo novo por janela.
- **V5. Threads.** O `threadpool_info()` tem de mostrar `num_threads=1`, e o `SVC.predict` com 1 e com 4
  threads não deve mudar (confirma a §0.4, item 3). Se o SVM mudar, o SVM também entra no subexperimento de
  threads.

**Vira trabalho:** tickets 13, 18, 19 e 20; ADR 0004; decisões 56 a 58 e 61; linhas novas no dicionário.

---

## 3. Mapa de reestruturação

Princípio: **nenhum arquivo de ticket é renomeado.** Os tickets 04–08 continuam no mesmo número e arquivo,
porque `mkdocs.yml` e `docs/index.md` (que eu não posso alterar) apontam para eles. Os que ficaram grandes
dividem a **aula** em NN-1 e NN-2, como a decisão 26 prevê.

| Ticket atual | Ação | Nº final | Fase | Motivo (seção) | Decisões | Aula escrita desatualizada e o que muda |
|---|---|---|---|---|---|---|
| 01 Scaffolding | manter | 01 | 1 Treino | — | — | — |
| 02 Carga e limpeza | manter (sem mudança de critério) | 02 | 1 | §2.1a, §2.1e | 45 | `02-carga-e-limpeza.md`: (a) dizer que IP, portas e MAC saem das **features**, mas continuam no bruto para agrupar (ticket 09); (b) a pendência nº 20 ("é MQTT?") ganha encaminhamento: ticket 11 |
| 03 Gaps sem vazamento | manter | 03 | 1 | §2.1d | 45 | `03-gaps-sem-vazamento.md`: (a) um parágrafo explicando que os gaps não vazam em nenhuma unidade de split, porque são causais; (b) "Onde estamos" mostra a ordem nova `load_raw → add_gaps → flow_key → drop_unused_columns` (o passo novo entra no ticket 09) |
| 04 Split, Pipeline e avaliação | reescrever (aulas 04-1 split e Pipeline; 04-2 avaliação) | 04 | 1 | §2.1c, §2.1e, §2.2 | 49 | — (sem aula) |
| 05 Registro e baseline | reescrever | 05 | 1 | §2.1e | 50 | — |
| 06 Seleção de features | reescrever | 06 | 1 | §2.1b, §2.1f | 47 | — |
| 07 Optuna por seletor | reescrever | 07 | 1 | §2.1a, §2.1c | 46, 48 | — |
| 08 Artefatos e análise | reescrever (aulas 08-1 exportação e manifesto; 08-2 análise pela CV) | 08 | 1 | §2.1c, §2.3 | 48, 52 | — |
| novo | criar (experimento) | 09 Unidade do split e sementes | 1 | §2.1a, §2.1f | 44, 45 | — |
| novo | criar (condicional ao 09) | 10 Modo corrigido do `RunConfig` | 1 | §2.1a | 44, 46 | — |
| novo | criar (experimento) | 11 Detecta DoS ou detecta MQTT? | 1 | §2.1e | 50 | — |
| novo | criar | 12 Comparação estatística pareada | 2 Avaliação | §2.2 | 51 | — |
| novo | criar | 13 Pacote `edge_bench` e profiler de processo novo | 2 | §2.2, §2.4 | 55, 56, 57 | — |
| novo | criar | 14 Triagem offline de custo | 2 | §2.2 | 59 | — |
| novo | criar | 15 Escolha para o Pi e bundle | 2 | §2.2, §2.3 | 59, 53 | — |
| novo | criar | 16 API nova: `/predict` binário e paridade | 3 Dispositivo | §2.3 | 53, 54, 62 | — |
| novo | criar | 17 Linhas de base e variante JSON | 3 | §2.3 | 54 | — |
| novo | criar | 18 Instrumentação de recursos no Pi | 3 | §2.4 | 56, 57, 58 | — |
| novo | criar (experimento) | 19 Validação do protocolo no Pi (V1–V5) | 3 | §2.4 | 56 | — |
| novo | criar | 20 Gerador de carga e matriz de execuções | 3 | §2.4; plano §3, §5, §6 | 56 | — |
| novo | criar | 21 Pareto 3D, hipervolume e tabelas | 3 | §2.2, §2.4 | 49, 59 | — |
| novo | criar (status **bloqueado**) | 22 Latência pacote-a-veredito (E9) | 3 | §2.3 | 63 | — |
| spec 0000 | reescrever como spec da fase 1 (mesmo arquivo) | 0000 | 1 | todas de §2.1 | 60 | — |
| — | criar | spec 0001 avaliação e seleção | 2 | §2.2 | 60 | — |
| — | criar | spec 0002 inferência e medição no dispositivo | 3 | §2.3, §2.4 | 60 | — |
| — | criar | ADR 0002 unidade do split | 1 | §2.1a | 44 | — |
| — | criar | ADR 0003 contrato de dados treino → API | 1–3 | §2.3 | 52, 53 | — |
| — | criar | ADR 0004 escopo da medição de recursos | 3 | §2.4 | 56 | — |

Também ficam desatualizados, e são da autora: `docs/index.md` (o "Mapa das aulas" só vai até 08), a `nav` do
`mkdocs.yml` (tickets 09–22, specs 0001–0002, ADRs 0002–0004), a definição de "Fronteira de Pareto" no
`docs/glossario.md` e no `GLOSSARY.md` (a Etapa B acrescenta "Fronteira de Pareto 3D" ao `GLOSSARY.md`; a
página do site é aula da autora) e o `AGENTS.md`, cujas seções "Deploy models" e "Pareto" ainda citam `S`.

---

## 4. Decisões novas (texto para acrescentar ao fim de `docs/decisions.md`)

```markdown
## 2026-10-30

Contexto: análise metodológica da Etapa A (`docs/analises/claude-science-2026-10-30.md`), aprovada pela
autora em AAAA-MM-DD. Números entre colchetes referem-se às seções do relatório.

44. **Unidade do split (ADR 0002).** O split estratificado aleatório 80/20, seed 42, continua sendo o
    primário do modo do artigo. O `RunConfig` ganha `split_strategy` (`stratified_random`, `flow_group`,
    `temporal_per_class`), com default `stratified_random`. O ticket 09 decide, pelo critério escrito nele,
    se o primário muda. Motivo: o efeito medido do agrupamento por fluxo numa árvore foi de 0,0017 de F1
    macro, abaixo do ruído do teste [§2.1a]. Complementa a decisão 2, sem substituí-la.
45. **Chave de fluxo e ordem do pipeline de dados.** O fluxo é a 5-tupla bidirecional (IP:porta ordenados);
    pacotes sem IP são agrupados pelo par de MAC. A chave sai do bruto antes da limpeza:
    `load_raw → add_gaps → flow_key → drop_unused_columns`. **Substitui a decisão 41** só na ordem. Os gaps
    não vazam em nenhuma unidade de split, porque são causais e não usam rótulo [§2.1d]; a ADR 0001 fica
    como está.
46. **A CV do tuning herda a unidade do split.** Com `flow_group`, o Optuna usa `StratifiedGroupKFold` com
    os mesmos grupos. O tuning recebe um `cv_splitter` em vez de construir o `StratifiedKFold` por dentro.
    Complementa a decisão 14.
47. **Seletores ajustados uma vez, com checagem de estabilidade.** A decisão 17 fica como está. O ticket 06
    mede o Jaccard entre o conjunto do treino inteiro e o de cada fold. Se o mínimo ficar abaixo de 0,8, a
    melhor configuração desse seletor é reavaliada com o seletor dentro da CV [§2.1b].
48. **A escolha de configuração nunca usa o teste.** O ranking e a escolha usam a média de CV (MCC e F1
    macro guardados por trial). O teste é avaliado uma vez para todas as configurações. Entre as
    configurações a até 1 erro-padrão da melhor, fica a de menor custo. A correlação de postos entre CV e
    teste é reportada [§2.1c].
49. **Métricas acrescentadas e escalar de Pareto.** Às métricas da decisão 11 somam-se MCC, recall de DoS,
    FPR de normal, FPR em pacotes MQTT normais com IC de Wilson e IC bootstrap de 95% do F1 macro e do MCC.
    O MCC é o escalar de seleção e de Pareto; o `S = (Acc + F1w)/2` deixa de ser usado. O objetivo do Optuna
    continua F1 macro (decisão 14).
50. **Baseline de regra e recortes por MQTT.** A regra "pacote é MQTT ⇒ DoS" entra em toda tabela de
    baseline, e as métricas são recortadas por `is_mqtt` e por `mqtt.msgtype` (ticket 11) [§2.1e].
51. **Comparação entre configurações.** Bootstrap pareado de ΔMCC (2.000 reamostras), McNemar exato e
    correção de Holm contra a melhor. Equivalência prática: o IC de ΔMCC inteiro dentro de ±0,005.
    Desempate: p95 offline, depois PSS, depois número de features, depois família mais simples [§2.2].
52. **Exportação treino → API (ADR 0003).** Por configuração: `pipeline.joblib`, `X_test.npy`, `y_test.npy`,
    `test_index.npy`, `y_pred_expected.npy`, `proba_expected.npy`, `test_raw.csv` e `config_manifest.json`
    com sha256. Por run: `manifest.json` com o `RunConfig`, o commit, o sha256 do `DoS.csv` e as versões. O
    CSV bruto da decisão 1 continua, como proveniência.
53. **Paridade no startup.** A API nova recalcula as predições do `X_test.npy` e compara com
    `y_pred_expected.npy` antes de aceitar requisições. Ela se recusa a subir se a versão de scikit-learn ou
    de numpy divergir do manifesto.
54. **Formato de entrada da API nova.** O caminho de medição é binário (`application/octet-stream`, float64
    C-order, cabeçalhos de forma). O JSON é medido como variante. A leitura do CSV pelo servidor sai do
    caminho de medição [§2.3].
55. **Onde fica o código das fases 2 e 3.** A estatística e o Pareto ficam em `src/mqtt_dos/`. Profiler,
    API, sampler e gerador de carga ficam no membro de workspace uv `edge/` (pacote `edge_bench`), com
    dependências mínimas para o Pi e o mesmo `uv.lock` do treino. O código em
    `~/Documentos/inference/edge_bench/` é referência para as aulas, não é importado. **Substitui a decisão
    7** só na parte "um pacote".
56. **Protocolo de recursos (ADR 0004).** Duas execuções por célula: L (latência) e R (recursos). Processo
    novo por configuração e cgroup dedicado ao worker. O pico primário é o `ru_maxrss` do processo novo; o
    `memory.peak` é secundário (reset só no mesmo descritor, kernel ≥ 6.12). A memória em regime (PSS) é o
    eixo de memória do Pareto [§2.4].
57. **Threads fixadas e registradas.** Variáveis `*_NUM_THREADS=1`, `threadpoolctl.threadpool_limits(1)`,
    `n_jobs=1` e `threadpool_info()` gravado. O paralelismo só entra como fator no subexperimento LDA/RF.
58. **GPU.** Não usada: o manifesto registra `gpu_backend: "none"` e `vcgencmd get_mem gpu`. O ramo CUDA do
    `PeakMemoryProfiler` não é portado.
59. **Pareto 3D e escolha para o Pi.** Eixos: MCC × p95 com B = 1 no regime isolado × PSS em regime, mais
    hipervolume. Vão ao Pi a melhor configuração de cada família (pela CV, com desempate por custo), as não
    dominadas da triagem offline, até cerca de 10, e o conjunto LowVariance × {LDA, DT, GB, RF, SVM}, para
    comparar com o t16.
60. **Tickets e specs por fase.** Os tickets 04–08 mantêm número e arquivo (as aulas se dividem em NN-1 e
    NN-2 quando preciso). Os tickets novos vão de 09 a 22. Specs: `0000` (treino), `0001` (avaliação e
    seleção), `0002` (inferência e medição). **Substitui a decisão 22** ("oito tickets"). Não há renumeração
    a mapear.
61. **Correções ao plano de inferência de 2026-10.** (a) O `memory.peak` só aceita reset a partir do kernel
    6.12, e o reset vale só para o mesmo descritor (o plano dizia 6.3). (b) O
    `edge_bench.CgroupV2.reset_peak` não tem efeito, porque reabre o arquivo. (c) Os RF em uso têm
    `n_jobs=1`, e o `SVC.predict` provavelmente não usa BLAS, então a inflação não uniforme do t16 não é
    explicada por threads de RF ou SVM [§0.4].
62. **Versões.** A API nova usa exatamente as versões do `uv.lock` do treino. Os `.pkl` antigos de
    `api_inference/` não são carregados por ela (o do GradientBoosting não carrega em scikit-learn 1.9.1).
63. **Fora de escopo desta reestruturação:** latência pacote-a-veredito com tráfego reproduzido (E9; ticket
    22, bloqueado pelo pcap) e energia (INA219/USB). Ficam registrados, sem aula.
64. **Notebook de experimentos.** Os experimentos dos tickets 09, 11, 12 e 14 ficam em
    `notebooks/experiments.ipynb`, que roda em modo smoke no teste. O `notebooks/training.ipynb` continua só
    com o caminho do artigo. Complementa a decisão 7.
65. **Git só pelo humano.** Nenhum agente executa operações de git: `add`, `commit`, criação de branch,
    `merge`, `rebase`, `push` ou abertura de PR. O agente sugere o comando e a mensagem, e a autora executa.
    Prevalece sobre o §0 do briefing `docs/claude-science-melhorias.md` e reafirma a regra do `AGENTS.md`
    ("nunca faça commit, push ou PR").
```

---

## 5. Comandos para rodar no Raspberry Pi

Rode do usuário que vai executar a API, com a API parada.

| # | Comando | O que cada resultado muda |
|---|---|---|
| C1 | `cat /proc/device-tree/model; free -m; getconf PAGESIZE` | Pi 4 com 4096: nada muda. Pi 5 com 16384: o RSS e o PSS ficam em granularidade de 16 KiB, o que deve ser registrado e impede comparar a memória direto com o t16. RAM menor que 4 GB: recalibrar o `--vm-bytes` de L3/L4 |
| C2 | `uname -r; cat /etc/os-release \| head -3` | ≥ 6.12: reset do `memory.peak` utilizável (V4). Entre 5.19 e 6.11: `memory.peak` só leitura, então escopo novo por janela. Abaixo de 5.19: sem `memory.peak`; usar `ru_maxrss`/`VmHWM` |
| C3 | `stat -fc %T /sys/fs/cgroup; cat /sys/fs/cgroup/cgroup.controllers` | `cgroup2fs` com `memory` listado: OK. Sem `memory`: acrescentar `cgroup_enable=memory cgroup_memory=1` ao `/boot/firmware/cmdline.txt` e reiniciar. `tmpfs` (v1): o protocolo cai para métricas de processo |
| C4 | `cat /proc/self/cgroup; systemd-run --user --scope -p MemoryAccounting=yes true && echo user-scope-ok` | Se o escopo de usuário falhar, usar `sudo systemd-run --scope` ou delegar o controlador `memory` ao usuário. Em Docker, `0::/` indica um namespace próprio; a decisão host × Docker (P1) muda o escopo |
| C5 | `cat /proc/pressure/cpu` | Arquivo ausente: acrescentar `psi=1` ao `cmdline.txt`. Sem PSI, as linhas novas de PSI ficam vazias e a contenção volta a ser estimada por `schedstat` |
| C6 | `vcgencmd get_throttled; vcgencmd measure_temp; vcgencmd measure_clock arm; vcgencmd get_mem arm; vcgencmd get_mem gpu` | `0x0`: OK. Bit 0 ou bit 16 (subtensão): trocar a fonte antes de qualquer medição. Bits 1–3: refrigeração |
| C7 | `cat /sys/devices/system/cpu/cpu0/cpufreq/{scaling_governor,scaling_available_governors,scaling_max_freq}` | Se `performance` não estiver disponível, registrar o governor e a frequência por célula, e a comparação entre células fica mais fraca |
| C8 | `python3 --version; uv python list \| head` | Se o Python do sistema não for 3.13, `uv python install 3.13`; o workspace exige `>=3.13,<3.14` |
| C9 | `uv run --package edge_bench python -m threadpoolctl -i numpy sklearn` (depois do ticket 13) | Mostra BLAS, versão, `num_threads` e arquitetura. Se o padrão for maior que 1, confirmar que a variável de ambiente o leva a 1 |
| C10 | `docker info --format '{{.CgroupVersion}} {{.CgroupDriver}}'` (se usar Docker) | v2/systemd: dá para usar um escopo por container. v1: rodar no host |
| C11 | `findmnt -no SOURCE,FSTYPE /; ethtool eth0 \| grep Speed` | Cartão SD: o nível L4 (`--hdd`) e o log NDJSON competem pelo cartão; preferir SSD USB. Velocidade abaixo de 1000 Mb/s: B = 18.925 em binário passa a pesar na latência do cliente |
| C12 | `systemctl list-units --type=service --state=running --no-pager` | Desligar desktop e serviços não essenciais e registrar a lista no `run_meta` |
| C13 | `uv run --package edge_bench python -c "import sklearn; print(sklearn.__version__)"` | Tem de bater com o `manifest.json`; senão, a API (ticket 16) não sobe |

---

## 6. Perguntas para a autora

1. **Dispositivo:** modelo, RAM, SO e kernel do Pi; a API roda em Docker ou direto no host? (C1–C4 e C10
   respondem a maior parte.)
2. **Pcap original:** a captura do MQTT-UAD está disponível? Ela decide o ticket 22 (E9). Os pacotes normais
   de `Intrusion.csv` e `MitM.csv` são do mesmo testbed? Se forem, servem de validação externa do FPR em MQTT
   normal (ticket 11).
3. **Dois artigos:** "Deployment-Aware Machine Learning for DoS Detection in Edge-Based IoT Networks" (o PDF
   da raiz) e "Edge-Based Machine Learning for MQTT Intrusion Detection: A Pareto Analysis…" (citado no plano)
   são versões do mesmo trabalho ou dois artigos? Isso decide contra qual tabela a reprodução se compara.
4. **PDF:** `WPMC_2026_rasp__v1_ok_-2.pdf` (citado no briefing) e `WPMC_2026_rasp__v1_ok_.pdf` (na raiz,
   fora do git) são o mesmo arquivo?
5. **Profiler:** qual é o caminho do `PeakMemoryProfiler`? A §2.4 foi escrita sobre a descrição do briefing.
6. **Skill do curso:** o `~/.claude/skills/mkdocs-project-course/` não é legível daqui. Os tickets novos
   seguem os 01–08 e acrescentam Contexto, Arquivos, Aula e Origem. Isso bate com a skill?
7. **Local do código (decisão 55):** membro de workspace `edge/` ou um segundo pacote em `src/`? O workspace é
   um conceito novo do uv e vira uma aula (ticket 13).
8. **Comparabilidade com o t16 (decisão 59):** levar ao Pi o conjunto LowVariance × 5 modelos, mesmo que
   alguns sejam dominados?
9. **Escalar de qualidade:** MCC (proposta) ou F1 macro?
10. **Primário:** se o ticket 09 confirmar efeito pequeno, a autora aceita manter o split do artigo como
    primário?
11. **"Mais de 50" configurações:** contei 42 + 7 de baseline = 49. Há outra variação a considerar?
12. **Proveniência do t16:** qual CSV e qual `.pkl` deram a acurácia 0,9688 para `lowvariance_decisiontree`,
    contra 0,9754 no relatório de treino?
13. **Commits (respondida em 2026-10-30):** nenhum agente executa operações de git (commit, branch, merge,
    PR). Elas são só sugeridas e a autora as executa. Isso prevalece sobre o §0 do briefing (decisão 65).
14. **Energia:** há orçamento para um INA219 ou medidor USB? Se houver, a decisão 63 muda e entra um ticket de
    energia.

---

## 7. Recomendações não adotadas ou fora de escopo

| Recomendação | Situação | Motivo |
|---|---|---|
| Trocar o primário para split por fluxo já | não adotada nesta fase | efeito medido pequeno; o ticket 09 decide por critério |
| Seletor dentro da CV em todo o grid | não adotada | efeito medido nulo (ANOVA) e custo alto; substituída pela checagem de estabilidade |
| CV aninhada | não adotada | inviável com o SVM; substituída pela escolha pela CV e pela regra de 1 erro-padrão |
| Deixa-um-host-de-fora | fora de escopo | 89,5% do DoS sai de um host |
| Energia (E12) | fora de escopo (decisão 63) | depende de hardware |
| Pacote-a-veredito (E9) | registrado como ticket 22, bloqueado | depende do pcap |

*(A seção final da Etapa B — arquivos alterados, commits e pendências — é acrescentada depois da aprovação.)*
