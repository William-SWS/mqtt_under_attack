# Resumo: Fronteira de Pareto para Acurácia, Tempo e Memória

A **fronteira de Pareto** é usada quando existem vários objetivos que entram em conflito.

Neste caso, deseja-se:

- **maximizar a acurácia**;
- **minimizar o tempo de processamento**;
- **minimizar o consumo de memória**.

## Dominância de Pareto

Um modelo **A domina** um modelo **B** quando:

- A possui acurácia maior ou igual à de B;
- A possui tempo menor ou igual ao de B;
- A possui consumo de memória menor ou igual ao de B;
- A é estritamente melhor em pelo menos um desses critérios.

Quando um modelo é dominado, existe outra alternativa claramente melhor ou igual em todos os objetivos.

## Exemplo

| Modelo | Acurácia | Tempo | Memória |
|---|---:|---:|---:|
| A | 94% | 2 ms | 120 MB |
| B | 96% | 4 ms | 180 MB |
| C | 97% | 8 ms | 260 MB |
| D | 95% | 5 ms | 200 MB |

O modelo **B domina D**, pois:

- possui maior acurácia;
- é mais rápido;
- consome menos memória.

Assim, D não pertence à fronteira.

Os modelos A, B e C podem permanecer na fronteira porque representam diferentes compromissos:

- A prioriza velocidade e memória;
- B oferece um equilíbrio intermediário;
- C prioriza acurácia.

## Passos para encontrar a fronteira

1. Avaliar todos os modelos nas mesmas condições.
2. Registrar acurácia, tempo e memória.
3. Comparar cada modelo com todos os demais.
4. Marcar como dominado o modelo para o qual existe outro melhor ou igual em todos os objetivos.
5. Manter os modelos não dominados.

Esses modelos formam a **fronteira de Pareto empírica**.

## Importante

A fronteira de Pareto não escolhe automaticamente um único melhor modelo.

Ela mostra quais alternativas representam os melhores compromissos entre os objetivos. A escolha final depende dos requisitos do projeto, por exemplo:

- acurácia mínima;
- limite máximo de tempo;
- quantidade de memória disponível.

## Pseudocódigo

```text
para cada modelo B:
    dominado = falso

    para cada modelo A:
        se A for melhor ou igual em todos os objetivos
        e melhor em pelo menos um:
            B é dominado
            dominado = verdadeiro

    se B não for dominado:
        adicionar B à fronteira
```

## Interpretação

Um modelo pertence à fronteira de Pareto quando não é possível melhorar um dos critérios sem piorar pelo menos outro.

Em trabalhos científicos, recomenda-se usar a expressão:

> **fronteira de Pareto empírica entre os modelos avaliados**

Isso deixa claro que a análise considera apenas os modelos e configurações testados.

## Referências

- JIN, Y.; SENDHOFF, B. *Pareto-Based Multiobjective Machine Learning: An Overview and Case Studies*. IEEE Transactions on Systems, Man, and Cybernetics, Part C, v. 38, n. 3, p. 397–415, 2008.
- MIETTINEN, K. *Nonlinear Multiobjective Optimization*. Springer, 1999.
