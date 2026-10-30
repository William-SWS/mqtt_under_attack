# Pacote de execução da Etapa B — para o agente de codificação

**Origem:** `docs/analises/claude-science-2026-10-30.md` (relatório da Etapa A). Este arquivo diz **o que
escrever, onde e em que ordem**. A justificativa de cada item está no relatório, na seção citada em
"Origem".

**Pré-condição:** a autora aprovou o mapa (§3 do relatório), com ou sem ajustes, e respondeu às perguntas da
§6. Toda resposta que mudar um item abaixo prevalece sobre este arquivo. Uma recomendação rejeitada não vira
ticket: ela entra no relatório como "não adotada", com o motivo da autora.

---

## 0. Regras para quem executa

1. **Escopo de escrita permitido:** `docs/issues/` (criar e reescrever tickets e specs), `docs/decisions.md`
   (só acrescentar ao fim), `docs/adr/` (só criar ADRs novos), `GLOSSARY.md` (só acrescentar) e
   `docs/analises/claude-science-2026-10-30.md` (a seção final).
2. **Proibido alterar:** `src/`, `tests/`, `notebooks/`, `pyproject.toml`, `uv.lock`, `mkdocs.yml`,
   `docs/index.md`, as aulas `docs/0*.md`, `docs/glossario.md`, `docs/referencia.md`, `docs/recursos.md`,
   `AGENTS.md`, `CLAUDE.md`, `course/`, `api_inference/`, `scripts/`, `paretto/`, `data/`, `outputs/`,
   `notebooks_refactored/` e `reports_refactored/`. Um ticket pode conter assinatura de função e nome de
   teste, nunca a implementação.
3. **Nenhum arquivo de ticket é renomeado ou apagado.** Os nomes atuais de 04–08 são referenciados por
   `mkdocs.yml` e `docs/index.md`.
4. **Git: o agente não executa nenhuma operação de git.** Isso inclui `git add`, `commit`, `branch`,
   `switch -c`, `checkout -b`, `merge`, `rebase`, `push`, abrir PR, `stash` e `reset` (decisão 65). O agente
   só edita arquivos e, ao fim de cada mudança lógica, **sugere** à autora o comando e a mensagem de commit,
   em português, com os caminhos explícitos. Quem executa é a autora.
   - Sugira sempre `git add <caminho explícito>`, nunca `git add -A`, `git add .` ou `git commit -a`. No
     ambiente da autora isso é só boa prática; no sandbox do Claude Science, `.claude/` e `.vscode/`
     aparecem como apagados.
   - Pare depois de cada grupo de commits sugeridos na §1 e espere a autora confirmar que os executou antes
     de seguir, para que cada commit dela contenha só uma mudança lógica.
5. **Formato de ticket** (o dos tickets 01–08, mais os campos exigidos pelo briefing):

   ```markdown
   # NN: Título

   **What to build:** uma frase sobre o entregável que roda.

   **Blocked by:** NN, NN

   **Status:** ready-for-agent | ready-for-agent (condicional ao NN) | blocked

   **Origem:** relatório §x.y

   **Contexto:** decisões N, N (e ADR NNNN)

   **Arquivos:** caminhos que a autora cria ou muda

   - [ ] critério verificável (nome de teste ou comando, com o resultado esperado)

   **Aula:** NN (ou NN-1 e NN-2). Pergunta que a aula responde; conceitos novos (no máximo ~3 por aula,
   decisão 26); erro comum que ela previne.
   ```

   Se a autora disser que a skill define outro formato (P6), siga a skill e registre a divergência no
   relatório.
6. **Decisões:** o texto das decisões 44–65 está na §4 do relatório. Copie-o literalmente, preencha a data
   de aprovação e ajuste só o que a autora mandar.

---

## 1. Sequência de commits sugeridos (executados pela autora, nunca pelo agente)

A mensagem fica na coluna da direita. O agente escreve os arquivos de uma linha, mostra
`git add <arquivos> && git commit -m "<mensagem>"` e espera.

| # | Arquivo(s) | Mensagem |
|---|---|---|
| 1 | `docs/adr/0002-unidade-do-split.md` | `docs(adr): ADR 0002 unidade do split` |
| 2 | `docs/adr/0003-contrato-de-dados-treino-api.md` | `docs(adr): ADR 0003 contrato de dados treino → API` |
| 3 | `docs/adr/0004-escopo-da-medicao-de-recursos.md` | `docs(adr): ADR 0004 escopo da medição de recursos` |
| 4 | `docs/decisions.md` (acrescentar a §4 do relatório) | `docs(decisoes): decisões 44–65 da análise de 2026-10-30` |
| 5 | `docs/issues/0000-spec-treino-unificado.md` | `docs(spec): spec 0000 vira a spec da fase 1 (treino)` |
| 6 | `docs/issues/0001-spec-avaliacao-e-selecao.md` | `docs(spec): spec 0001 da fase 2 (avaliação e seleção)` |
| 7 | `docs/issues/0002-spec-inferencia-no-dispositivo.md` | `docs(spec): spec 0002 da fase 3 (inferência e medição)` |
| 8–12 | `docs/issues/04-…` a `08-…` (um por commit) | `docs(ticket): reescreve o ticket NN (<motivo curto>)` |
| 13–26 | `docs/issues/09-…` a `22-…` (um por commit) | `docs(ticket): cria o ticket NN <título>` |
| 27 | `GLOSSARY.md` | `docs(glossario): termos das fases 1–3` |
| 28 | `docs/analises/claude-science-2026-10-30.md` | `docs(analise): seção final da Etapa B` |

## 2. Checagens antes de sugerir o último commit

1. `uv run mkdocs build --strict -d /tmp/site-check` termina com código 0. Os arquivos novos não estão na
   `nav`, e isso gera só INFO.
2. Para cada ticket NN, todo número em **Blocked by** é menor que NN. Comando:
   `grep -H '^\*\*Blocked by' docs/issues/[0-9][0-9]-*.md`, conferido à mão.
3. Todo ticket novo ou reescrito tem **Origem** e **Contexto**, e todo número de decisão citado existe em
   `docs/decisions.md`.
4. Todo termo em negrito do glossário novo (§6 abaixo) aparece em pelo menos um ticket.
5. Releitura de 01 a 22: cada ticket usa só conceitos e código de tickets anteriores. Registre o resultado
   na seção final do relatório.

---

## 3. Tickets reescritos (04–08) — texto integral

### `docs/issues/04-split-pipeline-avaliacao.md`

