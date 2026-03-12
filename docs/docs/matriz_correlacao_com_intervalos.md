# Seleção de Features com Intervalos de Tempo (Gaps)

## Documentação: Métodos de Seleção de Features para Dataset com Features de Intervalo

Este documento descreve o processo de seleção de características aplicado ao dataset DoS do MQTT Under Attack com **features de intervalo de tempo** (`publish_gap` e `connect_gap`) adicionadas.

---

## 1. Introdução

### 1.1 Objetivo

Avaliar e comparar diferentes métodos de seleção de features para o dataset de ataques DoS em redes MQTT, incluindo as novas features de intervalo temporal:

- **`publish_gap`**: Intervalo de tempo entre pacotes PUBLISH consecutivos
- **`connect_gap`**: Intervalo de tempo entre pacotes CONNECT consecutivos

### 1.2 Dataset Utilizado

| Atributo | Valor |
|----------|-------|
| **Arquivo** | `DoS_with_gap_features.csv` |
| **Localização** | `data/processed/` |
| **Origem** | Dataset DoS do MQTT Under Attack com features de intervalo adicionadas |

### 1.3 Métodos Implementados

Este notebook implementou **6 métodos** de seleção de features:

| Método | Categoria | Abordagem |
|--------|-----------|-----------|
| mRMR | Filter | Informação Mútua |
| Fisher's Score | Filter | Variância inter/intra classes |
| Correlação de Pearson | Filter | Correlação linear |
| ExtraTreesClassifier | Embedded | Importância baseada em árvores |
| LinearSVC (L1) | Embedded | Coeficientes do modelo |
| Lasso (L1) | Embedded | Regularização L1 |

---

## 2. Pré-processamento

### 2.1 Seleção de Features Numéricas

Foram selecionadas apenas features numéricas (`int64`, `float64`) do dataset.

### 2.2 Features Removidas (Irrelevantes)

As seguintes colunas foram removidas por serem irrelevantes para detecção de ataques:

```python
colunas_para_remover = [
    'frame.time_delta_displayed', 'frame.time_epoch', 'frame.time_invalid', 
    'frame.time_relative', 'tcp.srcport', 'tcp.dstport', 
    'frame.coloring_rule.name', 'frame.coloring_rule.string', 
    'frame.comment', 'frame.comment.expert', 'frame.encap_type', 
    'frame.file_off', 'frame.ignored', 'frame.incomplete', 
    'frame.interface_id', 'frame.interface_name', 'frame.link_nr', 
    'frame.marked', 'frame.md5_hash', 'frame.number', 'frame.offset_shift',
    'mqtt.msgid', 'mqtt.username', 'mqtt.passwd', 
    'mqtt.willmsg', 'mqtt.willtopic'
]
```

### 2.3 Tratamento de Valores

- Valores ausentes (`NaN`) substituídos por `0`
- Valores infinitos (`inf`, `-inf`) substituídos por `0`
- Target (`type`) codificado via `LabelEncoder`

---

## 3. Métodos de Seleção de Features

### 3.1 mRMR (Minimum Redundancy Maximum Relevance)

**O que é:**
O mRMR é um método de seleção de features que otimiza dois critérios simultaneamente:
- **Máxima Relevância**: seleciona features com alta correlação com o target
- **Mínima Redundância**: penaliza features correlacionadas entre si

**Implementação:**
```python
from mrmr import mrmr_classif
K = 15  # Número de features a selecionar
selected_features = mrmr_classif(X=X, y=y, K=K)
```

**Características:**
- Requer instalação: `pip install mrmr-selection`
- Usa informação mútua para calcular relevância e redundância
- A ordem das features retornadas indica importância
- Computacionalmente mais caro que métodos univariados

---

### 3.2 Fisher's Score

**O que é:**
O Fisher's Score mede a capacidade discriminativa de cada feature calculando a razão entre a variância **entre classes** (inter-class) e a variância **dentro das classes** (intra-class).

**Fórmula:**

