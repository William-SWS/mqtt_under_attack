# 0000: Esquema de treino unificado — detecção de DoS em MQTT

## Problem Statement

Quem mantém o projeto tem hoje dois notebooks que treinam modelos de forma diferente: `04_pipeline.ipynb`
(seis modelos × sete seletores) e `04_svm.ipynb` (SVM só em LowVariance). Eles divergem no contrato do
modelo salvo (LDA/QDA esperam dados já escalonados, o SVM embute o scaler), no protocolo de tuning
(CV de 3 folds com F1 weighted contra hold-out) e nas métricas. Os nomes dos seletores não correspondem
ao que o código faz (Pearson e Fisher são o mesmo cálculo; "mRMR" é informação mútua; "ExtraTrees" é
um RandomForest) e o protocolo do código não é o descrito no paper WPMC. Há dois vazamentos: os gaps são
calculados agrupando pelo rótulo, e os pesos do Smart Voting são otimizados no teste. O repositório
mistura dezenas de notebooks e artefatos antigos, e os notebooks grandes são difíceis de ler.

## Solution

Um único esquema de treino, escrito como pacote Python pequeno e testado, mais um notebook de narrativa.
Sete modelos passam pelo mesmo caminho: dados limpos → gaps sem vazamento → split → baseline →
seleção com seis seletores → Optuna por seletor (protocolo do paper) → avaliação → artefatos. Cada modelo
sai como um Pipeline de inferência que aceita features brutas. O projeto é entregue como curso MkDocs, uma
aula por ticket, e o usuário digita o código seguindo as aulas. Todas as decisões ficam em
`docs/decisions.md`.

## User Stories

1. Como pesquisador, quero que os sete modelos sejam treinados e avaliados com o mesmo protocolo, para que a comparação entre eles seja justa.
2. Como pesquisador, quero que o SVM use as mesmas features e o mesmo split dos outros modelos, para que não haja dúvida sobre qual conjunto de features cada um viu.
3. Como pesquisador, quero que os gaps de publish e connect não dependam do rótulo, para que o modelo não receba o alvo como feature.
4. Como pesquisador, quero que a seleção de features, a imputação e o escalonamento sejam ajustados só no treino, para evitar vazamento.
5. Como pesquisador, quero seis seletores com nomes que correspondam ao que fazem, para descrever o método no artigo sem ressalvas.
6. Como pesquisador, quero o protocolo de Optuna do paper (TPE, 30 trials, 5 folds estratificados, F1 macro), para que o código reproduza o texto.
7. Como pesquisador, quero reduzir trials e folds por configuração, para rodar uma versão rápida (smoke) em minutos.
8. Como pesquisador, quero ajustar o SVM numa subamostra durante o tuning e treinar o final no treino completo, para que o grid caiba num tempo razoável.
9. Como pesquisador, quero accuracy, precision weighted, F1 weighted, F1 macro e log loss para cada configuração, para usar as mesmas métricas do paper.
10. Como pesquisador, quero FP/FN por classe e matriz de confusão por configuração, para analisar os erros.
11. Como pesquisador, quero tempos de fit, predict e predict_proba por configuração, para discutir custo computacional.
12. Como pesquisador, quero uma tabela de baseline com os sete modelos nas 22 features, para medir o ganho da seleção e do tuning.
13. Como pesquisador, quero um resultado por seletor e modelo (42 configurações), para montar a análise de Pareto depois.
14. Como pesquisador, quero ver quais features cada seletor escolheu e onde eles concordam, para interpretar os resultados.
15. Como pesquisador, quero que QDA e GaussianNB tenham probabilidades calibradas sem triplicar o custo de inferência, para que o log loss seja justo e o modelo caiba no Raspberry Pi.
16. Como engenheiro de inferência, quero que cada modelo salvo seja um Pipeline que aceita features brutas, para que a API não precise saber qual modelo exige escalonamento.
17. Como engenheiro de inferência, quero um CSV de teste bruto por configuração, para validar o modelo salvo direto contra ele.
18. Como engenheiro de inferência, quero que os artefatos novos fiquem em uma pasta por run, para não sobrescrever os que a API usa hoje.
19. Como mantenedor, quero um manifesto do run com configuração, features por seletor e versões das bibliotecas, para reproduzir qualquer resultado.
20. Como mantenedor, quero rodar com um `run_name` e saber que o mesmo nome sobrescreve, para controlar o que fica no disco.
21. Como estudante do projeto, quero um notebook que conte a história do pipeline em seções curtas, para entender sem ler código de implementação.
22. Como estudante do projeto, quero ver a distribuição dos gaps por classe no notebook, para entender por que essas features discriminam.
23. Como estudante do projeto, quero uma aula por etapa com o código para digitar, para aprender construindo.
24. Como estudante do projeto, quero testes que falhem quando o código está errado e passem quando está certo, para ter feedback imediato em cada aula.
25. Como mantenedor, quero um teste que garanta que gaps não usam o rótulo, para que o vazamento não volte.
26. Como mantenedor, quero um teste que garanta que todo Pipeline aceita as features brutas do seletor e devolve probabilidades válidas, para travar o contrato.
27. Como mantenedor, quero um smoke test do grid completo numa amostra pequena, para detectar quebras de integração antes de uma rodada longa.
28. Como mantenedor, quero uma lista explícita do que pode ser apagado depois, para limpar o repositório sem medo.
29. Como mantenedor, quero que `api_inference/`, `scripts/` e os notebooks e artefatos antigos continuem intactos, para que nada em produção quebre durante a refatoração.
30. Como mantenedor, quero um `AGENTS.md` enxuto e correto, para que qualquer agente de código trabalhe no repo sem se perder.

