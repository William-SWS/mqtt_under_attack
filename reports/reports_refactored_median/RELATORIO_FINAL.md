# Relatorio de Analise: Deteccao de Ataques DoS em MQTT

**Data:** 2026-05-04 20:50
**Modelos avaliados:** LDA, QDA, GaussianNB, DecisionTree, RandomForest, GradientBoosting

## 1. Resultado Principal
- Melhor modelo global: RandomForest (Optuna) (Otimizado (Optuna))
- Acuracia: 0.9643
- Precisao: 0.9653
- F1 Score: 0.9642
- Log Loss: 0.1001

## 2. Metricas Obrigatorias por Etapa
As quatro metricas obrigatorias (acuracia, precisao, f1 e log_loss) foram calculadas em baseline, selecao de features, ensemble e Optuna (global e por seletor).

### Baseline
| Modelo           |   accuracy |   precision |       f1 |   log_loss |
|:-----------------|-----------:|------------:|---------:|-----------:|
| GradientBoosting |   0.962589 |    0.963909 | 0.962522 |   0.107844 |
| DecisionTree     |   0.961955 |    0.962724 | 0.961907 |   0.142707 |
| RandomForest     |   0.961321 |    0.963113 | 0.961235 |   0.151049 |
| LDA              |   0.632602 |    0.645004 | 0.628545 |   0.639049 |
| QDA              |   0.531096 |    0.64228  | 0.38948  |   3.34301  |
| GaussianNB       |   0.529247 |    0.627151 | 0.386283 |   5.79464  |

### Selecao de Features - Melhor Modelo por Seletor
| seletor      | modelo           |   n_features |   accuracy |   precision |       f1 |   log_loss |
|:-------------|:-----------------|-------------:|-----------:|------------:|---------:|-----------:|
| ExtraTrees   | GradientBoosting |           15 |   0.962589 |    0.963909 | 0.962522 |   0.107865 |
| Fisher       | DecisionTree     |           15 |   0.95181  |    0.953957 | 0.951684 |   0.159733 |
| LassoCV      | DecisionTree     |           15 |   0.954452 |    0.956567 | 0.954335 |   0.154766 |
| LinearSVC_L1 | GradientBoosting |           15 |   0.962589 |    0.963909 | 0.962522 |   0.107857 |
| LowVariance  | GradientBoosting |           12 |   0.962589 |    0.963909 | 0.962522 |   0.107848 |
| Pearson      | DecisionTree     |           15 |   0.95181  |    0.953957 | 0.951684 |   0.159733 |
| mRMR         | GradientBoosting |           15 |   0.962589 |    0.963909 | 0.962522 |   0.107863 |

### Ensemble
| Metodo      |   accuracy |   precision |       f1 |   log_loss |
|:------------|-----------:|------------:|---------:|-----------:|
| Soft Voting |   0.960317 |    0.962456 | 0.960216 |   0.255323 |
| Averaging   |   0.950594 |    0.954409 | 0.950398 |   0.362502 |

### Optuna Global
| modelo                    |   accuracy |   precision |       f1 |   log_loss |
|:--------------------------|-----------:|------------:|---------:|-----------:|
| RandomForest (Optuna)     |   0.96428  |    0.96531  | 0.964226 |   0.100106 |
| GradientBoosting (Optuna) |   0.964122 |    0.965029 | 0.964072 |   0.101071 |
| DecisionTree (Optuna)     |   0.962325 |    0.96314  | 0.962276 |   0.137091 |
| LDA (Optuna)              |   0.633765 |    0.6465   | 0.629602 |   0.640557 |
| QDA (Optuna)              |   0.612206 |    0.620921 | 0.609248 |   0.70439  |
| GaussianNB (Optuna)       |   0.530832 |    0.636233 | 0.389589 |   4.49152  |

### Optuna por Seletor - Melhor Modelo por Seletor
| seletor      | modelo           |   n_features |   accuracy |   precision |       f1 |   log_loss |
|:-------------|:-----------------|-------------:|-----------:|------------:|---------:|-----------:|
| LowVariance  | RandomForest     |           12 |   0.964227 |    0.965318 | 0.964171 |   0.102402 |
| LinearSVC_L1 | GradientBoosting |           15 |   0.964122 |    0.965029 | 0.964072 |   0.101065 |
| ExtraTrees   | GradientBoosting |           15 |   0.964122 |    0.965029 | 0.964072 |   0.101071 |
| mRMR         | GradientBoosting |           15 |   0.964122 |    0.965029 | 0.964072 |   0.101063 |
| LassoCV      | DecisionTree     |           15 |   0.955667 |    0.957206 | 0.955577 |   0.152797 |
| Fisher       | DecisionTree     |           15 |   0.952972 |    0.954489 | 0.952877 |   0.159059 |
| Pearson      | DecisionTree     |           15 |   0.952972 |    0.954489 | 0.952877 |   0.159059 |

