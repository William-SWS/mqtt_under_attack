# Missão: MQTT DoS — treino unificado

## Por quê
Autora do paper WPMC, quer refatorar o código dele para ficar legível (a estrutura do repositório e os
notebooks), mantendo só o que o artigo descreve e removendo o que ficou de fora.

## Sucesso é
- Rodar `notebooks/training.ipynb` com o protocolo do paper (7 modelos × 6 seletores) e gerar `outputs/<run>/` com Pipelines que aceitam features brutas.
- Explicar cada etapa do pacote `mqtt_dos`.
- Entender cada método de seleção de características, o funcionamento de cada modelo de treinamento, a otimização, a engenharia de features e a limpeza de dados.

## Ponto de partida
- Python e scikit-learn bem conhecidos (treina modelos em notebooks).
- `uv`, `pytest` e a estrutura de pacote `src/` são novos.
- Estuda no Linux.

## Restrições
- Sem prazo informado.

## Fora de escopo
- Adaptar a `api_inference/` (fase posterior).
