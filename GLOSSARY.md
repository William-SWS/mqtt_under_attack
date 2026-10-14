# Glossário

Linguagem do domínio do projeto. Sem detalhes de implementação.

**Registro (record)**: uma linha do dataset, um pacote MQTT capturado, com rótulo `normal` ou `DoS`.

**Feature candidata**: atributo disponível antes da seleção. São 22: 20 colunas limpas do Wireshark mais
`publish_gap` e `connect_gap`.

**Gap de publish / gap de connect**: tempo desde a mensagem anterior do mesmo tipo (PUBLISH ou CONNECT)
no fluxo completo de tráfego, em ordem temporal. É 0 para a primeira ocorrência. Não depende do rótulo.

**Seletor**: estratégia que escolhe um subconjunto de features candidatas usando apenas o treino.
Os seis são LowVariance, ANOVA, MutualInformation, Lasso, LinearSVC e ExtraTrees.

**Conjunto de features**: lista de features escolhida por um seletor.

**Modelo**: um dos sete classificadores comparados: LDA, QDA, GaussianNB, DecisionTree, RandomForest,
GradientBoosting e SVM.

**Configuração (seletor–modelo)**: um par seletor × modelo. São 42 no resultado principal.

**Baseline**: avaliação dos sete modelos com hiperparâmetros default sobre as 22 features candidatas,
sem seleção. Serve de referência.

**Pipeline de inferência**: o objeto único que recebe features brutas e devolve predição e
probabilidades, incorporando imputação, escalonamento e calibração quando o modelo precisa.

**Features brutas**: valores como saem da limpeza, antes de imputação e escalonamento.

**Partição de treino / de teste**: divisão estratificada 80/20 com seed 42 (75.700 e 18.925 registros).
O teste só é usado na avaliação final.

**Vazamento (leakage)**: informação do teste ou do rótulo influenciando o treino ou as features.

**Calibração**: ajuste das probabilidades de um modelo para que reflitam a frequência real de acerto.

**Run**: uma execução completa do esquema de treino sob um `run_name`, com todos os seus artefatos.

**Fronteira de Pareto**: conjunto de configurações que não são dominadas ao mesmo tempo em qualidade
(média de accuracy e F1 weighted) e custo de inferência por registro.