### Comparacao Sem Optuna vs Com Optuna por Seletor
| seletor      | modelo_sem_optuna   |   f1_sem_optuna |   log_loss_sem_optuna | modelo_com_optuna   |   f1_com_optuna |   log_loss_com_optuna |   delta_f1 |
|:-------------|:--------------------|----------------:|----------------------:|:--------------------|----------------:|----------------------:|-----------:|
| ExtraTrees   | GradientBoosting    |        0.962522 |              0.107865 | GradientBoosting    |        0.964072 |              0.101071 | 0.00154975 |
| Fisher       | DecisionTree        |        0.951684 |              0.159733 | DecisionTree        |        0.952877 |              0.159059 | 0.00119237 |
| LassoCV      | DecisionTree        |        0.954335 |              0.154766 | DecisionTree        |        0.955577 |              0.152797 | 0.00124147 |
| LinearSVC_L1 | GradientBoosting    |        0.962522 |              0.107857 | GradientBoosting    |        0.964072 |              0.101065 | 0.00154975 |
| LowVariance  | GradientBoosting    |        0.962522 |              0.107848 | RandomForest        |        0.964171 |              0.102402 | 0.00164906 |
| Pearson      | DecisionTree        |        0.951684 |              0.159733 | DecisionTree        |        0.952877 |              0.159059 | 0.00119237 |
| mRMR         | GradientBoosting    |        0.962522 |              0.107863 | GradientBoosting    |        0.964072 |              0.101063 | 0.00154975 |

## 3. Tempos de Execucao
Os tempos foram medidos com `time.perf_counter()` e registrados em segundos. Em linhas onde a medida nao se aplica, o valor fica como `NaN`.

### 3.1 Resumo Por Etapa
| stage                            |   n_registros |   tempo_total_sec |   tempo_medio_sec |   tempo_min_sec |   tempo_max_sec |
|:---------------------------------|--------------:|------------------:|------------------:|----------------:|----------------:|
| optuna_by_selector_optimization  |            42 |        717.064    |         17.0729   |       3.51357   |       72.9392   |
| optuna_global_optimization       |             6 |        121.635    |         20.2725   |       3.91932   |       65.6524   |
| feature_selection_selector_total |             7 |         47.7182   |          6.81689  |       4.99798   |        8.57226  |
| feature_selection                |            42 |         40.6873   |          0.968745 |       0.0641613 |        5.54322  |
| optuna_by_selector_training      |            42 |         23.501    |          0.559548 |       0.0626194 |        2.33625  |
| ensemble_base_training           |             6 |          7.94304  |          1.32384  |       0.0709872 |        5.40025  |
| baseline                         |             6 |          7.20142  |          1.20024  |       0.0705305 |        5.10709  |
| optuna_global_training           |             6 |          4.16835  |          0.694725 |       0.0665492 |        2.13446  |
| ensemble_soft_voting             |             1 |          0.169843 |          0.169843 |       0.169843  |        0.169843 |
| ensemble_averaging               |             1 |          0.15635  |          0.15635  |       0.15635   |        0.15635  |

### 3.2 Resumo Por Modelo
| modelo           |   n_registros |   tempo_total_sec |   tempo_medio_sec |   tempo_min_sec |   tempo_max_sec |
|:-----------------|--------------:|------------------:|------------------:|----------------:|----------------:|
| GradientBoosting |            25 |          505.834  |          20.2334  |       1.05452   |        72.9392  |
| RandomForest     |            25 |          243.834  |           9.75334 |       0.480523  |        33.5889  |
| QDA              |            25 |           49.7281 |           1.98913 |       0.0977607 |         6.65519 |
| DecisionTree     |            25 |           46.6972 |           1.86789 |       0.079237  |         6.31694 |
| LDA              |            25 |           45.0894 |           1.80358 |       0.105497  |         5.92905 |
| GaussianNB       |            25 |           31.0172 |           1.24069 |       0.0626194 |         4.22831 |

