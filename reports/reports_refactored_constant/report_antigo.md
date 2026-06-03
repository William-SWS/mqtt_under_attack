# Relatorio de Analise: Deteccao de Ataques DoS em MQTT

**Data:** 2026-04-26 18:18
**Modelos avaliados:** LDA, QDA, GaussianNB, DecisionTree, RandomForest, GradientBoosting

## 1. Resultado Principal
- Melhor modelo global: DecisionTree (Optuna (ExtraTrees))
- Acuracia: 0.9754
- Precisao: 0.9757
- F1 Score: 0.9754
- Log Loss: 0.0806

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
| DecisionTree (Optuna)     |   0.975376 |    0.975665 | 0.97536  |  0.0806129 |
| GradientBoosting (Optuna) |   0.974478 |    0.974994 | 0.974454 |  0.0783547 |
| RandomForest (Optuna)     |   0.974478 |    0.975014 | 0.974454 |  0.0710875 |
| LDA (Optuna)              |   0.923646 |    0.932385 | 0.923029 |  0.376519  |
| QDA (Optuna)              |   0.923065 |    0.931535 | 0.922457 |  0.883461  |
| GaussianNB (Optuna)       |   0.920581 |    0.928356 | 0.919992 |  2.8342    |

### Optuna por Seletor - Melhor Modelo por Seletor
| seletor      | modelo       |   n_features |   accuracy |   precision |       f1 |   log_loss |
|:-------------|:-------------|-------------:|-----------:|------------:|---------:|-----------:|
| ExtraTrees   | DecisionTree |           15 |   0.975376 |    0.975665 | 0.97536  |  0.0806129 |
| LowVariance  | DecisionTree |           12 |   0.975376 |    0.975665 | 0.97536  |  0.0806129 |
| LinearSVC_L1 | DecisionTree |           15 |   0.975376 |    0.975665 | 0.97536  |  0.0806129 |
| mRMR         | DecisionTree |           15 |   0.975376 |    0.975665 | 0.97536  |  0.0806129 |
| Fisher       | DecisionTree |           15 |   0.968085 |    0.968698 | 0.968051 |  0.107308  |
| LassoCV      | DecisionTree |           15 |   0.968085 |    0.968698 | 0.968051 |  0.105586  |
| Pearson      | DecisionTree |           15 |   0.968085 |    0.968698 | 0.968051 |  0.107308  |

### Comparacao Sem Optuna vs Com Optuna por Seletor
| seletor      | modelo_sem_optuna   |   f1_sem_optuna |   log_loss_sem_optuna | modelo_com_optuna   |   f1_com_optuna |   log_loss_com_optuna |    delta_f1 |
|:-------------|:--------------------|----------------:|----------------------:|:--------------------|----------------:|----------------------:|------------:|
| ExtraTrees   | GradientBoosting    |        0.97504  |             0.073568  | DecisionTree        |        0.97536  |             0.0806129 | 0.000320365 |
| Fisher       | DecisionTree        |        0.96794  |             0.106537  | DecisionTree        |        0.968051 |             0.107308  | 0.000110525 |
| LassoCV      | DecisionTree        |        0.96794  |             0.108282  | DecisionTree        |        0.968051 |             0.105586  | 0.000110256 |
| LinearSVC_L1 | GradientBoosting    |        0.97504  |             0.0735972 | DecisionTree        |        0.97536  |             0.0806129 | 0.000320365 |
| LowVariance  | GradientBoosting    |        0.97504  |             0.0736098 | DecisionTree        |        0.97536  |             0.0806129 | 0.000320365 |
| Pearson      | DecisionTree        |        0.96794  |             0.106537  | DecisionTree        |        0.968051 |             0.107308  | 0.000110525 |
| mRMR         | GradientBoosting    |        0.974987 |             0.0736257 | DecisionTree        |        0.97536  |             0.0806129 | 0.000373157 |

