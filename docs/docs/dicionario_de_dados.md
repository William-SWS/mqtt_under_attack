# 📘 Dicionário de Dados — Dataset MQTT_UAD (DoS)

Este documento descreve as **67 features do dataset MQTT_UAD (DoS)**, extraídas do trabalho publicado no Figshare:
> [MQTT_UAD: MQTT Under Attack Dataset](https://figshare.com/articles/dataset/MQTT_UAD_MQTT_Under_Attack_Dataset_A_public_dataset_for_the_detection_of_attacks_in_IoT_networks_using_MQTT_protocol/24420958)

O dataset contém **94.625 registros** de tráfego de rede capturados via Wireshark, com pacotes MQTT normais e de ataques DoS.

---

## 📊 Resumo do Dataset

| Métrica | Valor |
|---------|-------|
| Total de registros | 94.625 |
| Total de features | 67 |
| Features numéricas | 41 |
| Features textuais/categóricas | 26 |
| Classes (target) | `normal`, `dos` |

---

## 🆕 Features Derivadas (Time Gaps)

Estas features **não existem no dataset original** e foram criadas através de engenharia de atributos para capturar comportamentos temporais de ataques (rajadas de pacotes).

### `publish_gap` ⭐
- **Descrição**: Intervalo de tempo (em segundos) entre mensagens PUBLISH consecutivas.
- **Derivação**: Calculada subtraindo o timestamp (`frame.time_epoch`) da mensagem PUBLISH atual pelo timestamp da mensagem PUBLISH anterior.
  - **Filtro**: `mqtt.msgtype == 3` (PUBLISH).
  - **Preenchimento**: Os valores calculados nas linhas de PUBLISH são propagados para as linhas subsequentes (`ffill`) até o próximo PUBLISH. O primeiro valor é preenchido com 0.
- **Função**: Identifica a frequência de envio de dados. Em ataques de flood, esse valor tende a zero.
- **Situação na Seleção**: 🚀 **Alta Relevância**. Selecionada por **6 de 6 métodos** (mRMR, Fisher, Pearson, ExtraTrees, LinearSVC, Lasso). É uma das features mais fortes para detecção.

### `connect_gap`
- **Descrição**: Intervalo de tempo (em segundos) entre mensagens CONNECT consecutivas.
- **Derivação**: Calculada subtraindo o timestamp (`frame.time_epoch`) da mensagem CONNECT atual pelo timestamp da mensagem CONNECT anterior.
  - **Filtro**: `mqtt.msgtype == 1` (CONNECT).
  - **Preenchimento**: Propagação (`ffill`) similar ao `publish_gap`.
- **Função**: Identifica tentativas frequentes de conexão ou reconexão (ataques de exaustão de conexão).
- **Situação na Seleção**: verd **Média Relevância**. Selecionada por **3 de 6 métodos** (ExtraTrees, LinearSVC, Lasso). Útil para tipos específicos de ataque que envolvem o handshake de conexão.

---

## ⭐ Features de Alta Relevância (Selecionadas por 6/6 métodos)

As seguintes features foram selecionadas por **todos os 6 métodos de seleção** (mRMR, Fisher's Score, Pearson, ExtraTrees, LinearSVC, Lasso), sendo as mais importantes para detecção de DoS:

### `frame.cap_len` ⭐
- **Descrição**: Tamanho do frame capturado em bytes
- **Tipo**: Inteiro (int64)
- **Relevância**: ⭐⭐⭐ MUITO ALTA
- **Uso**: Discriminação de padrões de ataque DoS

### `frame.len` ⭐
- **Descrição**: Tamanho total do frame em bytes
- **Tipo**: Inteiro (int64)
- **Relevância**: ⭐⭐⭐ MUITO ALTA
- **Observação**: Altamente correlacionado com `frame.cap_len`

### `mqtt.len` ⭐
- **Descrição**: Tamanho remanescente da mensagem MQTT (remaining length)
- **Tipo**: Inteiro (int64)
- **Relevância**: ⭐⭐⭐ MUITO ALTA
- **Uso**: Fundamental para identificar pacotes anômalos

### `mqtt.msgtype` ⭐
- **Descrição**: Tipo da mensagem MQTT
- **Tipo**: Inteiro (int64) - códigos numéricos
- **Valores**: 1=CONNECT, 2=CONNACK, 3=PUBLISH, 4=PUBACK, 8=SUBSCRIBE, etc.
- **Relevância**: ⭐⭐⭐ MUITO ALTA
- **Uso**: Identificar padrões de mensagens em ataques

### `mqtt.qos` ⭐
- **Descrição**: Quality of Service da mensagem MQTT
- **Tipo**: Inteiro (int64)
- **Valores**: 0 (At most once), 1 (At least once), 2 (Exactly once)
- **Relevância**: ⭐⭐⭐ MUITO ALTA

### `mqtt.clientid_len` ⭐
- **Descrição**: Comprimento do Client ID em bytes
- **Tipo**: Inteiro (int64)
- **Relevância**: ⭐⭐⭐ MUITO ALTA
- **Uso**: Client IDs muito curtos ou longos podem indicar anomalias

### `mqtt.topic_len` ⭐
- **Descrição**: Comprimento do nome do tópico MQTT
- **Tipo**: Inteiro (int64)
- **Relevância**: ⭐⭐⭐ MUITO ALTA

### `mqtt.kalive` ⭐
- **Descrição**: Valor do Keep Alive em segundos
- **Tipo**: Inteiro (int64)
- **Relevância**: ⭐⭐⭐ MUITO ALTA
- **Observação**: Valores extremos podem indicar ataques

### `mqtt.conack.flags.reserved` ⭐
- **Descrição**: Bits reservados no CONNACK flags
- **Tipo**: Inteiro (int64)
- **Relevância**: ⭐⭐⭐ MUITO ALTA
- **Observação**: Deve ser sempre 0 em tráfego normal

---

## ⭐⭐ Features de Relevância Média-Alta (5/6 métodos)

### `mqtt.retain`
- **Descrição**: Flag Retain da mensagem PUBLISH
- **Tipo**: Binário (0/1)
- **Relevância**: ⭐⭐ ALTA

### `mqtt.conflag.cleansess`
- **Descrição**: Flag Clean Session no CONNECT
- **Tipo**: Binário (0/1)
- **Relevância**: ⭐⭐ ALTA
- **Uso**: Sessões não-limpas podem indicar comportamento suspeito

### `mqtt.proto_len`
- **Descrição**: Comprimento do nome do protocolo
- **Tipo**: Inteiro (int64)
- **Relevância**: ⭐⭐ ALTA

---

## ⭐ Features de Relevância Média (4/6 métodos)

### `frame.time_delta`
- **Descrição**: Intervalo de tempo entre pacotes consecutivos
- **Tipo**: Float (float64)
- **Relevância**: ⭐ MÉDIA-ALTA
- **Uso**: Muito útil para detectar rajadas de pacotes (DoS)

### `mqtt.conack.val`
- **Descrição**: Código de retorno do CONNACK
- **Tipo**: Inteiro (int64)
- **Valores**: 0=Aceito, 1-5=Recusado (diversos motivos)
- **Relevância**: ⭐ MÉDIA

### `mqtt.ver`
- **Descrição**: Versão do protocolo MQTT
- **Tipo**: Inteiro (int64)
- **Valores**: 3 (MQTT 3.1), 4 (MQTT 3.1.1), 5 (MQTT 5.0)
- **Relevância**: ⭐ MÉDIA

---

## 🏷️ Variável Alvo (Target)

### `type`
- **Descrição**: Classe do tráfego de rede
- **Tipo**: Categórico (string)
- **Valores no dataset DoS**:
  - `normal` - Tráfego MQTT legítimo
  - `dos` - Tráfego de ataque DoS

---

## ⏱️ Features Temporais (Frame)

### `frame.time_delta`
- **Descrição**: Tempo desde o pacote anterior
- **Tipo**: Float
- **Relevância**: ⭐ MÉDIA (selecionada por 4 métodos)

### `frame.time_delta_displayed`
- **Descrição**: Tempo desde o pacote anterior exibido
- **Tipo**: Float
- **Relevância**: ❌ BAIXA (redundante com `frame.time_delta`)

### `frame.time_epoch`
- **Descrição**: Timestamp Unix absoluto
- **Tipo**: Float
- **Relevância**: ❌ INÚTIL (metadado de captura)

### `frame.time_invalid`
- **Descrição**: Indica se o timestamp é inválido
- **Tipo**: Float (maioria nulo)
- **Relevância**: ❌ INÚTIL (constante)

### `frame.time_relative`
- **Descrição**: Tempo relativo ao início da captura
- **Tipo**: Float
- **Relevância**: ❌ INÚTIL (metadado de captura)

---

## 🌐 Features de Rede (IP/TCP/Ethernet)

### `ip.src`
- **Descrição**: Endereço IP de origem
- **Tipo**: String
- **Relevância**: ❌ INÚTIL (identificador específico do ambiente)
- **Observação**: **Não usar** - causa overfitting

### `ip.dst`
- **Descrição**: Endereço IP de destino
- **Tipo**: String
- **Relevância**: ❌ INÚTIL
- **Observação**: **Não usar** - causa overfitting

### `tcp.srcport`
- **Descrição**: Porta TCP de origem
- **Tipo**: Inteiro
- **Relevância**: ❌ BAIXA (geralmente efêmera)

### `tcp.dstport`
- **Descrição**: Porta TCP de destino
- **Tipo**: Inteiro
- **Relevância**: ❌ BAIXA (geralmente 1883 fixo)

### `eth.src`
- **Descrição**: Endereço MAC de origem
- **Tipo**: String
- **Relevância**: ❌ INÚTIL (identificador específico)

### `eth.dst`
- **Descrição**: Endereço MAC de destino
- **Tipo**: String
- **Relevância**: ❌ INÚTIL (identificador específico)

---

## 📦 Features de Frame/Captura (Metadados Wireshark)

> ⚠️ A maioria destas features são **metadados de captura do Wireshark** e **não devem ser usadas** em modelos de produção.

### `frame.cap_len` ⭐
- **Relevância**: ⭐⭐⭐ MUITO ALTA (ver seção de features importantes)

### `frame.len` ⭐
- **Relevância**: ⭐⭐⭐ MUITO ALTA (ver seção de features importantes)

### `frame.coloring_rule.name`
- **Descrição**: Nome da regra de coloração do Wireshark
- **Tipo**: String
- **Relevância**: ❌ INÚTIL (anotação visual)

### `frame.coloring_rule.string`
- **Descrição**: String da regra de coloração
- **Tipo**: String
- **Relevância**: ❌ INÚTIL

### `frame.comment`
- **Descrição**: Comentários do usuário no Wireshark
- **Tipo**: String
- **Relevância**: ❌ INÚTIL

### `frame.comment.expert`
- **Descrição**: Comentários especializados
- **Tipo**: String
- **Relevância**: ❌ INÚTIL

### `frame.encap_type`
- **Descrição**: Tipo de encapsulamento
- **Tipo**: Inteiro (constante = 1)
- **Relevância**: ❌ INÚTIL (constante)

### `frame.file_off`
- **Descrição**: Offset no arquivo de captura
- **Tipo**: Inteiro
- **Relevância**: ❌ INÚTIL

### `frame.ignored`
- **Descrição**: Frame marcado como ignorado
- **Tipo**: Binário (sempre 0)
- **Relevância**: ❌ INÚTIL (constante)

### `frame.incomplete`
- **Descrição**: Frame incompleto
- **Tipo**: Float (sempre nulo)
- **Relevância**: ❌ INÚTIL (constante)

### `frame.interface_id`
- **Descrição**: ID da interface de captura
- **Tipo**: Float (constante)
- **Relevância**: ❌ INÚTIL

### `frame.interface_name`
- **Descrição**: Nome da interface de captura
- **Tipo**: String
- **Relevância**: ❌ INÚTIL

### `frame.link_nr`
- **Descrição**: Número do link
- **Tipo**: Float (sempre nulo)
- **Relevância**: ❌ INÚTIL

### `frame.marked`
- **Descrição**: Frame marcado no Wireshark
- **Tipo**: Binário (sempre 0)
- **Relevância**: ❌ INÚTIL

### `frame.md5_hash`
- **Descrição**: Hash MD5 do frame
- **Tipo**: String
- **Relevância**: ❌ INÚTIL

### `frame.number`
- **Descrição**: Número sequencial do pacote na captura
- **Tipo**: Inteiro
- **Relevância**: ❌ INÚTIL (sequencial)

### `frame.offset_shift`
- **Descrição**: Deslocamento de offset
- **Tipo**: Float (sempre 0)
- **Relevância**: ❌ INÚTIL

---

## 🔌 Features de Conexão MQTT (CONNECT/CONNACK)

### `mqtt.clientid`
- **Descrição**: Identificador do cliente MQTT
- **Tipo**: String
- **Relevância**: ❌ BAIXA (texto identificador)
- **Observação**: Requer encoding especial se usado

### `mqtt.clientid_len` ⭐
- **Relevância**: ⭐⭐⭐ MUITO ALTA (ver seção de features importantes)

### `mqtt.conack.flags`
- **Descrição**: Flags completos do CONNACK (bitfield)
- **Tipo**: Inteiro
- **Relevância**: ❌ BAIXA (redundante com flags individuais)

### `mqtt.conack.flags.reserved` ⭐
- **Relevância**: ⭐⭐⭐ MUITO ALTA (ver seção de features importantes)

### `mqtt.conack.flags.sp`
- **Descrição**: Session Present flag no CONNACK
- **Tipo**: Binário
- **Relevância**: ⭐ BAIXA-MÉDIA (3/6 métodos)

### `mqtt.conack.val`
- **Relevância**: ⭐ MÉDIA (ver seção de features média relevância)

### `mqtt.conflag.cleansess`
- **Relevância**: ⭐⭐ ALTA (ver seção 5/6 métodos)

### `mqtt.conflag.passwd`
- **Descrição**: Flag indicando presença de senha
- **Tipo**: Binário
- **Relevância**: ⭐ BAIXA

### `mqtt.conflag.qos`
- **Descrição**: QoS do Will Message
- **Tipo**: Inteiro
- **Relevância**: ⭐ BAIXA

### `mqtt.conflag.reserved`
- **Descrição**: Bit reservado nos Connect Flags
- **Tipo**: Binário (sempre 0)
- **Relevância**: ❌ INÚTIL (constante)

### `mqtt.conflag.retain`
- **Descrição**: Will Retain flag
- **Tipo**: Binário
- **Relevância**: ⭐ BAIXA (2/6 métodos)

### `mqtt.conflag.uname`
- **Descrição**: Flag indicando presença de username
- **Tipo**: Binário
- **Relevância**: ⭐ BAIXA (2/6 métodos)

### `mqtt.conflag.willflag`
- **Descrição**: Will Flag (Last Will and Testament)
- **Tipo**: Binário
- **Relevância**: ⭐ BAIXA

### `mqtt.conflags`
- **Descrição**: Connect Flags completos (bitfield)
- **Tipo**: Inteiro
- **Relevância**: ❌ BAIXA (redundante com flags individuais)

### `mqtt.kalive` ⭐
- **Relevância**: ⭐⭐⭐ MUITO ALTA (ver seção de features importantes)

### `mqtt.proto_len`
- **Relevância**: ⭐⭐ ALTA (ver seção 5/6 métodos)

### `mqtt.protoname`
- **Descrição**: Nome do protocolo (sempre "MQTT" ou "MQIsdp")
- **Tipo**: String
- **Relevância**: ❌ INÚTIL (constante)

### `mqtt.ver`
- **Relevância**: ⭐ MÉDIA (ver seção 4/6 métodos)

---

## 📤 Features de Mensagens MQTT (PUBLISH)

### `mqtt.dupflag`
- **Descrição**: Flag de mensagem duplicada
- **Tipo**: Binário
- **Relevância**: ⭐ BAIXA (2/6 métodos)

### `mqtt.hdrflags`
- **Descrição**: Header flags completos (bitfield)
- **Tipo**: Inteiro
- **Relevância**: ❌ BAIXA (redundante)

### `mqtt.len` ⭐
- **Relevância**: ⭐⭐⭐ MUITO ALTA (ver seção de features importantes)

### `mqtt.msg`
- **Descrição**: Conteúdo/payload da mensagem
- **Tipo**: String
- **Relevância**: ❌ BAIXA (texto - requer NLP)

### `mqtt.msgid`
- **Descrição**: ID da mensagem (para QoS 1 e 2)
- **Tipo**: Inteiro
- **Relevância**: ❌ BAIXA (identificador sequencial)

### `mqtt.msgtype` ⭐
- **Relevância**: ⭐⭐⭐ MUITO ALTA (ver seção de features importantes)

### `mqtt.qos` ⭐
- **Relevância**: ⭐⭐⭐ MUITO ALTA (ver seção de features importantes)

### `mqtt.retain`
- **Relevância**: ⭐⭐ ALTA (ver seção 5/6 métodos)

### `mqtt.topic`
- **Descrição**: Nome do tópico MQTT
- **Tipo**: String
- **Relevância**: ❌ BAIXA (texto - requer encoding)

### `mqtt.topic_len` ⭐
- **Relevância**: ⭐⭐⭐ MUITO ALTA (ver seção de features importantes)

---

## 🔐 Features de Autenticação MQTT

### `mqtt.username`
- **Descrição**: Nome de usuário para autenticação
- **Tipo**: String
- **Relevância**: ❌ INÚTIL (identificador)

### `mqtt.username_len`
- **Descrição**: Comprimento do username
- **Tipo**: Inteiro
- **Relevância**: ⭐ BAIXA

### `mqtt.passwd`
- **Descrição**: Senha de autenticação
- **Tipo**: String
- **Relevância**: ❌ INÚTIL (dado sensível)

### `mqtt.passwd_len`
- **Descrição**: Comprimento da senha
- **Tipo**: Inteiro
- **Relevância**: ⭐ BAIXA

---

## 📡 Features de Assinatura MQTT (SUBSCRIBE)

### `mqtt.sub.qos`
- **Descrição**: QoS solicitado na assinatura
- **Tipo**: Inteiro
- **Relevância**: ⭐ BAIXA

### `mqtt.suback.qos`
- **Descrição**: QoS concedido no SUBACK
- **Tipo**: Inteiro
- **Relevância**: ⭐ BAIXA

---

## 🪦 Features de Last Will and Testament

### `mqtt.willmsg`
- **Descrição**: Mensagem do testamento
- **Tipo**: String
- **Relevância**: ❌ INÚTIL (texto)

### `mqtt.willmsg_len`
- **Descrição**: Comprimento da mensagem do testamento
- **Tipo**: Inteiro
- **Relevância**: ⭐ BAIXA

### `mqtt.willtopic`
- **Descrição**: Tópico do testamento
- **Tipo**: String
- **Relevância**: ❌ INÚTIL (texto)

### `mqtt.willtopic_len`
- **Descrição**: Comprimento do tópico do testamento
- **Tipo**: Inteiro
- **Relevância**: ⭐ BAIXA

---

## 📋 Resumo de Relevância por Feature

### ⭐⭐⭐ Alta Relevância (6/6 métodos) - **USAR**
| Feature | Tipo | Descrição |
|---------|------|-----------|
| `frame.cap_len` | int64 | Tamanho do frame capturado |
| `frame.len` | int64 | Tamanho do frame |
| `mqtt.clientid_len` | int64 | Comprimento do Client ID |
| `mqtt.qos` | int64 | Quality of Service |
| `mqtt.conack.flags.reserved` | int64 | Flags reservados CONNACK |
| `mqtt.len` | int64 | Tamanho da mensagem MQTT |
| `mqtt.topic_len` | int64 | Comprimento do tópico |
| `mqtt.kalive` | int64 | Keep Alive |
| `mqtt.msgtype` | int64 | Tipo de mensagem |

### ⭐⭐ Relevância Média-Alta (5/6 métodos) - **USAR**
| Feature | Tipo |
|---------|------|
| `mqtt.retain` | int64 |
| `mqtt.conflag.cleansess` | int64 |
| `mqtt.proto_len` | int64 |

### ⭐ Relevância Média (4/6 métodos) - **CONSIDERAR**
| Feature | Tipo |
|---------|------|
| `frame.time_delta` | float64 |
| `mqtt.conack.val` | int64 |
| `mqtt.ver` | int64 |

### ❌ Baixa Relevância ou Inúteis - **DESCARTAR**
- Todos os metadados de captura (`frame.file_off`, `frame.number`, etc.)
- Identificadores de rede (`ip.src`, `ip.dst`, `eth.src`, `eth.dst`)
- Features constantes (`frame.time_invalid`, `mqtt.conflag.reserved`)
- Conteúdo textual (`mqtt.msg`, `mqtt.topic`, `mqtt.clientid`)

---

## 🧠 Recomendações para Modelagem

### Pré-processamento Recomendado
1. **Remover** features de metadados Wireshark
2. **Remover** identificadores de rede (IPs, MACs)
3. **Tratar valores ausentes** (fillna com 0 ou estratégia específica)
4. **Normalizar** features numéricas (para SVM, KNN, MLP)
5. **Usar LabelEncoder** para a variável target

### Features Recomendadas para Modelo de DoS
```python
features_recomendadas = [
    'frame.cap_len', 'frame.len', 'frame.time_delta',
    'mqtt.len', 'mqtt.msgtype', 'mqtt.qos', 'mqtt.retain',
    'mqtt.clientid_len', 'mqtt.topic_len', 'mqtt.kalive',
    'mqtt.conack.flags.reserved', 'mqtt.conack.val',
    'mqtt.conflag.cleansess', 'mqtt.proto_len', 'mqtt.ver'
]
```

### Algoritmos Compatíveis
- ✅ Random Forest
- ✅ ExtraTrees
- ✅ XGBoost / LightGBM
- ✅ SVM (com normalização)
- ✅ Logistic Regression
- ✅ MLP / Redes Neurais
- ✅ KNN (com normalização)

---

## 📚 Referência

Dataset original: [MQTT_UAD - MQTT Under Attack Dataset](https://figshare.com/articles/dataset/MQTT_UAD_MQTT_Under_Attack_Dataset_A_public_dataset_for_the_detection_of_attacks_in_IoT_networks_using_MQTT_protocol/24420958)

---
