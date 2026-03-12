# 📊 Feature Engineering: `publish_gap` e `connect_gap`

Este documento descreve o processo de criação das features derivadas **`publish_gap`** e **`connect_gap`**, que representam os intervalos de tempo entre mensagens PUBLISH e CONNECT consecutivas no protocolo MQTT.

---

## 📌 Objetivo

Criar features que capturem o **intervalo temporal entre pacotes específicos do protocolo MQTT**, úteis para detectar ataques DoS que geram rajadas de mensagens em curtos períodos.

| Feature | Mensagem MQTT | Código `msgtype` | Propósito |
|---------|---------------|------------------|-----------|
| `publish_gap` | PUBLISH | 3 | Detectar flooding de publicações |
| `connect_gap` | CONNECT | 1 | Detectar flooding de conexões |

---

## 🔬 Método Utilizado

### Estratégia: Diferença Temporal com Forward Fill

Ambas as features são calculadas usando a mesma estratégia:

1. **Filtragem** de pacotes do tipo específico (PUBLISH ou CONNECT)
2. **Diferença temporal** (`diff()`) entre timestamps consecutivos
3. **Propagação de valores** (`ffill`) para linhas que não são do tipo filtrado
4. **Preenchimento inicial** (`fillna(0)`) para linhas antes da primeira ocorrência

---

## 📝 Feature 1: `publish_gap`

### O que é considerado
- **Apenas mensagens PUBLISH** (`mqtt.msgtype == 3`)
- **Timestamp absoluto** (`frame.time_epoch`) em segundos Unix

### O que é desconsiderado
- Mensagens de outros tipos (CONNECT, CONNACK, SUBSCRIBE, etc.)
- Diferenças entre sessões ou clientes distintos (cálculo global)

### Código

```python
# Criar coluna publish_gap com NaN para todos
df['publish_gap'] = np.nan

# Calcular o intervalo apenas para linhas PUBLISH (msgtype == 3)
publish_mask = df['mqtt.msgtype'] == 3
df.loc[publish_mask, 'publish_gap'] = df.loc[publish_mask, 'frame.time_epoch'].diff()

# Utilizando forward fill para propagar último valor conhecido
df['publish_gap'] = df['publish_gap'].ffill().fillna(0)
```

### Explicação Linha a Linha

| Linha | Código | Explicação |
|-------|--------|------------|
| 1 | `df['publish_gap'] = np.nan` | Inicializa coluna com NaN para todas as linhas |
| 2 | `publish_mask = df['mqtt.msgtype'] == 3` | Cria máscara booleana para filtrar PUBLISH |
| 3 | `df.loc[publish_mask, 'publish_gap'] = ...diff()` | Calcula diferença temporal apenas entre PUBLISH consecutivos |
| 4 | `df['publish_gap'].ffill().fillna(0)` | Propaga valores para não-PUBLISH e preenche início com 0 |

---

## 📝 Feature 2: `connect_gap`

### O que é considerado
- **Apenas mensagens CONNECT** (`mqtt.msgtype == 1`)
- **Timestamp absoluto** (`frame.time_epoch`) em segundos Unix

### O que é desconsiderado
- Mensagens de outros tipos (PUBLISH, CONNACK, SUBSCRIBE, etc.)
- Diferenças entre clientes ou IPs distintos (cálculo global)

### Código

```python
# Criar coluna connect_gap com NaN para todos
df['connect_gap'] = np.nan

# Calcular o intervalo apenas para linhas CONNECT (msgtype == 1)
connect_mask = df['mqtt.msgtype'] == 1
df.loc[connect_mask, 'connect_gap'] = df.loc[connect_mask, 'frame.time_epoch'].diff()

# Utilizando forward fill para propagar último valor conhecido
df['connect_gap'] = df['connect_gap'].ffill().fillna(0)
```

### Explicação Linha a Linha

| Linha | Código | Explicação |
|-------|--------|------------|
| 1 | `df['connect_gap'] = np.nan` | Inicializa coluna com NaN para todas as linhas |
| 2 | `connect_mask = df['mqtt.msgtype'] == 1` | Cria máscara booleana para filtrar CONNECT |
| 3 | `df.loc[connect_mask, 'connect_gap'] = ...diff()` | Calcula diferença temporal apenas entre CONNECT consecutivos |
| 4 | `df['connect_gap'].ffill().fillna(0)` | Propaga valores para não-CONNECT e preenche início com 0 |

---

## 📊 Tabela de Tipos de Mensagem MQTT

