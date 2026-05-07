FROM python:3.12-slim

# Устанавливаем системные зависимости для Postgres
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем проект
COPY . .

# Открываем порт для Django
EXPOSE 8000

# По умолчанию запускаем сервер (но Docker Compose сможет это переопределить)
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app.wsgi:application"]