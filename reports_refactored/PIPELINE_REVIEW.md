# Revisão do Pipeline: Vazamento de Dados e Problemas de Métrica

Análise de `notebooks_refactored/04_pipeline.ipynb` e `notebooks_refactored/04_svm.ipynb`,
cobrindo a preparação dos dados e o treinamento. Os achados estão ordenados por gravidade.

Contexto do dataset: `data/raw/MQTT Under Attack Dataset/DoS.csv` é **binário** (45.514 `DoS`
vs 49.111 `normal`, 94.625 linhas). Ambos os notebooks fazem um split aleatório estratificado
80/20 com `random_state=42`.

---

## 1. Crítico: vazamento de dados

### L1. Os pesos do Smart Soft Voting são ajustados diretamente no conjunto de teste

`04_pipeline.ipynb`, célula 42 (`smart_voting`):

```python
def ensemble_objective(trial):
    ...
    return f1_score(y_test, y_pred, average='weighted', zero_division=0)

study_ensemble.optimize(ensemble_objective, n_trials=100, ...)
```

O estudo Optuna maximiza o **F1 do conjunto de teste**. O "Smart Soft Voting" reportado é
otimista porque o conjunto de teste foi usado como conjunto de ajuste. É o vazamento mais
evidente do pipeline.

**Correção:** ajustar os pesos do ensemble somente nos dados de treino (por exemplo, um split
de validação ou `cross_val_predict`) e avaliar no teste exatamente uma vez, no final.

### L2. `publish_gap` / `connect_gap` são calculados antes do split

`04_pipeline.ipynb` células 9–11 e `04_svm.ipynb` célula 3:

```python
df_full = df_full.sort_values('frame.time_epoch')   # dataset completo
...                                                  # np.diff na sequência completa
df_clean['publish_gap'] = df_full['publish_gap'].values
X_train, X_test, ... = train_test_split(...)         # split acontece DEPOIS
```

As features de gap derivam da ordenação temporal do dataset completo, então o valor de uma
amostra depende de outras amostras que podem acabar no split oposto. É pré-processamento
aplicado no pool treino+teste antes da divisão, exatamente a classe de vazamento que o
`Pipeline` do scikit-learn existe para evitar.

**Correção:** dividir primeiro, depois calcular as features de gap de forma independente
dentro do treino e dentro do teste, usando apenas amostras anteriores (gap retroativo, não
prospectivo). Alternativamente, calcular a feature dentro de um `Pipeline` com um transformer
customizado, para que seja reajustado a cada fold.

### L3. Split aleatório em um dataset de IDS temporal e com rajadas

Ambos os notebooks usam `train_test_split(stratify=y)` sem nenhum agrupamento temporal. Num
dataset de IDS em nível de pacote, um ataque é uma rajada de muitos pacotes quase idênticos
numa janela curta de tempo. Um split aleatório espalha pacotes da *mesma* rajada entre treino
e teste, então o modelo consegue memorizar a assinatura da rajada e as métricas ficam
infladas. Provavelmente é uma fonte de otimismo maior do que qualquer bug individual de
métrica.

**Correção:** dividir por tempo (ou por sessão/fluxo de captura, quando disponível), por
exemplo `TimeSeriesSplit` ou um corte fixo num timestamp. Reportar as métricas num conjunto de
teste separado por tempo.

---

## 2. Problemas de cálculo de métrica

### M1. Sem recall; apenas médias weighted

O `evaluate_model` de `04_pipeline.ipynb` (célula 18) reporta `accuracy`, `precision`
(weighted), `f1` (weighted) e `log_loss`, mas **omite o recall por completo**. Para um IDS, o
número operacionalmente relevante é o recall/TPR da classe `DoS` (taxa de detecção de ataque).
O balanceamento atual de 48/52 faz com que weighted ≈ macro aqui, então a lacuna é pequena
hoje, mas médias weighted mascaram falha por classe conforme o desbalanceamento cresce.

**Correção:** sempre reportar precision/recall/F1 por classe mais as médias macro, e destacar
o recall da classe `DoS`.

### M2. As probabilidades do ensemble são não calibradas enquanto as métricas individuais são calibradas