$$F(f) = \frac{\sum_{c=1}^{C} n_c (\mu_c - \mu)^2}{\sum_{c=1}^{C} n_c \sigma_c^2}$$

Onde:
- $\mu_c$ = média da feature na classe $c$
- $\sigma_c$ = desvio padrão da feature na classe $c$
- $\mu$ = média global da feature
- $n_c$ = número de amostras na classe $c$

**Implementação:**
```python
def fisher_score(X, y):
    n_samples, n_features = X.shape
    classes = np.unique(y)
    overall_mean = X.mean(axis=0)
    scores = np.zeros(n_features)
    
    for i in range(n_features):
        feature_values = X.iloc[:, i].values
        between_class_var = 0
        within_class_var = 0
        
        for c in classes:
            class_mask = (y == c)
            n_c = np.sum(class_mask)
            if n_c > 0:
                class_mean = feature_values[class_mask].mean()
                class_var = feature_values[class_mask].var()
                between_class_var += n_c * (class_mean - overall_mean.iloc[i]) ** 2
                within_class_var += n_c * class_var
        
        if within_class_var > 1e-10:
            scores[i] = between_class_var / within_class_var
    return scores
```

**Características:**
- Features com alto score separam bem as classes
- Método **univariado** (avalia cada feature independentemente)
- Não considera redundância entre features
- Sensível a outliers

---

### 3.3 Correlação de Pearson

**O que é:**
Mede a relação linear entre cada feature e o target. O valor varia de -1 a +1:
- |r| próximo de 1: forte relação linear
- |r| próximo de 0: sem relação linear

**Fórmula:**

$$r = \frac{\sum_{i=1}^{n}(x_i - \bar{x})(y_i - \bar{y})}{\sqrt{\sum_{i=1}^{n}(x_i - \bar{x})^2} \sqrt{\sum_{i=1}^{n}(y_i - \bar{y})^2}}$$

**Implementação:**
```python
from scipy.stats import pearsonr

def pearson_correlation_with_target(X, y):
    correlations = np.zeros(X.shape[1])
    p_values = np.zeros(X.shape[1])
    
    for i in range(X.shape[1]):
        corr, p_val = pearsonr(X.iloc[:, i].values, y)
        correlations[i] = corr
        p_values[i] = p_val
    
    return correlations, p_values
```

**Características:**
- Usamos |r| (valor absoluto) pois correlações negativas também são úteis
- O p-value indica significância estatística
- Captura apenas relações **lineares**
- Método muito rápido e interpretável

**Legenda de significância:**
- `***` p < 0.001
- `**` p < 0.01
- `*` p < 0.05

---

### 3.4 ExtraTreesClassifier (Extremely Randomized Trees)

**O que é:**
Ensemble de árvores de decisão que calcula a importância de features baseada na redução de impureza (Gini) média ao longo de todas as árvores.

**Implementação:**
```python
from sklearn.ensemble import ExtraTreesClassifier

extra_tree = ExtraTreesClassifier(n_estimators=100, random_state=42, n_jobs=-1)
extra_tree.fit(X, y)
importances = extra_tree.feature_importances_
```

**Características:**
- Captura relações **não-lineares**
- Robusto a outliers
- Não requer normalização dos dados
- A soma das importâncias = 1.0
- Usar `random_state` para reprodutibilidade

---

### 3.5 LinearSVC com L1 (Support Vector Classifier)

**O que é:**
SVM linear com regularização L1 (Lasso) que força alguns coeficientes a zero, realizando seleção de features implicitamente.

**Implementação:**
```python
from sklearn.svm import LinearSVC
from sklearn.preprocessing import StandardScaler

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

svc = LinearSVC(C=0.1, penalty='l1', dual=False, max_iter=5000, random_state=42)
svc.fit(X_scaled, y)

# Para multiclasse: média dos coeficientes absolutos
coef_importance = np.mean(np.abs(svc.coef_), axis=0)
```

**Parâmetros testados:**

