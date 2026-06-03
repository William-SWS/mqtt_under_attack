# Relatorio de Analise: Deteccao de Ataques DoS em MQTT

**Data:** 2026-05-04 00:15
**Modelos avaliados:** LDA, QDA, GaussianNB, DecisionTree, RandomForest, GradientBoosting

## 1. Resultado Principal
- Melhor modelo global: GradientBoosting (Optuna (mRMR))
- Acuracia: 0.9754
- Precisao: 0.9757
- F1 Score: 0.9754
- Log Loss: 0.0714

## 2. Metricas Obrigatorias por Etapa
As quatro metricas obrigatorias (acuracia, precisao, f1 e log_loss) foram calculadas em baseline, selecao de features, ensemble e Optuna (global e por seletor).

### Baseline
| Modelo           |   accuracy |   precision |       f1 |   log_loss |
|:-----------------|-----------:|------------:|---------:|-----------:|
| GradientBoosting |   0.975059 |    0.975443 | 0.97504  |  0.0735627 |
| DecisionTree     |   0.97432  |    0.974573 | 0.974304 |  0.135895  |
| RandomForest     |   0.974055 |    0.974682 | 0.974028 |  0.0724223 |
| LDA              |   0.923857 |    0.932576 | 0.923244 |  0.376601  |
| QDA              |   0.923065 |    0.931535 | 0.922457 |  0.901391  |
| GaussianNB       |   0.920476 |    0.928173 | 0.91989  |  2.71742   |

### Selecao de Features - Melhor Modelo por Seletor
| seletor      | modelo           |   n_features |   accuracy |   precision |       f1 |   log_loss |
|:-------------|:-----------------|-------------:|-----------:|------------:|---------:|-----------:|
| ExtraTrees   | GradientBoosting |           15 |   0.975059 |    0.975443 | 0.97504  |  0.073568  |
| Fisher       | DecisionTree     |           15 |   0.967979 |    0.968728 | 0.96794  |  0.106537  |
| LassoCV      | DecisionTree     |           15 |   0.967979 |    0.96872  | 0.96794  |  0.108282  |
| LinearSVC_L1 | GradientBoosting |           15 |   0.975059 |    0.975443 | 0.97504  |  0.0735972 |
| LowVariance  | GradientBoosting |           12 |   0.975059 |    0.975443 | 0.97504  |  0.0736098 |
| Pearson      | DecisionTree     |           15 |   0.967979 |    0.968728 | 0.96794  |  0.106537  |
| mRMR         | GradientBoosting |           15 |   0.975007 |    0.975388 | 0.974987 |  0.0736257 |

### Ensemble
| Metodo      |   accuracy |   precision |       f1 |   log_loss |
|:------------|-----------:|------------:|---------:|-----------:|
| Soft Voting |   0.927926 |    0.93658  | 0.927354 |   0.10671  |
| Averaging   |   0.925495 |    0.934599 | 0.924876 |   0.108458 |

### Optuna Global
| modelo                    |   accuracy |   precision |       f1 |   log_loss |
|:--------------------------|-----------:|------------:|---------:|-----------:|
| GradientBoosting (Optuna) |   0.975376 |    0.975733 | 0.975358 |  0.0714057 |
| RandomForest (Optuna)     |   0.973052 |    0.973826 | 0.973019 |  0.0884397 |
| DecisionTree (Optuna)     |   0.971096 |    0.971715 | 0.971066 |  0.0820838 |
| LDA (Optuna)              |   0.923646 |    0.932385 | 0.923029 |  0.376519  |
| GaussianNB (Optuna)       |   0.923382 |    0.932785 | 0.922725 |  1.19332   |
| QDA (Optuna)              |   0.923065 |    0.931535 | 0.922457 |  0.983869  |

### Optuna por Seletor - Melhor Modelo por Seletor
| seletor      | modelo           |   n_features |   accuracy |   precision |       f1 |   log_loss |
|:-------------|:-----------------|-------------:|-----------:|------------:|---------:|-----------:|
| ExtraTrees   | GradientBoosting |           15 |   0.975376 |    0.975733 | 0.975358 |  0.0714057 |
| LowVariance  | GradientBoosting |           12 |   0.975376 |    0.975733 | 0.975358 |  0.0714057 |
| LinearSVC_L1 | GradientBoosting |           15 |   0.975376 |    0.975733 | 0.975358 |  0.0714057 |
| mRMR         | GradientBoosting |           15 |   0.975376 |    0.975733 | 0.975358 |  0.0714057 |
| Fisher       | GradientBoosting |           15 |   0.967926 |    0.968528 | 0.967892 |  0.0999679 |
| Pearson      | GradientBoosting |           15 |   0.967926 |    0.968528 | 0.967892 |  0.0999679 |
| LassoCV      | GradientBoosting |           15 |   0.967873 |    0.968493 | 0.967839 |  0.102422  |

