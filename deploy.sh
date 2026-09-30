#!/bin/bash

set -e

echo "Получаем данные с гита"
git pull origin main

echo "Сборка и перезапуск Docker Compose"
docker compose up -d --build

echo "Применяем миграции"
docker compose exec -T web python manage.py migrate

echo "Собираем статику"
docker compose exec -T web python manage.py collectstatic --no-input

echo "Удаляем старые образы"
docker image prune -f

echo "Деплой прошёл успешно"
