# ---------------- Базовый образ ----------------
FROM python:3.9-slim

# ---------------- Системные зависимости ----------------
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ---------------- Установка Poetry ----------------
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"

# ---------------- Рабочая директория ----------------
WORKDIR /app

# ---------------- Копирование зависимостей ----------------
COPY pyproject.toml poetry.lock* /app/

# ---------------- Установка зависимостей ----------------
RUN poetry install --no-root --only main

# ---------------- Копирование проекта ----------------
COPY . /app

# ---------------- Переменные окружения ----------------
ENV PYTHONUNBUFFERED=1

# ---------------- Команда по умолчанию ----------------
CMD ["poetry", "run", "python", "manage.py", "runserver", "0.0.0.0:8000"]
