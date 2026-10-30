# Prompt para o agente de codificação — Etapa B (reestruturação do plano do curso)

Copie tudo o que está entre as linhas `---` e cole no agente de codificação. Antes, preencha o bloco
"Respostas da autora". Os valores que já estão lá são as recomendações do relatório; troque o que você
discordar.

---

## Tarefa

Você vai executar a **Etapa B** da reestruturação do plano deste repositório (`mqtt_under_attack`). A Etapa A
(análise) está pronta e aprovada. A Etapa B transforma as recomendações aprovadas em **tickets, specs,
ADRs, decisões e glossário**. Você não escreve código de produto: este repositório é um curso, e a autora
digita o código seguindo as aulas.

## Leia antes, nesta ordem

1. `AGENTS.md` (seções "Refatoração em curso" e "Convenções do curso") e `CLAUDE.md`.
2. `course/MISSION.md`, `course/NOTES.md`, as últimas entradas de `course/LOG.md` e `course/learning-records/`.
3. A skill `mkdocs-project-course`: o `SKILL.md` e as referências. Ela define o formato dos tickets e a
   relação ticket → aula.
4. `docs/decisions.md` (1–43), `docs/adr/0001-gaps-sem-rotulo.md`, `GLOSSARY.md`,
   `docs/issues/0000-spec-treino-unificado.md` e `docs/issues/01`–`08`.
5. `docs/analises/claude-science-2026-10-30.md`: o relatório da Etapa A, com o mapa de reestruturação na §3,
   o texto das decisões 44–65 na §4 e as perguntas na §6.
6. `docs/analises/claude-science-2026-10-30-etapa-b.md`: o **pacote de execução**, com o texto integral dos
   tickets, specs, ADRs, glossário, a ordem das mudanças e as checagens. É ele que você executa.

## Regras (não negociáveis)

- **Git: você não executa nenhuma operação de git.** Nada de `add`, `commit`, `branch`, `switch`,
  `checkout`, `merge`, `rebase`, `stash`, `reset`, `push` ou PR (decisão 65). Depois de cada mudança lógica
  da §1 do pacote, mostre o comando sugerido, por exemplo
  `git add docs/adr/0002-unidade-do-split.md && git commit -m "docs(adr): ADR 0002 unidade do split"`, e
  **pare até eu confirmar** que executei.
- **Só escreva em:** `docs/issues/`, `docs/decisions.md` (só acrescentar ao fim), `docs/adr/` (só arquivos
  novos), `GLOSSARY.md` (só acrescentar) e a seção final de `docs/analises/claude-science-2026-10-30.md`.
- **Não altere:** `src/`, `tests/`, `notebooks/`, `pyproject.toml`, `uv.lock`, `mkdocs.yml`, `docs/index.md`,
  as aulas `docs/0*.md`, `docs/glossario.md`, `AGENTS.md`, `course/`, `api_inference/`, `scripts/`,
  `paretto/`, `data/`, `outputs/` e nenhum código antigo.
- **Não renomeie nem apague tickets.** Os arquivos de 04–08 mantêm o nome; ticket abandonado é marcado,
  não apagado.
- Docs em pt-BR; identificadores em inglês.

## Respostas da autora (edite antes de colar)

- P6 (formato dos tickets): siga a skill. Se ela divergir do formato da §0 do pacote, **me mostre a
  divergência antes de escrever** e use o formato da skill acrescido de Origem, Contexto, Arquivos e Aula.
- P7 (local do código das fases 2 e 3): membro de workspace uv `edge/` (pacote `edge_bench`), como na
  decisão 55.
- P8 (âncoras do t16): sim, levar ao Pi o conjunto LowVariance × {LDA, DT, GB, RF, SVM}.
- P9 (escalar de qualidade): MCC.
- P10 (split primário): manter o split do artigo como primário até o ticket 09 decidir pelo critério.
- P13 (git): respondida acima; só sugestões.
- Data de aprovação para o cabeçalho das decisões: AAAA-MM-DD.
- Recomendações rejeitadas: nenhuma. *(Se houver, liste aqui com o motivo; elas não viram ticket e entram no
  relatório como "não adotadas".)*
- As perguntas P1–P5, P11, P12 e P14 continuam abertas e **não bloqueiam** a Etapa B. Mantenha-as como
  pendências nos tickets que dependem delas (11, 19 e 22).

## Como executar

1. **Checagem de formato:** compare o formato da skill com o da §0 do pacote e me relate as divergências.
   Espere eu aprovar.
2. Siga a **§1 do pacote** na ordem: ADRs 0002–0004, decisões 44–65, spec 0000 reescrita, specs 0001 e 0002,
   tickets 04–08 reescritos, tickets 09–22 novos e glossário. Copie os textos do pacote; ajuste só o que as
   minhas respostas ou a skill exigirem. Após cada linha da §1, sugira o commit e pare.
3. Rode as **checagens da §2 do pacote**, entre elas `uv run mkdocs build --strict -d /tmp/site-check` (aqui
   você pode rodar `uv`, porque está na minha máquina). Releia os tickets de 01 a 22 e confirme que cada um
   só depende de tickets anteriores e que todo critério de aceite é verificável.
4. Escreva a **seção final** do relatório: arquivos alterados, commits sugeridos (com as mensagens),
   recomendações não adotadas e pendências.

## Entrega final (na conversa)

- A lista de arquivos criados e alterados.
- A lista de **aulas a regerar** com a skill e o que muda em cada uma (a §3 do relatório já aponta a 02 e a
  03). Não as regere agora: isso é uma tarefa separada, que eu vou pedir.
- Um **bloco sugerido para a `nav` do `mkdocs.yml`** com os tickets 09–22, as specs 0001–0002 e os ADRs
  0002–0004. Não edite o arquivo; eu aplico.
- Os comandos de git sugeridos que ainda faltarem.
- As pendências que dependem de mim: as perguntas abertas e os comandos para rodar no Pi (§5 do
  relatório).

---

## Prompt seguinte (depois da Etapa B, numa conversa nova)

> Leia `AGENTS.md`, `course/` e a seção final de `docs/analises/claude-science-2026-10-30.md`. Revise as aulas
> `docs/02-carga-e-limpeza.md` e `docs/03-gaps-sem-vazamento.md` com a skill `mkdocs-project-course`,
> aplicando só as mudanças listadas na §3 do relatório (02: colunas de IP/porta/MAC saem das features, mas
> ficam no bruto para agrupar, e a pendência "é MQTT?" passa a apontar para o ticket 11; 03: os gaps não
> vazam em nenhuma unidade de split, e "Onde estamos" mostra a ordem `load_raw → add_gaps → flow_key →
> drop_unused_columns`). Não mude o código das aulas. Registre a revisão no `course/LOG.md`, como a skill
> manda. Não execute nenhuma operação de git; só sugira o commit.
