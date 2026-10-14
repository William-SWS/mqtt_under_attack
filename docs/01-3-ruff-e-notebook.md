# 01-3. Ruff e notebook ligado ao ambiente

## Objetivos desta aula

Ao final desta aula você vai entender:

- o que fazem um **linter** e um **formatador**, e por que o ruff passa a olhar só o código novo;
- como um notebook usa o **kernel do ambiente do projeto** para importar `mqtt_dos`;
- como um **teste de execução do notebook** garante que ele roda de cima a baixo.

E vai ter construído:

- a configuração do ruff para `src/`, `tests/` e o notebook novo;
- o `notebooks/training.ipynb`, com as seções 0 a 8 e a configuração do run;
- um teste que executa o notebook inteiro.

**Vitória da aula:** `uv run pytest` mostra `9 passed`, incluindo o notebook executado de ponta a ponta, e
`uv run ruff check` responde `All checks passed!`. Com isso, o ticket 01 está completo.

## Onde estamos

Na [aula 01-2](01-2-pacote-e-primeiro-teste.md) você criou o pacote `mqtt_dos`, o `RunConfig` e os primeiros
8 testes. Esta aula fecha o scaffolding: estilo de código verificado automaticamente e o notebook de
narrativa ligado ao pacote. A aula 02 começa o pipeline de verdade, com a carga e a limpeza dos dados.

### Relembrando

??? question "1. Por que `RunConfig` é `frozen=True` e como se cria uma variação dele?"

    Para que nenhum parâmetro mude no meio de um run. Uma variação é uma configuração nova, criada com
    `dataclasses.replace(config, n_trials=2)`, que também passa pela validação do `__post_init__`.

??? question "2. Como o pytest decide que uma função é um teste?"

    Ela está num arquivo `test_*.py` (dentro de `tests/`, pelo `testpaths`) e o nome dela começa com `test_`.
    Fora disso, é ignorada sem aviso.

## Antes de começar

Os testes da aula 01-2 precisam estar verdes:

```bash title="$ Execução no terminal (na pasta do projeto)"
uv run pytest
```

Para abrir o notebook você precisa do VS Code com a extensão Jupyter (ou do JupyterLab, veja o passo 4).

## Conceitos

### Linter e formatador (ruff)

