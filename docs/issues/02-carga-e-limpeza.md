# 02: Carga e limpeza dos dados

**What to build:** ler o CSV bruto de DoS e produzir a tabela limpa com as 20 colunas preditoras mais o rótulo, com a lista de colunas removidas documentada. No notebook, o leitor vê o formato, as classes e os nulos por coluna.

**Blocked by:** 01

**Status:** ready-for-agent

- [ ] A carga devolve 94.625 linhas e 67 colunas, com 49.111 `normal` e 45.514 `DoS`.
- [ ] A limpeza remove as 46 colunas listadas e devolve 20 preditoras mais `type`.
- [ ] Remover coluna inexistente não quebra; colunas ausentes na lista são ignoradas com aviso.
- [ ] Testes unitários com dados sintéticos cobrem a limpeza.
- [ ] O notebook mostra a distribuição de classes e a tabela de nulos por coluna.
