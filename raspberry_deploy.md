# Guia de Deploy IoT: Modelos de DoS MQTT no Raspberry Pi

Este guia orienta o processo de implantação dos modelos de classificação de ataques DoS MQTT, treinados e otimizados (salvos em `models_optimized/`), em um Raspberry Pi. O foco principal é viabilizar inferência em tempo real e de baixo custo computacional (edge computing).

## 1. Instalação e Configuração Inicial do SO no Raspberry Pi

Para obter melhor desempenho na execução do Python e das bibliotecas de Machine Learning na arquitetura ARM, recomendamos o sistema operacional de 64 bits.

1. **Baixe o Raspberry Pi Imager:** Acesse o site oficial (https://www.raspberrypi.com/software/) e baixe a ferramenta.
2. **Escolha o Sistema Operacional:** Selecione **Raspberry Pi OS (64-bit)** (Recomendamos a versão *Lite* caso não precise de interface gráfica para economizar recursos).
3. **Configure SSH e Wi-Fi:** Nas opções avançadas (ícone da engrenagem) do Imager, ative o protocolo SSH, configure a senha do padrão do usuário `pi` e insira suas credenciais Wi-Fi.
4. **Grave no Cartão SD:** Insira um cartão MicroSD no computador e clique em *Gravar*.
5. **Primeiro Boot:** Insira o cartão no Raspberry Pi e ligue-o. Acesse-o via seu terminal SSH a partir da sua máquina:
   ```bash
   ssh pi@192.168.20.83
   ```
6. **Atualize o Sistema:**
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

## 2. Configuração do Ambiente Python e Dependências Pesadas

A instalação de bibliotecas como `scikit-learn`, `numpy` e `pandas` pode ser lenta no Raspberry Pi caso precisem ser compiladas a partir da fonte. A melhor abordagem é usar pacotes pré-compilados do repositório nativo ou baixar exclusivamente os pacotes otimizados para arquitetura ARM provenientes do `piwheels`.

1. **Instale o Python e ferramentas essenciais:**
   ```bash
   sudo apt install -y python3 python3-pip python3-venv
   ```
2. **Crie um Ambiente Virtual (Recomendado):**
   ```bash
   python3 -m venv ~/mqtt_env
   source ~/mqtt_env/bin/activate
   ```
3. **Instale as bibliotecas pesadas usando pacotes providos pelo PiWheels:**
   Quando usa o Pip no Raspberry Pi OS, ele naturalmente baixa as rodas (*wheels*) da plataforma nativa (muito mais rápido que compilar do zero). Instale-os com:
   ```bash
   pip install setuptools wheel numpy pandas scikit-learn joblib paho-mqtt
   ```
   *Alternativa (Sem venv): Em versões mais antigas usar o pacote dpkg pode ser necessário (`sudo apt install python3-numpy python3-sklearn python3-pandas`).*

## 3. Transferência dos Modelos para o Raspberry Pi

Os modelos salvos na pasta `models_optimized/` pelo script `main.py` (em formato `.joblib`) bem como o script de inferência precisam ser enviados para o Rapsberry Pi. Usaremos o utilitário `scp` (Secure Copy).

Na sua máquina local/desktop, rode:

```bash
# Crie o diretório de destino no Raspberry Pi via SSH:
ssh pi@192.168.20.83 "mkdir -p ~/mqtt_infer/models"

# Transfira o melhor modelo (ex: RandomForest otimizado)
scp models_optimized/RandomForest_optimized.joblib pi@192.168.20.83:~/mqtt_infer/models/

# Transfira o script de inferência modularizado
scp scripts/pi_inference.py pi@192.168.20.83:~/mqtt_infer/
```

## 4. Script Leve de Inferência em Tempo Real

No Raspberry Pi, CPU e RAM são recursos valiosos. O script `pi_inference.py` se conecta localmente (ou via cloud) aos tópicos de dados de um broker, captura o fluxo MQTT e aplica a predição no modelo sem bloquear a interface de rede principal (inferência sob demanda e ultraleve).

O script é executado assim (logado no Pi):

```bash
source ~/mqtt_env/bin/activate
cd ~/mqtt_infer
python pi_inference.py --model models/RandomForest_optimized.joblib --broker localhost --topic "sensor/#"
```
*(O código deste arquivo foi salvo dentro da pasta `scripts/` durante a refatoração.)*

## 5. Configuração do Serviço Systemd (Autostart Automático)

Para garantir que o script de detecção de ataque rode rodando como *daemon* em background e sobreviva a qualquer reinicialização na placa, configuraremos o **systemd**.

1. **Crie o arquivo de serviço para sua unidade:**
   ```bash
   sudo nano /etc/systemd/system/mqtt_infer.service
   ```

2. **Insira as diretivas a seguir:** *(Ajuste `User` ou os diretórios se tiver utilizado nomes diferentes)*

   ```ini
   [Unit]
   Description=MQTT DoS Inference Detector Service
   After=network.target

   [Service]
   Type=simple
   User=pi
   WorkingDirectory=/home/pi/mqtt_infer
   ExecStart=/home/pi/mqtt_env/bin/python /home/pi/mqtt_infer/pi_inference.py --model models/RandomForest_optimized.joblib --broker 127.0.0.1
   Restart=on-failure
   RestartSec=5
   StandardOutput=syslog
   StandardError=syslog
   SyslogIdentifier=mqtt_infer

   [Install]
   WantedBy=multi-user.target
   ```

3. **Recarregue o systemd, ative e inicie o serviço:**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable mqtt_infer.service
   sudo systemctl start mqtt_infer.service
   ```

4. **Monitore e valide se está operando normal:**
   ```bash
   journalctl -u mqtt_infer -f
   ```

Tudo pronto! Você refatorou com sucesso uma prova de conceito complexa em Jupyter e levou sua predição anti-DoS aos tráfegos de linha de frente utilizando princípios de Edge Computing e Machine Learning Ops.
