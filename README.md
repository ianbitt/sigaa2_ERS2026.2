# Matrícula Escalável

Sistema distribuído de inscrição em disciplinas resiliente a picos de acesso.
Projeto Final de Engenharia de Sistemas Distribuídos — UFPB, 2026.2.

## Equipe

| Integrante | Contato |
| --- | --- |
| Daniel Victor Carneiro Brandão da Costa | danielvictorcarneiro21@gmail.com |
| Davi Nasiasene Amorim | davi.ted@hotmail.com |
| Ian Rocha Bittencourt | ianbittencourt03@gmail.com |

## Problema

No início do período, milhares de alunos disputam poucas vagas no mesmo instante. Sistemas monolíticos degradam, caem ou aceitam matrículas além da capacidade (overbooking). Este projeto propõe uma arquitetura distribuída que absorve o pico por meio de fila, protege o núcleo com rate limit e load shedding e garante que nenhuma vaga seja excedida nem duplicada, mesmo com retentativas e falhas parciais.

## Áreas técnicas

- **Aprofundadas:** Escalabilidade e Desempenho
- **Complementar:** Confiabilidade (e Deployment, como bônus)

## Padrões arquiteturais

| # | Padrão | Área |
| --- | --- | --- |
| 1 | Queue / Competing Consumers | Escalabilidade |
| 2 | Rate Limit + Load Shedding | Desempenho |
| 3 | CQRS + Cache-Aside | Desempenho |
| 4 | Idempotência | Confiabilidade |
| 5 | Transactional Outbox + Retry/DLQ | Confiabilidade |
| 6 | Circuit Breaker + Bulkhead | Confiabilidade |

Padrões considerados e descartados (com justificativa nos ADRs): SAGA/Orchestration, Inbox, Request Hedging, Service Mesh, Event Sourcing.

## Arquitetura

> TODO (Projeto 02): inserir o diagrama C4 níveis 1 (contexto) e 2 (containers).

### Serviços

| Serviço | Responsabilidade |
| --- | --- |
| Gateway | Entrada única, rate limit |
| Inscrição | Processa a fila de matrículas (workers) |
| Vagas | Controle atômico de vagas |
| Consulta | Leitura de vagas e disciplinas (CQRS, cache) |
| Notificação | Envia confirmações a partir de eventos |

### Decisões arquiteturais (ADRs)

Os ADRs ficam em [`docs/adr/`](docs/adr/).

| ADR | Decisão | Status |
| --- | --- | --- |
| 001 | Como garantir zero overbooking | A decidir (Projeto 02) |
| 002 | [Broker: RabbitMQ] | A decidir |

## Stack

Python com FastAPI · RabbitMQ · PostgreSQL · Redis · Docker Compose · GitHub Actions · k6 · Prometheus · Grafana · OpenTelemetry + Jaeger

## Como executar

> TODO: preencher quando o Docker Compose estiver pronto.

```bash
# pré-requisitos: Docker e Docker Compose
git clone https://github.com/ianbitt/sigaa2_ERS2026.2.git
cd sigaa2_ERS2026.2
docker compose up --build
```

- Gateway: `http://localhost:[porta]`
- Grafana: `http://localhost:[porta]`
- RabbitMQ (management): `http://localhost:[porta]`

## Testes

| Tipo | O que valida | Como rodar |
| --- | --- | --- |
| Carga progressiva | Fila, rate limit, load shedding (p95, taxa de sucesso) | `[comando k6]` |
| Concorrência | Muitas requisições para a mesma vaga, sem overbooking | `[comando]` |
| Resiliência | Queda de instância de inscrição, do broker e da notificação | `[comando]` |
| Integração | Fluxo completo, Outbox, retry e DLQ | `[comando]` |

### Critérios de sucesso

1. Com [5.000] usuários em 1 minuto disputando [200] vagas: zero matrículas além da capacidade e zero duplicadas.
2. p95 da consulta de vagas abaixo de [200 ms] sob essa carga.
3. Sob sobrecarga, taxa de sucesso das matrículas aceitas ≥ [95%], com comparativo com e sem load shedding.
4. Queda de uma instância de inscrição no pico: nenhuma matrícula perdida ou duplicada e recuperação em menos de [30 s].
5. Serviço de notificação fora do ar: inscrição continua com taxa de sucesso ≥ [95%] e notificações pendentes entregues após a recuperação.

### Resultados

> TODO (Projeto 03): gráficos e métricas coletadas.

## Cronograma

| Entrega | Data | Status |
| --- | --- | --- |
| Projeto 01: grupo e tema | 09/10/2026 | Em andamento |
| Projeto 02: documentação inicial | 06/11/2026 | Pendente |
| Projeto 03: documentação final e apresentação | 11/12/2026 | Pendente |

## Ferramentas de IA utilizadas

> Seção obrigatória. A omissão desclassifica a entrega. Atualizar ao longo do projeto.

| Ferramenta | Onde atuou | Como foi orientada | O que funcionou | O que precisou ser corrigido ou foi descartado |
| --- | --- | --- | --- | --- |
| Claude | Avaliação dos padrões e rascunho da proposta de tema | [contexto fornecido: documento do projeto e material de padrões] | Ajudou na criação do documento e definição de testes | - |

## Licença e atribuições