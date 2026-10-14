# 02. Carga e limpeza dos dados

## Objetivos desta aula

Ao final desta aula você vai entender:

- o critério da **limpeza orientada à implantação**: por que cada grupo de colunas sai antes do treino;
- o que significa a **ausência estrutural** de valores nos campos MQTT, e o que ela revela sobre as classes;
- como emitir e testar **avisos** quando o código encontra algo inesperado, mas não fatal.

E vai ter construído:

- o módulo `mqtt_dos.data`, com `load_raw` e `drop_unused_columns`;
- 4 testes da limpeza com dados sintéticos;
- a seção 1 do notebook: formato, classes e nulos por coluna e por classe.

**Vitória da aula:** no notebook, `drop_unused_columns(load_raw()).shape` devolve `(94625, 21)`, ou seja, as 20
preditoras da Tabela I do paper mais o rótulo, e a tabela de nulos por classe aparece logo abaixo.

## Onde estamos

O ticket 01 ([aulas 01-1 a 01-3](01-3-ruff-e-notebook.md)) montou o ambiente, o pacote `mqtt_dos` com o
`RunConfig` e o notebook de narrativa com o teste que o executa. Esta é a primeira aula do pipeline: dados
brutos → tabela limpa. A aula 03 acrescenta os gaps de publish e connect.

### Relembrando

??? question "1. Onde mora o caminho do CSV bruto, e por que ele é calculado a partir de `__file__`?"

    Em `RAW_DATA_PATH`, no `config.py`. Partir de `__file__` dá um caminho estável, que não depende da pasta
    de onde você roda o notebook ou os testes.

??? question "2. Você adicionou uma função nova ao pacote e o notebook diz que ela não existe. O que verificar primeiro?"

    Se o kernel foi reiniciado. A instalação editável faz o arquivo novo valer na hora, mas um kernel que já
    importou o módulo continua com a versão antiga na memória (veja Erros comuns).

## Antes de começar

```bash title="$ Execução no terminal (na pasta do projeto)"
uv run pytest
uv run ruff check
```

Os 9 testes do ticket 01 precisam passar. Nenhuma ferramenta nova: o pandas foi instalado na aula 01-1.

## Conceitos

### Limpeza orientada à implantação

