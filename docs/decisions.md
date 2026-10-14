# Registro de decisões

Log cronológico e **append-only**: uma seção `## AAAA-MM-DD` por data, decisões novas sempre no fim.
Correções são novas entradas citando a antiga pelo número. ADRs (decisões difíceis de reverter) ficam
em `docs/adr/`; detalhes por etapa ficam nos tickets em `docs/issues/`.

## 2026-10-13

Contexto: refatoração do repositório para manter só o esquema de treino unificado
(`04_pipeline.ipynb` + `04_svm.ipynb`), a `api_inference/` e `scripts/`. A API fica para uma fase
posterior. Nada do que é antigo é apagado nesta fase.

1. **Contrato único de modelo.** Todo modelo salvo é um `sklearn.Pipeline` completo
   (imputer constante 0 → [StandardScaler] → [calibrador] → modelo) que recebe as features **brutas**
   do seletor. Há um CSV de teste bruto por configuração seletor–modelo. Motivo: hoje LDA/QDA são
   salvos sem scaler (esperam CSV pré-escalado), enquanto o SVM é salvo com scaler embutido.
2. **Gaps sem vazamento.** `publish_gap` e `connect_gap` são calculados sobre o fluxo inteiro ordenado
   por `frame.time_epoch`, **sem agrupar por `type`** (o rótulo). Hoje o agrupamento por rótulo vaza o
   alvo para a feature e não é reproduzível na inferência. As métricas novas deixam de ser comparáveis
   1:1 com as do artigo.
3. **SVM é o 7º modelo** do registro e roda em todos os seletores, com o mesmo protocolo dos demais.
4. **Removidos do pipeline:** Optuna global por consenso e os ensembles (Averaging, Hard Voting,
   Smart Soft Voting). O Smart Voting otimizava pesos no conjunto de teste (vazamento).
5. **Projeto-curso.** O usuário implementa `src/` e `tests/` seguindo as aulas da skill
   `mkdocs-project-course`. Agentes escrevem apenas docs e aulas (`docs/NN-*.md`), nunca o código de
   `src/`, salvo pedido explícito do usuário.
6. **Idioma.** Docs, tickets e aulas em pt-BR. Identificadores de código e colunas de relatório em
   inglês (`selector`, `model`, `fit_time_sec`).
7. **Layout.** Pacote `src/mqtt_dos/` com a lógica e **um** notebook `notebooks/training.ipynb` com a
   narrativa, a EDA e os gráficos, chamando o pacote. Sem CLI por ora.
8. **O que se mantém além do núcleo:** `paretto/`. O restante não relacionado vai para a lista de
   limpeza futura da spec (nada é apagado agora).
9. **Artefatos novos em `outputs/<run_name>/`.** Nada é escrito em `api_inference/` nesta fase
   (modelos, datasets e relatórios antigos permanecem intactos).
10. **Subamostra no tuning.** O Optuna pode ajustar um modelo numa subamostra estratificada do treino
    (default 15000 linhas para o SVM, configurável por modelo). O fit final usa sempre o treino completo.
    Motivo: SVM leva ~2 min por fit em 60 mil linhas; no grid 7 seletores × CV levaria horas.
11. **Métricas do paper WPMC:** accuracy, precision (weighted), F1 weighted, F1 macro, log loss; mais
    FP/FN por classe e tempos de fit/predict/proba.
12. **Spec e tickets** em arquivos locais `docs/issues/` (não há issue tracker).
13. **Seletores = os 6 do paper:** LowVariance, ANOVA, MutualInformation, Lasso, LinearSVC, ExtraTrees
    (`ExtraTreesClassifier` de verdade; hoje o código usa RandomForest). Deixam de existir as
    duplicatas Pearson/Fisher (ambas eram `f_classif`) e o "mRMR" (era só informação mútua).
14. **Protocolo do Optuna = paper:** TPE com seed 42, 30 trials, `StratifiedKFold(5)`, objetivo
    F1 macro. Trials e folds são configuráveis no `RunConfig` para rodadas rápidas. O código atual usava
    10–12 trials, 3 folds e F1 weighted.
