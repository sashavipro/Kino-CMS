#!/bin/sh

# Ожидаем, пока PostgreSQL будет готов принимать соединения
echo "Waiting for postgres..."
while ! nc -z db 5432; do
  sleep 0.1
done
echo "PostgreSQL started"

# Применяем миграции
echo "Applying database migrations..."
python manage.py migrate

# Собираем статику
echo "Collecting static files..."
python manage.py collectstatic --no-input

# Запускаем Gunicorn
echo "Starting gunicorn..."
gunicorn Config.wsgi:application --bind 0.0.0.0:8000