A **[limpeza](glossario.md#limpeza-orientada-a-implantacao)** decide quais colunas do CSV do Wireshark
chegam ao modelo. O critério não é estatístico, e sim de implantação: só fica o que **generaliza** para
tráfego novo e **existe** quando o modelo roda no Raspberry Pi. São 46 colunas removidas, em quatro grupos:

| Grupo | Exemplos | Por que sai |
|---|---|---|
| Metadados do frame (19) | `frame.number`, `frame.md5_hash`, `frame.time_epoch` | identificadores memorizam pacotes; timestamps absolutos dizem *quando* a captura foi feita, não *como* é o tráfego; o resto é artefato de análise do Wireshark |
| Endereços IP e MAC (4) | `ip.src`, `eth.dst` | identificam as máquinas do testbed, não o ataque |
| Portas TCP (2) | `tcp.srcport` | efêmeras, dependem da sessão |
| Campos MQTT textuais, de sessão, compostos ou quase vazios (21) | `mqtt.clientid`, `mqtt.passwd`, `mqtt.hdrflags`, `mqtt.ver` | texto de sessão e de payload (e questão de privacidade); `hdrflags` é um campo de bits já decomposto em `msgtype`, `qos` e `retain` |

Os dados confirmam boa parte da lista: 19 das 46 colunas estão **inteiramente vazias** no dataset, e outras
10 têm um único valor. Colunas assim não carregam informação nenhuma.

Analogia: antes de padronizar um protocolo de laboratório, você tira dele tudo o que só existe na bancada
original, como o número de série do equipamento e a hora em que cada amostra foi pesada.

O problema que resolve: um modelo treinado com `ip.src` acertaria muito no teste, porque as máquinas do
ataque são as mesmas nas duas partições, e falharia em qualquer outra rede. É vazamento por identificador.

!!! note "Uma coluna que não cabe bem na justificativa"

    `mqtt.dupflag` está no grupo dos "quase vazios", mas tem 59,4% de nulos, a mesma taxa de `mqtt.qos`,
    que fica. A lista é mantida como está para reproduzir os 20 atributos da Tabela I do paper. Se você
    quiser rever essa escolha, é uma decisão de pesquisa, e entra no log de decisões.

Fonte: o próprio paper (*Deployment-Aware Machine Learning for DoS Detection in Edge-Based IoT Networks*,
seção III, que descreve as 46 colunas removidas e a Tabela I das 20 que ficam).

### Ausência estrutural de valores

Um valor ausente (`NaN`) nem sempre é um defeito de captura. Aqui ele quase sempre é **estrutural**: o campo
não existe naquele pacote. `mqtt.kalive` só existe em mensagens CONNECT; `mqtt.msgtype` só existe em pacotes
MQTT. Um ACK de TCP não tem tipo de mensagem MQTT. O pandas marca isso com `NaN`, e você detecta com
`isna()`. A média de um `isna()` é a proporção de nulos.

Analogia: um questionário com perguntas condicionais. "Idade do primeiro filho" em branco não é um erro de
quem respondeu, é informação: a pessoa não tem filhos.

Por que importa para o projeto: é isso que justifica a imputação **constante 0**, ajustada só no treino (aula
04), em vez da mediana. Preencher `mqtt.kalive` de um pacote que não é CONNECT com a mediana dos CONNECTs
inventaria um valor que não existe; com 0 o modelo continua sabendo que "o campo não estava lá".

E há um achado que só aparece quando você separa os nulos **por classe**:

| | DoS | normal |
|---|---|---|
| pacotes sem `mqtt.msgtype` (não MQTT) | 14,2% | 99,0% |

Quase todo o tráfego `normal` do dataset não é MQTT, enquanto 86% do `DoS` é. Um modelo pode aprender boa
parte da separação só a partir de "este pacote é MQTT?".

!!! warning "Uma pergunta de pesquisa, não um erro do código"

    Este curso não muda o escopo do paper. O achado fica registrado como pendência para você, como autora,
    decidir se merece uma discussão no texto ou um experimento à parte. É o tipo de coisa que um revisor
    pergunta.

Fonte: [pandas — Working with missing data](https://pandas.pydata.org/docs/user_guide/missing_data.html)
("To detect these missing value, use the `isna()` or `notna()` methods").

### Avisos

Um **[aviso](glossario.md#aviso)** (`warnings.warn`) avisa sobre algo inesperado sem interromper o programa.
É diferente de um erro (`raise`), que para tudo. A categoria padrão é `UserWarning`. Com `stacklevel=2`, a
mensagem aponta para a linha de quem **chamou** a função, que é onde o problema está. No teste,
`pytest.warns` funciona como o `pytest.raises` da aula 01-2: o teste falha se o aviso **não** aparecer.

Analogia: o alarme de "porta aberta" da geladeira. Não desliga o aparelho, mas você fica sabendo.

O problema que resolve: o ticket pede que a limpeza aceite um CSV sem alguma das 46 colunas (outra versão do
dataset, por exemplo). Ignorar em silêncio esconderia uma diferença entre datasets; parar com erro impediria
trabalhar com eles. O aviso fica no meio.

Fontes: [Python — warnings](https://docs.python.org/3/library/warnings.html);
[pytest — How to capture warnings](https://docs.pytest.org/en/stable/how-to/capture-warnings.html).

## Ponte teoria → projeto

O ticket [02](issues/02-carga-e-limpeza.md) pede a carga (94.625 × 67), a limpeza para 20 preditoras mais
`type`, a tolerância a colunas ausentes com aviso, testes sintéticos e, no notebook, classes e nulos. A
decisão 1 (imputação constante 0 dentro do Pipeline) e a decisão 2 (gaps sem `type`) do
[log de decisões](decisions.md) dependem do que esta aula mostra sobre os nulos.

Para a sua missão: a limpeza é a primeira escolha metodológica do paper, e esta aula põe por escrito, no
código, o porquê de cada coluna sair.

## Mão na massa

### Passo 1 — O módulo e a lista de colunas

Crie `src/mqtt_dos/data.py`. O começo traz os imports e o nome do rótulo:

```python title="src/mqtt_dos/data.py" linenums="1"
"""Carga e limpeza do dataset bruto de DoS."""

from pathlib import Path
import warnings

import pandas as pd

from mqtt_dos.config import RAW_DATA_PATH

TARGET_COLUMN = "type"  # (1)!
```

1.  O nome do rótulo aparece em vários módulos (limpeza, split, gaps). Uma constante evita que um `"Type"`
    digitado errado em algum lugar passe despercebido.

Logo abaixo vem a tupla `DROP_COLUMNS`, com as 46 colunas nos quatro grupos da tabela da seção Conceitos.
**Essa lista é dado, não lógica:** digitá-la à mão não ensina nada e convida erros de digitação. Copie-a do
bloco "Arquivo completo: src/mqtt_dos/data.py" no fim da aula (é a mesma lista do `04_pipeline.ipynb`). O
formato dela é este:

```python title="src/mqtt_dos/data.py (formato de DROP_COLUMNS)" linenums="12"
DROP_COLUMNS = (
    # Metadados do frame: timestamps absolutos, identificadores e artefatos do Wireshark  # (1)!
    "frame.time_delta_displayed",
    "frame.time_epoch",
    # ... as outras 17 colunas frame.* ...
    # Endereços IP e MAC: identificam máquinas, não padrões de tráfego
    "ip.src",
    # ... ip.dst, eth.src, eth.dst, depois as portas e os campos MQTT ...
)
```

1.  Um comentário por grupo deixa a justificativa no próprio código. Quem ler daqui a um ano não precisa
    procurar no paper por que `ip.src` saiu.

??? question "Pare e pense: `frame.time_epoch` está na lista. A aula 03 precisa dele para calcular os gaps. Como as duas coisas convivem?"

    Os gaps são calculados **antes** da limpeza, sobre a tabela bruta, e só depois o `frame.time_epoch` é
    descartado. O notebook antigo resolvia isso lendo o CSV duas vezes; aqui vai ser uma sequência
    `load_raw → add_gaps → drop_unused_columns`.

### Passo 2 — Carregar o CSV

No fim do arquivo, depois da tupla:

```python title="src/mqtt_dos/data.py (continuação)" linenums="66"
def load_raw(path: Path = RAW_DATA_PATH) -> pd.DataFrame:  # (1)!
    """Lê o CSV bruto exportado do Wireshark."""
    return pd.read_csv(path, low_memory=False)  # (2)!
```

1.  O caminho padrão é o do dataset real, mas os testes podem passar outro arquivo.
2.  Com o padrão `low_memory=True`, o pandas lê o arquivo em pedaços e pode inferir tipos diferentes para a
    mesma coluna em pedaços diferentes. Cinco colunas textuais do CSV (`mqtt.clientid`, `mqtt.msg`, ...)
    caem nisso e geram um `DtypeWarning` (veja Erros comuns). `False` lê tudo antes de decidir o tipo.

### Passo 3 — Limpar com aviso

```python title="src/mqtt_dos/data.py (continuação)" linenums="71"
def drop_unused_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Remove as colunas que não generalizam ou não existem em produção."""
    missing = [column for column in DROP_COLUMNS if column not in df.columns]
    if missing:
        warnings.warn(f"colunas ausentes ignoradas na limpeza: {missing}", stacklevel=2)  # (1)!
    present = [column for column in DROP_COLUMNS if column in df.columns]
    return df.drop(columns=present)  # (2)!
```

1.  A mensagem lista as colunas que faltaram, para que um dataset diferente seja notado na hora.
    `stacklevel=2` faz o aviso apontar para a linha que chamou `drop_unused_columns`.
2.  `drop` devolve um DataFrame **novo** e não altera o original. O `errors="ignore"` do pandas também
    aceitaria colunas ausentes, mas sem avisar; por isso filtramos as presentes à mão.

### Passo 4 — A seção 1 do notebook

Abra o `notebooks/training.ipynb` e reinicie o kernel (o módulo `data` é novo). Troque o texto da célula
`## 1. Dados brutos` por:

```markdown title="notebooks/training.ipynb — célula Markdown da seção 1"
## 1. Dados brutos

O CSV exportado do Wireshark tem 94.625 pacotes e 67 colunas. A limpeza remove as 46 colunas que não generalizam ou não existem em produção e deixa 20 preditoras mais o rótulo `type`.
```

Logo abaixo dela, crie estas células de código:

```python title="notebooks/training.ipynb — carga" linenums="1"
from mqtt_dos.data import TARGET_COLUMN, drop_unused_columns, load_raw

raw = load_raw()
raw.shape
```

```text title="Saída esperada"
(94625, 67)
```

```python title="notebooks/training.ipynb — classes" linenums="1"
raw[TARGET_COLUMN].value_counts()
```

```text title="Saída esperada"
type
normal    49111
DoS       45514
Name: count, dtype: int64
```

```python title="notebooks/training.ipynb — limpeza" linenums="1"
clean = drop_unused_columns(raw)
clean.shape
```

```text title="Saída esperada"
(94625, 21)
```

**O que aconteceu:** os números da seção III do paper (94.625 registros, 67 colunas, 49.111 normal e 45.514
DoS, 20 preditoras) saíram do código, não de uma tabela digitada.

Agora os nulos por coluna:

```python title="notebooks/training.ipynb — nulos por coluna" linenums="1"
null_percent = clean.isna().mean().mul(100).round(1)  # (1)!
null_percent.sort_values(ascending=False).to_frame("null_percent")
```

1.  `isna()` vira uma tabela de `True`/`False`; a média de cada coluna é a fração de `True`.

```text title="Saída esperada (trecho)"
                            null_percent
mqtt.clientid_len                   99.7
mqtt.conflag.qos                    99.7
...
mqtt.conack.val                     99.2
...
mqtt.retain                         59.4
mqtt.qos                            59.4
mqtt.topic_len                      59.3
mqtt.msgtype                        58.2
mqtt.len                            58.2
frame.cap_len                        0.0
frame.len                            0.0
frame.time_delta                     0.0
type                                 0.0
```

??? question "Pare e pense: 58,2% dos pacotes não têm `mqtt.msgtype`. Você espera essa taxa igual nas duas classes?"

    Não, e a diferença é enorme: 14,2% no DoS contra 99,0% no normal. A próxima célula mostra isso.

Uma célula Markdown explicando o que vem a seguir:

```markdown title="notebooks/training.ipynb — célula Markdown"
Os nulos não são falhas de captura: um campo MQTT fica vazio quando o pacote não é MQTT, ou quando aquele tipo de mensagem não tem o campo. Vale olhar a proporção por classe.
```

E os nulos por classe:

```python title="notebooks/training.ipynb — nulos por classe" linenums="1"
predictors = clean.drop(columns=TARGET_COLUMN)
predictors.isna().groupby(clean[TARGET_COLUMN]).mean().mul(100).round(1).T  # (1)!
```

1.  Agrupa a tabela de nulos pelo rótulo e tira a média em cada grupo. O `.T` transpõe o resultado para
    ficar uma linha por coluna, que é mais fácil de ler.

```text title="Saída esperada (trecho)"
type                         DoS  normal
frame.time_delta             0.0     0.0
frame.cap_len                0.0     0.0
frame.len                    0.0     0.0
mqtt.clientid_len           99.3   100.0
...
mqtt.kalive                 99.3   100.0
mqtt.len                    14.2    99.0
mqtt.msgtype                14.2    99.0
mqtt.qos                    16.0    99.5
mqtt.retain                 16.0    99.5
mqtt.topic_len              16.0    99.5
```

**O que aconteceu:** é a tabela da seção Conceitos, gerada pelo seu código. Rode o notebook inteiro (Run
All) para conferir que tudo funciona na ordem.

## Testando

Crie `tests/test_data.py`. Os testes usam DataFrames pequenos, montados no próprio teste, sem depender do
CSV real:

```python title="tests/test_data.py" linenums="1"
import pandas as pd
import pytest

from mqtt_dos.data import DROP_COLUMNS, TARGET_COLUMN, drop_unused_columns


def make_frame(columns):  # (1)!
    return pd.DataFrame({column: [1.0, 2.0] for column in columns})


def test_drop_columns_has_46_unique_names():
    assert len(DROP_COLUMNS) == 46
    assert len(set(DROP_COLUMNS)) == 46  # (2)!
```

1.  Uma função auxiliar (sem o prefixo `test_`, então o pytest não a roda como teste) que cria um DataFrame
    com as colunas pedidas e duas linhas quaisquer. Os valores não importam: a limpeza só olha os nomes.
2.  Se uma coluna for colada duas vezes na lista, o `set` fica menor que a tupla e o teste acusa.

```python title="tests/test_data.py (continuação)" linenums="16"
def test_drop_removes_listed_columns_and_keeps_the_rest():
    raw = make_frame([*DROP_COLUMNS, "frame.len", "mqtt.msgtype", TARGET_COLUMN])  # (1)!

    clean = drop_unused_columns(raw)

    assert list(clean.columns) == ["frame.len", "mqtt.msgtype", TARGET_COLUMN]


def test_drop_does_not_change_the_input():
    raw = make_frame([*DROP_COLUMNS, "frame.len"])

    drop_unused_columns(raw)

    assert len(raw.columns) == 47  # (2)!
```

1.  `*DROP_COLUMNS` "desempacota" a tupla dentro da lista: as 46 colunas mais três que devem sobreviver.
2.  O original continua com as 47 colunas. Se a função usasse `inplace=True`, a tabela bruta do notebook
    perderia colunas sem você perceber.

```python title="tests/test_data.py (continuação)" linenums="32"
def test_missing_columns_are_ignored_with_a_warning():
    raw = make_frame(["frame.number", "frame.len"])

    with pytest.warns(UserWarning, match="frame.time_epoch"):  # (1)!
        clean = drop_unused_columns(raw)

    assert list(clean.columns) == ["frame.len"]
```

1.  O DataFrame tem só uma das 46 colunas; o aviso deve aparecer e citar uma das que faltam. Fora do aviso,
    a limpeza ainda remove a que existe.

```bash title="$ Execução no terminal (na pasta do projeto)"
uv run pytest tests/test_data.py -v
```

```text title="Saída esperada (trecho)"
tests/test_data.py::test_drop_columns_has_46_unique_names PASSED         [ 25%]
tests/test_data.py::test_drop_removes_listed_columns_and_keeps_the_rest PASSED [ 50%]
tests/test_data.py::test_drop_does_not_change_the_input PASSED           [ 75%]
tests/test_data.py::test_missing_columns_are_ignored_with_a_warning PASSED [100%]

============================== 4 passed in 0.79s ===============================
```

E a verificação completa:

```bash title="$ Execução no terminal (na pasta do projeto)"
uv run pytest
uv run ruff check
uv run ruff format --check
```

```text title="Saída esperada (o tempo varia)"
13 passed in 4.30s
All checks passed!
7 files already formatted
```

**Como ler:** 9 testes do ticket 01 mais 4 novos. O tempo subiu porque agora o teste do notebook lê o CSV
real de 94 mil linhas.

## Erros comuns

**1. Ler o CSV sem `low_memory=False`:**

```text
DtypeWarning: Columns (28: mqtt.clientid, 30: mqtt.conack.flags, 41: mqtt.conflags, 46: mqtt.msg, 52: mqtt.protoname) have mixed types. Specify dtype option on import or set low_memory=False.
```

Causa: a leitura em pedaços deu tipos diferentes para essas colunas. Todas elas são removidas na limpeza,
mas o aviso polui o notebook e esconde avisos que importam. Correção: passo 2.

**2. Remover uma coluna que não existe sem filtrar antes:**

```text
KeyError: "['frame.number'] not found in axis"
```

Causa: o `drop` do pandas, por padrão, exige que todas as colunas existam. Correção: filtrar as presentes,
como no passo 3.

**3. Um `pytest.warns` que espera um aviso que não vem.** Se todas as 46 colunas existirem, não há aviso:

```text
E       Failed: DID NOT WARN. No warnings of type (<class 'UserWarning'>,) were emitted.
E        Emitted warnings: [].
```

Correção: o teste precisa montar um DataFrame em que de fato falte alguma coluna.

**4. Kernel desatualizado no notebook.** Você editou `data.py`, mas o kernel já tinha importado o módulo:

```text
ImportError: cannot import name 'predictor_columns' from 'mqtt_dos.data' (.../src/mqtt_dos/data.py)
```

Causa: o Python importa cada módulo uma vez por processo. Correção: **Restart** do kernel e Run All. O
`uv run pytest` não tem esse problema, porque cada execução começa um processo novo.

## Código completo desta aula

??? example "Arquivo completo: src/mqtt_dos/data.py"

    ```python
    """Carga e limpeza do dataset bruto de DoS."""

    from pathlib import Path
    import warnings

    import pandas as pd

    from mqtt_dos.config import RAW_DATA_PATH

    TARGET_COLUMN = "type"

    DROP_COLUMNS = (
        # Metadados do frame: timestamps absolutos, identificadores e artefatos do Wireshark
        "frame.time_delta_displayed",
        "frame.time_epoch",
        "frame.time_invalid",
        "frame.time_relative",
        "frame.coloring_rule.name",
        "frame.coloring_rule.string",
        "frame.comment",
        "frame.comment.expert",
        "frame.encap_type",
        "frame.file_off",
        "frame.ignored",
        "frame.incomplete",
        "frame.interface_id",
        "frame.interface_name",
        "frame.link_nr",
        "frame.marked",
        "frame.md5_hash",
        "frame.number",
        "frame.offset_shift",
        # Endereços IP e MAC: identificam máquinas, não padrões de tráfego
        "ip.src",
        "ip.dst",
        "eth.src",
        "eth.dst",
        # Portas TCP
        "tcp.srcport",
        "tcp.dstport",
        # Campos MQTT textuais, de sessão, compostos ou quase vazios
        "mqtt.clientid",
        "mqtt.conack.flags",
        "mqtt.conflags",
        "mqtt.dupflag",
        "mqtt.hdrflags",
        "mqtt.msg",
        "mqtt.msgid",
        "mqtt.passwd",
        "mqtt.passwd_len",
        "mqtt.proto_len",
        "mqtt.protoname",
        "mqtt.sub.qos",
        "mqtt.suback.qos",
        "mqtt.topic",
        "mqtt.username",
        "mqtt.username_len",
        "mqtt.ver",
        "mqtt.willmsg",
        "mqtt.willmsg_len",
        "mqtt.willtopic",
        "mqtt.willtopic_len",
    )


    def load_raw(path: Path = RAW_DATA_PATH) -> pd.DataFrame:
        """Lê o CSV bruto exportado do Wireshark."""
        return pd.read_csv(path, low_memory=False)


    def drop_unused_columns(df: pd.DataFrame) -> pd.DataFrame:
        """Remove as colunas que não generalizam ou não existem em produção."""
        missing = [column for column in DROP_COLUMNS if column not in df.columns]
        if missing:
            warnings.warn(f"colunas ausentes ignoradas na limpeza: {missing}", stacklevel=2)
        present = [column for column in DROP_COLUMNS if column in df.columns]
        return df.drop(columns=present)
    ```

??? example "Arquivo completo: tests/test_data.py"

    ```python
    import pandas as pd
    import pytest

    from mqtt_dos.data import DROP_COLUMNS, TARGET_COLUMN, drop_unused_columns


    def make_frame(columns):
        return pd.DataFrame({column: [1.0, 2.0] for column in columns})


    def test_drop_columns_has_46_unique_names():
        assert len(DROP_COLUMNS) == 46
        assert len(set(DROP_COLUMNS)) == 46


    def test_drop_removes_listed_columns_and_keeps_the_rest():
        raw = make_frame([*DROP_COLUMNS, "frame.len", "mqtt.msgtype", TARGET_COLUMN])

        clean = drop_unused_columns(raw)

        assert list(clean.columns) == ["frame.len", "mqtt.msgtype", TARGET_COLUMN]


    def test_drop_does_not_change_the_input():
        raw = make_frame([*DROP_COLUMNS, "frame.len"])

        drop_unused_columns(raw)

        assert len(raw.columns) == 47


    def test_missing_columns_are_ignored_with_a_warning():
        raw = make_frame(["frame.number", "frame.len"])

        with pytest.warns(UserWarning, match="frame.time_epoch"):
            clean = drop_unused_columns(raw)

        assert list(clean.columns) == ["frame.len"]
    ```

As células do notebook estão no passo 4.

## Exercícios

1. **Só as preditoras.** As aulas 04 a 07 vão precisar da lista de colunas preditoras (tudo menos `type`)
   muitas vezes. Crie `predictor_columns(df)` em `data.py`, preservando a ordem do DataFrame. Está pronto
   quando este teste passar:

    ```python title="tests/test_exercicio_02.py"
    import pandas as pd

    from mqtt_dos.data import TARGET_COLUMN, predictor_columns


    def test_predictor_columns_excludes_the_target():
        clean = pd.DataFrame({"frame.len": [60], TARGET_COLUMN: ["normal"], "mqtt.qos": [0.0]})

        assert predictor_columns(clean) == ["frame.len", "mqtt.qos"]
    ```

    ```text title="Saída esperada (antes)"
    E   ImportError: cannot import name 'predictor_columns' from 'mqtt_dos.data' (.../src/mqtt_dos/data.py)
    !!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
    ```

    Repare: não é uma falha de teste, é um **erro de coleta**. O pytest nem conseguiu importar o arquivo.

??? tip "Solução"

    ```python title="src/mqtt_dos/data.py (no fim)"
    def predictor_columns(df: pd.DataFrame) -> list[str]:
        """Nomes das colunas preditoras, na ordem do DataFrame."""
        return [column for column in df.columns if column != TARGET_COLUMN]
    ```

    Depois: `1 passed`.

2. **Uma redundância que nenhum nulo mostra.** No notebook, descubra em que fração das linhas
   `frame.cap_len` é igual a `frame.len`. Antes de rodar, escreva seu palpite. O que esse resultado significa
   para os seletores da aula 06?

??? tip "Solução"

    ```python title="notebooks/training.ipynb"
    (clean["frame.cap_len"] == clean["frame.len"]).mean()
    ```

    ```text title="Saída esperada"
    1.0
    ```

    As duas colunas são idênticas em 100% dos pacotes: o Wireshark capturou cada pacote inteiro, então o
    tamanho capturado é o tamanho real. Uma é cópia da outra. O LowVariance mede a variância de cada coluna
    **isoladamente**, então mantém as duas. Guarde isso para a aula 06.

3. **Leitura parcial para testes rápidos** (combina com o `tmp_path` do pytest). Faça `load_raw` aceitar
   `nrows`, para ler só as primeiras linhas. O teste abaixo usa o `tmp_path`, uma pasta temporária nova que o
   pytest cria para cada teste quando você pede um argumento com esse nome. Acrescente ao arquivo do exercício
   (e inclua `load_raw` no import):

    ```python title="tests/test_exercicio_02.py (acrescentar)"
    def test_load_raw_reads_only_the_first_rows(tmp_path):
        csv_path = tmp_path / "mini.csv"
        csv_path.write_text("frame.len,type\n60,normal\n1514,DoS\n77,DoS\n")

        raw = load_raw(csv_path, nrows=2)

        assert raw["frame.len"].tolist() == [60, 1514]
    ```

    ```text title="Saída esperada (antes)"
    E       TypeError: load_raw() got an unexpected keyword argument 'nrows'
    ========================= 1 failed, 1 passed in 0.22s ==========================
    ```

??? tip "Solução"

    ```python title="src/mqtt_dos/data.py"
    def load_raw(path: Path = RAW_DATA_PATH, nrows: int | None = None) -> pd.DataFrame:
        """Lê o CSV bruto exportado do Wireshark."""
        return pd.read_csv(path, low_memory=False, nrows=nrows)
    ```

    `int | None = None` quer dizer "um inteiro ou nada"; com `None`, o `read_csv` lê o arquivo inteiro, então
    o comportamento padrão não muda. Depois: `2 passed`.

## Quiz de fixação

??? question "1. Com suas palavras: por que `ip.src` sai, mesmo que provavelmente aumente a acurácia no teste?"

    Porque o modelo aprenderia *quais máquinas* atacam no testbed, não *como* é um ataque. As mesmas máquinas
    estão no treino e no teste, então a acurácia sobe, mas o modelo falha em qualquer outra rede. É vazamento
    por identificador, e o critério da limpeza é o que existe e generaliza em produção.

??? question "2. Por que a imputação com a mediana faria pouco sentido para `mqtt.kalive`?"

    Porque o nulo é estrutural: o campo não existe em pacotes que não são CONNECT. A mediana dos CONNECTs
    atribuiria um keep-alive a pacotes que não têm keep-alive. Com 0, o "não estava lá" continua visível para
    o modelo. É o que o histórico do projeto já mostrava: a mediana derrubava LDA e QDA.

**3. A limpeza recebe um CSV sem `frame.md5_hash`. O que acontece?**

- a) A função para com um `KeyError`
- b) A coluna é ignorada com um aviso
- c) A coluna é ignorada em silêncio

??? question "Resposta da 3"

    **b)**. Ela emite `UserWarning` citando a coluna e remove as demais. O a) seria o comportamento do `drop`
    sem filtro; o c) seria o do `errors="ignore"`, que esconderia a diferença entre datasets.

