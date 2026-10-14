# Referência rápida

Comandos, padrões de código e receitas curtas, agrupados por ferramenta, cada um com "quando usar" e um
link para a aula que o ensinou. Cresce a cada aula.

## uv

| Comando | Quando usar | Aula |
|---|---|---|
| `uv python pin 3.13` | fixar a versão do Python do projeto (grava `.python-version`) | [01-1](01-1-ambiente-com-uv.md) |
| `uv add <pacote>` | adicionar uma dependência do treino (manifesto + lockfile + ambiente) | [01-1](01-1-ambiente-com-uv.md) |
| `uv add --dev <pacote>` | adicionar uma ferramenta de desenvolvimento ao grupo `dev` | [01-1](01-1-ambiente-com-uv.md) |
| `uv sync` | recriar ou acertar o ambiente a partir do lockfile | [01-1](01-1-ambiente-com-uv.md) |
| `uv run <comando>` | rodar qualquer comando dentro do ambiente do projeto | [01-1](01-1-ambiente-com-uv.md) |
| `uv lock --check` | conferir, sem mudar nada, se o lockfile corresponde ao manifesto | [01-1](01-1-ambiente-com-uv.md) |
| `uv tree --depth 1` | ver as dependências diretas e de que grupo são | [01-1](01-1-ambiente-com-uv.md) |
| `uv tree --invert --package <pacote>` | descobrir quem trouxe uma dependência indireta | [01-1](01-1-ambiente-com-uv.md) |

## MkDocs

| Comando | Quando usar | Aula |
|---|---|---|
| `uv run mkdocs serve` | abrir o curso no navegador (`http://127.0.0.1:8000/`); `Ctrl+C` para parar | [01-1](01-1-ambiente-com-uv.md) |
| `uv run mkdocs build --strict` | gerar o site e falhar em qualquer aviso | [01-1](01-1-ambiente-com-uv.md) |

## git

| Comando | Quando usar | Aula |
|---|---|---|
| `git status --short` | ver o que mudou (`M` modificado, `??` novo) | [01-1](01-1-ambiente-com-uv.md) |
| `git add <arquivos>` + `git commit -m "..."` | registrar o fim de uma aula | [01-1](01-1-ambiente-com-uv.md) |

## pytest

| Comando | Quando usar | Aula |
|---|---|---|
| `uv run pytest` | rodar todos os testes (`tests/`) | [01-2](01-2-pacote-e-primeiro-teste.md) |
| `uv run pytest <arquivo> -v` | ver cada teste numa linha | [01-2](01-2-pacote-e-primeiro-teste.md) |
| `uv run pytest "<arquivo>::<teste>"` | rodar um teste só | [01-2](01-2-pacote-e-primeiro-teste.md) |
| `uv run pytest -k "<trecho>"` | rodar os testes cujo nome contém um trecho | [01-2](01-2-pacote-e-primeiro-teste.md) |

| Padrão | Quando usar | Aula |
|---|---|---|
| `assert valor == esperado` | afirmar um resultado | [01-2](01-2-pacote-e-primeiro-teste.md) |
| `with pytest.raises(Erro, match="trecho"):` | afirmar que um erro acontece, pelo motivo certo | [01-2](01-2-pacote-e-primeiro-teste.md) |
| `@pytest.mark.parametrize("nome", [v1, v2])` | rodar o mesmo teste com vários valores | [01-2](01-2-pacote-e-primeiro-teste.md) |

## Python

| Padrão | Quando usar | Aula |
|---|---|---|
| `@dataclass(frozen=True)` | configuração que não pode mudar depois de criada | [01-2](01-2-pacote-e-primeiro-teste.md) |
| `field(default_factory=lambda: {...})` | valor padrão mutável (dict, list) numa dataclass | [01-2](01-2-pacote-e-primeiro-teste.md) |
| `def __post_init__(self):` | validar os campos logo após a criação | [01-2](01-2-pacote-e-primeiro-teste.md) |
| `dataclasses.replace(obj, campo=valor)` | criar uma variação de uma dataclass congelada | [01-2](01-2-pacote-e-primeiro-teste.md) |
| `Path(__file__).resolve().parents[N]` | caminho estável a partir do próprio arquivo | [01-2](01-2-pacote-e-primeiro-teste.md) |

## ruff

| Comando | Quando usar | Aula |
|---|---|---|
| `uv run ruff check` | procurar problemas no código novo | [01-3](01-3-ruff-e-notebook.md) |
| `uv run ruff check --fix` | corrigir o que o ruff sabe corrigir (marcado com `[*]`) | [01-3](01-3-ruff-e-notebook.md) |
| `uv run ruff format --check` | conferir a formatação sem mudar nada | [01-3](01-3-ruff-e-notebook.md) |
| `uv run ruff format` | aplicar a formatação | [01-3](01-3-ruff-e-notebook.md) |

## Notebook

| Comando | Quando usar | Aula |
|---|---|---|
| Kernel `.venv/bin/python` no VS Code | abrir `notebooks/training.ipynb` com o ambiente do projeto | [01-3](01-3-ruff-e-notebook.md) |
| `uv run --with jupyter jupyter lab` | abrir o JupyterLab com o ambiente do projeto | [01-3](01-3-ruff-e-notebook.md) |

## Verificação completa do projeto

```bash
uv run pytest
uv run ruff check
uv run ruff format --check
```
