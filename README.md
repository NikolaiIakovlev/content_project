# Content Project

## Описание:
Тестовый проект на Django с DRF, реализующий работу со страницами и контентом (Video, Audio, Text) с возможностью управления через админку и API. Счетчики просмотров контента увеличиваются атомарно, поддерживается фоновая обработка через Celery + Redis. 
Базовая модель контета содержит поле счетчика просмотров, которое увеличивается при каждом обращении к API. От 
нее наследуются классы для видео, аудио и текста. Так же на основании нее происходит проверка для ограничения 
типов данных которые можно добавить на страницу через связующую таблицу.

## 📦 Основные технологии

Python 3.9+

Django 4.2

Django REST Framework

DRF Spectacular (Swagger/OpenAPI)

PostgreSQL (prod) / SQLite (dev)

Celery + Redis для фоновых задач

Poetry для управления зависимостями



## ⚡ Установка через Poetry

### Клонировать проект:

git clone git@github.com:NikolaiIakovlev/content_project.git

cd content_project


### Установить Poetry (если не установлен):

pip install poetry


Установить зависимости проекта:

poetry install


#### Создать .env файл:

# .env
SECRET_KEY=super-secret-key
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

# PostgreSQL
POSTGRES_DB=content_db
POSTGRES_USER=content_user
POSTGRES_PASSWORD=superpassword
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Redis
REDIS_URL=redis://localhost:6379/0


Применить миграции:

poetry run python manage.py migrate


Создать суперпользователя:

poetry run python manage.py createsuperuser

## 🔧 Настройка PostgreSQL и Redis

### PostgreSQL:

# Создать базу и пользователя (пример)
psql -U postgres
CREATE DATABASE content_db;
CREATE USER content_user WITH PASSWORD 'superpassword';
GRANT ALL PRIVILEGES ON DATABASE content_db TO content_user;


### Redis (через Docker):

docker run -p 6379:6379 --name content-redis -d redis

## 🚀 Запуск проекта

Запуск Django сервера:

poetry run python manage.py runserver


## Запуск Celery worker:

poetry run celery -A config worker --loglevel=info


## Swagger/OpenAPI:

URL: http://127.0.0.1:8000/api/schema/ (JSON)

Swagger UI: http://127.0.0.1:8000/api/docs/

📚 API Endpoints
Метод	URL	Описание
GET	/api/pages/	Список всех страниц с пагинацией
GET	/api/pages/<id>/	Детальная информация о странице, увеличивает счетчики контента

## Пример ответа /api/pages/:

[
  {
    "id": 1,
    "title": "Page 1",
    "created_at": "2025-09-01T04:50:01.147603Z",
    "detail_url": "/api/pages/1/"
  }
]


## Пример ответа /api/pages/1/:

{
  "id": 1,
  "title": "Page 1",
  "created_at": "2025-09-01T04:50:01.147603Z",
  "contents": [
    {
      "id": 5,
      "type": "Video",
      "title": "Video 1",
      "counter": 3,
      "order": 1,
      "video_url": "https://example.com/video.mp4",
      "subtitles_url": "https://example.com/subs.srt"
    },
    {
      "id": 6,
      "type": "Audio",
      "title": "Audio 1",
      "counter": 1,
      "order": 2,
      "transcript": "Text transcript..."
    }
  ]
}

## 🧪 Тесты

Запуск автотестов через Poetry:

poetry run pytest


Минимум один положительный тест на каждый API endpoint

Проверка корректного увеличения счетчиков

💾 Статические файлы

## Для продакшена:

poetry run python manage.py collectstatic


Статические файлы будут собраны в STATIC_ROOT (staticfiles/)

## 🔒 Продакшн рекомендации

DEBUG=False

Использовать реальные домены в ALLOWED_HOSTS

Использовать HTTPS через Nginx / Gunicorn

Настроить Celery + Redis для фоновых задач

Вынести все секретные ключи в .env

## Для установки в Docker:
Соберите и запустите контейнеры:

- docker-compose up --build


 - Создайте суперпользователя:

 - docker-compose exec web poetry run python manage.py createsuperuser


 - Откройте веб-интерфейс Django:

 - http://127.0.0.1:8000/admin/
