---
title: Fluxo da API de Inferência
tags:
  - artigo
  - figura
created: 2026-07-29
---

# Fluxo da API de Inferência

```mermaid
graph LR
    C[Cliente] -->|POST /benchmark/{id}| API[API de Inferência]
    API -->|carrega| M[(Modelo .pkl)]
    API -->|carrega| D[(Dataset de Teste<br/>18925 amostras)]
    API -->|executa predict batch| P[Predição]
    P -->|retorna| API
    API -->|JSON:| R[Tempo de inferência<br/>Acurácia<br/>Predições por segundo]
```
