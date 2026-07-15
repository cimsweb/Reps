# MVP2.2-003 — Indexing

## Goal

Хранить сессии и сообщения агента; обеспечить выборку активных сессий и черновиков до подтверждения.

## Requirements

### Таблицы

- `agent_sessions` — поля из MVP2.2-001
- `agent_messages` — `session_id` FK, `role`, `content`, `metadata` JSONB, `sort_order`

### Индексы

| Index                                     | Назначение                             |
| ----------------------------------------- | -------------------------------------- |
| `agent_sessions (coach_id, status)`       | Активные сессии тренера                |
| `agent_sessions (athlete_id, status)`     | Активные сессии спортсмена             |
| `agent_sessions (planned_workout_id)`     | Одна активная report-сессия на workout |
| `agent_messages (session_id, sort_order)` | История диалога                        |

### Инварианты

- Одна **active** `report_assistance` сессия на `planned_workout_id`
- Черновик (`metadata.draft`) хранится в последнем assistant message с типом `draft`
- При `confirm` — сессия `completed`, draft не удаляется (аудит)

### Репозитории

- `AgentSessionRepository` — create, get, list_active, complete, abandon
- `AgentMessageRepository` — append, list_by_session

### Очистка

- Фоновая задача или lazy cleanup: `abandoned` сессии старше 7 дней (опционально cron script в `scripts/`, не обязателен для MVP)

## Acceptance Criteria

- [ ] Миграция применяется, FK cascade при удалении user
- [ ] Unique active report session per workout enforced
- [ ] История сообщений сохраняется в порядке
- [ ] Integration-тесты репозиториев
- [ ] `ruff`, `mypy`, `pytest` проходят

## Dependencies

- [MVP2.2-002-data-ingestion.md](MVP2.2-002-data-ingestion.md) закрыт

## Декомпозиция

```
MVP2.2-003 — Indexing
 ├── agent_sessions, agent_messages
 ├── индексы и unique active report session
 └── репозитории + cleanup policy
```
