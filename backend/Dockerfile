FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS uv
FROM python:3.13-slim

COPY --from=uv /usr/local/bin/uv /usr/local/bin/uvx /bin/
WORKDIR /app

ENV UV_PROJECT_ENVIRONMENT=/app/.venv \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-install-project

COPY src ./src
RUN uv sync --frozen --no-dev

EXPOSE 8000
CMD ["uv", "run", "--no-dev", "--no-sync", "backend"]
