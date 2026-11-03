"""Esqueleto de serviço: só /health e /metrics.

O mesmo código serve para todos os serviços. O nome vem da variável
de ambiente SERVICE_NAME, definida no docker-compose.yml.
"""

import os

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

SERVICE_NAME = os.getenv("SERVICE_NAME", "servico")

app = FastAPI(title=SERVICE_NAME)

# Expõe /metrics no formato do Prometheus (requisições, latência, erros).
Instrumentator().instrument(app).expose(app, include_in_schema=False)


@app.get("/health")
async def health() -> dict[str, str]:
    """Liveness: responde 200 se o processo está de pé.

    Mais tarde, cada serviço pode checar as próprias dependências aqui
    (PostgreSQL, Redis, RabbitMQ) e responder 503 se alguma estiver fora.
    """
    return {"status": "ok", "service": SERVICE_NAME}