## Implementation Decisions

Vocabulário conforme `GLOSSARY.md`; decisões numeradas em `docs/decisions.md` (D1–D25).

- **Configuração do run.** Um objeto de configuração central reúne: nome do run, seed (42), fração de teste (0.2), número de trials (30), folds (5), top-k dos seletores (15), subamostra de tuning por modelo (SVM = 15000) e as listas de modelos e seletores a executar. Trocar para uma rodada rápida é só construir outra configuração.
- **Dados.** Carregar o CSV bruto de DoS, remover as 46 colunas inúteis (identificadores, timestamps absolutos, IPs/MACs, portas, payloads, metadados do Wireshark) e manter 20 colunas mais o rótulo. A lista de colunas removidas vem do `04_pipeline.ipynb`.
- **Gaps.** Ordenar o fluxo por tempo e, para cada tipo de mensagem (CONNECT=1, PUBLISH=3), calcular a diferença para a ocorrência anterior no fluxo inteiro; a primeira ocorrência e as demais mensagens ficam 0. Não se agrupa por rótulo. A ordem original das linhas é preservada na saída.
- **Split.** Estratificado, 80/20, seed 42, antes de qualquer ajuste de imputação, escala ou seleção.
- **Registro de modelos.** Cada modelo é descrito por: nome, fábrica com hiperparâmetros default, função que declara o espaço de busca do Optuna, se exige escalonamento, se exige calibração. LDA, QDA e SVM exigem escalonamento; QDA e GaussianNB exigem calibração sigmoide com `ensemble=False`. Os espaços de busca de LDA, QDA, GaussianNB, DecisionTree, RandomForest e GradientBoosting vêm do `04_pipeline.ipynb`; o do SVM (C, gamma, kernel rbf) vem do `04_svm.ipynb`.
- **Pipeline de inferência.** Construído a partir de um modelo e hiperparâmetros: imputer constante 0, scaler quando exigido, modelo (envolvido no calibrador quando exigido). O SVM treina com `probability=True` apenas no fit final.
- **Seleção.** Seis seletores ajustados no treino imputado. Lasso e LinearSVC operam sobre dados escalonados internamente. LowVariance (threshold 0.01) não trunca; os demais devolvem as 15 melhores features. Uma função devolve o mapeamento seletor → lista de features, e outra a matriz de consenso (quantos seletores escolheram cada feature) apenas para análise.
- **Tuning.** Um estudo Optuna por (seletor, modelo): TPE seed 42, `StratifiedKFold` com 5 folds embaralhados, objetivo F1 macro, scaler dentro de cada fold via Pipeline, subamostra estratificada quando configurada. Trials que falham são podados, e o grid registra a falha em vez de abortar.
- **Avaliação.** Uma função recebe um Pipeline ajustado e o teste e devolve as cinco métricas, FP/FN por classe, matriz de confusão e os três tempos. É usada no baseline e no resultado final.
- **Artefatos.** Por run: Pipelines `.pkl`, CSVs de teste brutos, tabelas de baseline e de tuning, melhores parâmetros, features por seletor, matrizes de confusão, tempos, gráficos e um manifesto. Tudo sob a pasta do run; nada em `api_inference/`.
- **Notebook.** Seções: configuração, dados, gaps, split, baseline, seleção, tuning, resultados, salvar. Só narrativa, chamadas ao pacote e gráficos. Sem funções de pipeline definidas em células.
- **Reaproveitamento.** Lista de colunas, espaços de busca e a lógica de avaliação são transpostos dos notebooks atuais como conteúdo das aulas; não há import dos notebooks antigos.

