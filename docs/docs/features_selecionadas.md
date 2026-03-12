### `frame.cap_len` 
- **Descrição**: Tamanho do frame capturado em bytes
- **Tipo**: Inteiro (int64)

### `frame.len` 
- **Descrição**: Tamanho total do frame em bytes
- **Tipo**: Inteiro (int64)

### `mqtt.conack.flags.reserved` 
- **Descrição**: Bits reservados no CONNACK flags
- **Tipo**: Inteiro (int64)
- **Observação**: Deve ser sempre 0 em tráfego normal


### `mqtt.qos` 
- **Descrição**: Quality of Service da mensagem MQTT
- **Tipo**: Inteiro (int64)
- **Valores**: 0 (At most once), 1 (At least once), 2 (Exactly once)

### `mqtt.msgtype` 
- **Descrição**: Tipo da mensagem MQTT
- **Tipo**: Inteiro (int64) - códigos numéricos
- **Valores**: 1=CONNECT, 2=CONNACK, 3=PUBLISH, 4=PUBACK, 8=SUBSCRIBE, etc.