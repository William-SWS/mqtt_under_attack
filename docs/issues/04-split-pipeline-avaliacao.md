# 04: Split, Pipeline de inferência e avaliação de um modelo

**What to build:** o caminho ponta a ponta com um único modelo: split estratificado, construção do Pipeline (imputer, scaler quando exigido, modelo), treino e avaliação com todas as métricas do paper. O leitor treina uma árvore de decisão e vê a tabela de métricas e a matriz de confusão no notebook.

**Blocked by:** 03

**Status:** ready-for-agent

- [ ] Split 80/20 estratificado, seed 42, com 75.700 linhas de treino e 18.925 de teste; nenhum ajuste usa o teste.
- [ ] Um Pipeline construído para um modelo aceita features brutas (com NaN) e devolve predição e probabilidades.
- [ ] A avaliação devolve accuracy, precision weighted, F1 weighted, F1 macro, log loss, FP/FN por classe, matriz de confusão e tempos de fit/predict/proba.
- [ ] Testes cobrem o contrato do Pipeline (probabilidades somam 1; entrada com NaN) e a avaliação em dados sintéticos.
- [ ] O notebook exibe as métricas e a matriz de confusão do modelo.
- [ ] ADR "contrato `Pipeline` único" criado.
