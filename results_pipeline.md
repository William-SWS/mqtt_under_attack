# Relatório de Resultados: Pipeline DoS (Estratégias de Imputação)

Este relatório consolida a análise técnica e o impacto metrológico entre as três abordagens tomadas para inferir os Missing Values (Valores Ausentes) durante o pipeline de detecção de ataques DoS em pacotes MQTT.

## 1. Abordagens Avaliadas

Foram avaliados 3 fluxos de execução:

| Cenário | Notebook | Estratégia de Valores Ausentes | Risco Identificado |
|---|---|---|---|
| **Original (Baseline)** | `01_dos_complete_pipeline.ipynb` | `fillna(0)` aplicado **globalmente** antes do `train_test_split`. | "Design Leakage". Impede substituição segura para métodos complexos como média/mediana, pois quebra rigor da etapa de Teste separada. |
| **Cenário 1 (Constant)** | `02_dos_complete_pipeline.ipynb` | `SimpleImputer(strategy='constant', fill_value=0)` localmente e pós-split. | Seguro metodologicamente ("Scikit-Learn Standard"). Matematicamente igual ao original para matrizes. |
| **Cenário 2 (Median)** | `03_dos_complete_pipeline.ipynb` | `SimpleImputer(strategy='median')` localmente e pós-split. | Preenche vazios temporais / pacotes contínuos interpolando via "Mediana" da população de Treino. |

---

## 2. Visão Geral de Performance e Redução de Eficiência

A sua análise visual das matrizes está **correta e metodologicamente confirmada**. O emprego da Mediana para este dataset provocou uma degradação severa nas camadas de Inteligência Artificial, gerando instabilidade na classificação, principalmente prejudicado em algoritmos Lineares e Probabilísticos, mas também com impacto notório nas árvores.

* **Top F1-Score Cenário 1 (Constant):** `0.9754` (DecisionTree via Optuna)
* **Top F1-Score Baseline Original:** `0.9754` (DecisionTree via Optuna)
* **Top F1-Score Cenário 2 (Median):** `0.9642` (RandomForest via Optuna) **(Queda de ~1.1%)**

### A Queda Catastrófica de Algoritmos Discriminantes na Mediana
No baseline, LDA e QDA apresentavam um F1 em torno de `0.92`. Ao trocar o Zero por Mediana:
* LDA caiu para `0.63` de F1-Score.
* QDA despencou para absurdos `0.38` de F1-Score.
* A Matriz do QDA indicou que ele "surtou", prevendo maciçamente falsos positivos (classificando a classe 0 como classe 1).

> [!CAUTION]
> **Por que a Mediana piorou o sistema?**
> Ao calcular gaps de mensagens (como features derivadas `publish_gap`), os pacotes normais do DoS podem possuir muitos zeros caso não sejam o tipo de pacote medido. Preencher os dados faltantes de Wireshark com a *mediana de atraso temporal* força pacotes instantâneos a parecerem "pacotes rotineiros atrasados", destruindo o threshold de separação entre tráfego normal e tráfego que bombardeia e abusa da rede de maneira atípica. Como os modelos Lineares confiam muito no threshold de centroides da distribuição, a nova mediana corrompe a fronteira de decisão deles completamente. O valor de Timeout 0 faz absoluto sentido físico para pacotes que "nunca chegaram" neste escopo de rede em vez de fingirmos que eles "chegaram com tempo médio".

---

## 3. Comprovação pelas Matrizes de Confusão

*Note: O Cenário 1 (Constant) possui resultados virtualmente idênticos ao Pipeline Original. A adoção da Constante apenas formalizou o pipeline contra Leakage.*

### 🟩 Padrão Positivo: Cenário 1 (Zero Isolado)
Note o sólido contraste diagonal e as baixíssimas taxas cruzadas de GradientBoosting e DecisionTree, com o LDA minimamente estável.

![Matrizes Constant](/home/william/Projetos/mqtt_under_attack/reports/reports_refactored_constant/optuna_confusion_matrices.png)

### 🟥 Degradação: Cenário 2 (Mediana)
Note o enfraquecimento diagonal explícito de LDA, QDA e GaussianNB a pontos críticos. Os métodos de árvore sofreram em menor proporção pois resistem mais a ruídos em splits numéricos, contudo, também geraram mais Falsos Positivos sob "Mediana" do que sob a "Constante = 0".

![Matrizes Median](/home/william/Projetos/mqtt_under_attack/reports/reports_refactored_median/optuna_confusion_matrices.png)

---

## 4. Evoluções da Acurácia de Base e Impacto da Decisão

### Gráfico Comparativo: Acurácia Baseline Constant (Eixo 0.90+)
O modelo clássico atinge um baseline homogêneo perto dos grandes marcos de viabilidade comercial e IoT. 

![Acurácia Constant](/home/william/Projetos/mqtt_under_attack/reports/reports_refactored_constant/baseline_comparison.png)

### Gráfico Comparativo: Acurácia Baseline Median
Veja como LDA, QDA e NB cederam na barra de Log Loss chegando quase aos limiares de acerto "Random" em decorrência da Mediana descaracterizando os pacotes:

![Acurácia Median](/home/william/Projetos/mqtt_under_attack/reports/reports_refactored_median/baseline_comparison.png)

---

## 5. Conclusão Final

- A abordagem de Preenchimento Estático Semântico de Ausência de Comunicação (`Constant=0`) refletida no Original e no cenário refatorado `02_dos_complete_pipeline.ipynb` **é a ideal**.
-  A introdução de SimpleImputer no código corrigiu a integridade do código (tornando-o protegido de Data Leakage futuro) sem alterar os benefícios matemáticos prévios.
- O cenário 2 de `Mediana` foi testado por rigor e serve como prova acadêmica fundamental de que preencher métricas de tráfego de rede (Network Packets / IoT) usando preenchimento estatístico (que é muito comum em tabelas convencionais de Marketing e Vendas) é um malefício à identificação de padrões intrusivos. Em redes, o valor Missing e o Zero informam um fenômeno físico real na linha de transmissão.

> [!IMPORTANT]
> **Veredito para Produção (Raspberry Pi/IoT):** Recomenda-se prosseguir na implantação ou modelagem final empacotando os artefatos provenientes exclusivamente do **Cenário 1 (`models_refactored_strategy_constant`)** com a estratégia focada em Árvore (RandomForest, ExtraTrees ou LightGBM/GradientBoosting).
