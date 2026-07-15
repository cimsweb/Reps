# MVP2.2-001 — Project Setup

## Goal

Подготовить инфраструктуру **ИИ-агента**: абстракция провайдера, сессии диалога, промпт-шаблоны, API-контракты. Без вызовов LLM в продакшен-потоке (заглушки).

## Requirements

### Домен

- `AgentSession` — сессия диалога:
    - `id`, `kind` (`plan_creation` | `report_assistance`)
    - `coach_id` / `athlete_id`, `athlete_id` контекста для плана
    - `planned_workout_id` — для report assistance
    - `status` (`active` | `completed` | `abandoned`)
    - `created_at`, `updated_at`
- `AgentMessage` — сообщение в сессии:
    - `role` (`user` | `assistant` | `system`)
    - `content` (text)
    - `metadata` (JSON: suggested_draft_id, tool_calls — опционально)
- `TrainingPlanDraft` — черновик от агента (может ссылаться на `ParsedTrainingDraft` из MVP 2.1)
- `ReportDraft` — уже есть в MVP 2.1; переиспользовать

### AIService (infrastructure)

Интерфейс в `application/ports/ai_service.py`:

```python
class AIService(Protocol):
    async def complete(
        self,
        messages: list[ChatMessage],
        *,
        response_schema: type[BaseModel] | None = None,
    ) -> ChatCompletion: ...
```

- Реализация-заглушка `StubAIService` для тестов
- Реализация `OpenAICompatibleAIService` (или выбранный провайдер) — конфиг через `.env`:
    - `AI_API_KEY`, `AI_BASE_URL`, `AI_MODEL`

### Промпт-шаблоны (файлы в `infrastructure/ai/prompts/`)

1. **`coach_plan_system.md`** — роль тренерского ассистента:
    - знает типы run/bike/gym, зоны, раунды, разминку
    - задаёт уточняющие вопросы при неполном брифе
    - выход: JSON-схема `TrainingPlanDraft` или уточняющий вопрос (discriminated union)

2. **`athlete_report_system.md`** — роль ассистента отчёта:
    - из короткого ввода выясняет трудность, эмоции, детали
    - спрашивает про Garmin если не указан
    - не выдумывает факты

### API (документация `docs/api/training-ai.md`)

| Method | Path                                                | Назначение                    |
| ------ | --------------------------------------------------- | ----------------------------- |
| POST   | `/coach/athletes/{id}/training-plans/ai/sessions`   | Начать сессию создания плана  |
| POST   | `/coach/training-plans/ai/sessions/{id}/messages`   | Отправить сообщение / бриф    |
| GET    | `/coach/training-plans/ai/sessions/{id}`            | Состояние + последний draft   |
| POST   | `/coach/training-plans/ai/sessions/{id}/confirm`    | Сохранить draft как план      |
| POST   | `/athlete/planned-workouts/{id}/report/ai/sessions` | Начать сессию отчёта          |
| POST   | `/athlete/report/ai/sessions/{id}/messages`         | Сообщение спортсмена          |
| POST   | `/athlete/report/ai/sessions/{id}/confirm`          | Подтвердить и сохранить отчёт |

### Ограничения (зафиксировать в домене)

- Макс. **20 сообщений** на сессию
- Таймаут вызова ИИ: **30 с**
- Сессия истекает через **24 ч** без активности

### Не входит

- Реализация диалоговых use cases (MVP2.2-002)
- UI чата

## Acceptance Criteria

- [ ] Сущности AgentSession, AgentMessage в domain + миграция
- [ ] AIService port + StubAIService
- [ ] Промпт-файлы с версией в git
- [ ] `docs/api/training-ai.md` описывает контракты
- [ ] Заготовки use cases с NotImplementedError
- [ ] `ruff`, `mypy`, `pytest` проходят

## Dependencies

- [mvp-2.1.md](mvp-2.1.md) полностью закрыт (особенно ParsedTrainingDraft)

## Декомпозиция

```
MVP2.2-001 — Project Setup
 ├── AgentSession, AgentMessage
 ├── AIService port + stub
 ├── промпт-шаблоны coach / athlete
 └── docs/api/training-ai.md
```
