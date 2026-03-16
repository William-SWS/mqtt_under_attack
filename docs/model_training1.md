# Documentação: matriz_correlacao_with_gaps

## Derivação de features e prevenção de vazamento
- Fonte de dados: `data/processed/DoS_with_gap_features.csv` carregado na notebook [notebooks/matriz_correlacao_with_gaps.ipynb](notebooks/matriz_correlacao_with_gaps.ipynb#L11-L52).
- As features `publish_gap` e `connect_gap` foram criadas no notebook [notebooks/publish_feature.ipynb](notebooks/publish_feature.ipynb#L100-L185) com o fluxo:
  - Divisão treino/teste estratificada (70/30) **antes** de qualquer cálculo temporal para evitar vazamento.
  - Para cada split, `publish_gap` = diferença em `frame.time_epoch` apenas em linhas `mqtt.msgtype == 3`; `connect_gap` = diferença em `frame.time_epoch` apenas em linhas `mqtt.msgtype == 1`.
  - Valores iniciais `NaN` são substituídos por `0` após o `diff`, de modo independente em treino e teste; colunas `mqtt.proto_len` e `mqtt.ver` removidas.
  - Dataset consolidado salvo em `data/processed/DoS_with_gap_2.csv` e depois enriquecido (versão `DoS_with_gap_features.csv`) preservando as colunas de gap. Esse fluxo impede que gaps usem timestamps do conjunto de validação/teste.
- Na limpeza local do notebook, colunas de metadata e credenciais são removidas e valores ausentes/infinitos zerados antes do label encoding ([notebooks/matriz_correlacao_with_gaps.ipynb](notebooks/matriz_correlacao_with_gaps.ipynb#L62-L111)).

## Métodos de seleção de features (reexecutados a cada fold)
- mRMR (`mrmr_classif`, K=15 por padrão): busca máxima relevância mínima redundância; cai para `K` disponível se houver menos colunas.
- Fisher Score: ordena `fisher_score` e pega top `K_fisher` (15).
- Correlação de Pearson: ordena correlação absoluta com `y` e pega top `K_pearson` (15).
- ExtraTrees: `ExtraTreesClassifier(n_estimators=300, random_state=42, n_jobs=-1)`, top `K_tree` (15) via `feature_importances_`.
- LinearSVC L1: `StandardScaler` + `LinearSVC(C=0.1, penalty='l1', dual=False, max_iter=5000, random_state=42)`, top `K_svc` (15) pelo módulo das coeficientes.
- LassoCV: `StandardScaler` + `LassoCV(cv=3, max_iter=10000, random_state=42, n_jobs=-1)`, top `K_lasso` (15) pelo módulo das coeficientes.
- Baixa variância: `VarianceThreshold(threshold=0.0)`, mantém colunas com variância > 0.
- Referência de código: [notebooks/matriz_correlacao_with_gaps.ipynb](notebooks/matriz_correlacao_with_gaps.ipynb#L2375-L2635).

## Modelos de treinamento e hiperparâmetros
- RandomForest: `n_estimators=200`, `max_depth=None`, `random_state=42`, `n_jobs=-1`.
- LogisticRegression: `solver='lbfgs'`, `max_iter=2000`, `n_jobs=-1`.
- GaussianNB: parâmetros padrão.
- SVM RBF: `kernel='rbf'`, `C=1.0`, `gamma='scale'`, `probability=True`, `random_state=42`.
- DecisionTree: `random_state=42`.
- Factories garantem novo modelo por fold (evita reaproveitar estado). Ver [notebooks/matriz_correlacao_with_gaps.ipynb](notebooks/matriz_correlacao_with_gaps.ipynb#L2530-L2545).

## Cross-validation
- Esquema: `StratifiedKFold(n_splits=5, shuffle=True, random_state=42)`.
- Em cada fold: selecionador executa apenas em `X_train`, gera subconjunto de colunas, e o modelo treina/prediz em `X_train[cols]`/`X_val[cols]` (sem vazamento de seleção ou dos gaps).
- Métricas por modelo: accuracy, precision_macro, recall_macro, f1_macro, MCC; log_loss quando `predict_proba` ou `decision_function` estão disponíveis. Médias e desvios por fold são armazenados.
- Visualização: gráficos horizontais com barras de erro e anotações numéricas para cada métrica (accuracy, precision, recall, F1, MCC, log loss). Código em [notebooks/matriz_correlacao_with_gaps.ipynb](notebooks/matriz_correlacao_with_gaps.ipynb#L2637-L2758).
- Células de execução por seletor (mRMR, Fisher, Pearson, ExtraTrees, LinearSVC_L1, LassoCV, LowVariance) estão no fim do notebook e repetem o fluxo de CV e gráficos para cada seletor ([notebooks/matriz_correlacao_with_gaps.ipynb](notebooks/matriz_correlacao_with_gaps.ipynb#L2760-L2814)).

## Observações rápidas sobre vazamento
- Os gaps são calculados após o split e nunca a partir de linhas de validação/teste.
- A seleção de features é refeita dentro de cada fold, garantindo que apenas dados de treino do fold influenciem o espaço de features usado na validação.