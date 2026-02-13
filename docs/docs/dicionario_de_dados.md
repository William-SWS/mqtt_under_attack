# 📘 Dicionário de Dados — Dataset MQTT_UAD

Este documento descreve as **features utilizadas no dataset MQTT_UAD**, conforme o artigo, organizadas por camada e função no protocolo MQTT.  
O objetivo é facilitar **consulta, pré-processamento, seleção de características e interpretação de modelos de ML** para detecção de ataques.

---

## 🏷️ Variável alvo

### `label`
- **Descrição**: Classe do tráfego de rede
- **Tipo**: Categórico
- **Valores possíveis**:
  - `normal`
  - `dos`
  - `mitm`
  - `intrusion`
- **Uso**: Variável alvo (target)

---

## 🌐 Features de rede (IP / TCP)

### `src_ip`
- **Descrição**: Endereço IP de origem
- **Tipo**: String (categórico)
- **Observação**: Geralmente removido ou transformado (hash/encoding)

### `dst_ip`
- **Descrição**: Endereço IP de destino
- **Tipo**: String (categórico)

### `src_port`
- **Descrição**: Porta TCP de origem
- **Tipo**: Inteiro

### `dst_port`
- **Descrição**: Porta TCP de destino (ex.: 1883)
- **Tipo**: Inteiro

### `packet_length`
- **Descrição**: Tamanho do pacote em bytes
- **Tipo**: Numérico contínuo
- **Relevância**: Alta para DoS

### `tcp_flags`
- **Descrição**: Flags TCP (SYN, ACK, FIN, etc.)
- **Tipo**: Categórico ou binário codificado
- **Uso**: Análise de conexões anômalas

### `inter_arrival_time`
- **Descrição**: Tempo entre pacotes consecutivos
- **Tipo**: Numérico contínuo
- **Relevância**: Muito alta para DoS

---

## 🔌 Features de conexão MQTT (CONNECT)

### `mqtt_msgtype`
- **Descrição**: Tipo da mensagem MQTT
- **Tipo**: Categórico
- **Valores**: CONNECT, CONNACK, PUBLISH, SUBSCRIBE, etc.

### `mqtt_protocol_level`
- **Descrição**: Versão do protocolo MQTT
- **Tipo**: Inteiro

### `mqtt_clean_session`
- **Descrição**: Flag Clean Session
- **Tipo**: Binário (0/1)

### `mqtt_will_flag`
- **Descrição**: Indica se o cliente configurou Last Will and Testament
- **Tipo**: Binário (0/1)
- **Observação**: Feature comportamental

### `mqtt_keep_alive`
- **Descrição**: Valor do Keep Alive (em segundos)
- **Tipo**: Inteiro

---

## 📤 Features de publicação MQTT (PUBLISH)

### `mqtt_qos`
- **Descrição**: Quality of Service da mensagem
- **Tipo**: Ordinal
- **Valores**: 0, 1, 2

### `mqtt_retain`
- **Descrição**: Flag Retain
- **Tipo**: Binário (0/1)

### `mqtt_topic_length`
- **Descrição**: Comprimento do tópico MQTT
- **Tipo**: Inteiro

### `mqtt_payload_length`
- **Descrição**: Tamanho do payload MQTT
- **Tipo**: Inteiro
- **Relevância**: Importante para DoS

---

## 📡 Features de assinatura (SUBSCRIBE)

### `mqtt_subscribe_count`
- **Descrição**: Número de mensagens SUBSCRIBE em uma janela temporal
- **Tipo**: Inteiro
- **Relevância**: Ataques de Intrusion

### `mqtt_suback_return_code`
- **Descrição**: Código de retorno do SUBACK
- **Tipo**: Categórico

---

## 🔄 Features de controle MQTT

### `mqtt_pingreq_count`
- **Descrição**: Quantidade de mensagens PINGREQ em uma janela
- **Tipo**: Inteiro

### `mqtt_disconnect_flag`
- **Descrição**: Indica ocorrência de DISCONNECT
- **Tipo**: Binário (0/1)

---

## ⏱️ Features agregadas por janela temporal

> Recomendado usar janelas de **1s, 5s ou 10s**

### `connect_rate`
- **Descrição**: Número de mensagens CONNECT por janela
- **Tipo**: Inteiro
- **Relevância**: Muito alta para DoS

### `publish_rate`
- **Descrição**: Número de mensagens PUBLISH por janela
- **Tipo**: Inteiro
- **Relevância**: Muito alta para DoS

### `subscribe_rate`
- **Descrição**: Número de mensagens SUBSCRIBE por janela
- **Tipo**: Inteiro

### `unique_topics_count`
- **Descrição**: Número de tópicos MQTT distintos
- **Tipo**: Inteiro

### `mean_packet_size`
- **Descrição**: Tamanho médio dos pacotes na janela
- **Tipo**: Numérico contínuo

### `std_packet_size`
- **Descrição**: Desvio padrão do tamanho dos pacotes
- **Tipo**: Numérico contínuo

---

## 🧠 Observações finais
- Nem todas as features precisam ser usadas simultaneamente
- Recomenda-se:
  - **Seleção de características**
  - **Normalização** (para SVM, KNN, MLP)
  - **Ablation study por grupo de features**
- Este dicionário é compatível com:
  - Random Forest
  - SVM
  - Logistic Regression
  - MLP
  - KNN

---
