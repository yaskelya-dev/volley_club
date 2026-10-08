FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app


# Непривилегированный системный пользователь.
RUN groupadd --system appuser \
    && useradd \
        --system \
        --gid appuser \
        --create-home \
        appuser


COPY requirements.txt ./

RUN pip install \
    --no-cache-dir \
    -r requirements.txt


COPY alembic.ini ./
COPY migrations ./migrations
COPY src ./src


RUN chown -R appuser:appuser /app

USER appuser


EXPOSE 8000


# Требуемый локальный контракт:
# python3 -m src.main
#
# docker-compose переопределяет command на src.entrypoint,
# который перед запуском приложения применяет миграции.
CMD ["python3", "-m", "src.main"]
