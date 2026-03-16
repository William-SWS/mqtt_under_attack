# Documentação: model_training

## Derivação de features e prevenção de vazamento
- Fonte de dados: `data/processed/DoS_with_gap_2.csv` carregado na notebook [notebooks/model_training.ipynb](notebooks/model_training.ipynb#L62-L111).
- As colunas `publish_gap` e `connect_gap` foram construídas em [notebooks/publish_feature.ipynb](notebooks/publish_feature.ipynb#L100-L185):
  - Split estratificado 70/30 em treino/teste **antes** de calcular os gaps.
  - `publish_gap`: `diff` de `frame.time_epoch` apenas em linhas `mqtt.msgtype == 3` dentro de cada split; `NaN` → `0` após o cálculo.
  - `connect_gap`: `diff` de `frame.time_epoch` apenas em linhas `mqtt.msgtype == 1` dentro de cada split; `NaN` → `0` após o cálculo.
  - Colunas `mqtt.proto_len` e `mqtt.ver` removidas; dataset final salvo como `DoS_with_gap_2.csv`. Isso evita que tempos do conjunto de validação/teste vazem para o cálculo das features temporais.
- No pré-processamento local, remove-se metadados e credenciais, preenche-se ausentes/infinitos com 0 e aplica-se label encoding ([notebooks/model_training.ipynb](notebooks/model_training.ipynb#L80-L120)).

## Métodos de seleção de features (reexecutados a cada fold)
- mRMR (`mrmr_classif`, K=15 default ou `K_mrmr`): máxima relevância, mínima redundância.
- Fisher Score: ordena `fisher_score`; pega top `K_fisher` (15).
- Correlação de Pearson: correlação absoluta com `y`; top `K_generic` (15).
- ExtraTrees: `ExtraTreesClassifier(n_estimators=300, random_state=42, n_jobs=-1)`; top `K_importance` (15) via `feature_importances_`.
- LinearSVC L1: `StandardScaler` + `LinearSVC(C=0.1, penalty='l1', dual=False, max_iter=5000, random_state=42)`; top `K_linear` (15) pelo módulo das coeficientes.
- LassoCV: `StandardScaler` + `LassoCV(cv=3, max_iter=10000, random_state=42, n_jobs=-1)`; top `K_lasso` (15) por coeficientes.
- Baixa variância: `VarianceThreshold(threshold=0.0)`; mantém variância > 0.
- Referência: [notebooks/model_training.ipynb](notebooks/model_training.ipynb#L1481-L1585).

## Modelos de treinamento e hiperparâmetros
- RandomForest: `n_estimators=200`, `max_depth=None`, `random_state=42`, `n_jobs=-1`.
- LogisticRegression: `solver='lbfgs'`, `max_iter=2000`, `n_jobs=-1`.
- GaussianNB: padrão.
- SVM RBF: `kernel='rbf'`, `C=1.0`, `gamma='scale'`, `probability=True`, `random_state=42`.
- DecisionTree: `random_state=42`.
- Factories retornam instâncias novas a cada fold para evitar reuso de estado (ver [notebooks/model_training.ipynb](notebooks/model_training.ipynb#L1468-L1480)).

## Cross-validation
- Esquema: `StratifiedKFold(n_splits=5, shuffle=True, random_state=42)`.
- Fluxo por fold: seletor roda em `X_train` do fold → define colunas → modelo treina em `X_train[cols]` → avalia em `X_val[cols]`; seleção não vê dados de validação.
- Métricas: accuracy, precision_macro, recall_macro, f1_macro, MCC; log_loss quando disponível via `predict_proba` ou `decision_function` (com softmax para scores). Médias e desvios são armazenados.
- Visualização: gráficos horizontais com barras de erro e anotações numéricas (accuracy, precision, recall, F1, MCC, log loss). Código em [notebooks/model_training.ipynb](notebooks/model_training.ipynb#L1587-L1664).
- Células dedicadas executam o ciclo para cada seletor (mRMR, Fisher, Pearson, ExtraTrees, LinearSVC_L1, LassoCV, LowVariance) e geram tabelas/plots ([notebooks/model_training.ipynb](notebooks/model_training.ipynb#L1666-L1762)).

## Observações rápidas sobre vazamento
- As features de gap são calculadas por split antes de qualquer treino, impedindo contaminação temporal.
- A seleção de features é refeita dentro de cada fold da CV, isolando o conjunto de validação de qualquer decisão de seleção ou ajuste de hiperparâmetros.