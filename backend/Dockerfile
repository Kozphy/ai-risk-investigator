FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends build-essential libpq-dev \
  && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./
COPY scripts ./scripts

RUN pip install --no-cache-dir -e .

RUN mkdir -p /data/uploads /data/knowledge /data/reports

EXPOSE 8000
CMD ["bash", "scripts/entrypoint.sh"]
