# ADR-002: Read model próprio da Consulta (CQRS + Cache-Aside)

- **Status:** Proposto
- **Data:** 03/11/2026
- **Decisores:** Daniel Victor Carneiro Brandão da Costa, Davi Nasiasene Amorim, Ian Rocha Bittencourt

## Contexto

No pico de matrícula, a consulta de vagas recebe muito mais requisições do que a própria matrícula: alunos atualizam a página o tempo todo para ver se ainda há vaga. A meta é **p95 da consulta abaixo de 200 ms sob carga** (critério de sucesso 2), sem que essas leituras disputem recursos com as escritas no banco de Vagas, que é o ponto crítico do sistema (ver ADR-001).

A Consulta usa **Cache-Aside** com Redis: procura primeiro no cache e, em caso de *miss* (chave inexistente, TTL expirado ou Redis reiniciado), busca na fonte de dados e popula o cache. Falta decidir **qual é essa fonte**.

## Decisão

A Consulta tem um **read model próprio**, atualizado de forma assíncrona pelos eventos que Vagas publica via Outbox em `matriculas.eventos`.

- **Armazenamento:** um database `consulta` próprio, na mesma instância do PostgreSQL usada por Vagas, com usuário separado. Cada serviço só acessa o seu database.
- **Schema otimizado para leitura:**
  - `turmas_leitura (turma_id, nome, vagas_restantes, versao)`
  - `pedidos_leitura (pedido_id, aluno_id, turma_id, status)`
- **Atualização por eventos:** os eventos carregam o **valor absoluto** de `vagas_restantes` e uma `versao` crescente por turma, e não um "menos um". A Consulta só aplica o evento se `versao` for maior que a armazenada. Assim, eventos **repetidos ou fora de ordem** não corrompem o read model.

```sql
INSERT INTO turmas_leitura (turma_id, vagas_restantes, versao)
VALUES (:turma_id, :vagas_restantes, :versao)
ON CONFLICT (turma_id) DO UPDATE
   SET vagas_restantes = EXCLUDED.vagas_restantes,
       versao          = EXCLUDED.versao
 WHERE turmas_leitura.versao < EXCLUDED.versao;
```

- **Cache-Aside:** a leitura procura no Redis primeiro. No *miss*, lê `turmas_leitura` e grava no Redis com TTL curto. Ao aplicar um evento, a Consulta invalida a chave daquela turma no Redis.
- **Carga inicial:** a abertura de turmas gera o evento `turma_aberta` (também via Outbox), que cria a linha no read model.
- **Status do pedido:** `GET /matriculas/{pedido_id}` lê `pedidos_leitura`. Se o pedido ainda não existir lá, a resposta é "em processamento".

### Mitigação de *cache stampede*

Quando a chave de uma turma disputada expira, muitas requisições podem dar *miss* ao mesmo tempo. Para evitar isso:

- **Lock de recomputação:** só a primeira requisição consulta a fonte (lock com `SET ... NX` no Redis); as demais aguardam brevemente e leem do cache.
- **TTL com jitter:** cada chave recebe uma variação aleatória no prazo, para não expirarem juntas.
- **Aquecimento:** as turmas são carregadas no Redis antes da abertura da matrícula.

## Alternativas consideradas

| Alternativa | Motivo do descarte |
| --- | --- |
| Ler direto do PostgreSQL de Vagas | Acopla Consulta ao schema de Vagas e coloca as leituras do pico no banco crítico de escrita |
| Réplica de leitura do PostgreSQL de Vagas | Tira a carga do primário, mas mantém o acoplamento ao schema e exige configurar replicação |
| Redis como único read model, sem banco | Deixa de ser Cache-Aside; um reinício do Redis exige reconstruir o read model do zero |

## Consequências

**Positivas**
- Consulta e Vagas ficam desacoplados: cada um evolui seu schema sem afetar o outro.
- As leituras do pico não chegam ao banco de Vagas.
- O schema de leitura é simples e rápido, o que favorece o p95 abaixo de 200 ms.
- O read model tolera eventos duplicados e fora de ordem graças à `versao`.

**Negativas**
- **Consistência eventual:** a consulta pode mostrar, por alguns instantes, vagas que já foram ocupadas. Isso não causa overbooking, porque quem decide é a transação de Vagas (ADR-001); o aluno apenas recebe a recusa.
- Mais código: consumidor de eventos, carga inicial e invalidação do cache.
- A instância do PostgreSQL é compartilhada; a separação é lógica (databases distintos), não física. Em produção, cada database iria para sua própria instância.

## ADRs relacionados

- **ADR-001:** define a transação de Vagas que publica `matricula_confirmada` (com `vagas_restantes` e `versao`) e `matricula_recusada`, eventos que este read model consome.