### Comparacao Sem Optuna vs Com Optuna por Seletor
| seletor      | modelo_sem_optuna   |   f1_sem_optuna |   log_loss_sem_optuna | modelo_com_optuna   |   f1_com_optuna |   log_loss_com_optuna |     delta_f1 |
|:-------------|:--------------------|----------------:|----------------------:|:--------------------|----------------:|----------------------:|-------------:|
| ExtraTrees   | GradientBoosting    |        0.97504  |             0.073568  | GradientBoosting    |        0.975358 |             0.0714057 |  0.00031816  |
| Fisher       | DecisionTree        |        0.96794  |             0.106537  | GradientBoosting    |        0.967892 |             0.0999679 | -4.77794e-05 |
| LassoCV      | DecisionTree        |        0.96794  |             0.108282  | GradientBoosting    |        0.967839 |             0.102422  | -0.000101587 |
| LinearSVC_L1 | GradientBoosting    |        0.97504  |             0.0735972 | GradientBoosting    |        0.975358 |             0.0714057 |  0.00031816  |
| LowVariance  | GradientBoosting    |        0.97504  |             0.0736098 | GradientBoosting    |        0.975358 |             0.0714057 |  0.00031816  |
| Pearson      | DecisionTree        |        0.96794  |             0.106537  | GradientBoosting    |        0.967892 |             0.0999679 | -4.77794e-05 |
| mRMR         | GradientBoosting    |        0.974987 |             0.0736257 | GradientBoosting    |        0.975358 |             0.0714057 |  0.000370952 |

## 3. Tempos de Execucao
Os tempos foram medidos com `time.perf_counter()` e registrados em segundos. Em linhas onde a medida nao se aplica, o valor fica como `NaN`.

### 3.1 Resumo Por Etapa
| stage                            |   n_registros |   tempo_total_sec |   tempo_medio_sec |   tempo_min_sec |   tempo_max_sec |
|:---------------------------------|--------------:|------------------:|------------------:|----------------:|----------------:|
| optuna_by_selector_optimization  |            42 |       1244.4      |         29.6286   |       3.78968   |      140.963    |
| optuna_global_optimization       |             6 |        223.44     |         37.24     |       3.92238   |      140.408    |
| optuna_by_selector_training      |            42 |         83.6384   |          1.99139  |       0.0659681 |       11.3989   |
| feature_selection_selector_total |             7 |         51.677    |          7.38243  |       5.36576   |        8.99705  |
| feature_selection                |            42 |         44.2522   |          1.05362  |       0.0684694 |        5.56206  |
| optuna_global_training           |             6 |         15.323    |          2.55383  |       0.0711657 |       11.1748   |
| baseline                         |             6 |          8.07767  |          1.34628  |       0.076245  |        5.69184  |
| ensemble_base_training           |             6 |          7.78279  |          1.29713  |       0.0780903 |        5.36141  |
| ensemble_soft_voting             |             1 |          0.179706 |          0.179706 |       0.179706  |        0.179706 |
| ensemble_averaging               |             1 |          0.158243 |          0.158243 |       0.158243  |        0.158243 |

### 3.2 Resumo Por Modelo
| modelo           |   n_registros |   tempo_total_sec |   tempo_medio_sec |   tempo_min_sec |   tempo_max_sec |
|:-----------------|--------------:|------------------:|------------------:|----------------:|----------------:|
| GradientBoosting |            25 |         1019.47   |          40.7789  |       1.45184   |       140.963   |
| RandomForest     |            25 |          433.896  |          17.3558  |       1.1585    |        60.8964  |
| QDA              |            25 |           52.4787 |           2.09915 |       0.110987  |         6.85191 |
| LDA              |            25 |           47.5899 |           1.90359 |       0.108826  |         6.19874 |
| DecisionTree     |            25 |           41.3096 |           1.65238 |       0.0659681 |         5.16251 |
| GaussianNB       |            25 |           32.1696 |           1.28678 |       0.0684694 |         3.9933  |