O `evaluate_model` envolve `QDA` e `GaussianNB` em `CalibratedClassifierCV(method='sigmoid')`
e reporta as métricas calibradas. Mas a célula 35 guarda o estimador base cru
(`optuna_trained_models[model_name] = base_model`), e o ensemble (células 39–42) chama
`model.predict_proba()` nesses modelos **não calibrados**. O soft voting/ajuste de pesos,
portanto, mistura probabilidades não calibradas enquanto a tabela por modelo reporta as
calibradas.

A mesma inconsistência vaza para os artefatos: `result['model']` (calibrado) é salvo na célula
45, enquanto a célula 50 salva `optuna_trained_models` (não calibrado). Dois arquivos `.pkl`
do mesmo modelo podem divergir dos números reportados.

**Correção:** persistir e usar no ensemble exatamente o estimador cujas métricas foram
reportadas. Decidir explicitamente se QDA/NB são calibrados ou não e usar o mesmo objeto em
todos os lugares.

### M3. Os seletores "Pearson" e "Fisher" são idênticos; "mRMR" está rotulado errado

`04_pipeline.ipynb` célula 23: `Pearson` e `Fisher` usam ambos `SelectKBest(f_classif)` (valor
F da ANOVA, não correlação de Pearson), e `mRMR` é apenas `mutual_info_classif` top-k. O
`selected_features.json` salvo confirma que `Pearson` e `Fisher` produzem listas de features
byte a byte idênticas. O relatório, portanto, conta duas vezes um método e apresenta um mRMR
que não é mRMR.

**Correção:** implementar um seletor de correlação de Pearson de verdade (ou removê-lo) e,
ou implementar mRMR real (relevância − redundância), ou renomear a coluna para `MutualInfo`.

---

## 3. Problemas de pré-processamento

### P1. Imputação com 0 constante confunde "ausente" com um valor real

As colunas `mqtt.*` ficam vazias para todo tráfego não-MQTT (por exemplo, as linhas SSH/TCP
visíveis no CSV cru). Imputar com `0` torna "não é um pacote MQTT" indistinguível de um valor
real de 0 (por exemplo, `mqtt.msgtype = 0` é o código "reserved" do MQTT). A correção do
split está correta (a imputação acontece pós-split), mas a representação engana o modelo.

**Correção:** usar um marcador de ausência (por exemplo, `SimpleImputer(add_indicator=True)`,
ou um sentinela `-1`/`NaN` com um modelo que o trate), ou uma flag categórica `is_mqtt`.

### P2. Seletores baseados em L1 ajustados em features não escaladas

`LassoCV` e `LinearSVC_L1` na célula 23 rodam sobre `X_train` cru (imputado, não
padronizado). A penalidade L1 é dependente de escala, então colunas de grande escala
(`frame.len`, `frame.cap_len`) dominam a seleção independentemente da relevância. Seletores
baseados em árvore e `f_classif`/`mutual_info` são invariantes a escala e não são afetados.

**Correção:** padronizar antes da seleção baseada em L1, ou ranquear pelos coeficientes
padronizados.

### P3. StandardScaler sobre colunas bimodais majoritariamente imputadas

Após a imputação com 0, muitas colunas `mqtt.*` são 0 para ~metade das linhas (todo tráfego
não-MQTT) e assumem valores reais no restante. O `StandardScaler` sobre uma coluna bimodal
produz uma distribuição em dois aglomerados que não é o que o scaler pressupõe. Isso afeta
principalmente os modelos sensíveis a escala (LDA, QDA, SVM); os modelos de árvore ignoram.

**Correção:** aplicar escala apenas em features genuinamente contínuas, ou normalizar por
modelo dentro de um `ColumnTransformer` que separe colunas contínuas cruas de colunas
imputadas/indicadoras.

---

## 4. O que mudar (checklist)

1. **Pesos do ensemble:** ajustar apenas em treino/validação; nunca passar `y_test` para o
   Optuna.
2. **Features de gap:** dividir primeiro, calcular por split com gaps retroativos (apenas
   passado), ou colocá-las num transformer customizado dentro de um `Pipeline`.
3. **Estratégia de split:** adotar split temporal para este dataset temporal/com rajadas e
   reportar a pontuação do conjunto separado por tempo como número principal.