| Valor `msgtype` | Tipo | Feature Relacionada |
|-----------------|------|---------------------|
| **1** | **CONNECT** | `connect_gap` |
| 2 | CONNACK | - |
| **3** | **PUBLISH** | `publish_gap` |
| 4 | PUBACK | - |
| 5 | PUBREC | - |
| 6 | PUBREL | - |
| 7 | PUBCOMP | - |
| 8 | SUBSCRIBE | - |
| 9 | SUBACK | - |
| 10 | UNSUBSCRIBE | - |
| 11 | UNSUBACK | - |
| 12 | PINGREQ | - |
| 13 | PINGRESP | - |
| 14 | DISCONNECT | - |

---

## ⚙️ Parâmetros e Configurações

| Parâmetro | `publish_gap` | `connect_gap` |
|-----------|---------------|---------------|
| Tipo de mensagem | PUBLISH | CONNECT |
| Código `msgtype` | 3 | 1 |
| Campo de timestamp | `frame.time_epoch` | `frame.time_epoch` |
| Método de cálculo | `diff()` | `diff()` |
| Preenchimento | `ffill()` + `fillna(0)` | `ffill()` + `fillna(0)` |

---

## 🔄 Fluxo de Processamento

```
Dataset Original
       │
       ▼
┌──────────────────┐
│ Criar publish_gap│ ← Filtrar msgtype == 3, calcular diff(), ffill()
└──────────────────┘
       │
       ▼
┌──────────────────┐
│ Criar connect_gap│ ← Filtrar msgtype == 1, calcular diff(), ffill()
└──────────────────┘
       │
       ▼
┌──────────────────┐
│ Remover colunas  │ ← mqtt.proto_len, mqtt.ver
└──────────────────┘
       │
       ▼
Dataset Processado
(DoS_with_gap_features.csv)
```

---

## 📈 Interpretação dos Valores

### `publish_gap`

| Valor | Interpretação |
|-------|---------------|
| **0** | Primeiro PUBLISH ou linha antes de qualquer PUBLISH |
| **< 0.001s** | Intervalo muito curto → possível flooding/DoS via PUBLISH |
| **0.001 - 0.1s** | Intervalo normal para tráfego moderado |
| **> 1s** | Intervalo longo → tráfego esparso |

### `connect_gap`

| Valor | Interpretação |
|-------|---------------|
| **0** | Primeiro CONNECT ou linha antes de qualquer CONNECT |
| **< 0.01s** | Intervalo muito curto → possível flooding/DoS via CONNECT |
| **0.01 - 1s** | Intervalo normal (uma conexão a cada segundo) |
| **> 10s** | Intervalo longo → poucas conexões |

---

## 🎯 Relevância para Detecção de DoS

### `publish_gap`
- **Detectar Flooding de PUBLISH**: Ataques DoS via PUBLISH geram intervalos < 1ms
- **Padrão de ataque**: Muitos PUBLISH em rajada com `publish_gap` próximo de 0

### `connect_gap`
- **Detectar Flooding de CONNECT**: Ataques tentam sobrecarregar broker com conexões
- **Padrão de ataque**: Muitos CONNECT em sequência com `connect_gap` < 10ms

### Estatísticas Esperadas

| Classe | `publish_gap` médio | `connect_gap` médio |
|--------|---------------------|---------------------|
| `normal` | > 0.01s | > 1s |
| `dos` | < 0.001s | < 0.1s |

---

## ❌ Features Removidas

As seguintes features foram removidas do dataset final por baixa relevância:

| Feature Removida | Motivo |
|------------------|--------|
| `mqtt.proto_len` | Valor constante (sempre 4 para "MQTT") |
| `mqtt.ver` | Pouca variação e baixa importância nos métodos de seleção |

---

## 📁 Arquivos Gerados

| Arquivo | Localização | Descrição |
|---------|-------------|-----------|
| Dataset processado | `data/processed/DoS_with_gap_features.csv` | Dataset com `publish_gap` e `connect_gap`, sem `mqtt.proto_len` e `mqtt.ver` |

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

# ========== FEATURE 1: publish_gap ==========
df['publish_gap'] = np.nan
publish_mask = df['mqtt.msgtype'] == 3
df.loc[publish_mask, 'publish_gap'] = df.loc[publish_mask, 'frame.time_epoch'].diff()
df['publish_gap'] = df['publish_gap'].ffill().fillna(0)

# ========== FEATURE 2: connect_gap ==========
df['connect_gap'] = np.nan
connect_mask = df['mqtt.msgtype'] == 1
df.loc[connect_mask, 'connect_gap'] = df.loc[connect_mask, 'frame.time_epoch'].diff()
df['connect_gap'] = df['connect_gap'].ffill().fillna(0)

# ========== REMOVER FEATURES ==========
colunas_remover = ['mqtt.proto_len', 'mqtt.ver']
df = df.drop(columns=[c for c in colunas_remover if c in df.columns], errors='ignore')

# ========== SALVAR ==========
output_path = Path("../data/processed/DoS_with_gap_features.csv")
df.to_csv(output_path, index=False)
```

---