15. **Testes:** pytest unitários mais um smoke test do grid inteiro em amostra pequena (1–2 trials).
16. **Dependências** em `pyproject.toml` com uv (grupo dev: pytest, ruff, mkdocs-material, jupyter),
    layout `src/`. O `requirements.txt` antigo fica intocado.
17. **Seleção de features.** Lasso e LinearSVC ranqueiam por |coeficiente|, que depende da escala, então
    são ajustados sobre o treino escalonado (scaler interno ao seletor). LowVariance fica sem escala,
    com threshold 0.01 e sem truncar; os demais seletores escolhem top-15. A seleção usa só o treino.
18. **Etapas do pipeline:** Baseline (22 features candidatas, hiperparâmetros default, 7 modelos) e
    Optuna por seletor (6 seletores × 7 modelos). Sai a etapa intermediária "seleção com parâmetros default".
19. **Calibração de QDA e GaussianNB:** `CalibratedClassifierCV(method='sigmoid', cv=3, ensemble=False)`.
    Fica um único modelo mais uma sigmoide de 2 parâmetros, então o custo de inferência é praticamente
    o do modelo cru. Com `ensemble=True` (comportamento atual) o modelo implantado teria 3 cópias, o que
    distorce o Pareto qualidade × latência no Raspberry Pi.
20. **`run_name`** é definido no `RunConfig` (ex.: `paper_protocol`, `smoke`). Rodar de novo com o
    mesmo nome sobrescreve a pasta.
21. **Notebook novo em `notebooks/training.ipynb`.**
22. **Oito tickets**, em cadeia, cada um terminando em algo que roda (ver `docs/issues/`).
23. **Registro contínuo.** Toda decisão daqui em diante entra neste arquivo no momento em que é tomada
    (pedido do usuário).
24. **Fatos de partida verificados no código** (não são escolhas, mas justificam as decisões acima): a
    lista LowVariance é idêntica nos dois notebooks (12 features); a divergência entre SVM e demais está
    no contrato de entrada e no protocolo de tuning. O paper descreve 22 candidatas (20 colunas limpas +
    2 gaps), 30 trials, 5 folds e F1 macro como objetivo, divergindo do código atual.
25. **ADRs pendentes** (criar quando o ticket que toca a área chegar): contrato `Pipeline` único
    (tickets 04/05), gaps sem `type` (ticket 03), calibração com `ensemble=False` (ticket 05).
26. **Curso montado** (`/mkdocs-project-course init`): site MkDocs Material na raiz (`mkdocs.yml`), tema
    vermelho framboesa (inspirado no logotipo do Raspberry Pi, `#bc1142`) com alternador claro/escuro,
    idioma pt-BR. Regra: **uma aula por ticket** (`docs/NN-slug.md`), dividida em `NN-1`, `NN-2`... quando
    carregar mais de ~3 conceitos novos. O material antigo de `docs/` fica fora do site via `exclude_docs`.
27. **MkDocs em ambiente efêmero.** O `.venv` atual é Python 3.14.4 e o projeto exige `==3.13.9`, então
    um `uv sync` o substituiria. Até o ticket 01 definir o ambiente, o site roda com
    `uv run --no-project --with mkdocs --with mkdocs-material mkdocs build --strict`, sem alterar
    `pyproject.toml`, `uv.lock` nem `.venv`. O ticket 01 declara mkdocs e mkdocs-material no grupo dev.
    Fixar `mkdocs<2`: o aviso do Material informa que o MkDocs 2.0 quebra plugins e temas.
28. **Missão da aprendiz** (ver `course/MISSION.md`): refatorar o código do próprio paper para ficar
    legível, mantendo só o que o artigo descreve, e entender a fundo seletores, modelos, otimização,
    engenharia de features e limpeza de dados. As aulas terão mais conceito do que o padrão e podem ser
    divididas.
29. **`.gitignore`:** a linha `docs/` foi trocada por `api_inference/docs/` (a antiga ignorava toda pasta `docs/` e impedia versionar o log de decisões, os tickets e as aulas
    novas; os arquivos antigos de `docs/` já estavam rastreados) e adicionado `site/`.
