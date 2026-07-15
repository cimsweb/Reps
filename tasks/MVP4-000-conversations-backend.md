# MVP4-000 — Conversations Backend

## Goal

Добавить backend для человеческого чата coach ↔ athlete: схема БД, домен, use cases и REST API. Отдельно от AI agent sessions (`agent_sessions`).

## Requirements

- Таблицы `conversations` и `conversation_messages` (миграция 010)
- Один тред на пару coach + athlete (unique constraint)
- Типы сообщений: `text`, `question`
- Unread через `read_at` на входящих сообщениях
- Доступ только при активной связи `coach_athlete_links`
- REST API для coach и athlete (list, messages, send, mark read)

## Acceptance Criteria

- [x] Миграция `010_mvp4_conversations.py` создана
- [x] Domain entities, repositories, use cases
- [x] HTTP routes `/coach/*` и `/athlete/*`
- [x] Unit tests + integration test
- [x] API документация `docs/api/conversations.md`
- [x] `ruff`, `mypy`, `pytest` проходят

## Dependencies

- [mvp-3.md](mvp-3.md) закрыт
- Coach-athlete links работают (MVP 1)

## Декомпозиция

```
MVP4-000 — Conversations Backend
 ├── migration + ORM models
 ├── domain + repositories
 ├── use cases (send, list, read)
 ├── HTTP API
 └── tests + docs
```

## API endpoints

| Method | Path | Role |
|--------|------|------|
| GET | `/coach/conversations` | coach |
| GET | `/athlete/conversations` | athlete |
| GET | `/coach/conversations/{id}/messages` | coach |
| GET | `/athlete/conversations/{id}/messages` | athlete |
| POST | `/coach/athletes/{athlete_id}/messages` | coach |
| POST | `/athlete/coaches/{coach_id}/messages` | athlete |
| POST | `/coach/conversations/{id}/read` | coach |
| POST | `/athlete/conversations/{id}/read` | athlete |

## Связь с UI

- [MVP4-007-chat-ai-modals.md](MVP4-007-chat-ai-modals.md) — подключить frontend к этим endpoints вместо placeholder
