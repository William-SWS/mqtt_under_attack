# Documentação do projeto

Este projeto reúne dados e scripts para analisar ataques em ambientes MQTT, com foco em exploração dos dados, engenharia de atributos e modelagem preditiva.

## Objetivo

- Organizar o dataset **MQTT Under Attack** e suas transformações.
- Documentar a análise exploratória e a modelagem.
- Prover um caminho reprodutível para treinar e avaliar modelos.

## Estrutura principal

- **data/**: dados brutos, intermediários e processados.
- **mqtt_under_attack/**: código-fonte do pacote.
- **notebooks/**: análises exploratórias e estudos.
- **models/**: scripts de treino e predição.
- **reports/**: figuras e artefatos gerados.

## Como gerar a documentação

1. Instale as dependências do projeto.
2. Acesse a pasta docs/.
3. Execute o servidor local do MkDocs.

> Dica: o arquivo de configuração está em docs/mkdocs.yml.

## Próximos passos sugeridos

- Descrever o fluxo de preparação de dados.
- Documentar as features usadas em cada modelo.
- Registrar métricas e resultados no relatório.