## 3. Tempos de Execucao
Os tempos foram medidos com `time.perf_counter()` e registrados em segundos. Em linhas onde a medida nao se aplica, o valor fica como `NaN`.

### 3.1 Resumo Por Etapa
| stage                            |   n_registros |   tempo_total_sec |   tempo_medio_sec |   tempo_min_sec |   tempo_max_sec |
|:---------------------------------|--------------:|------------------:|------------------:|----------------:|----------------:|
| optuna_by_selector_optimization  |            42 |        834.263    |         19.8634   |       3.81831   |       90.5227   |
| optuna_global_optimization       |             6 |        142.563    |         23.7604   |       3.85938   |       89.1384   |
| optuna_by_selector_training      |            42 |         50.5805   |          1.2043   |       0.070345  |        6.83249  |
| feature_selection_selector_total |             7 |         49.9277   |          7.13253  |       5.15569   |        8.55048  |
| feature_selection                |            42 |         42.3377   |          1.00804  |       0.0681837 |        5.2651   |
| optuna_global_training           |             6 |          9.36771  |          1.56128  |       0.0760669 |        6.78861  |
| ensemble_base_training           |             6 |          7.43047  |          1.23841  |       0.0779156 |        5.1865   |
| baseline                         |             6 |          7.41422  |          1.2357   |       0.0730126 |        5.23713  |
| ensemble_soft_voting             |             1 |          0.168598 |          0.168598 |       0.168598  |        0.168598 |
| ensemble_averaging               |             1 |          0.153643 |          0.153643 |       0.153643  |        0.153643 |

### 3.2 Resumo Por Modelo
| modelo           |   n_registros |   tempo_total_sec |   tempo_medio_sec |   tempo_min_sec |   tempo_max_sec |
|:-----------------|--------------:|------------------:|------------------:|----------------:|----------------:|
| GradientBoosting |            25 |          677.087  |          27.0835  |       2.4643    |        90.5227  |
| RandomForest     |            25 |          239.381  |           9.57525 |       0.769762  |        31.6147  |
| QDA              |            25 |           52.2808 |           2.09123 |       0.106273  |         6.55559 |
| DecisionTree     |            25 |           46.5933 |           1.86373 |       0.0730674 |         6.10693 |
| LDA              |            25 |           46.2105 |           1.84842 |       0.110938  |         5.77801 |
| GaussianNB       |            25 |           32.4038 |           1.29615 |       0.0681837 |         3.98926 |

### 3.3 Resumo Por Seletor
| seletor      |   n_registros |   n_features |   tempo_total_sec |   tempo_medio_sec |   tempo_min_sec |   tempo_max_sec |
|:-------------|--------------:|-------------:|------------------:|------------------:|----------------:|----------------:|
| LowVariance  |            19 |           12 |           166.449 |           8.76049 |       0.0681837 |         88.1476 |
| ExtraTrees   |            19 |           15 |           166.183 |           8.74649 |       0.0685444 |         90.5227 |
| mRMR         |            19 |           15 |           165.031 |           8.68583 |       0.0709514 |         89.2354 |
| LinearSVC_L1 |            19 |           15 |           162.16  |           8.53472 |       0.0736548 |         88.8492 |
| Fisher       |            19 |           15 |           108.332 |           5.70167 |       0.070345  |         51.2422 |
| Pearson      |            19 |           15 |           107.051 |           5.63424 |       0.0724174 |         49.8912 |
| LassoCV      |            19 |           15 |           101.903 |           5.36334 |       0.0709456 |         46.1686 |

### 3.4 Etapas Mais Custosas
| stage                            |   tempo_total_sec |   tempo_medio_sec |
|:---------------------------------|------------------:|------------------:|
| optuna_by_selector_optimization  |          834.263  |          19.8634  |
| optuna_global_optimization       |          142.563  |          23.7604  |
| optuna_by_selector_training      |           50.5805 |           1.2043  |
| feature_selection_selector_total |           49.9277 |           7.13253 |
| feature_selection                |           42.3377 |           1.00804 |

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