### 3.3 Resumo Por Seletor
| seletor      |   n_registros |   n_features |   tempo_total_sec |   tempo_medio_sec |   tempo_min_sec |   tempo_max_sec |
|:-------------|--------------:|-------------:|------------------:|------------------:|----------------:|----------------:|
| mRMR         |            19 |           15 |          146.331  |           7.70162 |       0.0645571 |         71.1579 |
| ExtraTrees   |            19 |           15 |          144.265  |           7.59291 |       0.0641749 |         72.9392 |
| LowVariance  |            19 |           12 |          133.834  |           7.04387 |       0.0641613 |         63.9786 |
| LinearSVC_L1 |            19 |           15 |          132.466  |           6.97187 |       0.0636793 |         65.2278 |
| LassoCV      |            19 |           15 |           94.3717 |           4.96693 |       0.0655679 |         39.2775 |
| Pearson      |            19 |           15 |           89.0346 |           4.68603 |       0.0661193 |         37.4855 |
| Fisher       |            19 |           15 |           88.6688 |           4.66678 |       0.0626194 |         37.5898 |

### 3.4 Etapas Mais Custosas
| stage                            |   tempo_total_sec |   tempo_medio_sec |
|:---------------------------------|------------------:|------------------:|
| optuna_by_selector_optimization  |          717.064  |         17.0729   |
| optuna_global_optimization       |          121.635  |         20.2725   |
| feature_selection_selector_total |           47.7182 |          6.81689  |
| feature_selection                |           40.6873 |          0.968745 |
| optuna_by_selector_training      |           23.501  |          0.559548 |

## 4. Analise de Falsos Positivos e Falsos Negativos
Para cada seletor de caracteristicas, foram geradas matrizes de confusao para todos os modelos e tambem para o melhor modelo do seletor.

### 4.1 Melhor Modelo por Seletor - FP/FN por Classe
- LowVariance: modelo=GradientBoosting, F1=0.9625, FP=[95, 613], FN=[613, 95]
- Pearson: modelo=DecisionTree, F1=0.9517, FP=[122, 790], FN=[790, 122]
- Fisher: modelo=DecisionTree, F1=0.9517, FP=[122, 790], FN=[790, 122]
- mRMR: modelo=GradientBoosting, F1=0.9625, FP=[95, 613], FN=[613, 95]
- LassoCV: modelo=DecisionTree, F1=0.9543, FP=[101, 761], FN=[761, 101]
- LinearSVC_L1: modelo=GradientBoosting, F1=0.9625, FP=[95, 613], FN=[613, 95]
- ExtraTrees: modelo=GradientBoosting, F1=0.9625, FP=[95, 613], FN=[613, 95]

### 4.2 Matrizes de Confusao por Seletor
#### Seletor: LowVariance
- LDA: FP=[4714, 2224], FN=[2224, 4714], CM=[[6879, 2224], [4714, 5108]]
- QDA: FP=[102, 8774], FN=[8774, 102], CM=[[329, 8774], [102, 9720]]
- GaussianNB: FP=[107, 8802], FN=[8802, 107], CM=[[301, 8802], [107, 9715]]
- DecisionTree: FP=[160, 560], FN=[560, 160], CM=[[8543, 560], [160, 9662]]
- RandomForest: FP=[85, 634], FN=[634, 85], CM=[[8469, 634], [85, 9737]]
- GradientBoosting: FP=[95, 613], FN=[613, 95], CM=[[8490, 613], [95, 9727]]

#### Seletor: Pearson
- LDA: FP=[4671, 2291], FN=[2291, 4671], CM=[[6812, 2291], [4671, 5151]]
- QDA: FP=[3, 8881], FN=[8881, 3], CM=[[222, 8881], [3, 9819]]
- GaussianNB: FP=[108, 8771], FN=[8771, 108], CM=[[332, 8771], [108, 9714]]
- DecisionTree: FP=[122, 790], FN=[790, 122], CM=[[8313, 790], [122, 9700]]
- RandomForest: FP=[121, 801], FN=[801, 121], CM=[[8302, 801], [121, 9701]]
- GradientBoosting: FP=[125, 795], FN=[795, 125], CM=[[8308, 795], [125, 9697]]

#### Seletor: Fisher
- LDA: FP=[4671, 2291], FN=[2291, 4671], CM=[[6812, 2291], [4671, 5151]]
- QDA: FP=[3, 8881], FN=[8881, 3], CM=[[222, 8881], [3, 9819]]
- GaussianNB: FP=[108, 8771], FN=[8771, 108], CM=[[332, 8771], [108, 9714]]
- DecisionTree: FP=[122, 790], FN=[790, 122], CM=[[8313, 790], [122, 9700]]
- RandomForest: FP=[121, 801], FN=[801, 121], CM=[[8302, 801], [121, 9701]]
- GradientBoosting: FP=[125, 795], FN=[795, 125], CM=[[8308, 795], [125, 9697]]

