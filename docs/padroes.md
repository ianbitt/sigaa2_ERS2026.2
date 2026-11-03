# Padrões arquiteturais

O projeto implementa e testa seis padrões (o mínimo exigido é 3). Cada um está ligado a um container do [diagrama C4 nível 2](c4/nivel-2-containers.png) e a um critério de sucesso da proposta.

## Onde cada padrão aparece

| # | Padrão | Área | Container(s) | Problema que resolve | Critério validado |
| --- | --- | --- | --- | --- | --- |
| 1 | Queue / Competing Consumers | Escalabilidade | Fila `matriculas.pedidos` + Vagas (workers ×N) | Absorver o pico de pedidos e escalar o processamento de forma independente | 1, 4 |
| 2 | Rate Limit + Load Shedding | Desempenho | Gateway (contadores no Redis) | Proteger o núcleo contra excesso de requisições, rejeitando o excedente com 429/503 | 3 |
| 3 | CQRS + Cache-Aside | Desempenho | Consulta + read model (PostgreSQL) + Redis | Separar a leitura de vagas da escrita de matrículas e responder rápido sob carga | 2 |
| 4 | Idempotência | Confiabilidade | Inscrição (chave no Redis) + `UNIQUE (aluno_id, turma_id)` no PostgreSQL de Vagas | Fazer cliques repetidos e retentativas contarem como uma única matrícula | 1, 4 |
| 5 | Transactional Outbox + Retry/DLQ | Confiabilidade | Vagas + Outbox Relay + DLQs | Gravar matrícula e evento na mesma transação e garantir a entrega do evento | 4, 5 |
| 6a | Circuit Breaker | Confiabilidade | Notificação → Provedor de E-mail | Parar de chamar o provedor quando ele falha repetidamente, deixando os e-mails na fila até a recuperação | 5 |
| 6b | Bulkhead | Confiabilidade | Gateway (limite de conexões por serviço de destino) + limites de CPU/memória por container | Impedir que um serviço lento ou sobrecarregado consuma os recursos dos demais (ex.: Inscrição lenta não trava a Consulta) | 3, 5 |

Os critérios de sucesso estão na proposta e no [README](../README.md).

## Padrões considerados e descartados

| Padrão | Motivo |
| --- | --- |
| SAGA / Orchestration | Vaga, matrícula e outbox ficam numa única transação no serviço Vagas ([ADR-001](adr/0001-vagas-dono-da-escrita-de-matricula.md)), sem transação distribuída |
| Inbox | A idempotência dos consumidores é garantida pela `versao` no read model ([ADR-002](adr/0002-read-model-proprio-da-consulta.md)) e pela restrição `UNIQUE` |
| Request Hedging | Duplicaria requisições justamente no pico, aumentando a carga |
| Service Mesh | Complexidade de infraestrutura desproporcional para 6 containers |
| Event Sourcing | O estado atual (vagas e matrículas) atende ao domínio; o histórico completo de eventos não é requisito |