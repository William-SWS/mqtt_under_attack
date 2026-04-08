# Pipeline Refatorado para Classificacao de Ataques DoS em MQTT

## Visao Geral do Pipeline

O pipeline refatorado foi estruturado para manter rastreabilidade completa entre dados de entrada, transformacoes de features, treinamento de modelos, selecao de variaveis, estrategias de ensemble, otimizacao de hiperparametros e consolidacao final de resultados. O objetivo principal da refatoracao foi tornar o fluxo reproduzivel, padronizado em metricas e robusto para analise de erros de classificacao. Toda avaliacao foi centralizada em quatro metricas obrigatorias: acuracia, precisao, F1-score e log-loss.

A arquitetura operacional segue uma sequencia deterministica: leitura do dataset bruto DoS, limpeza de atributos de baixo valor analitico, engenharia temporal de gaps MQTT, particionamento treino-teste, normalizacao controlada para modelos lineares, execucao de baseline, selecao de features por multiplos seletores, treinamento por subconjunto selecionado, ensemble probabilistico, otimizacao por Optuna e agregacao final em artefatos tabulares, visuais e estruturados em JSON.

## Etapas de Refatoracao

A primeira etapa de refatoracao padronizou o conjunto de modelos avaliados ao longo de todo o notebook, eliminando divergencias entre blocos de baseline, selecao, ensemble e otimizacao. O pipeline passou a trabalhar de forma consistente com seis algoritmos: Linear Discriminant Analysis, Quadratic Discriminant Analysis, Gaussian Naive Bayes, Decision Tree, Random Forest e Gradient Boosting. Essa unificacao removeu variacao metodologica entre secoes e tornou comparacoes interetapas estatisticamente coerentes.

A segunda etapa consolidou a funcao de avaliacao para garantir que qualquer experimento reutilize o mesmo protocolo de scoring e diagnostico de erro. Isso inclui calculo das quatro metricas obrigatorias e geracao de matriz de confusao por experimento, com derivacao de falsos positivos e falsos negativos por classe. Essa mudanca foi central para manter simetria de analise entre baseline, selecao de features e modelos otimizados.

A terceira etapa introduziu controle explicito de escalonamento por tipo de modelo. Apenas LDA e QDA passam por versoes normalizadas dos atributos, enquanto modelos baseados em arvores e Naive Bayes operam com representacao nao escalada. Com isso, o pipeline passou a refletir melhor as hipoteses numericas de cada estimador sem contaminacao metodologica entre algoritmos.

A quarta etapa da refatoracao reorganizou o bloco de selecao de features para produzir duas camadas de auditoria: matrizes completas para cada combinacao seletor-modelo e uma matriz de referencia para o melhor modelo de cada seletor. Essa estrategia permitiu avaliar nao apenas desempenho agregado, mas tambem o padrao de erros por configuracao de variaveis.

A quinta etapa transformou o ensemble em um esquema probabilistico consistente com as saidas de todos os modelos base. Foram mantidas duas estrategias: Soft Voting ponderado pelo F1 dos modelos individuais e Averaging por media simples das probabilidades. Ambas as estrategias passaram a ser avaliadas com o mesmo protocolo de metricas e com matriz de confusao correspondente.

A sexta etapa reforcou a robustez do Optuna com espacos de busca controlados por modelo, tratamento de falhas numericas e budget de trials por algoritmo. Essa alteracao foi necessaria para reduzir interrupcoes em otimizacoes longas e manter estabilidade computacional durante o processo de validacao cruzada.

## Transformacoes Aplicadas

No pre-processamento, o pipeline removeu metadados e campos de baixo sinal provenientes da captura de rede, reduzindo ruido estrutural antes da etapa de modelagem. Em seguida, foram criadas as features temporais `publish_gap` e `connect_gap`, que adicionam informacao de dinamica de trafego MQTT e aumentam separabilidade entre padroes de comportamento benigno e malicioso.

Na camada de selecao de features, foram aplicados sete seletores complementares: LowVariance, Pearson, Fisher, mRMR, LassoCV, LinearSVC_L1 e ExtraTrees. O resultado foi consolidado em matrizes de consenso e avaliado por desempenho de classificacao em cada subconjunto, preservando comparabilidade entre modelos com base no mesmo conjunto de metricas.

Na camada de avaliacao final, os resultados de baseline, selecao, ensemble e Optuna foram unificados em um ranking global. O melhor desempenho registrado no artefato consolidado foi do DecisionTree otimizado por Optuna, com acuracia e F1 acima de 0.975 no conjunto de teste, mantendo precisao elevada e log-loss baixo.

## Artefatos Tecnicos Gerados

A refatoracao foi acompanhada por geracao de artefatos em formatos complementares para analise, auditoria e reproducao experimental. Os arquivos tabulares concentram desempenho por etapa, os JSONs guardam matrizes de confusao e os PNGs registram comparacoes visuais do comportamento dos modelos.

| Artefato | Tipo | Papel no Pipeline |
|---|---|---|
| `reports_refactored/baseline_results.csv` | CSV | Resultado baseline dos seis modelos com metricas obrigatorias |
| `reports_refactored/selection_results.csv` | CSV | Desempenho por seletor e modelo |
| `reports_refactored/ensemble_results.csv` | CSV | Comparacao entre Soft Voting e Averaging |
| `reports_refactored/optuna_results.csv` | CSV | Resultado em teste dos modelos otimizados |
| `reports_refactored/final_results_all_models.csv` | CSV | Consolidacao final das etapas |
| `reports_refactored/confusion_matrices_by_selector.json` | JSON | Matrizes por seletor-modelo |
| `reports_refactored/best_confusion_matrix_by_selector.json` | JSON | Melhor matriz por seletor |
| `reports_refactored/optuna_confusion_matrices.json` | JSON | Matrizes dos modelos otimizados |
| `reports_refactored/*.png` | Imagens | Evidencias visuais de desempenho e distribuicoes |

## Reprodutibilidade e Operacao

A reproducao do fluxo depende da execucao sequencial do notebook refatorado, com especial atencao ao bloco de otimizacao por Optuna, que e o trecho mais custoso computacionalmente. O diretório `reports_refactored` concentra os produtos finais e deve ser mantido como referencia de auditoria para comparacao entre execucoes. Para garantir consistencia entre versoes, recomenda-se preservar o mesmo ambiente Python, mesma seed aleatoria e mesma ordem de execucao das celulas.
