FROM python:3.14-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/apps \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    PATH="/app/.venv/bin:${PATH}"

WORKDIR /app

RUN python -m pip install --no-cache-dir --upgrade pip uv

COPY pyproject.toml uv.lock README.md ./
COPY main.py ./main.py
COPY apps ./apps

RUN uv sync --frozen --no-dev --extra production \
    && playwright install --with-deps chromium \
    && mkdir -p /app/data /app/sessions /app/logs

EXPOSE 8000

CMD ["python", "main.py", "backend", "--host", "0.0.0.0", "--port", "8000", "--no-reload", "--log-level", "info"]
