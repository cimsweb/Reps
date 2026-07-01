# Reps

## Description

Reps — AI-powered training platform connecting coaches and athletes. Coaches build structured workout plans, athletes log sessions and progress. Built-in AI analytics surfaces insights, tracks long-term trends, and generates performance reports. Clean dashboards, beautiful charts.

**Reps — платформа для тренера и спортсмена, где план превращается в прогресс.**

Инструмент для персональных тренеров по бегу, трейлу и OCR и их подопечных. Тренер составляет структурированные планы тренировок, спортсмен видит задание и фиксирует выполнение. ИИ помогает тренеру выстраивать программу и анализировать нагрузку, а спортсмену — оформлять подробные отчёты и отслеживать собственный прогресс.

**Для кого:** персональные тренеры по бегу, трейлраннеры, OCR-атлеты, беговые сообщества и клубы.

## MVP Goals

Текущий фокус — **MVP 0: авторизация и роли**.

| Цель               | Описание                               |
| ------------------ | -------------------------------------- |
| Регистрация и вход | Формы регистрации и аутентификации     |
| Роли               | Администратор, тренер, спортсмен       |
| Личные кабинеты    | Отдельный интерфейс под каждую роль    |
| Админ-панель       | Администратор видит всех пользователей |

**Критерий готовности MVP 0:** рабочая система аутентификации с разграничением прав.

Детальный чеклист — в [tasks/mvp-0.md](tasks/mvp-0.md). Общие правила разработки — в [AGENT.md](AGENT.md).

## Architecture

Проект строится по принципам DDD: зависимости направлены внутрь, domain не зависит от фреймворков.

```
src/
  domain/           # сущности, value objects, доменные сервисы
  application/      # use cases, commands, queries
  infrastructure/   # БД, API, внешние сервисы
  interfaces/       # HTTP, CLI
tests/
  unit/             # доменная логика без I/O
  integration/      # адаптеры инфраструктуры
```

- **Backend:** Python >= 3.13
- **Frontend:** React (JS/JSX), ESLint, Prettier
- **Принципы:** простота, минимум зависимостей, чистые интерфейсы

Полное описание структуры и стандартов кода — в `.cursor/rules/Python-Development-Rules.mdc`.

## Installation

### Требования

- Python >= 3.13
- Node.js >= 18
- [uv](https://docs.astral.sh/uv/) (рекомендуется) или `venv`

### Backend

```bash
# клонировать репозиторий и перейти в каталог проекта
cd Reps

# создать и активировать виртуальное окружение
uv venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# установить зависимости
uv sync --extra dev

# поднять PostgreSQL
docker compose up -d postgres

# применить миграции
cp .env.example .env
uv run alembic upgrade head

# создать admin-пользователя (логин/пароль из .env)
PYTHONPATH=src uv run python scripts/seed_admin.py
```

По умолчанию в `.env.example`:

- Email: `admin@admin.ru`
- Пароль: `123admin`

### Frontend

```bash
npm install
cd frontend && npm install
```

Или только зависимости UI:

```bash
npm --prefix frontend install
```

## Run

После установки зависимостей и миграций запустите API и frontend в отдельных терминалах.

**Важно:** backend-команды должны идти через `uv run` или активированный `.venv`. Иначе conda/base может подставить Python 3.12 и старый SQLAlchemy без `Uuid`.

```bash
# API (http://127.0.0.1:8000)
npm run dev:api

# UI (http://127.0.0.1:5173, проксирует /api → backend)
npm run dev:web
```

Эквивалент вручную:

```bash
source .venv/bin/activate
PYTHONPATH=src uvicorn interfaces.http.app:app --reload --host 127.0.0.1 --port 8000
```

Сборка frontend:

```bash
npm run build:web
```

Проверка стиля:

```bash
npm run lint
npm run format:check
```

Точка входа `python main.py` только настраивает логирование; для работы UI нужен `npm run dev:api`.

## Tests

```bash
# backend
uv run ruff check .
uv run ruff format .
uv run mypy src/ tests/
uv run pytest -m "not integration"

# интеграционные тесты (нужен PostgreSQL)
uv run pytest -m integration

# frontend
npm run lint
npm run format:check
```

Перед коммитом все проверки должны проходить без ошибок.

## Roadmap

Релизы выполняются строго по порядку.

| MVP       | Название                  | Этап        | Файл                             |
| --------- | ------------------------- | ----------- | -------------------------------- |
| **MVP 0** | Авторизация и роли        | Курс        | [tasks/mvp-0.md](tasks/mvp-0.md) |
| MVP 1     | Связка тренер ↔ спортсмен | После курса | [tasks/mvp-1.md](tasks/mvp-1.md) |
| MVP 2     | ИИ и аналитика            | Рост        | [tasks/mvp-2.md](tasks/mvp-2.md) |
| MVP 3     | Интеграции и экосистема   | Масштаб     | [tasks/mvp-3.md](tasks/mvp-3.md) |

### MVP 1 — Связка тренер ↔ спортсмен

Приглашения по email, обратная связь по тренировкам, профиль спортсмена, личные рекорды, ссылки на Garmin Connect.

### MVP 2 — ИИ и аналитика

ИИ для программ и отчётов, таблица результатов, графики динамики показателей.

### MVP 3 — Интеграции и экосистема

Автоматический импорт активностей через Garmin API, график успехов на данных с устройства.

---

License: [Apache-2.0](https://www.apache.org/licenses/LICENSE-2.0)