4. **Métricas:** adicionar recall (por classe + macro), destacar o recall de `DoS`, manter
   métricas weighted como secundárias.
5. **Consistência do estimador:** persistir e usar no ensemble exatamente o objeto
   calibrado/não calibrado cujas métricas foram reportadas; remover os caminhos `.pkl`
   duplicados.
6. **Seletores:** corrigir ou remover o par duplicado `Pearson`/`Fisher` e renomear ou
   implementar o `mRMR` corretamente.
7. **Imputação:** usar indicador de valor ausente para `mqtt.*` em vez de preencher cegamente
   com 0.
8. **Seleção de features:** padronizar antes da seleção baseada em L1.
9. **Escala:** restringir a escala a colunas contínuas via `ColumnTransformer`.
10. **Ajuste do SVM:** substituir o hold-out único 80/20 (`svm_hold_out`) pelo `svm_2_fold` já
    escrito, ou um `StratifiedKFold`, para a execução de produção.
11. **Ensemble:** remover o bloco de ensemble (células 38–43) e todas as referências nos
    resultados/relatório/resumo (células 47, 49, 52). O Optuna de modelos individuais
    permanece inalterado (ver seção 5).
12. **Manutenção:** extrair a lógica duplicada (limpeza de colunas, cálculo de gap, avaliação,
    timing) para um módulo compartilhado e remover código morto (ver seção 6).

---

## 5. Removendo o ensemble do fluxo (e do Optuna)

Contexto: hoje o ensemble **não** participa do ajuste de hiperparâmetros dos modelos. O
Optuna global (células 32–33) e o por seletor (célula 45) otimizam modelos individuais via
`cross_val_score(scoring='f1_weighted')`. A única interseção entre Optuna e ensemble é o
**Smart Soft Voting** (célula 42), que usa Optuna para ajustar pesos diretamente sobre
`y_test`. Como não haverá ensemble, esse acoplamento desaparece junto com o bloco.

### Passos concretos em `04_pipeline.ipynb`

1. **Remover o bloco de ensemble (células 38–43):**
   - 38 (markdown "Ensemble com Modelos Otimizados");
   - 39 (gera `probs_stack_opt` / `preds_stack_opt`);
   - 40 (Averaging), 41 (Hard Voting), 42 (Smart Soft Voting), 43 (comparação + save).
2. **Célula 47** (consolidação final): remover as três linhas
   `all_results.append({'categoria': 'Ensemble (Otimizado)', ...})`.
3. **Célula 49** (resumo): remover a linha `print("4. Ensemble: Soft Voting + Averaging")` e
   renumerar a etapa seguinte.
4. **Célula 52** (relatório): remover o bloco `report_lines.append('### Ensemble')` e o
   `ensemble_comparison.to_markdown(...)` correspondente.
5. **Célula 0** (objetivos em markdown): remover o item "5. Ensemble (Soft Voting +
   Averaging)" e renumerar.
6. **Manter** `optuna_trained_models` (usado na célula 50 para salvar os melhores modelos) e
   todo o Optuna de modelos individuais (células 32–33 e 45), que não contêm ensemble.
7. **Nenhuma mudança** é necessária no Optuna em si: `objective_factory` e
   `objective_selector_factory` já otimizam modelos individuais. O ajuste de pesos por Optuna
   (Smart Soft Voting) é exatamente o que deve ser excluído.

### Consequências

- O achado **L1** (vazamento do Smart Soft Voting) é eliminado por completo.
- O achado **M2** é parcialmente resolvido: sem ensemble, as probabilidades não calibradas não
  são mais combinadas. Ainda assim, alinhe os `.pkl` (célula 45 salva `result['model']`
  calibrado; célula 50 salva `base_model` não calibrado) ao objeto efetivamente avaliado.

### Artefatos que deixam de ser gerados

- `reports_ensemble_v2/ensemble_results.csv`
- `reports_ensemble_v2/cm_averaging.npy`, `cm_hard_voting.npy`, `cm_smart_voting.npy`

---

## 6. Legibilidade e manutenibilidade dos notebooks

### A. Duplicação entre notebooks e células

- A lista `columns_to_remove` (~47 itens) é copiada verbatim em `04_pipeline.ipynb` (célula 6)
  e `04_svm.ipynb` (célula 3).
