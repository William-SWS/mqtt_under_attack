Getting started
===============

## Configuração do `DATA_DIR` via `.env`

Os caminhos de dados deste projeto são centralizados na variável de ambiente **`DATA_DIR`**, lida a partir do arquivo `.env` na raiz do repositório.

1. Copie o arquivo de exemplo:
   - `cp .env.example .env`
2. Edite o arquivo `.env` e defina o caminho da pasta de dados:
   - Exemplo (dados dentro do próprio repositório):  
     `DATA_DIR=data`
   - Exemplo (dados em outro diretório do sistema):  
     `DATA_DIR=/caminho/completo/para/sua/pasta/data`
3. Se `DATA_DIR` **não** for definido, o projeto usa automaticamente `PROJ_ROOT/data` como pasta padrão.

Internamente, o módulo `mqtt_under_attack.config` carrega esta variável:

```python
from mqtt_under_attack.config import DATA_DIR, RAW_DATA_DIR, PROCESSED_DATA_DIR
```

Assim, qualquer script ou notebook pode construir caminhos de forma portátil, sem precisar alterar manualmente caminhos específicos de cada máquina.

## Importando dados a partir do `DATA_DIR`

### Em scripts Python

Exemplo de leitura de um CSV armazenado em `RAW_DATA_DIR`:

```python
import pandas as pd
from mqtt_under_attack.config import RAW_DATA_DIR

csv_path = RAW_DATA_DIR / "MQTT Under Attack Dataset" / "DoS.csv"
df = pd.read_csv(csv_path)
```

Como `RAW_DATA_DIR` é derivado de `DATA_DIR`, basta garantir que o `.env` está configurado corretamente; o mesmo código funcionará em máquinas diferentes.

### Em notebooks Jupyter

Dentro de um notebook, o padrão é o mesmo:

```python
import pandas as pd
from mqtt_under_attack.config import RAW_DATA_DIR, PROCESSED_DATA_DIR

dos_path = RAW_DATA_DIR / "MQTT Under Attack Dataset" / "DoS.csv"
df_dos = pd.read_csv(dos_path)
```

Se você mover a pasta de dados ou trabalhar em outra máquina, apenas atualize o `DATA_DIR` no `.env` — o código dos notebooks e scripts continua idêntico.