Um **[linter](glossario.md#linter)** lê o código sem executá-lo e aponta problemas: imports que não são
usados, imports fora de ordem, nomes indefinidos. Um **[formatador](glossario.md#formatador)** reescreve o
código num estilo único (quebras de linha, espaços, aspas). O ruff faz as duas coisas: `ruff check` é o
linter e `ruff format` é o formatador. Ambos leem a configuração da seção `[tool.ruff]` do manifesto.

Analogia: a revisão de normas da revista antes da revisão por pares. Ninguém discute vírgula e formato de
referência na revisão do conteúdo.

O problema que resolve: com o estilo garantido pela ferramenta, a leitura do código (e de cada `git diff`)
fica só no que importa. Uma ressalva honesta: o código antigo já falha no ruff hoje (33 erros), e consertá-lo
está fora de escopo, porque `scripts/` e os notebooks antigos não podem ser alterados. Por isso o `include`
do ruff passa a listar só o código novo (decisão 36).

Fonte: [Ruff — Configuring Ruff](https://docs.astral.sh/ruff/configuration/) ("Paths provided to `include`
_must_ match files"; notebooks são verificados por padrão desde a versão 0.6.0).

### Kernel do ambiente do projeto

O **[kernel](glossario.md#kernel)** é o processo Python que executa as células de um notebook. Ele precisa
ser o Python do ambiente do projeto (`.venv/bin/python`), com o pacote `ipykernel` instalado. Só assim
`import mqtt_dos` funciona dentro do notebook.

Analogia: um caderno de laboratório precisa estar na bancada certa. A mesma receita na bancada do lado
(o `.venv-legacy`) não acha os reagentes deste experimento.

O problema que resolve: com o kernel errado, o notebook usa outras versões das bibliotecas, ou nem acha o
pacote. É o mesmo tipo de divergência que motivou esta refatoração.

Fonte: [uv — Using uv with Jupyter](https://docs.astral.sh/uv/guides/integration/jupyter/) ("VS Code requires
`ipykernel` to be present in the project environment").

### Teste de execução do notebook

Um **[teste de execução do notebook](glossario.md#teste-de-execucao-do-notebook)** abre o notebook, roda
todas as células num kernel novo, de cima a baixo, e falha se alguma célula der erro. A biblioteca
`nbclient` faz isso: lê o arquivo com `nbformat`, executa com `NotebookClient` e levanta
`CellExecutionError` quando uma célula falha.

Analogia: reproduzir o experimento do zero, numa bancada limpa, em vez de confiar no caderno que já tem
resultados anotados.

O problema que resolve: notebooks costumam funcionar só na ordem em que foram rodados à mão, com variáveis
que sobraram de células apagadas. O teste garante que o `training.ipynb` roda inteiro, na ordem, a cada
`uv run pytest`.

Fonte: [nbclient — Executing notebooks](https://nbclient.readthedocs.io/en/latest/client.html).

## Ponte teoria → projeto

O ticket [01](issues/01-scaffolding.md) pede `uv run ruff check` passando e o notebook de treino com as
seções vazias e a célula de configuração executando. A decisão 7 do [log de decisões](decisions.md) define
o notebook como narrativa que só chama o pacote, e a história de usuário 21 da
[especificação](issues/0000-spec-treino-unificado.md) pede um notebook que conte o pipeline em seções curtas.

Para a sua missão, o notebook é a parte do código que o leitor do paper vai abrir primeiro. O teste de
execução garante que ele funcione para essa pessoa, e não só na sua sessão do Jupyter.

## Mão na massa

### Passo 1 — Apontar o ruff para o código novo

??? question "Pare e pense: com a configuração atual do ruff (que lista `scripts/`, `paretto/` e `notebooks_refactored/`), o que você espera de `uv run ruff check`?"

    Erros no código antigo. Na sua máquina, antes desta aula:

    ```text
    Found 33 errors.
    [*] 14 fixable with `--fix` (4 unsafe fixes available with `--fix --unsafe-fixes`).
    ```

    e `uv run ruff format --check` respondia `9 files would be reformatted, 9 files already formatted`.

Troque a seção `[tool.ruff]` do `pyproject.toml` pela versão abaixo (as seções `[tool.ruff.lint]` e
`[tool.ruff.lint.isort]` continuam iguais):

```toml title="pyproject.toml ([tool.ruff])" linenums="1" hl_lines="3-9"
[tool.ruff]
line-length = 99
src = ["src", "tests"]  # (1)!
include = [  # (2)!
    "pyproject.toml",
    "src/**/*.py",
    "tests/**/*.py",
    "notebooks/training.ipynb",
]
```

1.  Diz ao ruff onde está o código "de primeira parte". É assim que ele sabe que `mqtt_dos` é do projeto e
    o separa de `pytest` e `nbformat` ao ordenar os imports.
2.  O `include` substitui a seleção padrão de arquivos. Listando só o código novo, o ruff ignora o código
    antigo, que não pode ser alterado nesta fase. O notebook novo entra pelo nome.

```bash title="$ Execução no terminal (na pasta do projeto)"
uv run ruff check
uv run ruff format --check
```

```text title="Saída esperada"
All checks passed!
3 files already formatted
```

**O que aconteceu:** o linter não achou problema no código da aula 01-2, e o formatador conferiu os três
arquivos Python (`__init__.py`, `config.py`, `test_config.py`) sem mudar nada. O `--check` só confere;
sem ele, o `ruff format` reescreveria os arquivos.

### Passo 2 — Ferramentas de notebook

O `ipykernel` faz o Python do projeto servir de kernel; o `nbclient` executa notebooks pelo código, para o
teste do passo 5.

```bash title="$ Execução no terminal (na pasta do projeto)"
uv add --dev ipykernel nbclient
```

```text title="Saída esperada (trecho)"
Resolved 92 packages in 22ms
Installed 32 packages in 106ms
...
 + ipykernel==7.4.0
 + ipython==9.17.1
 + jupyter-client==8.10.0
 + nbclient==0.11.0
 + nbformat==5.11.1
...
```

### Passo 3 — Criar o notebook com o kernel certo

No VS Code: abra a pasta do projeto, crie o arquivo `notebooks/training.ipynb` e, no seletor de kernel
(canto superior direito), escolha **Python Environments** e depois o `.venv/bin/python` do projeto. Não
escolha o `.venv-legacy`.

!!! tip "Prefere JupyterLab?"

    Rode `uv run --with jupyter jupyter lab` na pasta do projeto: o JupyterLab abre usando o ambiente do
    projeto, sem instalar o Jupyter como dependência.

Crie as células abaixo, nesta ordem. A primeira é Markdown:

```markdown title="notebooks/training.ipynb — célula 1 (Markdown)"
# Treino unificado — detecção de DoS em MQTT

Notebook de narrativa do esquema de treino: a lógica mora no pacote `mqtt_dos`; aqui ficam a história, a exploração e os gráficos.

Kernel: o Python do ambiente do projeto (`.venv/bin/python`).
```

```markdown title="notebooks/training.ipynb — célula 2 (Markdown)"
## 0. Configuração

Todos os parâmetros do run vêm do `RunConfig`. Os defaults seguem o protocolo do paper (seed 42, split 80/20, 30 trials, 5 folds).
```

```python title="notebooks/training.ipynb — célula 3 (código)" linenums="1"
from mqtt_dos import RunConfig
from mqtt_dos.config import RAW_DATA_PATH

config = RunConfig()
config  # (1)!
```

1.  A última expressão de uma célula é exibida. Aqui aparece o `__repr__` gerado pela dataclass: o protocolo
    inteiro, para quem lê o notebook saber com que parâmetros ele rodou.

```python title="notebooks/training.ipynb — célula 4 (código)" linenums="1"
# Rodada rápida para testar o pipeline inteiro em minutos:
# from dataclasses import replace
# config = replace(config, run_name="smoke", n_trials=2, cv_folds=2)

print(f"Dataset bruto encontrado: {RAW_DATA_PATH.exists()}")  # (1)!
print(f"Artefatos deste run: {config.output_dir}")
```

1.  Confere de cara se o caminho do `config.py` acha o CSV, para que um problema de caminho apareça aqui
    e não na aula 02.

Depois, uma célula Markdown por seção, cada uma só com o título e o ticket que vai preenchê-la:
`## 1. Dados brutos` (ticket 02), `## 2. Gaps de publish e connect` (03), `## 3. Split` (04),
`## 4. Baseline` (05), `## 5. Seleção de features` (06), `## 6. Optuna por seletor` (07),
`## 7. Resultados` (08) e `## 8. Salvar artefatos` (08). Por exemplo:

```markdown title="notebooks/training.ipynb — célula 5 (Markdown)"
## 1. Dados brutos

_Construída no ticket 02._
```

Rode todas as células (**Run All**). A célula 4 mostra:

```text title="Saída esperada (o caminho é o da sua máquina)"
Dataset bruto encontrado: True
Artefatos deste run: /.../mqtt_under_attack/outputs/paper_protocol
```

**O que aconteceu:** o kernel do projeto importou `mqtt_dos` (instalado em modo editável na aula 01-2) e o
`RAW_DATA_PATH` apontou para o CSV real, mesmo com o notebook rodando de dentro de `notebooks/`.

### Passo 4 — Testar que o notebook roda inteiro

Crie `tests/test_notebook.py`:

```python title="tests/test_notebook.py" linenums="1"
from pathlib import Path

import nbformat
from nbclient import NotebookClient

NOTEBOOK_PATH = Path(__file__).resolve().parents[1] / "notebooks" / "training.ipynb"  # (1)!


def test_training_notebook_runs_from_top_to_bottom():
    notebook = nbformat.read(NOTEBOOK_PATH, as_version=4)  # (2)!
    client = NotebookClient(
        notebook,
        timeout=120,  # (3)!
        kernel_name="python3",
        resources={"metadata": {"path": str(NOTEBOOK_PATH.parent)}},  # (4)!
    )

    client.execute()  # (5)!
```

1.  O mesmo truque do `PROJECT_ROOT`: o caminho parte do próprio arquivo de teste, então funciona de qualquer
    pasta.
2.  Lê o notebook como dados (uma lista de células), no formato versão 4.
3.  Uma célula que demore mais de 120 segundos faz o teste falhar em vez de travar para sempre. As aulas
    seguintes vão usar o run `smoke` para manter o notebook rápido nos testes.
4.  Executa o notebook a partir da pasta `notebooks/`, como acontece quando você o abre no editor.
5.  Roda as células na ordem, num kernel novo. Se qualquer célula der erro, levanta `CellExecutionError` e o
    teste falha. Não é preciso um `assert`: o próprio erro é a falha.

Os imports estão na ordem que parece natural (`nbformat`, depois `nbclient`). Veja o que o ruff acha:

```bash title="$ Execução no terminal (na pasta do projeto)"
uv run ruff check
```

```text title="Saída esperada"
I001 [*] Import block is un-sorted or un-formatted
 --> tests/test_notebook.py:1:1
  |
1 | / from pathlib import Path
2 | |
3 | | import nbformat
4 | | from nbclient import NotebookClient
  | |___________________________________^
5 |
6 |   NOTEBOOK_PATH = Path(__file__).resolve().parents[1] / "notebooks" / "training.ipynb"
  |
help: Organize imports
  |
2 |
3 + from nbclient import NotebookClient
4 | import nbformat
  - from nbclient import NotebookClient
5 |
  |

Found 1 error.
[*] 1 fixable with `--fix`.
```

**O que aconteceu:** o projeto usa `force-sort-within-sections = true` (seção `[tool.ruff.lint.isort]`):
dentro de cada grupo, os imports são ordenados pelo nome do módulo, ignorando se começam com `from` ou
`import`. `nbclient` vem antes de `nbformat`. O `[*]` indica que o próprio ruff sabe corrigir:

```bash title="$ Execução no terminal (na pasta do projeto)"
uv run ruff check --fix
```

```text title="Saída esperada"
Found 1 error (1 fixed, 0 remaining).
```

## Testando

```bash title="$ Execução no terminal (na pasta do projeto)"
uv run pytest
uv run ruff check
uv run ruff format --check
```

```text title="Saída esperada (trecho)"
tests/test_config.py ........                                            [ 88%]
tests/test_notebook.py .                                                 [100%]

============================== 9 passed in 0.68s ===============================
All checks passed!
5 files already formatted
```

**Como ler:** os 8 testes da aula 01-2 e o novo teste do notebook passaram. O teste do notebook demora
mais (cerca de 1 segundo) porque inicia um kernel. Os 5 arquivos formatados são os 4 arquivos Python e o
notebook. Estes três comandos são o "está tudo certo?" do projeto daqui para frente.

## Erros comuns

**1. Notebook rodando no kernel antigo.** Se o VS Code estiver usando o `.venv-legacy`:

```text
ModuleNotFoundError: No module named 'mqtt_dos'
```

Causa: o pacote está instalado só no ambiente novo. Correção: troque o kernel para `.venv/bin/python`
(passo 3).

**2. Uma célula com erro quebra o teste.** Por exemplo, um erro de digitação como `config.n_trial`:

```text
E           nbclient.exceptions.CellExecutionError: An error occurred while executing the following cell:
...
E           AttributeError: 'RunConfig' object has no attribute 'n_trial'
```

O relatório mostra a célula e o erro dela. Correção: conserte a célula, rode o notebook inteiro no editor
para conferir e repita `uv run pytest`.

**3. Imports fora de ordem** (`I001`), como no passo 4. Correção: `uv run ruff check --fix`.

## Código completo desta aula

??? example "Arquivo completo: tests/test_notebook.py"

    ```python
    --8<-- "tests/test_notebook.py"
    ```

??? example "Trecho novo do pyproject.toml"

    ```toml
    [tool.ruff]
    line-length = 99
    src = ["src", "tests"]
    include = [
        "pyproject.toml",
        "src/**/*.py",
        "tests/**/*.py",
        "notebooks/training.ipynb",
    ]

    [dependency-groups]
    dev = [
        "ipykernel>=7.4.0",
        "mkdocs<2",
        "mkdocs-material>=9.7.7",
        "nbclient>=0.11.0",
        "pytest>=9.1.1",
        "ruff>=0.17.0",
    ]
    ```

O notebook `notebooks/training.ipynb` tem as células do passo 3.

## Exercícios

1. **O linter também lê o notebook.** Acrescente ao notebook, logo depois da célula 3, uma célula de código
   só com `import pandas as pd` e rode `uv run ruff check`. Está pronto quando você entender o erro, apagar a
   célula e o ruff voltar a responder `All checks passed!`.

??? tip "O que você deve ver"

    ```text title="Saída esperada"
    F401 [*] `pandas` imported but unused
     --> notebooks/training.ipynb:cell 4:1:18
      |
    1 | import pandas as pd
      |                  ^^
    help: Remove unused import: `pandas`
    ```

    O ruff aponta a **célula** (`cell 4`) e a coluna. Import sem uso em notebook é comum quando uma célula de
    exploração é apagada, e é justamente o tipo de sobra que deixa os notebooks antigos difíceis de ler.

2. **Uma seção de conclusões, com teste.** O paper termina com conclusões; o notebook também vai terminar.
   Primeiro escreva o teste, veja-o falhar e só então crie a seção Markdown `## 9. Conclusões` no fim do
   notebook. Está pronto quando este teste passar (junto com os outros):

    ```python title="tests/test_exercicio_01_3.py"
    from pathlib import Path

    import nbformat

    NOTEBOOK_PATH = Path(__file__).resolve().parents[1] / "notebooks" / "training.ipynb"


    def test_notebook_has_conclusions_section():
        notebook = nbformat.read(NOTEBOOK_PATH, as_version=4)
        headings = [cell.source.splitlines()[0] for cell in notebook.cells if cell.cell_type == "markdown"]

        assert "## 9. Conclusões" in headings
    ```

    ```text title="Saída esperada (antes)"
    E       AssertionError: assert '## 9. Conclusões' in ['# Treino unificado — detecção de DoS em MQTT', '## 0. Configuração', '## 1. Dados brutos', '## 2. Gaps de publish e connect', '## 3. Split', '## 4. Baseline', ...]
    ============================== 1 failed in 0.08s ===============================
    ```

??? tip "Solução"

    Acrescente no fim do notebook uma célula Markdown:

    ```markdown
    ## 9. Conclusões

    _Escrita ao final do curso._
    ```

    ```text title="Saída esperada (depois)"
    ============================== 1 passed in 0.07s ===============================
    ```

    Repare na mensagem de antes: o pytest mostrou a lista inteira dos títulos, sem você escrever nenhum
    `print`. É a introspecção do `assert` que você viu na aula 01-2.

3. **Formatador em ação.** O teste do exercício 2 tem uma linha com mais de 99 caracteres. Rode
   `uv run ruff format --check`, leia o que ele propõe e depois aplique com `uv run ruff format`. Está pronto
   quando o `--check` voltar a dizer que todos os arquivos estão formatados e o `uv run pytest` continuar verde.

??? tip "Solução"

    ```text title="Saída esperada (--check)"
    unformatted: File would be reformatted
      --> tests/test_exercicio_01_3.py:10:17
       |
    9  |     notebook = nbformat.read(NOTEBOOK_PATH, as_version=4)
       -     headings = [cell.source.splitlines()[0] for cell in notebook.cells if cell.cell_type == "markdown"]
    10 +     headings = [
    11 +         cell.source.splitlines()[0] for cell in notebook.cells if cell.cell_type == "markdown"
    12 +     ]
    13 |
       |

    1 file would be reformatted, 5 files already formatted
    ```

    ```text title="Saída esperada (ruff format)"
    1 file reformatted, 5 files left unchanged
    ```

    O formatador só muda a forma (quebras de linha), nunca o comportamento: por isso o pytest continua verde.

## Quiz de fixação

??? question "1. Com suas palavras: qual a diferença entre `ruff check` e `ruff format`?"

    `ruff check` é o linter: aponta problemas (import sem uso, imports fora de ordem) e, com `--fix`, corrige
    os que sabe corrigir. `ruff format` é o formatador: reescreve a forma do código (quebras de linha,
    espaços) sem mudar o que ele faz. `--check` só confere, sem alterar.

??? question "2. O notebook roda no seu editor, mas o teste do notebook falha. Qual é a causa mais provável?"

    O notebook depende de algo que existe só na sua sessão: uma variável criada por uma célula que já foi
    apagada, ou células rodadas fora de ordem. O teste roda num kernel novo, de cima a baixo. Correção:
    reinicie o kernel, rode tudo na ordem e conserte a célula que falhar.

**3. Por que o `include` do ruff lista só `src/`, `tests/` e o notebook novo?**

- a) Para o ruff rodar mais rápido no projeto
- b) Porque o código antigo não pode mudar agora
- c) Porque o ruff não lê notebooks por padrão

??? question "Resposta da 3"

    **b)**. O código antigo já tem 33 erros e não pode ser alterado nesta fase (decisões 8 e 36). O a) é um
    efeito colateral, não o motivo; o c) está errado: o ruff lê notebooks por padrão desde a versão 0.6.0.

??? question "4. (Revisão da 01-2) Por que `import mqtt_dos` funciona dentro de `notebooks/` sem nenhum `sys.path.append`?"

    Porque o pacote está instalado no ambiente do projeto em modo editável (o `[build-system]` com `uv_build`
    e o `uv sync` da aula 01-2), e o kernel do notebook é o Python desse ambiente. Os notebooks antigos
    precisavam de `sys.path.append` ou caminhos `../` porque o código não era um pacote instalado.

## Commit

```bash title="$ Execução no terminal (na pasta do projeto)"
git add pyproject.toml uv.lock notebooks/training.ipynb tests/test_notebook.py
git commit -m "feat: notebook de treino e ruff no código novo"
```

## Resumo

- O **ruff** é linter (`check`) e formatador (`format`); o `include` restringe a verificação ao código novo.
- O notebook usa o **kernel** do ambiente do projeto (`.venv/bin/python`, com `ipykernel`) e importa
  `mqtt_dos` direto.
- O **teste de execução do notebook** (`nbclient`) roda tudo de cima a baixo a cada `uv run pytest`.
- `uv run pytest`, `uv run ruff check` e `uv run ruff format --check` são a verificação completa do projeto.
  O ticket 01 está concluído.

## Fonte principal

- [Ruff — Configuring Ruff](https://docs.astral.sh/ruff/configuration/): leia a seção sobre `include` e a
  sobre notebooks Jupyter.

## Para saber mais

- [uv — Using uv with Jupyter](https://docs.astral.sh/uv/guides/integration/jupyter/)
- [nbclient — Executing notebooks](https://nbclient.readthedocs.io/en/latest/client.html)

!!! question "Ficou com dúvida?"

    O agente é o seu professor neste curso. Pergunte qualquer coisa que não ficou clara, colando a
    mensagem de erro exata e o que você já tentou.

**Próxima aula:** 02. Carga e limpeza dos dados.
