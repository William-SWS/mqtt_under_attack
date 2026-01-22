# MQTT Under Attack documentation!

## Description

Análise exploratória utilizando o dataset

## Observação de licença de uso

Esse projeto 


## Features primariamente selecionadas para a análise

Index(['frame.time_delta', 
'frame.cap_len',
 'frame.len', 
 'mqtt.clientid_len',
'mqtt.conack.flags.reserved',
'mqtt.conack.flags.sp',
'mqtt.conack.val',
       'mqtt.conflag.cleansess',
        'mqtt.conflag.passwd', 
        'mqtt.conflag.qos',
       'mqtt.conflag.reserved', 
       'mqtt.conflag.retain',
        'mqtt.conflag.uname',
       'mqtt.conflag.willflag', 
       'mqtt.dupflag',
        'mqtt.kalive', 
        'mqtt.len',
       'mqtt.msgtype', 
       'mqtt.passwd_len', 
       'mqtt.proto_len', 
       'mqtt.qos',
       'mqtt.retain', 
       'mqtt.sub.qos',
        'mqtt.suback.qos', 
        'mqtt.topic_len',
       'mqtt.username_len', 
       'mqtt.ver',
        'mqtt.willmsg_len',
       'mqtt.willtopic_len'],
      dtype='object')


### O que levou a retirar as outras features

- Serem metadados do wireshark
- Identificadores categóricos
- Conteúdo textual