#### Seletor: mRMR
- LDA: FP=[4663, 2290], FN=[2290, 4663], CM=[[6813, 2290], [4663, 5159]]
- QDA: FP=[101, 8775], FN=[8775, 101], CM=[[328, 8775], [101, 9721]]
- GaussianNB: FP=[107, 8802], FN=[8802, 107], CM=[[301, 8802], [107, 9715]]
- DecisionTree: FP=[160, 560], FN=[560, 160], CM=[[8543, 560], [160, 9662]]
- RandomForest: FP=[69, 661], FN=[661, 69], CM=[[8442, 661], [69, 9753]]
- GradientBoosting: FP=[95, 613], FN=[613, 95], CM=[[8490, 613], [95, 9727]]

#### Seletor: LassoCV
- LDA: FP=[4729, 2226], FN=[2226, 4729], CM=[[6877, 2226], [4729, 5093]]
- QDA: FP=[107, 8772], FN=[8772, 107], CM=[[331, 8772], [107, 9715]]
- GaussianNB: FP=[107, 8772], FN=[8772, 107], CM=[[331, 8772], [107, 9715]]
- DecisionTree: FP=[101, 761], FN=[761, 101], CM=[[8342, 761], [101, 9721]]
- RandomForest: FP=[101, 762], FN=[762, 101], CM=[[8341, 762], [101, 9721]]
- GradientBoosting: FP=[103, 760], FN=[760, 103], CM=[[8343, 760], [103, 9719]]

#### Seletor: LinearSVC_L1
- LDA: FP=[4663, 2290], FN=[2290, 4663], CM=[[6813, 2290], [4663, 5159]]
- QDA: FP=[100, 8775], FN=[8775, 100], CM=[[328, 8775], [100, 9722]]
- GaussianNB: FP=[107, 8802], FN=[8802, 107], CM=[[301, 8802], [107, 9715]]
- DecisionTree: FP=[160, 560], FN=[560, 160], CM=[[8543, 560], [160, 9662]]
- RandomForest: FP=[82, 641], FN=[641, 82], CM=[[8462, 641], [82, 9740]]
- GradientBoosting: FP=[95, 613], FN=[613, 95], CM=[[8490, 613], [95, 9727]]

#### Seletor: ExtraTrees
- LDA: FP=[4663, 2290], FN=[2290, 4663], CM=[[6813, 2290], [4663, 5159]]
- QDA: FP=[99, 8775], FN=[8775, 99], CM=[[328, 8775], [99, 9723]]
- GaussianNB: FP=[107, 8802], FN=[8802, 107], CM=[[301, 8802], [107, 9715]]
- DecisionTree: FP=[160, 560], FN=[560, 160], CM=[[8543, 560], [160, 9662]]
- RandomForest: FP=[68, 662], FN=[662, 68], CM=[[8441, 662], [68, 9754]]
- GradientBoosting: FP=[95, 613], FN=[613, 95], CM=[[8490, 613], [95, 9727]]

## 5. Artefatos Gerados
- reports/reports_refactored_median/baseline_results.csv
- reports/reports_refactored_median/baseline_timing_results.csv
- reports/reports_refactored_median/selection_results.csv
- reports/reports_refactored_median/selection_timing_results.csv
- reports/reports_refactored_median/selection_selector_timing_results.csv
- reports/reports_refactored_median/best_model_by_selector.csv
- reports/reports_refactored_median/ensemble_results.csv
- reports/reports_refactored_median/optuna_results.csv
- reports/reports_refactored_median/optuna_by_selector_results.csv
- reports/reports_refactored_median/best_optuna_model_by_selector.csv
- reports/reports_refactored_median/optuna_by_selector_comparison_cenario2_median.csv
- reports/reports_refactored_median/optuna_by_selector_best_params.json
- reports/reports_refactored_median/optuna_by_selector_confusion_matrices.json
- reports/reports_refactored_median/timing_results.csv
- reports/reports_refactored_median/timing_summary_by_stage.csv
- reports/reports_refactored_median/timing_summary_by_model.csv
- reports/reports_refactored_median/timing_summary_by_selector.csv
- reports/reports_refactored_median/final_results_all_models.csv
- reports/reports_refactored_median/confusion_matrices_by_selector.json
- reports/reports_refactored_median/best_confusion_matrix_by_selector.json
- reports/reports_refactored_median/optuna_confusion_matrices.json
- reports/reports_refactored_median/RELATORIO_FINAL.md
- models/models_optuna/*.pkl
- models/models_refactored/*.pkl
