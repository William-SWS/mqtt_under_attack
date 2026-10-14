# 03: Gaps de publish e connect sem vazamento

**What to build:** as duas features temporais calculadas no fluxo inteiro em ordem de tempo, sem usar o rótulo, anexadas à tabela limpa (22 candidatas). O notebook mostra a distribuição de cada gap por classe e explica a mudança em relação ao código antigo.

**Blocked by:** 02

**Status:** ready-for-agent

- [ ] O gap de PUBLISH (msgtype 3) é a diferença para o PUBLISH anterior no fluxo inteiro; o de CONNECT (msgtype 1) idem; a primeira ocorrência e as outras mensagens ficam 0.
- [ ] O resultado é o mesmo se os valores do rótulo forem embaralhados (teste que trava o vazamento).
- [ ] A ordem e o índice originais das linhas são preservados e o resultado alinha com a tabela limpa.
- [ ] A tabela final tem 22 colunas preditoras mais `type`.
- [ ] O notebook mostra histogramas e boxplots dos gaps por classe.
- [ ] Decisão registrada em `docs/decisions.md`; ADR "gaps sem `type`" criado.
- [x] Aula do curso escrita: `docs/03-gaps-sem-vazamento.md`

## Notas de execução

- Aula 03 escrita: ver `course/LOG.md`, entrada nº 25. Código a ser digitado pela usuária. ADR "gaps sem `type`" criado: `docs/adr/0001-gaps-sem-rotulo.md`.
