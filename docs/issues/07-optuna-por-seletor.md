# 07: Optuna por seletor — grid de 6 × 7

**What to build:** o resultado principal: para cada par (seletor, modelo), um estudo Optuna com o protocolo do paper, seguido do fit final no treino completo e da avaliação no teste. Inclui a subamostra de tuning para o SVM e um smoke test do grid inteiro.

**Blocked by:** 05, 06

**Status:** ready-for-agent

- [ ] Cada estudo usa TPE seed 42, `StratifiedKFold` com 5 folds, objetivo F1 macro; trials e folds vêm da configuração.
- [ ] A subamostra estratificada de tuning é aplicada quando configurada (SVM = 15000 linhas) e o fit final usa o treino completo.
- [ ] Trials que falham são podados; uma configuração sem trial válido é registrada como falha sem abortar o grid.
- [ ] O grid devolve a tabela de resultados (42 linhas no run completo), os melhores parâmetros e os Pipelines ajustados.
- [ ] Smoke test: grid em amostra pequena (1–2 trials, 2 folds, poucos modelos e seletores) conclui e devolve a estrutura esperada.
- [ ] O notebook roda o grid com `run_name='smoke'` e exibe a tabela e os históricos de otimização.