```markdown
# 04: Split, Pipeline de inferência e avaliação de um modelo

**What to build:** o caminho ponta a ponta com um único modelo: split estratificado, Pipeline que aceita
features brutas e uma avaliação que já devolve as métricas do paper, o MCC, os recortes por "é MQTT?" e os
intervalos de confiança. O leitor treina uma árvore de decisão e vê métricas, IC e matriz de confusão no
notebook.

**Blocked by:** 03

**Status:** ready-for-agent

**Origem:** relatório §2.1c, §2.1e, §2.2

**Contexto:** decisões 1, 11, 41, 45, 49

**Arquivos:** `src/mqtt_dos/split.py`, `src/mqtt_dos/pipeline.py`, `src/mqtt_dos/evaluation.py`,
`tests/test_split.py`, `tests/test_pipeline.py`, `tests/test_evaluation.py`, `notebooks/training.ipynb`
(seções 3 e 4)

- [ ] `split_indices(y, config) -> tuple[np.ndarray, np.ndarray]` devolve 75.700 e 18.925 índices
      (estratificado, seed 42) no CSV real (`test_split_sizes_on_real_data`, marcado como opcional).
- [ ] `build_pipeline(estimator, *, scale: bool, calibrate: bool) -> Pipeline` aceita features brutas com
      NaN e devolve probabilidades que somam 1 (`test_pipeline_accepts_nan`,
      `test_probabilities_sum_to_one`).
- [ ] Nenhum ajuste usa o teste: mudar os valores do teste não altera o Pipeline ajustado
      (`test_fit_ignores_test_rows`).
- [ ] `evaluate(pipeline, X_test, y_test, *, is_mqtt=None) -> EvaluationResult` devolve accuracy, precision
      weighted, F1 weighted, F1 macro, log loss, **MCC, recall de DoS, FPR de normal**, FP/FN por classe,
      matriz de confusão e os tempos de fit/predict/proba; com `is_mqtt`, devolve também as mesmas métricas
      nos recortes `mqtt` e `non_mqtt` (`test_evaluate_returns_all_metrics`,
      `test_evaluate_subsets_partition_the_test`).
- [ ] `bootstrap_ci(y_true, y_pred, metric, n_boot=2000, seed=42) -> tuple[float, float]` e
      `wilson_interval(k, n, alpha=0.05) -> tuple[float, float]` (`test_wilson_known_value`: k=2, n=80 →
      (0,0069; 0,0866) com 4 casas).
- [ ] O notebook mostra as métricas, o IC 95% do F1 macro e do MCC, a matriz de confusão e a tabela por
      recorte.
- [ ] ADR "contrato `Pipeline` único" criado (pendente desde a decisão 25).

**Aula:** dividida em 04-1 e 04-2.
- 04-1: "Por que o split vem antes de qualquer ajuste, e por que o modelo salvo é um Pipeline?" Conceitos:
  split estratificado; Pipeline (imputer → scaler → calibrador → modelo); contrato de entrada. Erro comum:
  ajustar o scaler antes do split.
- 04-2: "Quanto da métrica é sinal e quanto é ruído?" Conceitos: MCC contra F1/acurácia; recortes de
  avaliação; IC bootstrap e IC de Wilson. Erro comum: comparar 0,975 com 0,974 como se fossem diferentes.
```

### `docs/issues/05-registro-de-modelos-e-baseline.md`

```markdown
# 05: Registro dos sete modelos e baseline

**What to build:** os sete modelos num registro único e a tabela de baseline nas 22 features, com uma linha
de regra "pacote é MQTT ⇒ DoS" como referência mínima.

**Blocked by:** 04

**Status:** ready-for-agent

**Origem:** relatório §2.1e, §2.1f

**Contexto:** decisões 3, 18, 19, 49, 50

**Arquivos:** `src/mqtt_dos/registry.py`, `src/mqtt_dos/baseline.py`, `tests/test_registry.py`,
`tests/test_baseline.py`, `notebooks/training.ipynb` (seção 5)

- [ ] `MODEL_REGISTRY: dict[str, ModelSpec]` contém os 7 modelos; `ModelSpec` tem `name`, `factory`,
      `search_space`, `needs_scaling` e `needs_calibration` (`test_registry_has_seven_models`).
- [ ] LDA, QDA e SVM recebem scaler; QDA e GaussianNB recebem calibração sigmoide com `ensemble=False`
      (`test_scaling_and_calibration_flags`).
- [ ] Um QDA calibrado tem um único estimador base (`test_calibrated_qda_has_one_base_estimator`).
- [ ] `run_baseline(X_train, y_train, X_test, y_test, *, is_mqtt_test) -> pd.DataFrame` devolve 8 linhas
      (7 modelos e `Rule:is_mqtt`), ordenadas por MCC, com as colunas de `evaluate` e os tempos
      (`test_baseline_includes_rule_row`).
- [ ] No CSV real, a linha `Rule:is_mqtt` tem F1 macro 0,9294 e MCC 0,8661, com tolerância de 0,002: a
      ordem interna das classes no `stratify` pode mudar a permutação do split
      (`test_rule_baseline_on_real_data`, opcional).
- [ ] O notebook mostra a tabela e o gráfico do baseline, com a regra destacada.
- [ ] ADR "calibração com `ensemble=False`" criado (pendente desde a decisão 25).

**Aula:** 05 (ou 05-1 e 05-2 se a profundidade conceitual pedida na missão estourar). "O que cada modelo
assume sobre os dados, e quanto ele ganha de uma regra de uma linha?" Conceitos: registro de modelos;
calibração; baseline de regra. Erro comum: reportar 0,97 sem dizer que uma regra trivial dá 0,93.
```

### `docs/issues/06-selecao-de-features.md`

```markdown
# 06: Seleção de features com seis seletores

**What to build:** os seis seletores aplicados ao treino, a matriz de consenso e a checagem de estabilidade
de cada seletor entre folds.

**Blocked by:** 04

**Status:** ready-for-agent

**Origem:** relatório §2.1b, §2.1f

**Contexto:** decisões 13, 17, 47

**Arquivos:** `src/mqtt_dos/selection.py`, `tests/test_selection.py`, `notebooks/training.ipynb` (seção 6)

- [ ] Existem LowVariance, ANOVA, MutualInformation, Lasso, LinearSVC e ExtraTrees (`ExtraTreesClassifier`)
      (`test_six_selectors_exist`).
- [ ] LowVariance usa threshold 0.01 e não trunca (12 features no CSV real); os demais devolvem 15
      (`test_selector_sizes_on_real_data`, opcional).
- [ ] Lasso e LinearSVC não dependem da escala original das colunas (`test_scale_invariance_of_l1_selectors`).
- [ ] A seleção usa só o treino (`test_selection_ignores_test_rows`).
- [ ] `consensus_matrix(selected) -> pd.DataFrame` conta quantos seletores escolheram cada feature.
- [ ] `selection_stability(X_train, y_train, config, cv) -> pd.DataFrame` devolve o Jaccard entre o conjunto
      do treino inteiro e o de cada fold, por seletor (`test_stability_is_one_for_deterministic_selector`).
- [ ] O notebook mostra as features por seletor, o heatmap de consenso, a tabela de estabilidade e se algum
      seletor tem Jaccard mínimo abaixo de 0,8. Se tiver, registra que a reavaliação com o seletor dentro da
      CV vai entrar no ticket 08.
- [ ] O notebook mostra que `frame.cap_len` e `frame.len` são idênticas e quais seletores mantêm as duas
      (pendência nº 21 do LOG).

**Aula:** 06-1 (seletores de filtro: LowVariance, ANOVA, MI) e 06-2 (seletores embutidos: Lasso, LinearSVC,
ExtraTrees, mais estabilidade). "O conjunto escolhido é uma propriedade dos dados ou do sorteio do treino?"
Erro comum: ajustar o seletor no dataset inteiro.
```

