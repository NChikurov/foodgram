# Foodgram - Социальная сеть для обмена рецептами

Веб-приложение для публикации и обмена кулинарными рецептами. Пользователи могут создавать рецепты, подписываться на авторов, добавлять рецепты в избранное и формировать список покупок.

## Возможности

- Создание и публикация рецептов с фото
- Подписки на авторов
- Избранные рецепты
- Автоматический список покупок
- Фильтрация по тегам
- API для мобильных приложений

## Технологии

**Backend:** Python 3.9, Django 4.2, DRF, PostgreSQL  
**Frontend:** React 17, Node.js  
**DevOps:** Docker, Nginx, GitHub Actions

## Установка и запуск

### 1. Клонирование проекта
```bash
git clone https://github.com/username/foodgram.git
cd foodgram
```

### 2. Настройка окружения
Создайте файл `.env`:
```env
SECRET_KEY=your-secret-key
DEBUG=False
POSTGRES_DB=foodgram
POSTGRES_USER=foodgram_user
POSTGRES_PASSWORD=your-password
DB_HOST=db
DB_PORT=5432
```

### 3. Запуск приложения
```bash
# Разработка
docker-compose up -d

# Production
docker-compose -f docker-compose.production.yml up -d

# Настройка базы данных
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py load_ingredients
docker-compose exec backend python manage.py createsuperuser
```

Приложение доступно по адресу: http://localhost:8000

## API документация

- **ReDoc:** http://localhost:8000/api/docs/
- **Основные эндпоинты:**
  - `GET /api/recipes/` - список рецептов
  - `POST /api/recipes/` - создание рецепта
  - `POST /api/auth/token/login/` - получение токена
  - `GET /api/ingredients/` - список ингредиентов

## Структура проекта

```
├── backend/          # Django API
├── frontend/         # React приложение  
├── gateway/          # Nginx конфигурация
├── data/             # Фикстуры
└── docs/             # API документация
```

## Автор

[@NChikurov](https://github.com/NChikurov)