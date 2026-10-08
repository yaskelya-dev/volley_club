FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app


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

# Весь src копируется целиком, включая:
# src/static
# src/templates
# src/api
# src/services
# и остальные модули.
COPY src ./src


# Если static или templates случайно исчезнут из Docker context,
# image не будет собран.
RUN test -f /app/src/static/css/style.css \
    && test -f /app/src/templates/base.html


RUN chown -R appuser:appuser /app

USER appuser


EXPOSE 8000


CMD ["python3", "-m", "src.main"]
