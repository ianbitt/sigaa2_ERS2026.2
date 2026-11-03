from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_responde_ok():
    resposta = client.get("/health")

    assert resposta.status_code == 200
    assert resposta.json()["status"] == "ok"


def test_metrics_exposto():
    client.get("/health")
    resposta = client.get("/metrics")

    assert resposta.status_code == 200
    assert "http_requests_total" in resposta.text
