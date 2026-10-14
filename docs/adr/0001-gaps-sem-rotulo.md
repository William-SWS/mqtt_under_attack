# 1. Gaps de publish e connect calculados no fluxo inteiro, sem o rótulo

**Status:** aceita (2026-10-13; registrada em 2026-10-14)

## Contexto

`publish_gap` e `connect_gap` são as duas features temporais que o paper acrescenta às 20 colunas do
Wireshark. O código original (`04_pipeline.ipynb`, `04_svm.ipynb`) as calculava separadamente para cada valor
de `type`: o gap de um pacote DoS era o tempo desde o PUBLISH DoS anterior, ignorando os PUBLISH normais no
meio. Em produção não há rótulo, então essa feature não pode ser reproduzida na inferência (vazamento de rótulo).

## Decisão

Os gaps são calculados sobre o fluxo inteiro de pacotes, em ordem de `frame.time_epoch`, sem consultar `type`,
e antes da limpeza (que remove `frame.time_epoch`). Um teste afirma que trocar os rótulos não altera os gaps.

## Alternativas consideradas

- **Manter o cálculo por `type`:** preservaria a comparabilidade 1:1 com os números do artigo, mas mantém uma
  feature impossível de calcular em produção.
- **Flag para escolher entre os dois cálculos:** reproduziria os resultados antigos sob demanda, ao custo de
  manter código com vazamento no pacote. A comparação antigo × novo ficou no notebook, construída de propósito
  a partir de `add_gaps` aplicado a cada classe.

## Consequências

- As métricas novas deixam de ser comparáveis 1:1 com as do artigo.
- Medido neste dataset, o efeito numérico é pequeno: 6150 → 6151 gaps de PUBLISH não nulos, o maior
  `publish_gap` do DoS cai de 248,2 s para 48,3 s, e uma árvore treinada só com os dois gaps tem a mesma
  acurácia (0,5874) nas duas versões. A correção vale pelo método, não por um ganho numérico.
- O cálculo usa alinhamento por índice e não depende de o CSV estar ordenado (o código antigo dependia).