### `docs/issues/07-optuna-por-seletor.md`

```markdown
# 07: Optuna por seletor — grid de 6 × 7

**What to build:** para cada par (seletor, modelo), um estudo Optuna com o protocolo do paper que guarda,
além do F1 macro, o MCC médio e o desvio de CV, seguido do fit final no treino completo. A CV é recebida de
fora, para que o ticket 10 possa trocar a unidade do split sem mexer no tuning.

**Blocked by:** 05, 06

**Status:** ready-for-agent

**Origem:** relatório §2.1a, §2.1c

**Contexto:** decisões 10, 14, 46, 48

**Arquivos:** `src/mqtt_dos/tuning.py`, `tests/test_tuning.py`, `notebooks/training.ipynb` (seção 7)

- [ ] `tune_config(selector, model, X_train, y_train, config, *, cv_splitter, groups=None) -> TuningResult`;
      no modo do artigo, `cv_splitter` é `StratifiedKFold(5, shuffle=True, random_state=42)`
      (`test_default_cv_is_paper_protocol`).
- [ ] TPE seed 42, objetivo F1 macro, trials e folds vindos da configuração (`test_study_uses_tpe_seed`).
- [ ] Cada trial guarda em `user_attrs` a média e o desvio de F1 macro e de MCC nos folds;
      `TuningResult` expõe `cv_f1_macro_mean`, `cv_f1_macro_std`, `cv_mcc_mean` e `cv_mcc_std` do melhor
      trial (`test_tuning_result_has_cv_metrics`).
- [ ] A subamostra estratificada (SVM = 15.000) vale só no tuning; o fit final usa o treino completo
      (`test_final_fit_uses_full_train`).
- [ ] Trials com erro são podados; uma configuração sem trial válido vira linha `status="failed"` sem abortar
      o grid (`test_failed_config_does_not_abort_grid`).
- [ ] `run_grid(...) -> GridResult` devolve 42 linhas no run completo, com as métricas de CV e os Pipelines
      ajustados. Smoke: 1–2 trials, 2 folds, 2 modelos × 2 seletores (`test_grid_smoke`).
- [ ] **O grid não calcula métricas de teste**: o teste é avaliado só no ticket 08
      (`test_grid_result_has_no_test_columns`).
- [ ] O notebook roda o grid com `run_name='smoke'` e mostra a tabela de CV e os históricos.

**Aula:** 07-1 (TPE e espaço de busca) e 07-2 (CV como estimador de generalização; por que o grid não olha o
teste). Erro comum: escolher o melhor pelo teste.
```

### `docs/issues/08-artefatos-e-analise.md`

```markdown
# 08: Artefatos do run, exportação para a API e análise final

**What to build:** gravar tudo o que um run produz, incluindo o pacote verificável que a API vai consumir
(teste em `.npy`, predições esperadas e manifesto com sha256), avaliar o teste uma única vez e fechar o
notebook com a escolha pela CV.

**Blocked by:** 07

**Status:** ready-for-agent

**Origem:** relatório §2.1c, §2.3

**Contexto:** decisões 1, 9, 20, 48, 49, 52 (ADR 0003)

**Arquivos:** `src/mqtt_dos/artifacts.py`, `src/mqtt_dos/analysis.py`, `tests/test_artifacts.py`,
`tests/test_analysis.py`, `notebooks/training.ipynb` (seção 8)

- [ ] `export_run(grid, data, config) -> Path` cria `outputs/<run>/manifest.json` (`RunConfig`, commit git e
      flag de árvore suja, sha256 do `DoS.csv`, `split_strategy`, versões de Python, numpy, pandas,
      scikit-learn, optuna e joblib, plataforma) e um diretório por configuração em
      `outputs/<run>/configs/<selector>__<model>/` (`test_run_manifest_fields`).
- [ ] Cada diretório de configuração tem `pipeline.joblib`, `X_test.npy` (float64, C-order, NaN
      preservado), `y_test.npy` (int8), `test_index.npy`, `y_pred_expected.npy`, `proba_expected.npy`,
      `test_raw.csv` e `config_manifest.json`, com `features`, sha256 de cada arquivo, `best_params`, métricas
      de CV e de teste, `model_size_b` e complexidade estrutural (`n_nodes`, `n_estimators`, `n_support`
      quando houver) (`test_config_dir_contents`).
- [ ] As colunas de `X_test.npy` seguem `pipeline.feature_names_in_` (`test_x_test_columns_follow_feature_names_in`).
- [ ] Recarregar o `.joblib` e prever sobre o `.npy` reproduz `y_pred_expected.npy` exatamente
      (`test_exported_pipeline_reproduces_expected_predictions`).
- [ ] Os sha256 do manifesto batem com os arquivos (`test_manifest_hashes_match_files`).
- [ ] Nada é escrito em `api_inference/`; o mesmo `run_name` sobrescreve, um nome novo cria outra pasta.
- [ ] `select_by_cv(results, *, one_se=True) -> pd.DataFrame`: o ranking usa só as colunas de CV; entre as
      configurações a até 1 erro-padrão da melhor, marca a de menor `model_size_b`. O custo real entra no
      ticket 15 (`test_selection_ignores_test_columns`).
- [ ] A avaliação de teste é chamada uma vez por configuração, e a tabela final mostra a correlação de
      Spearman entre o MCC de CV e o MCC de teste.
- [ ] Se o ticket 06 marcou algum seletor instável, a melhor configuração dele é reavaliada com o seletor
      dentro da CV, e a diferença é mostrada.
- [ ] O notebook mostra o melhor por família de modelo (pela CV), heatmaps de métricas, matrizes de
      confusão, o delta contra o baseline e a linha da regra.
- [ ] O leitor confere que o LowVariance tem as mesmas 12 features dos notebooks antigos.

**Aula:** 08-1 (artefatos verificáveis: manifesto, hash, paridade) e 08-2 (escolher sem olhar o teste: regra
de 1 erro-padrão, correlação CV × teste). Erro comum: exportar um CSV e descobrir no Pi que a ordem das
colunas ou a versão do scikit-learn mudou.
```

---

## 4. Tickets novos (09–22) — texto integral

### `docs/issues/09-unidade-do-split.md`

