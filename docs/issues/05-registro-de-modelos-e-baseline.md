# 05: Registro dos sete modelos e baseline

**What to build:** os sete modelos descritos num registro único (fábrica, espaço de busca, exige escala, exige calibração) e a tabela de baseline: todos com hiperparâmetros default nas 22 features. O SVM entra aqui como mais um modelo, sem tratamento à parte.

**Blocked by:** 04

**Status:** ready-for-agent

- [ ] O registro contém LDA, QDA, GaussianNB, DecisionTree, RandomForest, GradientBoosting e SVM.
- [ ] LDA, QDA e SVM recebem scaler; QDA e GaussianNB recebem calibração sigmoide com `ensemble=False`.
- [ ] Construir o Pipeline de qualquer modelo a partir do registro funciona com a mesma função.
- [ ] O baseline roda os sete modelos e produz a tabela ordenada por F1 weighted, com tempos.
- [ ] Teste confirma que um QDA calibrado tem um único estimador base (não três).
- [ ] O notebook mostra a tabela e o gráfico comparativo do baseline.
- [ ] ADR "calibração com `ensemble=False`" criado.