## Testing Decisions

- Um bom teste verifica comportamento externo (entradas e saídas de cada função pública), não detalhes internos.
- Seam principal: a função que roda o grid sobre um conjunto de dados e devolve a tabela de resultados mais os Pipelines. O smoke test exercita esse seam numa amostra pequena (poucas centenas de linhas, 1–2 trials, 2 folds, subconjunto de modelos e seletores).
- Seams menores, por serem a fonte dos vazamentos corrigidos: gaps (o resultado não muda se o rótulo for embaralhado), split + imputação (nenhum ajuste usa o teste), contrato do Pipeline (aceita features brutas do seletor e devolve probabilidades que somam 1) e seleção (usa só o treino).
- Dados sintéticos pequenos construídos no próprio teste; sem depender do CSV real, exceto uma verificação opcional marcada.
- Não há prior art de testes no repositório; as aulas introduzem pytest do zero.

## Out of Scope

- `api_inference/`: adaptar a API, exportar modelos para ela e regenerar stress tests ficam para a fase seguinte.
- CLI, ensemble (Averaging, Hard e Soft Voting), Optuna global por consenso, seleção "com params default".
- Reexecutar os experimentos no Raspberry Pi, refazer `paretto/` e `scripts/plot_*` para o novo formato de relatório.
- Apagar qualquer arquivo. Lista de limpeza futura, para o usuário decidir:
  - `notebooks/` (antigos), `notebooks_refactored/` exceto `04_pipeline.ipynb` e `04_svm.ipynb`, e seu `run_pipeline.py`
  - `models_optimized/`, `data_refactored/`, CSVs legados em `data/processed/`
  - `docs/docs/`, `docs/mkdocs.yml`, `docs/model_training*.md`, `docs/pipeline_refactored.md`
  - `results_pipeline.md`, `results_new_pipeline.md`, `scripts_pipeline.md`, `stress_test_results.png`
  - PDFs da raiz, `raspberry_deploy.md`, `environment.yml`, `references/`, `assets/`, `obsidian_notes/`
  - Os artefatos de `04_pipeline`/`04_svm` (`models/models_ensemble_v2/`, `reports_refactored/`) até a API migrar.
  - Mantidos: `api_inference/`, `scripts/` (e `main.py`, que os orquestra), `paretto/`, `data/raw/`.

## Further Notes

- As métricas novas não serão comparáveis 1:1 com o artigo por causa do ajuste dos gaps e dos seletores.
- Adotar `Pipeline` único exige, na fase da API, regenerar os modelos antigos; os `.pkl` atuais de LDA/QDA esperam dados escalonados.
- O `CLAUDE.md` global do usuário orienta a usar grafos de código; o repositório não tem código novo ainda, então esta fase não precisou deles.
