# Divisão de responsabilidades

> **Status:** proposta, a confirmar com a equipe.

A divisão é por **dono de serviço**: cada integrante é responsável por implementar, testar e documentar os serviços e padrões da sua área durante todo o projeto. Decisões que afetam mais de um serviço são discutidas em conjunto e registradas em ADR.

## Responsabilidades por integrante

| Integrante | Serviços | Padrões | Responsabilidades transversais |
| --- | --- | --- | --- |
| Daniel Victor Carneiro Brandão da Costa | Inscrição, Vagas (workers) | Queue / Competing Consumers, Idempotência | Base Acadêmica simulada; transação de matrícula ([ADR-001](adr/0001-vagas-dono-da-escrita-de-matricula.md)) |
| Davi Nasiasene Amorim | Outbox Relay, Notificação | Transactional Outbox + Retry/DLQ, Circuit Breaker | Provedor de E-mail simulado; configuração do RabbitMQ (filas, exchanges, DLQs) |
| Ian Rocha Bittencourt | Gateway, Consulta | Rate Limit + Load Shedding, Bulkhead, CQRS + Cache-Aside | Provedor de Identidade simulado; CI, observabilidade (Prometheus, Grafana, Jaeger) e testes de carga (k6) |

## Entregas do Projeto 02 (06/11/2026)

| Entrega | Responsável |
| --- | --- |
| Diagrama C4 (níveis 1 e 2) | Davi e Daniel |
| ADR-001: Vagas como único dono da escrita de matrícula | Ian (revisão: todos) |
| ADR-002: Read model próprio da Consulta | Ian (revisão: todos) |
| Stack tecnológica e padrões arquiteturais | Ian |
| Setup do ambiente (Docker Compose e CI) | Ian |
| Apresentação | Todos |

## Regras de trabalho

- Toda mudança entra por **Pull Request**, revisado por pelo menos outro integrante.
- O merge só acontece com o **CI verde**.
- Decisões arquiteturais novas ou alteradas são registradas como **ADR** em `docs/adr/`.