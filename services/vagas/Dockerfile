FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /srv

# Dependências primeiro: o Docker reaproveita essa camada enquanto o
# requirements.txt não mudar, e o build fica mais rápido.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# Não rodar como root dentro do container.
RUN useradd --create-home appuser
USER appuser

EXPOSE 8000

# A imagem slim não tem curl, então o healthcheck usa o próprio Python.
HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
