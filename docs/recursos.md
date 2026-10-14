# Recursos

Fontes confiáveis em que o curso se baseia, todas lidas durante a montagem.

## Conhecimento

- [Documentação do uv](https://docs.astral.sh/uv/)
  Referência oficial do gerenciador de projetos e pacotes. Use para: `uv add`, `uv run`, `uv sync`, versões do Python.
  - [Installation](https://docs.astral.sh/uv/getting-started/installation/): instalador oficial.
  - [Project structure and files](https://docs.astral.sh/uv/concepts/projects/layout/): `pyproject.toml`, `.venv` e `uv.lock`, e o que vai para o git.
  - [Managing dependencies](https://docs.astral.sh/uv/concepts/projects/dependencies/): `uv add`, limites de versão, grupo `dev`.
  - [Configuring projects](https://docs.astral.sh/uv/concepts/projects/config/): `requires-python` e o que acontece sem `[build-system]`.
  - [Locking and syncing](https://docs.astral.sh/uv/concepts/projects/sync/): `uv lock`, `uv sync`, sincronização exata, `--locked`.
  - [Python versions](https://docs.astral.sh/uv/concepts/python-versions/): `uv python pin` e downloads automáticos.
  - [The uv build backend](https://docs.astral.sh/uv/concepts/build-backend/): `uv_build`, layout `src/`, `module-name`.
  - [Using uv with Jupyter](https://docs.astral.sh/uv/guides/integration/jupyter/): `ipykernel`, kernel no VS Code, `uv run --with jupyter jupyter lab`.
- [Python Packaging User Guide — Writing your pyproject.toml](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/)
  Guia oficial do formato do manifesto. Use para: tabelas `[build-system]`, `[project]`, campos `name`, `version`, `requires-python`.
- [Documentação do pytest](https://docs.pytest.org/en/stable/)
  Referência oficial do framework de testes, com tutorial para iniciantes. Use para: escrever e rodar testes.
  - [Good Integration Practices](https://docs.pytest.org/en/stable/explanation/goodpractices.html): layout `src/`, convenções de descoberta.
  - [How to write and report assertions](https://docs.pytest.org/en/stable/how-to/assert.html): `assert` e `pytest.raises`.
  - [How to parametrize](https://docs.pytest.org/en/stable/how-to/parametrize.html): `@pytest.mark.parametrize`.
- [Python — dataclasses](https://docs.python.org/3/library/dataclasses.html)
  Documentação oficial das dataclasses. Use para: `frozen`, `field(default_factory=...)`, `__post_init__`, `replace`.
- [Ruff — Configuring Ruff](https://docs.astral.sh/ruff/configuration/)
  Configuração do linter e formatador. Use para: `[tool.ruff]`, `include`, notebooks, `check` x `format`.
- [nbclient — Executing notebooks](https://nbclient.readthedocs.io/en/latest/client.html)
  Execução programática de notebooks. Use para: `NotebookClient`, `CellExecutionError`.
- [Guia do usuário do scikit-learn](https://scikit-learn.org/stable/user_guide.html)
  Cobre seleção de features (seção 1.13), pipelines (8.1), métricas (3.4) e validação cruzada (3.1). Use para: seletores, `Pipeline`, avaliação.
- [Documentação do Optuna](https://optuna.readthedocs.io/en/stable/)
  Otimização de hiperparâmetros com `Study` e `Trial`. Use para: estudos, trials e espaços de busca.
- [Documentação do MkDocs](https://www.mkdocs.org/)
  Gerador de sites a partir de Markdown. Use para: configuração do site do curso.
- [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/)
  Tema do site, com admonitions, blocos de código e abas. Use para: formatar as aulas.

## Lacunas

- Seletores de features (variância, ANOVA, informação mútua, Lasso, LinearSVC, ExtraTrees): fontes específicas a ler nas aulas 06 e 07.
- Calibração de probabilidades: fonte a ler na aula 05.