- A lógica de gap (`sort_values` + `np.diff` + atribuição por tipo de tráfego) está duplicada
  em `04_pipeline.ipynb` (célula 10) e `04_svm.ipynb` (célula 3).
- Dois helpers de avaliação divergentes: `evaluate_model` (pipeline) e `evaluate_svm` (SVM).
- Dois helpers de timing divergentes: `append_timing_record` (pipeline) e `append_timing` (SVM).

**Sugestão:** extrair para um módulo compartilhado (ex.: `src/features.py`,
`src/preprocessing.py`, `src/evaluation.py`, `src/timing.py`) importado pelos notebooks. Uma
única fonte da verdade elimina o risco de drift (um notebook muda a lista ou a lógica, o outro
não).

### B. Código morto e imports não usados

- `calculate_gaps` (célula 9 do pipeline) é um stub que nunca é chamado e não faz nada.
- `time_features` (célula 9) é calculado e nunca usado.
- Imports não usados no pipeline: `recall_score`, `roc_auc_score`, `roc_curve`,
  `ConfusionMatrixDisplay`, `SelectFromModel` e `from scipy.stats import mode` (célula 39,
  substituído por `pandas.DataFrame().mode`).

**Sugestão:** rodar um linter (ex.: `ruff check --select F401`) e remover tudo o que não é
usado. Código morto sugere intenção de funcionalidade que não existe.

### C. Números mágicos e estado global

- `RANDOM_STATE=42`, `N_FEATURES=15`, `VAL_SIZE=0.2` e os budgets de trials por modelo estão
  espalhados pelo notebook.
- `timing_records` é uma lista global mutada por `append_timing_record` (efeito colateral
  implícito, difícil de rastrear).
- `MODELS_REQUIRING_SCALING` e `MODELS_REQUIRING_CALIBRATION` são definidos longe do ponto de
  uso.

**Sugestão:** concentrar a configuração em constantes no topo (ou em um `config.py`) e
encapsular o timing num objeto ou context manager em vez de uma lista global.

### D. Clonagem frágil de estimadores

- `model.__class__(**model.get_params())` re-instancia via classe + parâmetros. É implícito e
  quebra com estimadores aninhados (como o `CalibratedClassifierCV` usado em QDA/NB).

**Sugestão:** usar `sklearn.base.clone(model)`, que é a forma canônica e segura.

### E. Células com múltiplas responsabilidades e prints pesados

- Células misturam transformação, salvamento em disco e impressão de DataFrames inteiros.
- `%pip install tabulate` dentro da célula 52: dependência deveria estar em `requirements.txt`,
  não instalada em runtime.
- `warnings.filterwarnings('ignore')` suprime `ConvergenceWarning` globalmente, escondendo
  modelos que não convergiram.
- Caminhos como `'../reports/reports_ensemble_v2/...'` repetidos como string (o `04_svm.ipynb`
  já faz melhor, com `Path` + constantes de diretório).

**Sugestão:** separar "compute" de "persistir/reportar"; usar constantes `Path` (como no SVM)
em vez de strings repetidas; tratar warnings pontualmente (`max_iter`, escalonamento) em vez de
suprimir globalmente.

### F. Numeração e documentação inconsistente

- A numeração das seções markdown do pipeline pula o 8 (vai de "7. Treinamento" para
  "9. Otimização").
- O markdown do SVM diz "25 trials", mas o código usa `N_TRIALS_FAST = 12` (drift doc/código).
- Idioma misto: campos de timing em português (`tempo_fit_sec`, `seletor`, `modelo`) com
  variáveis e funções em inglês.

**Sugestão:** uniformizar o idioma (o repo exige inglês) e manter doc/código sincronizados;
preferir gerar tabelas de parâmetros a partir do próprio código para evitar drift.

### G. Reprodutibilidade

- `np.random.seed` é definido, mas `random.seed` não; o SVM usa `n_jobs=-1` no Optuna, e
  trials paralelos podem não ser determinísticos.

**Sugestão:** fixar seeds de `numpy` e `random` e evitar paralelismo não determinístico no
Optuna, ou documentar a não determinismo aceito.
