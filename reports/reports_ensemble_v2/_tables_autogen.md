## Apêndice A — Melhores hiperparâmetros (Optuna Global)

| modelo           |   best_f1_cv | best_params                                                                                                                                        |
|:-----------------|-------------:|:---------------------------------------------------------------------------------------------------------------------------------------------------|
| GradientBoosting |     0.974659 | {"n_estimators": 191, "max_depth": 6, "learning_rate": 0.03504750508385013, "min_samples_split": 11}                                               |
| RandomForest     |     0.972321 | {"n_estimators": 296, "max_depth": 10, "min_samples_split": 98, "min_samples_leaf": 10, "max_features": "log2", "max_samples": 0.7198645099727456} |
| DecisionTree     |     0.971031 | {"max_depth": 5, "min_samples_split": 97, "min_samples_leaf": 79, "max_features": null}                                                            |
| LDA              |     0.926316 | {"solver": "svd", "tol": 1.493656855461763e-06}                                                                                                    |
| QDA              |     0.925776 | {"reg_param": 0.0396760507705299}                                                                                                                  |
| GaussianNB       |     0.925308 | {"var_smoothing": 6.351221010640695e-06}                                                                                                           |


## Apêndice B — Melhor par (seletor, modelo) no teste (Optuna por seletor)

| seletor      | modelo           |   n_features |   accuracy |   precision |       f1 |   log_loss |
|:-------------|:-----------------|-------------:|-----------:|------------:|---------:|-----------:|
| ExtraTrees   | GradientBoosting |           15 |   0.975376 |    0.975733 | 0.975358 |  0.0714057 |
| LowVariance  | GradientBoosting |           12 |   0.975376 |    0.975733 | 0.975358 |  0.0714057 |
| LinearSVC_L1 | GradientBoosting |           15 |   0.975376 |    0.975733 | 0.975358 |  0.0714057 |
| mRMR         | GradientBoosting |           15 |   0.975376 |    0.975733 | 0.975358 |  0.0714057 |
| Fisher       | GradientBoosting |           15 |   0.967926 |    0.968528 | 0.967892 |  0.0999679 |
| Pearson      | GradientBoosting |           15 |   0.967926 |    0.968528 | 0.967892 |  0.0999679 |
| LassoCV      | GradientBoosting |           15 |   0.967873 |    0.968493 | 0.967839 |  0.102422  |


## Apêndice C — Tempos por etapa (resumo)

| stage                            |   n_registros |   tempo_total_sec |   tempo_medio_sec |   tempo_min_sec |   tempo_max_sec |
|:---------------------------------|--------------:|------------------:|------------------:|----------------:|----------------:|
| optuna_by_selector_optimization  |            42 |       1203.86     |         28.6633   |       3.71955   |      136.598    |
| optuna_global_optimization       |             6 |        217.934    |         36.3224   |       3.87237   |      137.719    |
| optuna_by_selector_training      |            42 |         80.123    |          1.90769  |       0.0650877 |       11.0037   |
| feature_selection_selector_total |             7 |         49.1374   |          7.01963  |       5.11914   |        8.58978  |
| feature_selection                |            42 |         41.7721   |          0.994574 |       0.0675365 |        5.20033  |
| optuna_global_training           |             6 |         15.5744   |          2.59574  |       0.0687415 |       11.3587   |
| baseline                         |             6 |          7.77537  |          1.2959   |       0.0740205 |        5.47968  |
| ensemble_smart_voting            |             1 |          5.34694  |          5.34694  |       5.34694   |        5.34694  |
| ensemble_hard_voting             |             1 |          2.29984  |          2.29984  |       2.29984   |        2.29984  |
| ensemble_averaging               |             1 |          0.159039 |          0.159039 |       0.159039  |        0.159039 |


## Apêndice D — Tempos por modelo (resumo)

| modelo           |   n_registros |   tempo_total_sec |   tempo_medio_sec |   tempo_min_sec |   tempo_max_sec |
|:-----------------|--------------:|------------------:|------------------:|----------------:|----------------:|
| GradientBoosting |            24 |          982.68   |          40.945   |       1.27766   |       137.719   |
| RandomForest     |            24 |          417.127  |          17.3803  |       1.18422   |        59.2768  |
| QDA              |            24 |           49.9054 |           2.07939 |       0.104684  |         6.32439 |
| LDA              |            24 |           45.2096 |           1.88373 |       0.10637   |         5.56552 |
| DecisionTree     |            24 |           40.742  |           1.69758 |       0.0650877 |         5.21199 |
| GaussianNB       |            24 |           31.3733 |           1.30722 |       0.0675365 |         3.87237 |


## Apêndice E — Tempos por seletor (resumo)

| seletor      |   n_registros |   n_features |   tempo_total_sec |   tempo_medio_sec |   tempo_min_sec |   tempo_max_sec |
|:-------------|--------------:|-------------:|------------------:|------------------:|----------------:|----------------:|
| LowVariance  |            19 |           12 |           244.426 |          12.8645  |       0.0683038 |        134.731  |
| mRMR         |            19 |           15 |           239.831 |          12.6227  |       0.0678309 |        136.598  |
| ExtraTrees   |            19 |           15 |           232.875 |          12.2566  |       0.0679207 |        132.414  |
| LinearSVC_L1 |            19 |           15 |           227.913 |          11.9954  |       0.0678928 |        129.955  |
| Pearson      |            19 |           15 |           158.054 |           8.31866 |       0.0675844 |         80.5047 |
| Fisher       |            19 |           15 |           157.225 |           8.27501 |       0.067222  |         79.0421 |
| LassoCV      |            19 |           15 |           114.565 |           6.02975 |       0.0650877 |         47.4174 |
