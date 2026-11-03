# ADR-001: Vagas como único dono da escrita de matrícula

- **Status:** Proposto
- **Data:** 03/11/2026
- **Decisores:** Daniel Victor Carneiro Brandão da Costa, Davi Nasiasene Amorim, Ian Rocha Bittencourt

## Contexto

No pico de matrícula, milhares de pedidos disputam as mesmas vagas ao mesmo tempo. O sistema precisa garantir **zero matrículas além da capacidade** e **zero duplicadas**, mesmo com retentativas e falhas de instância (critérios de sucesso 1 e 4).

Processar uma matrícula envolve três escritas:

1. descontar uma vaga da turma, somente se houver vaga;
2. registrar a matrícula;
3. registrar o evento `matricula_confirmada` no Outbox, para a Notificação.

Se essas escritas ficarem em bancos de serviços diferentes (por exemplo, a vaga no banco de Vagas e a matrícula no banco de Inscrição), uma falha entre elas deixa o sistema inconsistente: ou a vaga é descontada sem matrícula (vaga perdida), ou a matrícula é gravada sem desconto (overbooking). Corrigir isso exigiria uma SAGA com compensações, padrão que a proposta descartou.

## Decisão

As três escritas ficam em **um único serviço, Vagas**, e acontecem **numa única transação** no PostgreSQL desse serviço. As responsabilidades se dividem assim:

- **Inscrição (API de entrada):** recebe o pedido, valida o pré-requisito, verifica a chave de idempotência e publica o pedido na fila `matriculas.pedidos` (RabbitMQ). Responde `202 Accepted`. **Não escreve** no banco de matrículas.
- **Vagas (workers):** várias instâncias consomem a fila (Competing Consumers) e executam a transação:

```sql
BEGIN;
UPDATE turmas
   SET vagas = vagas - 1, versao = versao + 1
 WHERE id = :turma_id AND vagas > 0
RETURNING vagas, versao;                      -- 0 linhas → sem vaga (ver abaixo)

INSERT INTO matriculas (pedido_id, aluno_id, turma_id)
VALUES (:pedido_id, :aluno_id, :turma_id);    -- UNIQUE (aluno_id, turma_id)

INSERT INTO outbox (tipo, payload)
VALUES ('matricula_confirmada',
        {pedido_id, aluno_id, turma_id, vagas_restantes, versao});
COMMIT;
```

- **Sem vaga:** se o `UPDATE` afetar 0 linhas, o worker não grava a matrícula, mas registra no Outbox o evento `matricula_recusada` (`pedido_id`, `aluno_id`, `turma_id`, motivo `sem_vaga`) e faz `COMMIT`. Sem esse evento, a Consulta nunca saberia o resultado do pedido e o aluno ficaria em "em processamento" indefinidamente.
- **Valor absoluto e versão no evento:** o evento de confirmação leva `vagas_restantes` e `versao` (crescente por turma), não um "menos um". Assim, o read model da Consulta (ADR-002) pode descartar eventos repetidos ou fora de ordem.
- A mensagem só recebe `ack` **depois** do `COMMIT`. Se o worker cair antes, o RabbitMQ reentrega a mensagem para outro worker.
- Na reentrega, a restrição `UNIQUE (aluno_id, turma_id)` impede a duplicata. O worker trata essa violação como "já processado" e dá `ack`.

## Alternativas consideradas

| Alternativa | Motivo do descarte |
| --- | --- |
| Inscrição e Vagas com bancos próprios + SAGA | Introduz transação distribuída e compensações; mais complexidade sem ganho para o escopo |
| Fundir Inscrição e Vagas num único serviço | Viável, mas mistura a entrada (sensível a pico) com o processamento; preferimos escalar cada parte de forma independente |
| Contador de vagas no Redis (`DECR`) | O contador e a matrícula ficam em sistemas diferentes, o que recria o problema de dupla escrita |
| `SELECT ... FOR UPDATE` seguido de `UPDATE` | Correto, mas mantém o lock por mais tempo; o `UPDATE` condicional resolve em um único comando |
| Uma fila por turma com um único consumidor (ordem estrita) | Garantiria a ordem de chegada, mas aumenta o número de filas e a complexidade de roteamento; fica registrada como possível evolução |

## Consequências

**Positivas**
- Zero overbooking e zero duplicata garantidos pelo próprio banco (atomicidade da transação e restrição `UNIQUE`).
- O Outbox fica consistente com a matrícula, sem dupla escrita.
- Inscrição e Vagas escalam de forma independente: mais instâncias de API para absorver o pico, mais workers para esvaziar a fila.

**Negativas**
- A resposta ao aluno é assíncrona (`202`): o resultado precisa ser consultado depois ou chegar por notificação.
- Turmas muito disputadas viram uma linha "quente": os workers serializam no lock dessa linha. Isso será medido nos testes de carga.
- O banco de Vagas é um ponto crítico. Perder esse banco interrompe as matrículas (aceitável no escopo; replicação fica fora do projeto).
- Recusas também geram eventos no Outbox, o que aumenta o volume de mensagens quando uma turma lota.
- **A ordem de processamento é aproximada, não estrita.** Com vários workers consumindo a mesma fila, um pedido que chegou antes pode terminar depois de outro (por latência do worker ou por reentrega após falha). Na disputa pela última vaga, o pedido que chegou depois pode ficar com ela. A diferença é de milissegundos e não afeta a correção: zero overbooking e zero duplicata continuam garantidos pela transação. Se a ordem estrita virar requisito, a evolução é usar uma fila por turma com um único consumidor.

## ADRs relacionados

- **ADR-002:** read model da Consulta, que consome `matricula_confirmada`, `matricula_recusada` e `turma_aberta`.