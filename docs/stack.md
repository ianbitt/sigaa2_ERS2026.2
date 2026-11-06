# Stack tecnológica

A stack usa **uma única linguagem (Python) em todos os serviços**, escolhida pela familiaridade da equipe, e apenas ferramentas de código aberto que rodam localmente. O foco do projeto é a arquitetura, não o aprendizado de tecnologias novas.

## Tecnologias e justificativas

| Camada | Tecnologia | Uso no sistema | Por quê | Alternativas descartadas |
| --- | --- | --- | --- | --- |
| Linguagem e framework | Python 3.12 + FastAPI | Todos os serviços | A equipe domina Python. FastAPI é assíncrono (bom para serviços que passam a maior parte do tempo esperando I/O: banco, fila, rede) e gera a documentação OpenAPI automaticamente | TypeScript/Fastify (só um integrante domina); Java/Spring e Go (a equipe não domina) |
| Mensageria | RabbitMQ 4 | Fila `matriculas.pedidos` (Competing Consumers) e exchange `matriculas.eventos` (pub/sub), com DLQs | Feito para filas de trabalho: confirmação por mensagem (ack), reentrega automática quando um worker cai e dead-letter nativo. Operação simples em um único container | Kafka (log de eventos com partições: mais pesado de operar e otimizado para replay de eventos, que não é requisito); Redis Streams (menos recursos de roteamento e DLQ) |
| Banco de dados | PostgreSQL 16 | Database `vagas` (turmas, matrículas, outbox) e database `consulta` (read model) | Transações ACID, `UPDATE` condicional atômico e restrição `UNIQUE`: a base da garantia de zero overbooking ([ADR-001](adr/0001-vagas-dono-da-escrita-de-matricula.md)) | MongoDB (modelo de documentos não traz ganho para dados relacionais com restrições); MySQL (viável, mas a equipe tem mais familiaridade com PostgreSQL) |
| Cache e estado efêmero | Redis 7 | Contadores de rate limit, chaves de idempotência e cache da Consulta (Cache-Aside) | Em memória e muito rápido; operações atômicas (`INCR`, `SET NX`) e expiração por chave (TTL), exatamente o que rate limit, idempotência e cache precisam | Memcached (sem `SET NX` com TTL nem estruturas de dados); cache em memória do processo (não é compartilhado entre instâncias) |
| Autenticação | JWT com HS256 (PyJWT) | Token emitido pelo Provedor de Identidade simulado e validado no Gateway | Validação local, sem chamada de rede por requisição; HS256 é mais barato de verificar que RS256, o que importa sob carga | Keycloak (pesado e fora do foco do projeto); RS256 (verificação mais cara) |
| Ambiente local | Docker Compose | Sobe toda a infraestrutura e os serviços com um comando | Ambiente idêntico na máquina de todos e no CI; healthchecks e ordem de inicialização declarados no próprio arquivo | Kubernetes/Minikube (complexidade desproporcional para o escopo; pode entrar no bônus de canary release) |
| CI | GitHub Actions | Lint, testes de cada serviço e subida do Compose a cada push | Integrado ao repositório e gratuito; o resultado aparece direto no commit e nos Pull Requests | GitLab CI e Jenkins (exigiriam outra plataforma ou um servidor próprio) |
| Testes de carga | k6 | Simular milhares de alunos disputando vagas (critérios 1 a 5) | Gera muita carga a partir de uma única máquina; thresholds de p95 e taxa de erro definidos no próprio script | Locust (em Python, mas gera menos carga por máquina); JMeter (configuração por interface gráfica, difícil de versionar) |
| Métricas | Prometheus + Grafana | Coleta das métricas RED (taxa, erros, duração) de todos os serviços e dashboards | Padrão de mercado e código aberto; o FastAPI expõe `/metrics` com uma biblioteca | Datadog e New Relic (pagos) |
| Tracing | OpenTelemetry + Jaeger | Rastrear um pedido passando por Gateway, Inscrição, fila e Vagas | OpenTelemetry é o padrão aberto de instrumentação; Jaeger visualiza os traces localmente | Zipkin (viável, com ecossistema menor) |
| Qualidade de código | Ruff + pytest | Lint, formatação e testes, no CI e localmente | Ruff substitui várias ferramentas (flake8, isort, black) e é muito rápido | flake8 + isort + black (três ferramentas para o mesmo resultado) |
| Diagramas | Mermaid (mermaid.live) | Diagramas C4 construídos em Mermaid e exportados como PNG, versionados em `docs/c4/` | Sintaxe simples de editar e versionar como texto, sem exigir ferramenta instalada; exportado como imagem para garantir que renderize igual em qualquer lugar (README, PDF, apresentação) | draw.io (arquivo binário, difícil de revisar em PR); Structurizr (exige ferramenta extra) |

## Bibliotecas Python previstas

| Biblioteca | Uso |
| --- | --- |
| `uvicorn` | Servidor ASGI que roda o FastAPI |
| `aio-pika` | Cliente assíncrono do RabbitMQ |
| `asyncpg` | Driver assíncrono do PostgreSQL |
| `redis` (`redis.asyncio`) | Cliente assíncrono do Redis |
| `httpx` | Chamadas HTTP entre serviços (Gateway → serviços, Inscrição → Base Acadêmica) |
| `PyJWT` | Emissão e validação dos tokens |
| `prometheus-fastapi-instrumentator` | Endpoint `/metrics` |
| `opentelemetry-*` | Instrumentação de tracing |

## Observações sobre Python

- **Nada de chamadas bloqueantes dentro de funções `async`:** usar sempre os clientes assíncronos (`asyncpg`, `aio-pika`, `redis.asyncio`, `httpx`). Uma chamada bloqueante trava o event loop e todas as requisições daquele processo.
- **Escala por processos:** o GIL limita cada processo Python a um núcleo, então a escala vem de mais workers do uvicorn ou de mais instâncias do container (`docker compose up --scale vagas=4`).