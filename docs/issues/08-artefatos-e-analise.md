# 08: Artefatos do run e análise final

**What to build:** gravar tudo o que um run produz numa pasta própria e fechar o notebook com a análise: melhor configuração por seletor, heatmaps de métricas, matrizes de confusão e comparação com o baseline. O leitor roda o run `paper_protocol` completo.

**Blocked by:** 07

**Status:** ready-for-agent

- [ ] A pasta do run contém os Pipelines `.pkl`, um CSV de teste bruto por configuração, as tabelas de baseline e de tuning, os melhores parâmetros, as features por seletor, as matrizes de confusão, os tempos e o manifesto do run.
- [ ] Cada `.pkl` carrega e faz `predict_proba` direto sobre o CSV bruto correspondente, sem passos extras (teste).
- [ ] Nada é escrito em `api_inference/` nem sobrescreve artefatos antigos.
- [ ] Rodar de novo com o mesmo `run_name` sobrescreve a pasta; outro nome cria outra.
- [ ] O notebook mostra o melhor modelo por seletor, heatmaps das métricas, matrizes de confusão e o delta contra o baseline.
- [ ] O leitor confere que o conjunto LowVariance tem as mesmas 12 features dos notebooks antigos.