### 3.3 Resumo Por Seletor
| seletor      |   n_registros |   n_features |   tempo_total_sec |   tempo_medio_sec |   tempo_min_sec |   tempo_max_sec |
|:-------------|--------------:|-------------:|------------------:|------------------:|----------------:|----------------:|
| LowVariance  |            19 |           12 |           250.583 |          13.1886  |       0.0673449 |        138.09   |
| ExtraTrees   |            19 |           15 |           248.942 |          13.1022  |       0.0690966 |        140.963  |
| LinearSVC_L1 |            19 |           15 |           244.376 |          12.8619  |       0.0689348 |        138.724  |
| mRMR         |            19 |           15 |           238.974 |          12.5776  |       0.0701179 |        137.687  |
| Fisher       |            19 |           15 |           159.526 |           8.39612 |       0.0682949 |         80.2026 |
| Pearson      |            19 |           15 |           158.19  |           8.32578 |       0.069024  |         78.8965 |
| LassoCV      |            19 |           15 |           123.378 |           6.4936  |       0.0659681 |         50.8407 |

### 3.4 Etapas Mais Custosas
| stage                            |   tempo_total_sec |   tempo_medio_sec |
|:---------------------------------|------------------:|------------------:|
| optuna_by_selector_optimization  |         1244.4    |          29.6286  |
| optuna_global_optimization       |          223.44   |          37.24    |
| optuna_by_selector_training      |           83.6384 |           1.99139 |
| feature_selection_selector_total |           51.677  |           7.38243 |
| feature_selection                |           44.2522 |           1.05362 |

## 4. Analise de Falsos Positivos e Falsos Negativos
Para cada seletor de caracteristicas, foram geradas matrizes de confusao para todos os modelos e tambem para o melhor modelo do seletor.

### 4.1 Melhor Modelo por Seletor - FP/FN por Classe
- LowVariance: modelo=GradientBoosting, F1=0.9750, FP=[97, 375], FN=[375, 97]
- Pearson: modelo=DecisionTree, F1=0.9679, FP=[108, 498], FN=[498, 108]
- Fisher: modelo=DecisionTree, F1=0.9679, FP=[108, 498], FN=[498, 108]
- mRMR: modelo=GradientBoosting, F1=0.9750, FP=[98, 375], FN=[375, 98]
- LassoCV: modelo=DecisionTree, F1=0.9679, FP=[109, 497], FN=[497, 109]
- LinearSVC_L1: modelo=GradientBoosting, F1=0.9750, FP=[97, 375], FN=[375, 97]
- ExtraTrees: modelo=GradientBoosting, F1=0.9750, FP=[97, 375], FN=[375, 97]

### 4.2 Matrizes de Confusao por Seletor
#### Seletor: LowVariance
- LDA: FP=[37, 1404], FN=[1404, 37], CM=[[7699, 1404], [37, 9785]]
- QDA: FP=[55, 1403], FN=[1403, 55], CM=[[7700, 1403], [55, 9767]]
- GaussianNB: FP=[105, 1400], FN=[1400, 105], CM=[[7703, 1400], [105, 9717]]
- DecisionTree: FP=[130, 357], FN=[357, 130], CM=[[8746, 357], [130, 9692]]
- RandomForest: FP=[79, 405], FN=[405, 79], CM=[[8698, 405], [79, 9743]]
- GradientBoosting: FP=[97, 375], FN=[375, 97], CM=[[8728, 375], [97, 9725]]

#### Seletor: Pearson
- LDA: FP=[46, 1450], FN=[1450, 46], CM=[[7653, 1450], [46, 9776]]
- QDA: FP=[46, 1473], FN=[1473, 46], CM=[[7630, 1473], [46, 9776]]
- GaussianNB: FP=[105, 1399], FN=[1399, 105], CM=[[7704, 1399], [105, 9717]]
- DecisionTree: FP=[108, 498], FN=[498, 108], CM=[[8605, 498], [108, 9714]]
- RandomForest: FP=[102, 511], FN=[511, 102], CM=[[8592, 511], [102, 9720]]
- GradientBoosting: FP=[102, 509], FN=[509, 102], CM=[[8594, 509], [102, 9720]]

#### Seletor: Fisher
- LDA: FP=[46, 1450], FN=[1450, 46], CM=[[7653, 1450], [46, 9776]]
- QDA: FP=[46, 1473], FN=[1473, 46], CM=[[7630, 1473], [46, 9776]]
- GaussianNB: FP=[105, 1399], FN=[1399, 105], CM=[[7704, 1399], [105, 9717]]
- DecisionTree: FP=[108, 498], FN=[498, 108], CM=[[8605, 498], [108, 9714]]
- RandomForest: FP=[102, 511], FN=[511, 102], CM=[[8592, 511], [102, 9720]]
- GradientBoosting: FP=[102, 509], FN=[509, 102], CM=[[8594, 509], [102, 9720]]

