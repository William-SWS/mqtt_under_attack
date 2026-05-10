# Resultados da Refatoração do Pipeline e Modelos para Deploy (Edge Computing)

Este documento sumariza a performance dos modelos antes e após a otimização com Optuna, com foco direto na viabilidade para deploy no Raspberry Pi (recursos restritos de CPU, RAM e processamento rápido de rede).

---

## 1. Ranking de Modelos no Novo Pipeline

### 1.1. Ranking dos Modelos em Baseline (Antes da Otimização)
Estes são os valores de performance bruta dos modelos (usando as features de consenso, sem Optuna):

| Posição | Modelo | Acurácia | Precisão | F1-Score | Log Loss | Tempo Total (Treino) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1º** | GradientBoosting | 0.9750 | 0.9754 | 0.9750 | 0.0735 | ~5.48 s |
| **2º** | DecisionTree | 0.9743 | 0.9745 | 0.9743 | 0.1358 | ~0.10 s |
| **3º** | RandomForest | 0.9740 | 0.9746 | 0.9740 | 0.0724 | ~1.84 s |
| **4º** | LDA | 0.9238 | 0.9325 | 0.9232 | 0.3766 | ~0.14 s |
| **5º** | QDA | 0.9230 | 0.9315 | 0.9224 | 0.9013 | ~0.13 s |
| **6º** | GaussianNB | 0.9204 | 0.9281 | 0.9198 | 2.7174 | ~0.07 s |

### 1.2. Ranking dos Melhores Pares (Seletor + Modelo Otimizado) para a Borda
Ao aplicarmos o Optuna, os seguintes pares emergiram como os mais táticos para o Raspberry Pi. O seletor **LowVariance** brilhou aqui pois usa **apenas 12 features**, reduzindo significativamente o custo computacional na placa de rede em comparação com as 15 ou 22 features dos outros métodos.

| Perfil do Modelo para Edge | Par (Seletor + Modelo) | F1-Score | Log Loss | Tempo de Treino (Fit) | Tempo de Inferência (Teste completo)* |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **O Campeão Geral** (Alta precisão + economia de features) | LowVariance + GradientBoosting | **0.9754** | **0.0714** | 10.88 s | 0.056 s |
| **O Atleta de Velocidade** (Ação instantânea para mitigação) | LowVariance + DecisionTree | **0.9688** | 0.0891 | 0.06 s | **0.001 s** |
| **A Força Paralelizada** (Uso dos 4 núcleos do Pi) | LowVariance + RandomForest | **0.9734** | 0.0848 | 3.41 s | 0.155 s |
| **O Teste de Teto** (Hardware vs Ganho com 15 features) | ExtraTrees + GradientBoosting | **0.9754** | **0.0714** | 10.73 s | 0.055 s |
| **O "Cabo de Salvação"** (Inferência linear de baixo custo) | LowVariance + LDA | **0.9232** | 0.3764 | 0.11 s | **0.001 s** |

*\*Nota: O tempo de inferência é sobre a matriz de teste inteira (~18.900 pacotes). Por pacote individual (em tempo real), todos responderão na casa dos microsegundos.*

---

## 2. Arquivos para Deploy no Raspberry Pi

Para subir ao Raspberry Pi, foram separados 5 modelos (arquivos `.pkl`) que cobrem todos os perfis descritos acima. O tamanho do arquivo em disco (`.pkl`) está diretamente atrelado à complexidade na RAM (Árvores complexas gastam mais RAM, matemática linear gasta menos).

Os caminhos base destes arquivos são a pasta: `models/models_ensemble_v2/optuna/`

| Arquivo (Modelo .pkl) | Tamanho em Disco (KB) | Tempo de Treinamento Otimizado (s) | Por que escolher? |
| :--- | :--- | :--- | :--- |
| `optuna_by_selector_lowvariance_gradientboosting.pkl` | **995.04 KB** | **10.88 s** | Melhor custo-benefício de acurácia global usando apenas 12 features. |
| `optuna_by_selector_lowvariance_decisiontree.pkl` | **6.76 KB** | **0.06 s** | Extremamente leve para RAM e CPU; escolha principal para ataques volumétricos. |
| `optuna_by_selector_lowvariance_randomforest.pkl` | **2418.87 KB** (~2.4 MB) | **3.41 s** | Mais pesado na RAM, mas permite `n_jobs=-1` (multiprocessing no Pi). |
| `optuna_by_selector_extratrees_gradientboosting.pkl` | **993.99 KB** | **10.73 s** | Usa 15 features. Deve ser usado para comparar e estressar o hardware em relação ao LowVariance. |
| `optuna_by_selector_lowvariance_lda.pkl` | **1.95 KB** | **0.11 s** | Arquivo quase inexistente em tamanho. Útil se a placa estiver sob estresse térmico/processamento crítico e perder acerto não for o problema primário. |