```markdown
# 09: Experimento — unidade do split e sementes

**What to build:** chave de fluxo, dois splits alternativos (por fluxo e temporal por classe) e uma tabela de
robustez que compara, para a melhor configuração de cada família, o split do paper contra os alternativos
com 5 sementes. O ticket termina com a decisão escrita sobre o split primário.

**Blocked by:** 08

**Status:** ready-for-agent

**Origem:** relatório §2.1a, §2.1f

**Contexto:** decisões 2, 41, 44, 45, 64 (ADR 0002)

**Arquivos:** `src/mqtt_dos/data.py` (nova `flow_key`), `src/mqtt_dos/split.py` (estende `split_indices`),
`src/mqtt_dos/robustness.py`, `tests/test_flow_key.py`, `tests/test_split.py`, `tests/test_robustness.py`,
`notebooks/experiments.ipynb` (novo)

- [ ] `flow_key(raw) -> pd.Series`: 5-tupla bidirecional (IP:porta ordenados); pacotes sem IP agrupados por
      par de MAC; calculada antes de `drop_unused_columns`. Trocar origem e destino não muda a chave
      (`test_flow_key_is_direction_free`). No CSV real há 1.329 fluxos (`test_flow_count_on_real_data`,
      opcional).
- [ ] `split_indices(y, config, *, groups=None, times=None)` aceita `strategy` em `{"stratified_random",
      "flow_group", "temporal_per_class"}`; com `flow_group`, nenhum fluxo aparece nos dois lados
      (`test_flow_group_split_has_no_shared_flow`); com `temporal_per_class`, todo pacote de teste é
      posterior a todo pacote de treino da mesma classe (`test_temporal_per_class_respects_time`).
- [ ] `split_robustness(raw, configs, *, seeds=(42, 0, 1, 2, 3)) -> pd.DataFrame` devolve, por família,
      estratégia e semente: F1 macro, MCC, recall de DoS, FPR, a fração de teste em fluxos vistos no treino
      e a fração de teste com duplicata exata no treino (`test_robustness_table_columns`).
- [ ] Variante extra só para LDA e QDA: `SimpleImputer(add_indicator=True)` contra a constante 0.
- [ ] O notebook reproduz, para a DecisionTree default, os valores do relatório §2.1a com tolerância de
      0,002: F1 macro de 0,9692 (aleatório), 0,9675 (fluxo) e 0,9715 (temporal por classe).
- [ ] **Critério de decisão, escrito no fim do notebook e acrescentado como decisão nova em
      `docs/decisions.md`:**
      - |ΔMCC (paper − flow_group)| ≤ 0,005 em todas as famílias → o paper continua primário, o ticket 10 só
        gera a tabela de robustez e ela vai para o apêndice;
      - ΔMCC > 0,01 em alguma família → `flow_group` vira primário e o ticket 10 roda o grid completo nele;
      - entre 0,005 e 0,01 → os dois são reportados, com `flow_group` como primário.

**Aula:** 09-1 (fluxo como unidade de dependência; GroupKFold e StratifiedGroupKFold; split temporal) e 09-2
(experimento de robustez com sementes e critério de decisão). "Pacotes vizinhos inflam a métrica?" Erro
comum: concluir "vaza" ou "não vaza" sem medir.
```

### `docs/issues/10-modo-corrigido.md`

```markdown
# 10: Modo corrigido do RunConfig

**What to build:** o `RunConfig` passa a escolher a unidade do split, e a CV do tuning a herda. O ticket roda
o run `corrected` no tamanho que o critério do ticket 09 mandar (grid completo ou só robustez).

**Blocked by:** 09

**Status:** ready-for-agent (condicional ao resultado do 09)

**Origem:** relatório §2.1a

**Contexto:** decisões 44, 46 e a decisão nova do ticket 09 (ADR 0002)

**Arquivos:** `src/mqtt_dos/config.py`, `src/mqtt_dos/tuning.py` (`make_cv`), `tests/test_config.py`,
`tests/test_tuning.py`, `notebooks/training.ipynb` (nota) ou `notebooks/experiments.ipynb`

- [ ] `RunConfig.split_strategy: Literal["stratified_random", "flow_group", "temporal_per_class"] =
      "stratified_random"`, validado em `__post_init__` (`test_unknown_split_strategy_is_rejected`).
- [ ] O default continua reproduzindo o paper: os testes do ticket 01 passam sem mudança.
- [ ] `make_cv(config, groups) -> BaseCrossValidator`: `StratifiedKFold` no modo do paper,
      `StratifiedGroupKFold` com `flow_group` (`test_make_cv_follows_split_strategy`).
- [ ] `manifest.json` registra `split_strategy` e o número de grupos.
- [ ] O run `corrected` roda no tamanho definido pelo 09, e o notebook mostra a tabela paper × corrigido por
      família.

**Aula:** 10. "Como manter duas versões do protocolo sem duplicar código?" Conceitos: configuração como
fonte única do protocolo; CV que segue a unidade do split. Erro comum: split por fluxo com CV aleatória
dentro do treino, que reintroduz o vazamento no tuning.
```

### `docs/issues/11-dos-ou-mqtt.md`

```markdown
# 11: Experimento — o modelo detecta DoS ou detecta MQTT?

**What to build:** os resultados recortados por `is_mqtt` e por `mqtt.msgtype`, a comparação com a regra
trivial e com um modelo sem features `mqtt.*`, e o FPR em MQTT normal com IC. O ticket termina com o texto
de limitação que vai para o artigo.

**Blocked by:** 08

**Status:** ready-for-agent

**Origem:** relatório §2.1e

**Contexto:** decisões 49, 50 (pendência nº 20 do `course/LOG.md`)

**Arquivos:** `src/mqtt_dos/evaluation.py` (`evaluate_by_msgtype`), `tests/test_evaluation.py`,
`notebooks/experiments.ipynb` (seção "DoS ou MQTT")

- [ ] `evaluate_by_msgtype(y_true, y_pred, msgtype) -> pd.DataFrame` com n, n_DoS, n_normal, recall de DoS,
      FPR e IC de Wilson do FPR por tipo de mensagem (`test_by_msgtype_counts_add_up`).
- [ ] Tabela, para a melhor configuração de cada família: completa, só MQTT, só não MQTT, regra
      `is_mqtt` e "sem `mqtt.*`". No CSV real, a DecisionTree default reproduz o relatório §2.1e com
      tolerância de 0,002.
- [ ] FPR em MQTT normal com IC de Wilson para cada família.
- [ ] (Se a autora confirmar a P2) FPR sobre os pacotes `normal` MQTT de `Intrusion.csv` e `MitM.csv`,
      sem treinar neles, como validação externa.
- [ ] **Critério de decisão:** se o limite superior do IC do FPR em MQTT normal passar de 5% para a
      configuração escolhida, o artigo declara essa limitação e a decisão nova registra que a validação
      externa é necessária; se ficar em 5% ou menos, o artigo reporta o FPR com o IC.

**Aula:** 11. "O que exatamente o modelo aprendeu?" Conceitos: validade de construto; artefato de coleta;
avaliação estratificada por subgrupo. Erro comum: tratar uma feature que só existe num dos cenários como
sinal de ataque.
```

### `docs/issues/12-comparacao-pareada.md`