| Parâmetro C | max_iter | Resultado |
|-------------|----------|-----------|
| 0.1 | 5000 | `publish_gap`: 10.1183, `mqtt.len`: 6.6288 |
| 0.01 | 50000 | `publish_gap`: 7.8773, `mqtt.len`: 4.4757 |

**Características:**
- **REQUER normalização** dos dados (StandardScaler)
- `C` controla regularização: menor C = mais features zeradas
- `dual=False` necessário para L1
- Produz modelo esparso

---

### 3.6 Lasso (L1 Regularization)

**O que é:**
Regressão linear com regularização L1 que minimiza:

$$\min_{\beta} \frac{1}{2n} ||y - X\beta||_2^2 + \alpha ||\beta||_1$$

O termo L1 (|β|) força coeficientes a zero.

**Implementação:**
```python
from sklearn.linear_model import LassoCV

lasso_cv = LassoCV(cv=5, random_state=42, max_iter=10000, n_jobs=-1)
lasso_cv.fit(X_scaled, y)
print(f"Alpha ótimo: {lasso_cv.alpha_}")
lasso_coef = np.abs(lasso_cv.coef_)
```

**Características:**
- **REQUER normalização** dos dados
- `LassoCV` seleciona α ótimo via cross-validation
- Produz modelo esparso e interpretável
- Sensível a multicolinearidade

---

## 4. Seleção via Low Variance

Além dos métodos principais, foi aplicado um filtro de variância para remover features com pouca variabilidade:

```python
from sklearn.feature_selection import VarianceThreshold

threshold = 0.05
selector = VarianceThreshold(threshold=threshold)
X_reduced = selector.fit_transform(X)
features_mantidas = X.columns[selector.get_support()].tolist()
```

Este método remove features que não têm variação suficiente para contribuir com a classificação.

---

## 5. Validação dos Métodos

### 5.1 Metodologia

Para validar cada método de seleção, foi treinado um modelo **RandomForestClassifier** com as features selecionadas:

```python
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, random_state=42, stratify=y
)

rf = RandomForestClassifier(n_estimators=100, max_depth=15, random_state=42, n_jobs=-1)
rf.fit(X_train[selected_features], y_train)
accuracy = accuracy_score(y_test, rf.predict(X_test[selected_features]))
```

### 5.2 Parâmetros do Modelo

| Parâmetro | Valor |
|-----------|-------|
| Estimadores | 100 |
| Profundidade máxima | 15 |
| Test size | 30% |
| Estratificação | Sim |
| Random state | 42 |

---

## 6. Comparação dos Métodos

### 6.1 Interseções entre Métodos

A análise de interseção permite identificar features que são consistentemente selecionadas por múltiplos métodos:

```python
set_mrmr = set(selected_features)
set_fisher = set(fisher_selected)
set_pearson = set(pearson_selected)
set_extratree = set(extratree_selected)
set_svc = set(svc_selected)
set_lasso = set(lasso_selected)

# Features em comum por todos os 6 métodos
common_all_6 = set_mrmr & set_fisher & set_pearson & set_extratree & set_svc & set_lasso
```

### 6.2 Ranking por Consenso

Features foram ranqueadas pelo número de métodos que as selecionaram:

- **6 métodos**: Features críticas, alta confiança
- **5 métodos**: Features muito importantes
- **4+ métodos**: Recomendadas para modelo final

---

## 7. Análise de Redundância

Para cada conjunto de features selecionadas, foi calculada a correlação média entre elas:

```python
def calculate_mean_correlation(features, X):
    X_subset = X[features]
    corr = X_subset.corr().abs()
    mask = np.triu(np.ones_like(corr, dtype=bool), k=1)
    return corr.where(mask).mean().mean()
```

Métodos com menor redundância média são preferíveis quando multicolinearidade é uma preocupação.

---

## 8. Visualizações

O notebook inclui as seguintes visualizações:

1. **Ranking mRMR**: Gráfico de barras horizontais das top K features
2. **Fisher's Score**: Gráfico com scores discriminativos
3. **Correlação de Pearson**: Gráfico com cores para correlação positiva/negativa
4. **ExtraTrees Importance**: Feature importance do ensemble
5. **LinearSVC Coeficientes**: Coeficientes absolutos do modelo
6. **Lasso Coeficientes**: Coeficientes da regularização L1
7. **Heatmap de Rankings**: Comparação visual dos rankings por método
8. **Matriz de Presença**: Quais features foram selecionadas por quais métodos

---

## 9. Conclusões e Recomendações

### 9.1 Comparação dos Métodos

| Aspecto | mRMR | Fisher | Pearson | ExtraTrees | LinearSVC | Lasso |
|---------|------|--------|---------|------------|-----------|-------|
| **Tipo** | Filter | Filter | Filter | Embedded | Embedded | Embedded |
| **Captura não-linearidade** | Parcial | Não | Não | ✅ Sim | Não | Não |
| **Considera redundância** | ✅ Sim | Não | Não | Parcial | Parcial | Parcial |
| **Requer normalização** | Não | Não | Não | Não | ✅ Sim | ✅ Sim |
| **Velocidade** | Média | Rápida | Rápida | Média | Média | Média |
| **Interpretabilidade** | Alta | Alta | Alta | Média | Alta | Alta |

### 9.2 Importância das Features de Intervalo

As features de intervalo temporal (`publish_gap` e `connect_gap`) demonstraram ser altamente relevantes:

- **`publish_gap`**: Frequentemente aparece entre as top features, especialmente nos métodos LinearSVC e Lasso
- **`connect_gap`**: Também selecionada por múltiplos métodos

Essas features capturam o comportamento temporal dos ataques DoS, onde:
- Ataques tendem a ter intervalos muito pequenos entre pacotes
- Tráfego normal tem padrões de intervalo mais variados

### 9.3 Recomendações por Cenário

1. **Análise Exploratória Rápida**
   - Use: Pearson ou Fisher's Score
   - Motivo: Rápidos e interpretáveis

2. **Evitar Multicolinearidade**
   - Use: mRMR
   - Motivo: Minimiza redundância explicitamente

3. **Relações Não-Lineares**
   - Use: ExtraTreesClassifier
   - Motivo: Baseado em árvores, captura interações

4. **Modelo Esparso + Interpretável**
   - Use: Lasso ou LinearSVC (L1)
   - Motivo: Produzem modelos com poucos coeficientes não-zero

5. **Consenso Robusto**
   - Use: Features selecionadas por 4+ métodos
   - Motivo: Alta confiabilidade, diferentes perspectivas concordam



---

## 10. Arquivos Gerados

| Arquivo | Descrição |
|---------|-----------|
| `feature_selection_results.csv` | Resultados completos da seleção |
| `recommended_features.csv` | Features recomendadas por consenso |
| `feature_consensus_ranking.csv` | Ranking por número de métodos |

---

## 11. Referências

- **Notebook**: `notebooks/matriz_correlacao_with_gaps.ipynb`
- **Dataset**: `data/processed/DoS_with_gap_features.csv`
- **Documentação das features de gap**: `docs/publish_and_connect_gap.md`

---

## Apêndice: Código de Validação Completa

```python
# Resumo final: Comparação de Acurácias de todos os métodos
results = {
    'Método': ['Todas Features', 'mRMR', 'Fisher', 'Pearson', 'ExtraTrees', 'LinearSVC', 'Lasso'],
    'Num Features': [X.shape[1], len(selected_features), K_fisher, K_pearson, K_tree, K_svc, K_lasso],
    'Acurácia': [acc_all, acc_mrmr, acc_fisher, acc_pearson, acc_tree, acc_svc, acc_lasso]
}

results_df = pd.DataFrame(results)
results_df['Redução (%)'] = ((X.shape[1] - results_df['Num Features']) / X.shape[1] * 100).round(1)
results_df = results_df.sort_values('Acurácia', ascending=False)
```