30. **Ticket 01 dividido em três aulas** (01-1 ambiente com uv; 01-2 pacote `src/`, `RunConfig` e pytest;
    01-3 ruff e notebook ligado ao ambiente), por carregar ~6 conceitos novos.
31. **`.venv` antigo** (Python 3.14.4, criado com pip) é renomeado para `.venv-legacy` antes do primeiro
    `uv sync`, em vez de ser apagado; os notebooks antigos podem continuar usando esse kernel.
32. **Versão do Python:** `requires-python = ">=3.13,<3.14"` mais `.python-version` com `3.13`, no lugar
    do pino exato `==3.13.9`. A versão exata usada fica no `uv.lock`. Corrige a decisão 16 apenas neste ponto.
33. **`[build-system]` do flit removido** na aula 01-1 (apontava para um módulo `mqtt_under_attack`
    inexistente e quebrava o `uv sync`); um `[build-system]` novo para o pacote `mqtt_dos` entra na aula 01-2.
34. **Aula 01-1 implementada pelo agente**, a pedido explícito da usuária ("essa parte do ambiente com uv é
    trivial. implemente para mim no projeto"), como exceção à decisão 5. Ambiente criado: CPython 3.13.13,
    pandas 3.0.6, scikit-learn 1.9.1, Optuna 5.0.0; grupo dev com pytest, ruff, mkdocs<2 e mkdocs-material.
    O site do curso passa a abrir com `uv run mkdocs serve` (a decisão 27, do ambiente efêmero, deixa de valer).
35. **Nome do projeto e do módulo:** o projeto continua `mqtt_under_attack` e o módulo importável é
    `mqtt_dos` (`[tool.uv.build-backend] module-name = "mqtt_dos"`), com build backend
    `uv_build>=0.11.17,<0.12.0`. Resolve a pendência da aula 01-2.
36. **Escopo do ruff:** o `include` passa a listar só `pyproject.toml`, `src/`, `tests/` e
    `notebooks/training.ipynb`. O código antigo já tinha 33 erros de lint e 9 arquivos fora do formato, e não
    pode ser alterado nesta fase. O `make lint` passa a verificar só o código novo.
37. **Ferramentas de notebook:** `ipykernel` (kernel do ambiente no VS Code) e `nbclient` (teste que executa
    o notebook inteiro) no grupo dev, em vez do metapacote `jupyter` previsto na decisão 16. O JupyterLab, se
    preciso, roda com `uv run --with jupyter jupyter lab` sem virar dependência.
38. **Aulas 01-2 e 01-3 implementadas pelo agente**, a pedido explícito da usuária, como exceção à decisão 5
    (como a decisão 34 para a 01-1). O ticket 01 está concluído: `uv run pytest` (9 testes, incluindo a
    execução do notebook), `uv run ruff check` e `uv run ruff format --check` passam.
39. **A partir da aula 02 a usuária digita o código** seguindo as aulas; a regra da decisão 5 volta a valer
    integralmente (as exceções 34 e 38 cobriram só o ticket 01).

## 2026-10-14

40. **`DROP_COLUMNS` e `TARGET_COLUMN` ficam em `mqtt_dos/data.py`**, junto da limpeza que os usa, e não em
    `config.py` como esboçado no plano. A lista é exatamente a do `04_pipeline.ipynb` (46 colunas, 4 grupos
    comentados).
41. **Ordem do pipeline de dados:** `load_raw → add_gaps → drop_unused_columns`. Os gaps precisam de
    `frame.time_epoch`, que a limpeza remove; o código antigo lia o CSV duas vezes para contornar isso.
42. **ADR 0001 criado** (`docs/adr/0001-gaps-sem-rotulo.md`) para a decisão 2, com a medição do efeito do
    vazamento antigo neste dataset (pequeno nos números, decisivo no método).
43. **`message_gap` usa alinhamento por índice** (`sort_values` + `reindex`) e não depende de o CSV estar
    ordenado por tempo. Índices duplicados não são suportados na versão da aula (exercício 2 mostra como).