#### Seletor: mRMR
- LDA: FP=[37, 1404], FN=[1404, 37], CM=[[7699, 1404], [37, 9785]]
- QDA: FP=[53, 1403], FN=[1403, 53], CM=[[7700, 1403], [53, 9769]]
- GaussianNB: FP=[105, 1400], FN=[1400, 105], CM=[[7703, 1400], [105, 9717]]
- DecisionTree: FP=[129, 357], FN=[357, 129], CM=[[8746, 357], [129, 9693]]
- RandomForest: FP=[81, 403], FN=[403, 81], CM=[[8700, 403], [81, 9741]]
- GradientBoosting: FP=[98, 375], FN=[375, 98], CM=[[8728, 375], [98, 9724]]

#### Seletor: LassoCV
- LDA: FP=[47, 1401], FN=[1401, 47], CM=[[7702, 1401], [47, 9775]]
- QDA: FP=[60, 1400], FN=[1400, 60], CM=[[7703, 1400], [60, 9762]]
- GaussianNB: FP=[105, 1399], FN=[1399, 105], CM=[[7704, 1399], [105, 9717]]
- DecisionTree: FP=[109, 497], FN=[497, 109], CM=[[8606, 497], [109, 9713]]
- RandomForest: FP=[103, 510], FN=[510, 103], CM=[[8593, 510], [103, 9719]]
- GradientBoosting: FP=[106, 503], FN=[503, 106], CM=[[8600, 503], [106, 9716]]

#### Seletor: LinearSVC_L1
- LDA: FP=[37, 1408], FN=[1408, 37], CM=[[7695, 1408], [37, 9785]]
- QDA: FP=[55, 1403], FN=[1403, 55], CM=[[7700, 1403], [55, 9767]]
- GaussianNB: FP=[105, 1400], FN=[1400, 105], CM=[[7703, 1400], [105, 9717]]
- DecisionTree: FP=[129, 357], FN=[357, 129], CM=[[8746, 357], [129, 9693]]
- RandomForest: FP=[78, 405], FN=[405, 78], CM=[[8698, 405], [78, 9744]]
- GradientBoosting: FP=[97, 375], FN=[375, 97], CM=[[8728, 375], [97, 9725]]

#### Seletor: ExtraTrees
- LDA: FP=[37, 1404], FN=[1404, 37], CM=[[7699, 1404], [37, 9785]]
- QDA: FP=[53, 1403], FN=[1403, 53], CM=[[7700, 1403], [53, 9769]]
- GaussianNB: FP=[105, 1400], FN=[1400, 105], CM=[[7703, 1400], [105, 9717]]
- DecisionTree: FP=[129, 357], FN=[357, 129], CM=[[8746, 357], [129, 9693]]
- RandomForest: FP=[78, 403], FN=[403, 78], CM=[[8700, 403], [78, 9744]]
- GradientBoosting: FP=[97, 375], FN=[375, 97], CM=[[8728, 375], [97, 9725]]

## 5. Artefatos Gerados
- reports_refactored/baseline_results.csv
- reports_refactored/baseline_timing_results.csv
- reports_refactored/selection_results.csv
- reports_refactored/selection_timing_results.csv
- reports_refactored/selection_selector_timing_results.csv
- reports_refactored/best_model_by_selector.csv
- reports_refactored/ensemble_results.csv
- reports_refactored/optuna_results.csv
- reports_refactored/optuna_by_selector_results.csv
- reports_refactored/best_optuna_model_by_selector.csv
- reports_refactored/optuna_by_selector_comparison_cenario1_constant.csv
- reports_refactored/optuna_by_selector_best_params.json
- reports_refactored/optuna_by_selector_confusion_matrices.json
- reports_refactored/timing_results.csv
- reports_refactored/timing_summary_by_stage.csv
- reports_refactored/timing_summary_by_model.csv
- reports_refactored/timing_summary_by_selector.csv
- reports_refactored/final_results_all_models.csv
- reports_refactored/confusion_matrices_by_selector.json
- reports_refactored/best_confusion_matrix_by_selector.json
- reports_refactored/optuna_confusion_matrices.json
- reports_refactored/RELATORIO_FINAL.md
- models/models_optuna/*.pkl
- models/models_refactored/*.pkl
