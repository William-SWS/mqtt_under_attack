# MQTT DoS — treino unificado

## O que você vai construir

Um esquema de treino único para detectar ataques de negação de serviço (DoS) em tráfego MQTT. Sete
modelos de aprendizado de máquina (LDA, QDA, GaussianNB, DecisionTree, RandomForest, GradientBoosting e
SVM) são combinados com seis seletores de features e ajustados com Optuna, seguindo o protocolo do
paper WPMC. Cada modelo sai pronto para inferência: um objeto único que recebe os dados brutos e devolve
a predição.

Ao final, um notebook conta a história do pipeline em seções curtas, e um pacote Python pequeno e testado
guarda a lógica. Nada do que ficou de fora do paper permanece no caminho principal.

## Para quem é este curso

Para quem sabe programar em Python e já treinou modelos com scikit-learn em notebooks, mas nunca
estruturou um projeto com `uv`, pacote em `src/` e testes. Não é preciso saber nada disso antes: cada
ferramenta é explicada na aula em que aparece.

O que você precisa: um computador com Linux, tempo para as aulas e disposição para **digitar** o código.

O objetivo, em suas palavras: refatorar o código do seu paper para que fique legível (a estrutura do
repositório e os notebooks), mantendo só o que o artigo descreve, e entender a fundo cada seletor de
features, cada modelo, a otimização, a engenharia de features e a limpeza de dados.

## Como usar este curso

1. Responda às perguntas de **Relembrando** de memória, antes de ler a aula.
2. Leia a aula.
3. **Digite** o código você mesmo. Não copie e cole.
4. Rode os comandos.
5. Compare com a **Saída esperada**.
6. Faça os exercícios até os testes passarem. Tente antes de abrir a solução.
7. Responda ao quiz antes de abrir as respostas.
8. Faça o commit.
9. Conte ao agente como foi com `/mkdocs-project-course progresso`. É isso que ajusta a próxima aula.

Digitar fixa mais do que copiar, e lembrar sem olhar fixa mais do que reler.

## Como ler os blocos de código

- O título do bloco mostra o arquivo em que o código vai.
- Os marcadores `(+)` abrem anotações que explicam a linha.
- Comandos e saídas ficam em blocos separados.
- O botão de copiar existe para comandos, não para substituir a digitação do código.

## Pré-requisitos gerais

- Linux, com acesso a um terminal.
- Conexão com a internet.
- Um editor de texto ou IDE.
- O `uv` e as demais ferramentas são instalados dentro das aulas.

## Mapa das aulas

"Implementada" quer dizer que o código da aula já está no repositório, feito pelo agente a seu pedido; a aula continua valendo como explicação.

| Aula | O que você constrói | Ticket | Status |
|---|---|---|---|
| [01-1](01-1-ambiente-com-uv.md) | Ambiente do projeto com `uv`, manifesto e lockfile | [01](issues/01-scaffolding.md) | disponível (implementada) |
| [01-2](01-2-pacote-e-primeiro-teste.md) | Pacote `src/mqtt_dos`, configuração do run e primeiro teste com pytest | [01](issues/01-scaffolding.md) | disponível (implementada) |
| [01-3](01-3-ruff-e-notebook.md) | ruff e notebook ligado ao ambiente | [01](issues/01-scaffolding.md) | disponível (implementada) |
| [02](02-carga-e-limpeza.md) | Carga do CSV bruto e limpeza para 20 colunas | [02](issues/02-carga-e-limpeza.md) | disponível |
| [03](03-gaps-sem-vazamento.md) | Gaps de publish e connect sem vazamento | [03](issues/03-gaps-sem-vazamento.md) | disponível |
| 04 | Split, Pipeline de inferência e avaliação de um modelo | [04](issues/04-split-pipeline-avaliacao.md) | em breve |
| 05 | Registro dos sete modelos e baseline | [05](issues/05-registro-de-modelos-e-baseline.md) | em breve |
| 06 | Seleção de features com seis seletores | [06](issues/06-selecao-de-features.md) | em breve |
| 07 | Optuna por seletor: grid de 6 × 7 | [07](issues/07-optuna-por-seletor.md) | em breve |
| 08 | Artefatos do run e análise final | [08](issues/08-artefatos-e-analise.md) | em breve |
