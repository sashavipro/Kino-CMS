# 1. Базовый образ
# Используем официальный образ Python. Тег slim-buster - это легковесный Debian.
FROM python:3.12-slim

# 2. Установка переменных окружения
# Предотвращает запись .pyc файлов
ENV PYTHONDONTWRITEBYTECODE 1
# Гарантирует, что вывод Python не будет буферизироваться
ENV PYTHONUNBUFFERED 1

# 3. Установка системных зависимостей
# postgresql-client нужен для psycopg2, netcat - для ожидания запуска БД
RUN apt-get update && apt-get install -y postgresql-client netcat-traditional

# 4. Установка рабочей директории
WORKDIR /app

# 5. Копирование и установка зависимостей Python
# Копируем только requirements.txt, чтобы Docker мог кэшировать этот слой
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# 6. Копирование всего остального кода проекта
COPY . /app/

# 7. Открываем порт, на котором будет работать Gunicorn
EXPOSE 8000

# 8. Команда по умолчанию для запуска приложения
# Мы будем запускать это через скрипт, чтобы сначала применить миграции
# CMD ["gunicorn", "Config.wsgi:application", "--bind", "0.0.0.0:8000"]