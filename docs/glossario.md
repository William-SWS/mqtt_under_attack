# Glossário

A linguagem do curso: cada aula usa a palavra deste glossário para cada conceito. Os termos do domínio
do projeto estão também em `GLOSSARY.md`, na raiz do repositório. Um termo entra aqui na aula que o explica.

### Ambiente de projeto
A pasta `.venv` com o Python e as bibliotecas de um único projeto, criada e mantida pelo `uv` a partir do lockfile.
_Evite_: venv, virtualenv, "o ambiente do pip". Aula: [01-1](01-1-ambiente-com-uv.md#ambiente-de-projeto)

### Manifesto do projeto
O arquivo `pyproject.toml`: declara o nome do projeto, as versões do Python aceitas (`requires-python`), as dependências do treino (`[project]`) e os grupos de desenvolvimento (`[dependency-groups]`).
_Evite_: requirements, arquivo de configuração. Aula: [01-1](01-1-ambiente-com-uv.md#manifesto-do-projeto-pyprojecttoml)

### Lockfile
O arquivo `uv.lock`, gerado pelo `uv`: guarda a versão exata de cada pacote, inclusive das dependências indiretas. Vai para o git e nunca é editado à mão.
_Evite_: arquivo de trava, requirements congelado. Aula: [01-1](01-1-ambiente-com-uv.md#lockfile-e-sincronizacao)

### Sincronização
Deixar o ambiente de projeto igual ao lockfile: instalar o que falta e remover o que sobra (`uv sync`). O `uv run` sincroniza antes de cada comando.
_Evite_: atualizar o ambiente, reinstalar. Aula: [01-1](01-1-ambiente-com-uv.md#lockfile-e-sincronizacao)

### Grupo de desenvolvimento
O grupo `dev` do manifesto: ferramentas usadas só ao desenvolver (testes, lint, documentação), fora das dependências do treino.
_Evite_: dev-dependencies. Aula: [01-1](01-1-ambiente-com-uv.md#manifesto-do-projeto-pyprojecttoml)

### Pacote
Uma pasta com `__init__.py` que o Python importa pelo nome (`import mqtt_dos`). No layout `src/`, mora em `src/mqtt_dos/` e é instalado no ambiente de projeto em modo editável.
_Evite_: módulo (para a pasta inteira), biblioteca. Aula: [01-2](01-2-pacote-e-primeiro-teste.md#pacote-instalavel-layout-src)

### Dataclass congelada
Uma classe declarada com `@dataclass(frozen=True)`: o Python gera `__init__`, `__repr__` e `__eq__`, e nenhum campo pode ser alterado depois da criação. Variações são criadas com `dataclasses.replace`.
_Evite_: objeto de configuração, struct. Aula: [01-2](01-2-pacote-e-primeiro-teste.md#dataclass-congelada)

### Teste
Uma função `test_*` num arquivo `test_*.py` que executa um pedaço do código e afirma o resultado esperado com `assert` ou `pytest.raises`. O pytest encontra e roda todos.
_Evite_: teste unitário (quando não for o caso), check. Aula: [01-2](01-2-pacote-e-primeiro-teste.md#testes-com-pytest)

### Linter
Ferramenta que lê o código sem executá-lo e aponta problemas, como imports sem uso ou fora de ordem (`ruff check`).
_Evite_: analisador, checker. Aula: [01-3](01-3-ruff-e-notebook.md#linter-e-formatador-ruff)

### Formatador
Ferramenta que reescreve a forma do código num estilo único sem mudar o comportamento (`ruff format`).
_Evite_: prettier, beautifier. Aula: [01-3](01-3-ruff-e-notebook.md#linter-e-formatador-ruff)

### Kernel
O processo Python que executa as células de um notebook. Neste projeto, o Python do ambiente de projeto (`.venv/bin/python`) com `ipykernel`.
_Evite_: interpretador do notebook. Aula: [01-3](01-3-ruff-e-notebook.md#kernel-do-ambiente-do-projeto)

### Teste de execução do notebook
Um teste que roda todas as células de um notebook num kernel novo, de cima a baixo, e falha se alguma der erro (`nbclient`).
_Evite_: smoke test do notebook. Aula: [01-3](01-3-ruff-e-notebook.md#teste-de-execucao-do-notebook)