```markdown
# 12: Comparação estatística pareada entre configurações

**What to build:** funções que dizem se duas configurações são de fato diferentes no mesmo teste, e uma
tabela que marca quais são equivalentes à melhor.

**Blocked by:** 08

**Status:** ready-for-agent

**Origem:** relatório §2.2

**Contexto:** decisões 48, 49, 51

**Arquivos:** `src/mqtt_dos/compare.py`, `tests/test_compare.py`, `notebooks/experiments.ipynb`
(seção "Comparação")

- [ ] `paired_bootstrap_delta(y, pred_a, pred_b, *, metric="mcc", n_boot=2000, seed=42) -> tuple[float,
      float, float]` (delta, lim. inf., lim. sup.), reamostrando índices em conjunto
      (`test_identical_predictions_give_zero_delta`).
- [ ] `mcnemar_exact(y, pred_a, pred_b) -> tuple[int, int, float]` (b, c, p) (`test_mcnemar_known_table`).
- [ ] `holm(pvalues) -> np.ndarray` (`test_holm_matches_reference`, comparando com `statsmodels` se
      instalado ou com uma tabela calculada à mão).
- [ ] `compare_against_best(predictions, y, *, margin=0.005) -> pd.DataFrame` com ΔMCC, IC, p ajustado e a
      coluna `equivalent_to_best` (`test_equivalence_flag_uses_margin`).
- [ ] O notebook aplica a função às 42 configurações e mostra quantas são equivalentes à melhor.

**Aula:** 12. "0,9754 é melhor que 0,9743?" Conceitos: teste pareado; McNemar; comparações múltiplas;
margem de equivalência. Erro comum: usar intervalos não pareados para predições sobre o mesmo teste.
```

### `docs/issues/13-edge-bench-e-profiler.md`

```markdown
# 13: Pacote edge_bench e profiler de processo novo

**What to build:** um membro de workspace uv (`edge/`, pacote `edge_bench`) com dependências mínimas para o
Pi, e um profiler que mede um diretório de configuração (do ticket 08) num processo novo: memória de pico,
memória em regime, latência e CPU por chamada, com threads fixadas.

**Blocked by:** 08

**Status:** ready-for-agent

**Origem:** relatório §2.2, §2.4

**Contexto:** decisões 55, 56, 57, 58, 61, 62 (ADR 0004)

**Arquivos:** `pyproject.toml` (bloco `[tool.uv.workspace]`), `edge/pyproject.toml`,
`edge/src/edge_bench/__init__.py`, `edge/src/edge_bench/profile.py`, `edge/tests/test_profile.py`. O código
de referência fica em `~/Documentos/inference/edge_bench/`; ele não é copiado nem importado.

- [ ] `uv sync` resolve os dois membros num único `uv.lock`;
      `uv run --package edge_bench python -c "import edge_bench"` funciona.
- [ ] As dependências de `edge_bench` não incluem optuna, matplotlib, seaborn nem pandas
      (`test_edge_bench_has_no_training_deps`, lendo `edge/pyproject.toml`).
- [ ] `profile_config(config_dir, *, batch_sizes=(1, 1024), n_calls=2000, warmup=200, timeout_s=600) ->
      dict` roda num processo filho criado com `spawn`, com `*_NUM_THREADS=1` no ambiente,
      `threadpool_limits(1)` e `n_jobs=1` depois do `load`
      (`test_profile_runs_in_fresh_process`, `test_threads_are_limited_to_one`).
- [ ] O dicionário devolvido tem `maxrss_b` (de `ru_maxrss` do filho), `pss_b` e `uss_b` depois do
      aquecimento, `model_rss_delta_b`, `model_size_disk_b`, e por B: `p50_ns`, `p95_ns`, `p99_ns`,
      `cpu_ns_per_record`, mais `threadpool_info` e `gpu_backend="none"` (`test_profile_output_fields`).
- [ ] Um filho que morre (por exemplo, OOM) vira um resultado com `status="crashed"` e `exitcode`, sem
      travar o pai e sem deixar temporários (`test_child_crash_is_reported_not_hung`).
- [ ] O cronômetro envolve só o `predict`; nenhuma leitura de `/proc` acontece dentro dele
      (`test_no_proc_reads_inside_timed_region`, com `/proc` simulado).

**Aula:** 13-1 (workspace uv; por que o Pi precisa de um pacote enxuto e do mesmo lockfile) e 13-2
(processo novo, `ru_maxrss`, PSS/USS, `thread_time_ns`, threads de BLAS). "Como medir o custo de um modelo
sem medir a própria medição?" Erro comum: ler o pico do cgroup sem ter zerado nem isolado o escopo.
```

### `docs/issues/14-triagem-offline.md`

