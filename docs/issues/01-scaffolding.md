# 01: Scaffolding do projeto

**What to build:** o esqueleto onde todo o resto vai morar: ambiente reproduzível com uv, pacote importável, pytest rodando e um notebook vazio que importa o pacote. O leitor termina com `uv run pytest` verde e `import mqtt_dos` funcionando dentro do notebook.

**Blocked by:** None (can start immediately)

**Status:** done

- [x] `uv sync` instala o ambiente (Python 3.13) com as dependências de treino e o grupo dev (pytest, ruff, mkdocs-material, jupyter).
- [x] O pacote `mqtt_dos` é importável e expõe a configuração do run (nome, seed, fração de teste, trials, folds, top-k, subamostra por modelo).
- [x] `uv run pytest` executa ao menos um teste da configuração e passa.
- [x] `uv run ruff check` passa.
- [x] O notebook de treino existe, com as seções vazias e a célula de configuração executando.
- [x] Os notebooks, `scripts/`, `api_inference/` e `requirements.txt` antigos continuam intactos.

## Notas de execução

- [x] Aula 01-1 (ambiente com uv) escrita: ver `course/LOG.md`, entrada nº 6. Aulas 01-2 e 01-3: ver entrada nº 13.
- Aula 01-1 implementada no repositório pelo agente a pedido da usuária: ver `course/LOG.md`, entrada nº 10.
- [x] Aulas 01-2 (pacote e primeiro teste) e 01-3 (ruff e notebook) escritas e implementadas no repositório pelo agente a pedido da usuária: ver `course/LOG.md`, entradas nº 12 e 13.
