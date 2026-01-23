# 📚 Dicionário de Dados - MQTT_UAD

Este dicionário descreve as variáveis utilizadas na análise de detecção de ataques DoS em redes MQTT.

| Variável | Tipo | Descrição Técnica |
| :--- | :--- | :--- |
| `frame.time_delta` | Float | Tempo entre o pacote atual e o anterior (segundos). |
| `frame.len` | Int | Tamanho total do quadro em bytes. |
| `mqtt.msgtype` | Int | Tipo de mensagem (ex: 1=CONNECT, 3=PUBLISH). |
| `mqtt.topic_len` | Int | Comprimento do nome do tópico utilizado. |
| `Label` | String/Int | Classe do tráfego: `normal` ou `DoS`. |