??? question "4. (Revisão da 01-2) Onde deveria morar um parâmetro como `nrows` para uma rodada `smoke` do notebook: no `RunConfig` ou numa variável solta no notebook? Por quê?"

    No `RunConfig`: é ali que estão todos os parâmetros de um run, congelados, e a rodada `smoke` é criada
    com `replace`. Uma variável solta no notebook pode mudar entre células e não fica registrada junto com o
    resto da configuração.

## Commit

```bash title="$ Execução no terminal (na pasta do projeto)"
git add src/mqtt_dos/data.py tests/test_data.py notebooks/training.ipynb
git commit -m "feat: carga e limpeza do dataset bruto (20 preditoras)"
```

## Resumo

- A **limpeza orientada à implantação** remove 46 colunas: metadados do frame, endereços, portas e campos
  MQTT textuais, de sessão, compostos ou quase vazios. Ficam as 20 preditoras da Tabela I mais `type`.
- Os nulos são **ausência estrutural**: o campo não existe naquele pacote. Por classe, eles mostram que
  quase todo o tráfego normal do dataset não é MQTT.
- Um **aviso** (`warnings.warn`, testado com `pytest.warns`) sinaliza colunas ausentes sem parar a limpeza.

## Fonte principal

- [pandas — Working with missing data](https://pandas.pydata.org/docs/user_guide/missing_data.html): leia
  as seções sobre valores ausentes por tipo de dado e sobre `isna()`.

## Para saber mais

- [pandas — read_csv](https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html) (parâmetro `low_memory`)
- [pandas — DataFrame.drop](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.drop.html) (parâmetros `columns` e `errors`)
- [Python — warnings](https://docs.python.org/3/library/warnings.html)
- [pytest — How to capture warnings](https://docs.pytest.org/en/stable/how-to/capture-warnings.html)
- [pytest — How to use temporary directories and files](https://docs.pytest.org/en/stable/how-to/tmp_path.html)

!!! question "Ficou com dúvida?"

    O agente é o seu professor neste curso. Pergunte qualquer coisa que não ficou clara, colando a
    mensagem de erro exata e o que você já tentou.

**Próxima aula:** 03. Gaps de publish e connect sem vazamento.
