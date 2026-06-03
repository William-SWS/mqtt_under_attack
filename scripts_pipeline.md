# Documentação do Pipeline de Classificação (MQTT DoS)

Este documento explica a estrutura e o funcionamento de cada script criado durante a refatoração do pipeline de Machine Learning focado em detecção de ataques DoS em redes MQTT. A arquitetura foi dividida em módulos para facilitar a manutenção, clareza e deploy.

## Ordem de Execução e Arquitetura

A execução do treinamento completo do pipeline segue um fluxo linear unidirecional e centralizado:

1. `data_loader.py` (Carrega e extrai as features)
2. `train.py` (Utiliza os dados processados para otimizar e treinar os modelos)
3. `evaluate.py` (Executa métricas de performance e valida as inferências)

Você **não precisa executar cada script individualmente**. O arquivo na raiz `main.py` atua como o **Orquestrador**, importando as funções na ordem correta.

Para rodar todo o pipeline de ponta a ponta, basta executar na raiz do projeto:
```bash
python main.py
```

---

## Detalhamento dos Scripts

### 1. `main.py` (O Orquestrador)
**Objetivo:** Integrar os três scripts do pipeline e fornecer um fluxo único de execução limpa.
**Como funciona:**
- Inicializa validando a existência do dataset bruto no diretório `data/raw/`.
- Repassa os dados para o `data_loader.py`.
- Define uma lista de algoritmos de Machine Learning (`RandomForest`, `DecisionTree`, `GaussianNB`, `LDA`, `QDA`, `GradientBoosting`).
- Em um laço de repetição (`for`), invoca primeiramente o `train.py` (passando a otimização assíncrona do `Optuna`) e depois o `evaluate.py` para cada um destes modelos, avaliando em tempo real os perfis.
- Por fim, aciona a função de gerar relatórios em lote, salvando as saídas em disco de forma automatizada e encerrando o pipe.

### 2. `scripts/data_loader.py` (Ingestão e Preparo)
**Objetivo:** Carregar os dados de tráfego, tratar o desbalanceamento, remover ruídos de captura do Wireshark e aplicar normalização tabular.
**Principais Funções:**
- `calculate_gaps(df)`: **A Função Crítica de Feature Engineering.** Reconstrói em série temporal os gaps de latência entre mensagens do tipo `CONNECT` e `PUBLISH`, extraindo do Payload o principal vetor temporal que denuncia tentativas de bloqueio exaustivo do protocolo MQTT.
- `clean_data(df)`: Exclui estaticamente cerca de 45 colunas irrelevantes deixadas puramente pela infraestrutura PCAP (como endereços físicos MAC, checksums, inteiros de interface de rede e hashes do Wireshark) que de outro modo confundiriam a predição.
- `split_and_scale(df)`: Fragmenta os dados aleatoriamente em conjuntos de Treino (80%) Teste (20%). Processa as amostras quantitativas em distribuições de curva normal (Z-Score) através da classe unificada de `StandardScaler`.
- `load_and_preprocess(raw_data_path)`: Função "Export" - é ela que é consumida pela `main.py` orquestradora para amarrar os passos do loader e devolver as variáveis finais prontas: `X_train`, `X_test`, `y_train` e `y_test`.

### 3. `scripts/train.py` (Treinamento e Otimização Automática)
**Objetivo:** Determinar a melhor combinação matemática (*Hyperparameter Tuning*) de forma autônoma (substituindo a dependência manual do Notebook) e salvar o objeto treinado em disco.
**Principais Funções:**
- `build_model_from_trial(model_name, trial)`: Mapeia e injeta as regras empíricas no motor do `Optuna`, definindo de qual minímo até qual máximo a IA vai simular pesos por tipo de método (ex: "Procure max_depths de 2 a 20" em Árvores de features para prevenir *overfitting* indesejado).
- `objective_factory(...)`: Empacota os estimadores e lida sensivelmente com o Cross Validation de 3 dobras (KFolds), mitigando o perigo de *Data Leakage*. Detecta modelos sensíveis a dispersão (como NaiveBayes e LDA) protegendo-os isoladamente com Pipelinagens próprias.
- `train_and_optimize(...)`: Inicia a "caça" às variáveis com redes bayesianas de probabilidade. Quando o melhor cenário é reportado, treina o formato preditivo final e aciona o sub-processo que serializa (com a biblioteca `joblib`) o classificador vencedor para dentro do diretório gerado `./models_optimized/`.

### 4. `scripts/evaluate.py` (Validação e Exportação de Métricas)
**Objetivo:** Garantir a taxa de acerto do modelo por bateria cruzada e documentar fisicamente (sem interface web/interativa do Jupyter) seu status produtivo.
**Principais Funções:**
- `evaluate_model(...)`: Roda intermitentemente predições de log-loss, medidores binários como Macro-F1 (vital dada a detecção de anomalia), limiares de acuidade (Accuracy), escoragens precisas contra tráfegos limpos e constroi e extrai perfeitamente as Matrizes de Confusão para mapear incidências de Falsos Positivos.
- `generate_report(results_list)`: Após o bloco da `main.py` transacionar em cadeia as listas consolidadas, essa chamada cria um DataFrame geral e cospe imediatamente gráficos em imagem renderizadas `f1_scores.png` e constroi a planilha indexada `final_results.csv`, direcionando pro arquivo persistente `./reports_optimized/`.

### Extra: `scripts/pi_inference.py`
**Objetivo:** Script extra acoplado unicamente à infraestrutura **Edge IoT**. Explicado com maestria no guia `raspberry_deploy.md`, esse script queima o pipeline e não interage com ele globalmente; ao invés disso, usa o `paho-mqtt` importado conectando-se a um broker live em ambiente hostil embarcado, escuta pacotes e despeja neles os *joblibs* gerados na Otimização descrita para avaliar latências.
