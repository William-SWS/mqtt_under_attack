### 1. Variáveis de Rede (Prefixo `frame.`)

Estas variáveis não são exclusivas do MQTT; elas descrevem o pacote físico trafegando na rede. São geradas pelo analisador (Wireshark).

| **Variável**           | **Significado Detalhado**                                                                                                                                                                                     | Dtype   |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------- |
| **`frame.time_delta`** | O tempo (em segundos) que passou entre a captura do pacote _anterior_ e o pacote _atual_. **Importância:** Em ataques DoS, esse valor tende a ser muito próximo de zero (inundação de pacotes).               | float64 |
| **`frame.cap_len`**    | _Captured Length_. O tamanho do pacote que foi efetivamente capturado e salvo no disco. Às vezes, para economizar espaço, capturam-se apenas os primeiros bytes (slicing), mas aqui parece ser o pacote todo. | int64   |
| **`frame.len`**        | _Wire Length_. O tamanho real do pacote quando ele passou pelo cabo/rede. Geralmente é igual ao `cap_len`, a menos que o pacote tenha sido cortado na captura.                                                | int64   |

- **Fonte:** [Wireshark Display Filter Reference: Frame](https://www.wireshark.org/docs/dfref/f/frame.html)


### 2. Variáveis Gerais do Protocolo MQTT (Prefixo `mqtt.`)

Estas descrevem o cabeçalho fixo ou variáveis presentes na maioria dos pacotes MQTT.

| **Variável**         | **Significado Detalhado**                                                                                                                                                            | Dtype   |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------- |
| **`mqtt.msgtype`**   | O tipo da mensagem (Packet Type). É um número inteiro que diz o que o pacote está fazendo.<br><br>  <br><br>Exemplos: `1` = CONNECT, `3` = PUBLISH, `8` = SUBSCRIBE, `12` = PINGREQ. | float64 |
| **`mqtt.len`**       | O tamanho apenas da parte da mensagem MQTT (excluindo cabeçalhos TCP/IP e Ethernet). Diz quanto de dados úteis (payload) o MQTT está carregando.                                     | float64 |
| **`mqtt.ver`**       | A versão do protocolo MQTT. Geralmente `3` (v3.1) ou `4` (v3.1.1).                                                                                                                   | float64 |
| **`mqtt.proto_len`** | O comprimento do nome do protocolo. No MQTT v3.1.1, o nome é "MQTT", então esse valor costuma ser 4.                                                                                 |         |


### 3. Conexão e Autenticação (Pacote CONNECT)

Estas variáveis aparecem apenas quando um cliente tenta se conectar ao Broker (servidor). Note que no seu dataset elas têm poucos valores não-nulos (`281`), indicando que ocorreram 281 tentativas de conexão.

| **Variável**                 | **Significado Detalhado**                                                                                                                        |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| **`mqtt.clientid_len`**      | O tamanho (quantidade de caracteres) do ID do Cliente. IDs muito longos ou aleatórios podem indicar ferramentas de ataque automáticas.           |
| **`mqtt.kalive`**            | _Keep Alive_. O tempo (em segundos) que o cliente propõe ao servidor para manter a conexão aberta sem enviar dados. Se exceder, a conexão cai.   |
| **`mqtt.conflag.cleansess`** | _Clean Session Flag_. Se `1` (True), o cliente pede uma sessão nova ("esqueça o que eu fiz antes"). Se `0`, pede para retomar uma sessão antiga. |
| **`mqtt.conflag.passwd`**    | Flag que indica se o pacote contém uma senha (`1` = Sim, `0` = Não).                                                                             |
| **`mqtt.conflag.uname`**     | Flag que indica se o pacote contém um nome de usuário.                                                                                           |
| **`mqtt.conflag.willflag`**  | Indica se o cliente está configurando uma mensagem de "Last Will" (Última Vontade/Testamento) para ser enviada caso ele caia abruptamente.       |
| **`mqtt.conflag.qos`**       | Define a qualidade de serviço (QoS) com a qual a mensagem de "Last Will" deve ser enviada, se houver.                                            |
| **`mqtt.conflag.retain`**    | Define se a mensagem de "Last Will" deve ser retida (salva) pelo Broker.                                                                         |
| **`mqtt.conflag.reserved`**  | Um bit reservado no protocolo para uso futuro. Deve ser sempre `0`. Se for `1`, o pacote é inválido ou malformado (possível ataque).             |
| **`mqtt.username_len`**      | O tamanho do nome de usuário (se houver). No seu dataset está vazio (`0 non-null`), indicando que não houve envio de usuário.                    |
| **`mqtt.passwd_len`**        | O tamanho da senha. Também está vazio no seu dataset.                                                                                            |
| **`mqtt.willmsg_len`**       | Tamanho da mensagem de "Last Will". Vazio no seu dataset.                                                                                        |
| **`mqtt.willtopic_len`**     | Tamanho do tópico da mensagem de "Last Will". Vazio no seu dataset.                                                                              |
- **Fonte:** [OASIS MQTT v3.1.1 Spec - Section 3.1: CONNECT](https://www.google.com/search?q=http://docs.oasis-open.org/mqtt/mqtt/v3.1.1/os/mqtt-v3.1.1-os.html%23_Toc398718028)


### 4. Resposta de Conexão (Pacote CONNACK)

Variáveis enviadas do Servidor para o Cliente confirmando a conexão.

| **Variável**                     | **Significado Detalhado**                                                                                                                                                    |
| -------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **`mqtt.conack.val`**            | _Connect Return Code_. O resultado da conexão.<br><br>  <br><br>`0` = Conexão Aceita. Outros valores (1-5) indicam erros (ex: protocolo inaceitável, falha de autenticação). |
| **`mqtt.conack.flags.sp`**       | _Session Present_. Indica se o servidor já tinha uma sessão salva para esse cliente (`1`) ou se é uma nova (`0`).                                                            |
| **`mqtt.conack.flags.reserved`** | Bits reservados no pacote de resposta. Devem ser `0`.                                                                                                                        |



### 5. Publicação de Mensagens (Pacote PUBLISH)

Variáveis relacionadas ao envio de dados (sensores, comandos, ou ataques de inundação).

|**Variável**|**Significado Detalhado**|
|---|---|
|**`mqtt.topic_len`**|O tamanho (em bytes) do nome do Tópico (ex: "casa/sala/temp"). **Crítico:** Em ataques de _Buffer Overflow_, hackers enviam tópicos gigantescos para estourar a memória.|
|**`mqtt.msg`**|Geralmente refere-se ao _Message ID_ (Identificador do Pacote). Usado apenas em QoS 1 e 2 para rastrear confirmações.|
|**`mqtt.qos`**|_Quality of Service_ da mensagem atual.<br><br>  <br><br>`0` = Atire e esqueça (mais rápido, usado em ataques DoS).<br><br>  <br><br>`1` = Entregar pelo menos uma vez.<br><br>  <br><br>`2` = Entregar exatamente uma vez.|
|**`mqtt.dupflag`**|_Duplicate Flag_. Se `1`, indica que é uma retransmissão de uma mensagem anterior. Ataques podem ter muitas duplicatas devido ao congestionamento que eles mesmos causam.|
|**`mqtt.retain`**|_Retain Flag_. Se `1`, o Broker deve salvar essa mensagem como a "última válida" para novos assinantes.|
- **Fonte:** [OASIS MQTT v3.1.1 Spec - Section 3.3: PUBLISH](https://www.google.com/search?q=http://docs.oasis-open.org/mqtt/mqtt/v3.1.1/os/mqtt-v3.1.1-os.html%23_Toc398718037)



### 6. Assinatura (Pacotes SUBSCRIBE / SUBACK)
| **Variável**          | **Significado Detalhado**                                                                                              |
| --------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| **`mqtt.sub.qos`**    | O nível de QoS máximo que o cliente está solicitando ao assinar um tópico.                                             |
| **`mqtt.suback.qos`** | O nível de QoS que o servidor _concedeu_ ao cliente (pode ser menor ou igual ao solicitado, ou `128` indicando falha). |




# Resultado do df.info()

![[Pasted image 20260128152119.png]]