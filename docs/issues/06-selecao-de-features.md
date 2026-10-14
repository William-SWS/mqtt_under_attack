# 06: Seleção de features com seis seletores

**What to build:** os seis seletores do paper aplicados ao treino, devolvendo a lista de features de cada um, mais a matriz de consenso para análise. O notebook mostra o que cada seletor escolheu e onde eles concordam.

**Blocked by:** 04

**Status:** ready-for-agent

- [ ] Existem LowVariance, ANOVA, MutualInformation, Lasso, LinearSVC e ExtraTrees (`ExtraTreesClassifier`).
- [ ] LowVariance usa threshold 0.01 sem truncar e, no dataset real, devolve 12 features; os demais devolvem 15.
- [ ] Lasso e LinearSVC operam sobre dados escalonados internamente; o resultado não depende da escala original das colunas (teste).
- [ ] A seleção usa apenas o treino (teste confirma que mudar o teste não altera o resultado).
- [ ] A matriz de consenso conta quantos seletores escolheram cada feature.
- [ ] O notebook exibe as features por seletor e o heatmap de consenso.
