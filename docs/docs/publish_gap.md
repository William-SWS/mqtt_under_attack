# 📊 Feature Engineering: `publish_gap`



## 🔬 Método Utilizado

### Estratégia: Diferença Temporal com Forward Fill

A feature é calculada usando:
1. **Filtragem** de pacotes do tipo PUBLISH (`mqtt.msgtype == 3`)
2. **Diferença temporal** (`diff()`) entre timestamps consecutivos
3. **Propagação de valores** (`ffill`) para linhas não-PUBLISH

---

## 📝 Explicação Linha a Linha

### Célula de Criação da Feature

```python
# Criar coluna publish_gap com NaN para todos
df['publish_gap'] = np.nan
```
**Explicação**: Inicializa a coluna `publish_gap` com valores `NaN` (Not a Number) para todas as linhas do DataFrame. Isso garante que apenas as linhas relevantes (PUBLISH) recebam valores calculados.

---

```python
# Calcular o intervalo apenas para linhas PUBLISH (msgtype == 3)
publish_mask = df['mqtt.msgtype'] == 3
```
**Explicação**: Cria uma máscara booleana que identifica quais linhas contêm mensagens do tipo PUBLISH. No protocolo MQTT, o `msgtype == 3` corresponde ao tipo PUBLISH.

| Valor `msgtype` | Tipo de Mensagem |
|-----------------|------------------|
| 1 | CONNECT |
| 2 | CONNACK |
| **3** | **PUBLISH** |
| 4 | PUBACK |
| 8 | SUBSCRIBE |
| 9 | SUBACK |

---

```python
df.loc[publish_mask, 'publish_gap'] = df.loc[publish_mask, 'frame.time_epoch'].diff()
```
**Explicação**: 
- `df.loc[publish_mask, 'frame.time_epoch']` → Seleciona o timestamp (Unix epoch) apenas das linhas PUBLISH
- `.diff()` → Calcula a diferença entre cada valor e o anterior
- O resultado é atribuído à coluna `publish_gap` apenas nas linhas PUBLISH

**Exemplo**:
| Índice | mqtt.msgtype | frame.time_epoch | publish_gap |
|--------|--------------|------------------|-------------|
| 0 | 3 (PUBLISH) | 1000.000 | NaN (primeiro) |
| 1 | 2 (CONNACK) | 1000.001 | NaN |
| 2 | 3 (PUBLISH) | 1000.005 | 0.005 |
| 3 | 3 (PUBLISH) | 1000.006 | 0.001 |

---

```python
#Utilizando forward fill para propagar último valor conhecido
df['publish_gap'] = df['publish_gap'].ffill().fillna(0)
```
**Explicação**:
- `.ffill()` (Forward Fill) → Propaga o último valor não-nulo para as linhas seguintes que têm NaN
- `.fillna(0)` → Preenche com 0 os valores que ainda são NaN (linhas antes do primeiro PUBLISH)

**Por que Forward Fill?**
- Mantém o contexto temporal: linhas não-PUBLISH "herdam" o último intervalo de PUBLISH observado
- Útil para modelos de ML que precisam de valores em todas as linhas
- Preserva a informação de que não houve novo PUBLISH desde o último intervalo calculado

**Exemplo após ffill**:
| Índice | mqtt.msgtype | publish_gap |
|--------|--------------|-------------|
| 0 | 3 (PUBLISH) | 0 (fillna) |
| 1 | 2 (CONNACK) | 0 (ffill do anterior) |
| 2 | 3 (PUBLISH) | 0.005 |
| 3 | 1 (CONNECT) | 0.005 (ffill) |
| 4 | 3 (PUBLISH) | 0.001 |

---

## ⚙️ Parâmetros e Configurações

| Parâmetro | Valor | Descrição |
|-----------|-------|-----------|
| `mqtt.msgtype` | 3 | Código do tipo PUBLISH no protocolo MQTT |
| `frame.time_epoch` | Unix timestamp | Timestamp absoluto do pacote em segundos |
| Método de diferença | `diff()` | Calcula diferença entre linhas consecutivas |
| Preenchimento | `ffill()` + `fillna(0)` | Forward fill seguido de preenchimento com zero |

---

## 📈 Interpretação dos Valores

| Valor de `publish_gap` | Interpretação |
|------------------------|---------------|
| **0** | Primeiro PUBLISH ou linha antes de qualquer PUBLISH |
| **< 0.001s** | Intervalo muito curto → possível flooding/DoS |
| **0.001 - 0.1s** | Intervalo normal para tráfego moderado |
| **> 1s** | Intervalo longo → tráfego esparso |

---

## 🎯 Relevância para Detecção de DoS

A feature `publish_gap` é especialmente útil para:

1. **Detectar Flooding**: Ataques DoS via PUBLISH geram intervalos muito pequenos (< 1ms)
2. **Identificar Padrões**: Tráfego normal tem intervalos mais regulares e maiores
3. **Complementar `frame.time_delta`**: Foca especificamente em mensagens PUBLISH

### Estatísticas Esperadas

| Classe | publish_gap médio | Observação |
|--------|-------------------|------------|
| `normal` | > 0.01s | Intervalos regulares |
| `dos` | < 0.001s | Rajadas de pacotes |

---

## 📁 Arquivos Gerados

| Arquivo | Localização | Descrição |
|---------|-------------|-----------|
| Dataset processado | `data/processed/DoS_with_publish_gap.csv` | Dataset original + coluna `publish_gap` |

---

## 🔗 Referências

- **Notebook de criação**: `notebooks/publish_feature.ipynb`
- **Dataset original**: `data/raw/MQTT Under Attack Dataset/DoS.csv`
- **Dicionário de dados**: `docs/docs/dicionario_de_dados.md`

---

## 📝 Código Completo

```python
import pandas as pd
import numpy as np
from pathlib import Path

# Carregar dataset
dos_path = Path("../data/raw/MQTT Under Attack Dataset/DoS.csv")
df = pd.read_csv(dos_path)

# Criar feature publish_gap
df['publish_gap'] = np.nan
publish_mask = df['mqtt.msgtype'] == 3
df.loc[publish_mask, 'publish_gap'] = df.loc[publish_mask, 'frame.time_epoch'].diff()
df['publish_gap'] = df['publish_gap'].ffill().fillna(0)

# Salvar dataset processado
output_path = Path("../data/processed/DoS_with_publish_gap.csv")
df.to_csv(output_path, index=False)
```

---