```markdown
# 14: Triagem offline de custo das 42 configurações

**What to build:** rodar o profiler do ticket 13 em todas as configurações do run, na máquina de
desenvolvimento, e juntar o custo à tabela de qualidade de CV.

**Blocked by:** 13

**Status:** ready-for-agent

**Origem:** relatório §2.2

**Contexto:** decisões 49, 57, 59

**Arquivos:** `edge/src/edge_bench/triage.py`, `edge/tests/test_triage.py`,
`notebooks/experiments.ipynb` (seção "Triagem")

- [ ] `triage_run(run_dir, *, out_csv) -> Path` percorre `configs/*`, chama `profile_config` e grava
      `outputs/<run>/triage/offline_<host>.csv`, uma linha por configuração, mais `host_fingerprint`
      (`test_triage_writes_one_row_per_config`, com 2 configurações de smoke).
- [ ] A ordem das configurações é sorteada com semente registrada.
- [ ] O notebook junta a triagem às métricas de CV e mostra qualidade × p95 (B = 1) × PSS.

**Aula:** 14. "O que dá para saber sobre o Pi sem o Pi, e o que não dá?" Conceitos: triagem; o que
transfere entre arquiteturas. Erro comum: levar latência absoluta de x86 para o artigo como se fosse do Pi.
```

### `docs/issues/15-escolha-para-o-pi.md`

```markdown
# 15: Escolha das configurações para o Pi e bundle

**What to build:** o Pareto 3D offline, a regra de escolha (melhor por família, não dominadas e as âncoras
do t16) e um bundle com só as configurações escolhidas, verificável por hash.

**Blocked by:** 12, 14

**Status:** ready-for-agent

**Origem:** relatório §2.2, §2.3

**Contexto:** decisões 51, 52, 53, 59 (ADR 0003)

**Arquivos:** `src/mqtt_dos/pareto.py`, `tests/test_pareto.py`, `edge/src/edge_bench/bundle.py`,
`edge/tests/test_bundle.py`, `notebooks/experiments.ipynb` (seção "Escolha")

- [ ] `pareto_mask(df, *, maximize, minimize) -> np.ndarray` (`test_pareto_mask_simple_cases`).
- [ ] `hypervolume(df, *, maximize, minimize, reference) -> float` (`test_hypervolume_known_value`).
- [ ] `choose_for_pi(cv_results, triage, comparison, *, cap=10, anchors=LOWVARIANCE_T16) -> pd.DataFrame`
      com a coluna `reason` (`best_of_family`, `pareto`, `anchor`) (`test_choice_includes_anchors`,
      `test_choice_respects_cap`).
- [ ] `selection_for_pi.json` gravado em `outputs/<run>/`.
- [ ] `build_bundle(run_dir, selection_json, out_dir) -> Path` copia os diretórios escolhidos e o
      `manifest.json` e grava `bundle_manifest.json` com sha256; `verify_bundle(dir)` falha se algum hash
      divergir (`test_bundle_detects_tampering`).

**Aula:** 15. "Quais modelos merecem horas de bateria no Pi?" Conceitos: dominância em 3 objetivos;
hipervolume; âncora de comparabilidade. Erro comum: levar ao Pi seis árvores equivalentes.
```

### `docs/issues/16-api-predict-binario.md`

```markdown
# 16: API de inferência nova — /predict binário e paridade no startup

**What to build:** um serviço FastAPI em `edge_bench` que carrega uma configuração do bundle, confere
versões, features e predições esperadas antes de aceitar requisições, e responde `POST /predict` com corpo
binário.

**Blocked by:** 15

**Status:** ready-for-agent

**Origem:** relatório §2.3

**Contexto:** decisões 53, 54, 57, 62 (ADR 0003)

**Arquivos:** `edge/src/edge_bench/api.py`, `edge/tests/test_api.py`, `edge/pyproject.toml` (fastapi,
uvicorn; httpx no grupo dev)

- [ ] `create_app(bundle_dir, model_id) -> FastAPI`; endpoints `POST /predict`
      (`application/octet-stream`, float64 C-order, cabeçalhos `X-Rows` e `X-Cols`), `GET /meta` e
      `GET /health`.
- [ ] O startup falha com mensagem clara se: algum sha256 divergir; a versão de scikit-learn ou de numpy
      divergir do manifesto; `feature_names_in_` divergir de `features`; as predições sobre `X_test.npy`
      divergirem de `y_pred_expected.npy` (`test_startup_rejects_*`, um teste por caso).
- [ ] `/predict` com B = 1 e com B = 18.925 devolve as mesmas predições que `y_pred_expected.npy` nas
      mesmas linhas (`test_predict_matches_expected`).
- [ ] Entrada com NaN dá o mesmo resultado com e sem `assume_finite=True` (`test_assume_finite_keeps_nan_handling`).
- [ ] O aviso "X does not have valid feature names" não é emitido por requisição (`test_no_feature_name_warning_per_request`).
- [ ] O endpoint é `def` (síncrono), e o processo usa `--workers 1` no regime isolado.
- [ ] O `run_meta` tem os campos da §2.3 do relatório (`test_run_meta_fields`).

**Aula:** 16-1 (FastAPI mínimo, endpoint síncrono e corpo binário) e 16-2 (paridade: como provar que o Pi
roda o modelo e o teste do treino). Erro comum: medir latência num servidor que lê o CSV do disco a cada
requisição.
```

### `docs/issues/17-linhas-de-base-e-json.md`

```markdown
# 17: Linhas de base e variante JSON

**What to build:** `/ping` (o mesmo caminho sem modelo), `/canary` (busy-loop calibrado) e `/predict-json`,
mais um experimento na máquina de desenvolvimento que mede o custo do transporte, do JSON e dos avisos.

**Blocked by:** 16

**Status:** ready-for-agent

**Origem:** relatório §2.3; plano de inferência §2.1–§2.2

**Contexto:** decisões 54

**Arquivos:** `edge/src/edge_bench/api.py`, `edge/tests/test_api.py`, `notebooks/experiments.ipynb`
(seção "Overhead")

- [ ] `/ping` percorre desserialização, conversão e resposta sem chamar o modelo (`test_ping_does_not_touch_model`).
- [ ] `/canary` executa N iterações calibradas e devolve o tempo (`test_canary_scales_with_iterations`).
- [ ] `/predict-json` aceita `list[list[float | None]]`, converte `None` em NaN e devolve as mesmas
      predições do binário (`test_json_and_binary_agree`).
- [ ] O notebook mede p50 e p95 para B ∈ {1, 32, 1024, 18925}: binário × JSON; ndarray × DataFrame ×
      ndarray com o aviso filtrado; `/predict − /ping`.

**Aula:** 17. "Quanto da latência é o modelo?" Conceitos: linha de base de transporte; canário;
decomposição por fase. Erro comum: atribuir ao modelo o custo do Pydantic.
```

### `docs/issues/18-instrumentacao-no-pi.md`

```markdown
# 18: Instrumentação de recursos no Pi

**What to build:** as leituras de cgroup, `/proc` e sensores do protocolo da §2.4, com escopo dedicado ao
worker, sampler em processo separado e log NDJSON. Inclui as linhas novas do dicionário de métricas.

**Blocked by:** 16

**Status:** ready-for-agent

**Origem:** relatório §2.4

**Contexto:** decisões 56, 57, 58, 61 (ADR 0004)

**Arquivos:** `edge/src/edge_bench/metrics.py`, `edge/src/edge_bench/sampler.py`,
`edge/scripts/run_cell.sh`, `edge/metrics_dictionary.csv` (cópia de
`~/Documentos/inference/dicionario_metricas_inferencia.csv`, mais as linhas novas), `edge/tests/test_metrics.py`

- [ ] `CgroupV2` resolve o caminho por `/proc/self/cgroup`, registra qual fonte foi usada e falha alto se o
      controlador `memory` não estiver ativo (`test_cgroup_path_from_proc_self`, com arquivos simulados).
- [ ] O reset do `memory.peak` mantém **um único descritor aberto** e lê pelo mesmo descritor; com kernel
      abaixo de 6.12, `peak_resettable=False` e o protocolo usa escopo novo
      (`test_peak_reset_reads_same_fd`).
- [ ] O snapshot inclui `memory.stat` (`anon`, `file`), `cpu.stat`, `cpu.pressure` e, se existir,
      `/proc/pressure/cpu` (`test_snapshot_fields`).
- [ ] `run_cell.sh` sobe `uvicorn --workers 1` dentro de `systemd-run --scope -p MemoryAccounting=yes
      -p CPUAccounting=yes`, com `taskset` disjunto para worker, sampler e estressores.
- [ ] O sampler roda como processo separado, fora do escopo do worker, e grava `resources.ndjson`.
- [ ] O `metrics_dictionary.csv` ganha as linhas novas da §2.4 (`cg_anon_b`, `cg_file_b`,
      `cg_cpu_psi_some_us`, `sys_cpu_psi_some_us`, `cpu_core_util_max_pct`, `gpu_backend`,
      `gpu_mem_split_mb`, `page_size_b`, `blas_info`), e todo campo gravado no NDJSON tem linha no dicionário
      (`test_every_logged_field_is_in_dictionary`).

**Aula:** 18-1 (cgroup v2: escopo, `memory.peak`, page cache) e 18-2 (PSI, sampler externo, NDJSON). Erro
comum: ler `MemTotal − MemAvailable` e chamar isso de memória do modelo.
```

### `docs/issues/19-validacao-do-protocolo.md`

```markdown
# 19: Experimento — validação do protocolo no Pi (V1–V6)

**What to build:** os seis experimentos que validam o protocolo no Pi real, cada um com critério de decisão,
antes de qualquer bateria que vá para o artigo.

**Blocked by:** 17, 18

**Status:** ready-for-agent

**Origem:** relatório §2.4, §2.2 (transferência), §5 (comandos)

**Contexto:** decisões 56, 57, 61

**Arquivos:** `edge/src/edge_bench/validation.py`, `notebooks/experiments.ipynb` (seção "Validação no Pi"),
`outputs/<run>/device/validation/`

- [ ] Antes: os comandos C1–C13 do relatório rodados no Pi e as saídas guardadas em `device/host.txt`.
- [ ] V1 (mesmo processo × processo novo): se a diferença for maior que 5%, o processo novo por configuração
      é obrigatório.
- [ ] V2 (custo do observador, n ≥ 10.000, blocos aleatorizados): se Δp95 ≤ máx(2%, 5 µs), L e R podem ser
      fundidas; senão, ficam separadas.
- [ ] V3 (amostra × contador numa rajada de 10.000 chamadas B = 1 de RF): se o máximo amostrado subestimar o
      pico em mais de 5%, só contadores entram nas tabelas.
- [ ] V4 (reset do `memory.peak` no mesmo descritor com 100 MB alocados): se não funcionar, escopo novo por
      janela.
- [ ] V5 (threads): `num_threads=1`; o `SVC.predict` com 1 e 4 threads não muda; se mudar, o SVM entra no
      subexperimento de threads.
- [ ] V6 (transferência): de 6 a 8 configurações medidas com `profile_config` no Pi e na máquina de
      desenvolvimento; se Spearman ρ < 0,9 ou houver inversão entre candidatas, a escolha do ticket 15 é
      refeita com os números do Pi.
- [ ] Cada resultado vira uma linha numa tabela de decisões e, se mudar o protocolo, uma decisão nova.

**Aula:** 19. "A régua mede o que diz medir?" Conceitos: validação de instrumento; critério de decisão
escrito antes do dado. Erro comum: rodar a bateria inteira e só depois descobrir que o pico estava sombreado.
```

### `docs/issues/20-carga-e-matriz.md`

```markdown
# 20: Gerador de carga e matriz de execuções

**What to build:** o gerador de carga no cliente (regimes fechado e aberto/Poisson) e o orquestrador da
matriz: estresse L0–L4, perfis D0–D3, B como fator, execuções L e R, ordem sorteada e critérios de descarte.

**Blocked by:** 19

**Status:** ready-for-agent

**Origem:** relatório §2.4; plano de inferência §3, §5 (E1–E8, E11) e §6

**Contexto:** decisões 56, 57

**Arquivos:** `edge/src/edge_bench/loadgen.py`, `edge/src/edge_bench/matrix.py`, `edge/scripts/run_matrix.sh`,
`edge/tests/test_loadgen.py`, `edge/tests/test_matrix.py`

- [ ] `loadgen` envia lotes de `X_test.npy` em corpo binário, nos regimes fechado e aberto (chegadas de
      Poisson com taxa λ) e grava `client.ndjson` com `req_id` e `t_mono`
      (`test_open_loop_interarrivals_are_exponential`).
- [ ] `build_matrix(factors, *, seed) -> list[Cell]` sorteia a ordem com semente registrada
      (`test_matrix_order_is_seeded_and_complete`).
- [ ] Cada célula grava `run_meta`, `requests.ndjson`, `resources.ndjson` (só em R) e `client.ndjson`.
- [ ] Critérios de descarte aplicados e registrados por célula: bits 0–3 de `get_throttled` no fim;
      temperatura inicial ≥ 55 °C ou máxima ≥ 80 °C; `majflt` > 0; sampler abaixo de 90% da taxa; até duas
      repetições, e depois a célula fica marcada (`test_discard_rules`).
- [ ] O OOM em D2/D3 é registrado como resultado da célula, não como falha do orquestrador.
- [ ] O gerador roda em outro host, por LAN cabeada (`host_fingerprint` do cliente no `client.ndjson`).

**Aula:** 20-1 (regime aberto × fechado; por que a fila só aparece no aberto) e 20-2 (desenho
experimental: fatores, aleatorização, descarte). Erro comum: rodar L0→L4 em ordem e confundir aquecimento
com estresse.
```

### `docs/issues/21-pareto-3d-e-tabelas.md`

```markdown
# 21: Análise final — Pareto 3D, hipervolume, tabelas e figuras

**What to build:** a análise no PC dos NDJSON do Pi: as tabelas T1–T4, as figuras F1–F5 do plano e a
fronteira 3D com hipervolume, com IC bootstrap para os percentis.

**Blocked by:** 20

**Status:** ready-for-agent

**Origem:** relatório §2.2, §2.4; plano de inferência §6.3

**Contexto:** decisões 49, 51, 59

**Arquivos:** `src/mqtt_dos/device_analysis.py`, `tests/test_device_analysis.py`,
`notebooks/experiments.ipynb` (seção "Resultados no Pi")

- [ ] `load_cells(device_dir) -> pd.DataFrame` junta os NDJSON por `req_id` e `t_mono`, descartando as
      células marcadas (`test_load_cells_joins_by_req_id`).
- [ ] p50/p95/p99 com IC bootstrap por célula; o maior percentil reportado respeita o n.
- [ ] T1 (qualidade), T2 (latência isolada B = 1), T3 (recursos: PSS em regime, pico, CPU-s/registro,
      disco) e T4 (degradação normalizada pelo canário).
- [ ] F1 (Pareto 3D: MCC × p95 × PSS, dominância calculada em 3D), F2 (latência × B, log-log), F3, F4 e F5.
- [ ] Tabela LaTeX de T1–T3 gerada para o artigo.

**Aula:** 21. "O que o artigo pode afirmar?" Conceitos: fronteira em 3 objetivos; IC de percentil;
normalização pelo canário. Erro comum: reportar mediana sem n e sem IC.
```

### `docs/issues/22-pacote-a-veredito.md`

```markdown
# 22: Latência pacote-a-veredito com tráfego reproduzido (E9)

**What to build:** a reprodução do tráfego da captura por um broker MQTT local, com extração das features e
dos gaps online no Pi, e medição do caminho pacote → veredito.

**Blocked by:** 21 e a disponibilidade do pcap original (pergunta P2 do relatório)

**Status:** blocked

**Origem:** relatório §2.3 (opção 4); plano de inferência §5, E9

**Contexto:** decisão 63

**Arquivos:** a definir quando o bloqueio cair

- [ ] Paridade entre o extrator online e o CSV: as features extraídas do pcap batem com `X_test.npy` nas
      mesmas linhas (teste a definir).
- [ ] Latência pacote → veredito decomposta em captura, extração, gaps e predict.

**Aula:** a definir. Fica fora de escopo nesta reestruturação (decisão 63).
```

---

## 5. Specs e ADRs — esboços a completar

### 5.1 `docs/issues/0000-spec-treino-unificado.md` (reescrever mantendo a estrutura)

- **Título:** `0000: Fase 1 — treino unificado (detecção de DoS em MQTT)`.
- **Solution:** acrescente ao fim: "A fase 1 termina com o modo do artigo reproduzido (tickets 04–08), o
  experimento da unidade do split (09), o modo corrigido (10) e o experimento 'DoS ou MQTT?' (11). As fases 2
  e 3 têm specs próprias (0001 e 0002)."
- **User Stories, acrescentar:**
  - 31: Como pesquisador, quero saber se pacotes do mesmo fluxo nos dois lados do split inflam a métrica,
    para defender o protocolo diante de um revisor.
  - 32: Como pesquisador, quero ver as métricas recortadas por "o pacote é MQTT?", para saber se o modelo
    detecta ataque ou detecta protocolo.
  - 33: Como pesquisador, quero escolher a configuração pela CV e reportar o teste uma vez, para evitar viés
    de seleção.
  - 34: Como engenheiro de inferência, quero o teste em `.npy` com predições esperadas e hashes, para provar
    que o Pi roda o modelo e os dados do treino.
- **Implementation Decisions:** troque a referência "D1–D25" por "D1–D65". No item **Split**, acrescente
  `split_strategy` (D44) e a chave de fluxo (D45). No item **Avaliação**, acrescente MCC, recortes e IC
  (D49–D50). No item **Tuning**, acrescente `cv_splitter` e as métricas de CV (D46, D48). No item
  **Artefatos**, use a lista da D52.
- **Testing Decisions:** acrescente como seams a paridade do artefato exportado, a ausência de fluxo
  compartilhado no `flow_group` e a ausência de colunas de teste no grid.
- **Out of Scope:** troque "`api_inference/`: adaptar a API…" por "A `api_inference/` atual continua
  intocada; a API nova é a fase 3 (spec 0002)".
- **Further Notes:** os números de vazamento medidos (relatório §2.1a, §2.1b).

### 5.2 `docs/issues/0001-spec-avaliacao-e-selecao.md` (criar)

Use a mesma estrutura da 0000 (Problem Statement, Solution, User Stories, Implementation Decisions, Testing
Decisions, Out of Scope, Further Notes):

- **Problem:** 42 configurações com qualidade praticamente empatada na faixa alta; a escolha antiga usava o
  teste e ignorava custo e memória.
- **Solution:** comparação pareada (12), profiler e triagem offline (13–14), escolha e bundle (15).
- **User Stories:**
  - decidir se duas configurações diferem;
  - levar ao Pi só o que pode estar na fronteira;
  - saber o que a triagem offline prevê sobre o Pi.
- **Implementation Decisions:** D48, D49, D51, D55, D57, D59.
- **Testing Decisions:** valores conhecidos de McNemar, Holm e hipervolume; o profiler sobrevive à queda do
  filho.
- **Out of Scope:** medição no Pi (spec 0002).

### 5.3 `docs/issues/0002-spec-inferencia-no-dispositivo.md` (criar)

- **Problem:** o t16 mede o sistema inteiro, com contenção, em lote único, sem garantia de identidade do
  modelo e dos dados (relatório §1, itens 1 e 3).
- **Solution:** API nova com paridade (16), linhas de base (17), instrumentação (18), validação (19), matriz
  (20) e análise (21); E9 bloqueado (22).
- **Implementation Decisions:** D53, D54, D56, D57, D58, D61, D62, D63.
- **Testing Decisions:** testes com `/proc` e `/sys` simulados na máquina de desenvolvimento; os
  experimentos V1–V6 no Pi são a validação real.
- **Out of Scope:** energia; a `api_inference/` antiga.

### 5.4 ADRs (formato da `0001-gaps-sem-rotulo.md`: Status, Contexto, Decisão, Alternativas, Consequências)

- **`0002-unidade-do-split.md`.** Status: aceita (revisável pelo ticket 09). Contexto: os números da §2.1a.
  Decisão: D44. Alternativas: só o artigo; trocar já para fluxo; deixa-um-host-de-fora (inviável).
  Consequências: dois modos no `RunConfig`; a CV herda a unidade (D46); o artigo declara a limitação do
  atacante novo.
- **`0003-contrato-de-dados-treino-api.md`.** Status: aceita. Contexto: a divergência 0,9688 × 0,9754, os CSVs
  escalonados para LDA/QDA e o `.pkl` do GB que não carrega em 1.9.1. Decisão: D52 e D53. Alternativas: CSV
  lido pelo servidor; JSON; tráfego reproduzido. Consequências: o ticket 08 cresce; a API recusa subir com
  versão divergente.
- **`0004-escopo-da-medicao-de-recursos.md`.** Status: aceita (revisável pelo ticket 19). Contexto: a §2.4
  e os 8 defeitos do profiler. Decisão: D56. Alternativas: sistema inteiro (t16); cgroup do container;
  amostragem contínua. Consequências: duas execuções por célula; processo novo por configuração; kernel e
  cgroup registrados.

---

## 6. Termos para acrescentar ao `GLOSSARY.md`

Em linguagem de domínio, sem detalhe de implementação, como os termos atuais:

- **Fluxo**: conjunto de pacotes entre os mesmos dois pares IP:porta, sem importar a direção; pacotes sem IP
  formam fluxo pelo par de endereços MAC.
- **Unidade do split**: o que é sorteado para o treino ou para o teste: o pacote (modo do artigo), o fluxo ou
  a posição no tempo.
- **Split por fluxo / split temporal por classe**: as duas alternativas ao split do artigo.
- **Duplicata exata**: registro de teste com o mesmo vetor de features de algum registro do treino.
- **Recorte MQTT**: avaliação restrita aos pacotes que têm a camada MQTT.
- **Regra "é MQTT"**: baseline que classifica como DoS todo pacote com camada MQTT.
- **MCC**: correlação entre o predito e o real numa tabela 2 × 2; escalar de qualidade do projeto.
- **FPR**: fração de pacotes normais classificados como DoS.
- **Comparação pareada**: comparação de duas configurações sobre os mesmos registros de teste.
- **Margem de equivalência**: diferença abaixo da qual duas configurações contam como iguais (0,005 de MCC).
- **Triagem offline**: medição de custo na máquina de desenvolvimento, antes do Pi.
- **Bundle**: o subconjunto de artefatos de um run levado ao Pi, com hashes.
- **Paridade**: a verificação de que o modelo no Pi reproduz as predições esperadas do treino.
- **Regime isolado / regime operacional**: um worker, um núcleo e concorrência 1, contra o serviço com
  vários workers sob carga.
- **Execução L / execução R**: execução que mede latência sem instrumentação de recursos, e execução que mede
  recursos.
- **Memória em regime (PSS)**: memória do worker com o modelo carregado e aquecido, rateando páginas
  compartilhadas.
- **Memória de pico**: o maior uso de memória numa janela; é o que provoca OOM.
- **Escopo dedicado**: o cgroup que contém só o worker em medição.
- **Efeito sombra**: um pico anterior à janela medida que esconde o pico da janela.
- **Efeito do observador**: o custo da própria medição embutido no número medido.
- **Linha de base de transporte (`/ping`) / canário (`/canary`)**: as referências para separar o custo do
  modelo do custo do serviço e da plataforma.
- **Tamanho de lote (B)**: o número de registros por requisição; B = 1 é o caso de IDS em linha.
- **Fronteira de Pareto 3D**: as configurações não dominadas em qualidade (MCC), p95 com B = 1 e memória em
  regime; **substitui** a definição de "Fronteira de Pareto" (D49, D59).
- **Hipervolume**: o volume dominado por uma fronteira, usado para comparar fronteiras.
