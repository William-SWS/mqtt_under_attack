import argparse
import joblib
import pandas as pd
import numpy as np
import time
import sys

try:
    import paho.mqtt.client as mqtt
except ImportError:
    print("Por favor, instale a biblioteca paho-mqtt: pip install paho-mqtt")
    sys.exit(1)

def on_connect(client, userdata, flags, rc):
    print(f"[*] Connected to broker with result code {rc}")
    client.subscribe(userdata['topic'])
    print(f"[*] Listening on topic {userdata['topic']}...")

def on_message(client, userdata, msg):
    # Resgata o modelo injetado via userdata do cliente MQTT
    model = userdata['model']
    
    # TODO (Custom Implementation):
    # Aqui o usuario de vera parsear os cabeçalhos/frames brutos da rede 
    # e converter na timeline/formato das features passadas no treino (como publish_gap).
    
    # MOCK (Dummy Payload): Simulando features de tamanho equivalente ao treinamento.
    # Evitamos quebrar substituindo dinamicamente pela interface do Scikit-Learn
    try:
        num_features = getattr(model, "n_features_in_", 78) # Tamanho generico fallback
        mock_features = np.zeros((1, num_features))
        
        # Realizando predicao leve (somente processamento matricial/arvore via CPU)
        start_time = time.time()
        prediction = model.predict(mock_features)
        latency = (time.time() - start_time) * 1000.0  # Em ms
        
        # Como as classes de trafego costumam ser inteiros: 0=Normal, etc.
        class_flag = "[NORMAL]" if prediction[0] == 0 else "[ATAQUE_IDENTIFICADO]"
        print(f"-> Predicao: {class_flag} | Topic: {msg.topic} | Latencia: {latency:.2f}ms")
        
    except Exception as e:
        print(f"Erro na inferencia do flow: {e}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Real-time MQTT DoS inference script for Edge/IoT Devices")
    parser.add_argument('--model', type=str, required=True, help="Path to the optimized joblib model file")
    parser.add_argument('--broker', type=str, default='127.0.0.1', help="MQTT Broker address (IP/Hostname)")
    parser.add_argument('--topic', type=str, default='#', help="MQTT Topic to monitor")
    parser.add_argument('--port', type=int, default=1883, help="MQTT Broker Port")
    
    args = parser.parse_args()
    
    print(f"[*] Loading model from disk: {args.model} ...")
    try:
        loaded_model = joblib.load(args.model)
        print("[+] Model loaded successfully.")
    except Exception as e:
        print(f"[-] Erro ao carregar o modelo: {e}")
        sys.exit(1)
    
    userdata = {
        'model': loaded_model,
        'topic': args.topic
    }
    
    # Compativel com paho-mqtt mais atual. Em versoes >= 2.0.0 CallbackAPIVersion pode ser necessario.
    # Instanciamos o client basico
    client = mqtt.Client(userdata=userdata)
    client.on_connect = on_connect
    client.on_message = on_message
    
    print(f"[*] Connecting to local broker -> {args.broker}:{args.port}")
    try:
        client.connect(args.broker, args.port, 60)
        client.loop_forever()
    except KeyboardInterrupt:
        print("\n[*] Script interrupted by user.")
        client.disconnect()
    except Exception as e:
        print(f"[-] Falha na conexao MQTT: {e}")
